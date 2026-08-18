#!/usr/bin/env bash
# ==============================================================================
# Deployment script for Atelier services to Google Cloud Run
# Usage: ./infra/deploy.sh [PROJECT_ID] [REGION]
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project)}"
REGION="${2:-europe-west3}"
REPO_NAME="atelier-repo"
TAG="$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')"

echo "🚀 Deploying Atelier services to Cloud Run..."
echo "   Project: $PROJECT_ID | Region: $REGION | Tag: $TAG"

# 1. Build and push atelier-agent
echo "📦 Building & Pushing atelier-agent container..."
AGENT_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/atelier-agent:${TAG}"
docker build -t "$AGENT_IMAGE" -f infra/Dockerfile.agent .
docker push "$AGENT_IMAGE"

# 2. Deploy atelier-agent to Cloud Run
echo "🚀 Deploying atelier-agent service..."
gcloud run deploy atelier-agent \
  --image="$AGENT_IMAGE" \
  --platform=managed \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=5 \
  --memory=1Gi \
  --cpu=1 \
  --set-env-vars="ENVIRONMENT=production,GCP_PROJECT=${PROJECT_ID},GCP_LOCATION=${REGION}"

AGENT_URL=$(gcloud run services describe atelier-agent --platform=managed --region="$REGION" --format='value(status.url)')
echo "✅ atelier-agent deployed at: $AGENT_URL"

# 3. Build and push Atelier.Web
echo "📦 Building & Pushing Atelier.Web container..."
WEB_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/atelier-web:${TAG}"
docker build -t "$WEB_IMAGE" --build-arg "AGENT_URL=${AGENT_URL}" -f infra/Dockerfile.web .
docker push "$WEB_IMAGE"

# 4. Deploy Atelier.Web to Cloud Run
echo "🚀 Deploying Atelier.Web service..."
gcloud run deploy atelier-web \
  --image="$WEB_IMAGE" \
  --platform=managed \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=5 \
  --memory=512Mi \
  --cpu=1 \
  --set-env-vars="ASPNETCORE_ENVIRONMENT=Production,Agent__BaseUrl=${AGENT_URL}"

WEB_URL=$(gcloud run services describe atelier-web --platform=managed --region="$REGION" --format='value(status.url)')
echo "🎉 Deployment complete!"
echo "🌐 Atelier Web UI: $WEB_URL"
echo "🤖 Atelier Agent:  $AGENT_URL"
