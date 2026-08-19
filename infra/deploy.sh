#!/usr/bin/env bash
# ==============================================================================
# Deployment script for Atelier services to Google Cloud Run
# Usage: ./infra/deploy.sh [PROJECT_ID] [REGION]
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project)}"
REGION="${2:-europe-west1}"

# Where the *model* lives, which is not where the *service* lives. `gemini-3.5-flash` is not
# published in europe-west1: pointing Vertex at the Cloud Run region made every critique in
# production return 404 and fall silently into the deterministic template. Overridable, but it
# must never again be derived from ${REGION}.
GEMINI_REGION="${3:-europe-west3}"
REPO_NAME="atelier-repo"
TAG="$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')"

echo "🚀 Deploying Atelier services to Cloud Run..."
echo "   Project: $PROJECT_ID | Region: $REGION | Tag: $TAG"

# 1. Build and push atelier-agent
echo "📦 Building & Pushing atelier-agent container..."
AGENT_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/atelier-agent:${TAG}"
docker build -t "$AGENT_IMAGE" -f infra/Dockerfile.agent .
docker push "$AGENT_IMAGE"

# 2. Deploy atelier-agent to Cloud Run (TEC-010: first deploy direct, subsequent via tagged candidate + smoke test)
echo "🚀 Deploying atelier-agent service..."
AGENT_EXISTS=$(gcloud run services list --platform=managed --region="$REGION" --project="$PROJECT_ID" --filter="metadata.name=atelier-agent" --format="value(metadata.name)" || true)

if [ -z "$AGENT_EXISTS" ]; then
  echo "   [First Deploy] Deploying atelier-agent with 100% traffic..."
  gcloud run deploy atelier-agent \
    --image="$AGENT_IMAGE" \
    --platform=managed \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --service-account="sa-atelier-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=5 \
    --memory=1Gi \
    --cpu=1 \
    --set-env-vars="ENVIRONMENT=production,GCP_PROJECT=${PROJECT_ID},GCP_LOCATION=${REGION},GEMINI_LOCATION=${GEMINI_REGION},MEMORY_BACKEND=firestore" \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
else
  echo "   [Subsequent Deploy] Deploying candidate revision for smoke test..."
  gcloud run deploy atelier-agent \
    --image="$AGENT_IMAGE" \
    --platform=managed \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --service-account="sa-atelier-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --no-traffic \
    --tag="candidate" \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=5 \
    --memory=1Gi \
    --cpu=1 \
    --set-env-vars="ENVIRONMENT=production,GCP_PROJECT=${PROJECT_ID},GCP_LOCATION=${REGION},GEMINI_LOCATION=${GEMINI_REGION},MEMORY_BACKEND=firestore" \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"

  # The candidate URL is the service host with the tag prefixed, which Cloud Run reports
  # itself. This used to prepend "candidate---atelier-agent-" to a value that already
  # contained the service name, producing candidate---atelier-agent-atelier-agent-... and a
  # 404 that aborted every promotion. The gate was right to abort; it was reading the wrong door.
  CANDIDATE_AGENT_URL="https://candidate---$(gcloud run services describe atelier-agent --region="$REGION" --project="$PROJECT_ID" --format='value(status.address.url)' | sed 's|https://||')"
  echo "🧪 Running smoke test on candidate: ${CANDIDATE_AGENT_URL}/api/health..."
  SMOKE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${CANDIDATE_AGENT_URL}/api/health" || echo "000")
  if [ "$SMOKE_CODE" != "200" ]; then
    echo "❌ Smoke test failed on atelier-agent candidate (HTTP $SMOKE_CODE). Aborting traffic promotion."
    exit 1
  fi
  echo "✅ Smoke test passed! Promoting traffic to latest revision..."
  gcloud run services update-traffic atelier-agent --region="$REGION" --project="$PROJECT_ID" --to-latest
fi

AGENT_URL=$(gcloud run services describe atelier-agent --platform=managed --region="$REGION" --project="$PROJECT_ID" --format='value(status.url)')
echo "✅ atelier-agent active at: $AGENT_URL"

# 3. Build and push Atelier.Web
echo "📦 Building & Pushing Atelier.Web container..."
WEB_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/atelier-web:${TAG}"
docker build -t "$WEB_IMAGE" --build-arg "AGENT_URL=${AGENT_URL}" -f infra/Dockerfile.web .
docker push "$WEB_IMAGE"

# 4. Deploy Atelier.Web to Cloud Run (TEC-010)
echo "🚀 Deploying Atelier.Web service..."
WEB_EXISTS=$(gcloud run services list --platform=managed --region="$REGION" --project="$PROJECT_ID" --filter="metadata.name=atelier-web" --format="value(metadata.name)" || true)

if [ -z "$WEB_EXISTS" ]; then
  echo "   [First Deploy] Deploying atelier-web with 100% traffic..."
  gcloud run deploy atelier-web \
    --image="$WEB_IMAGE" \
    --platform=managed \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --service-account="sa-atelier-web@${PROJECT_ID}.iam.gserviceaccount.com" \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=5 \
    --memory=512Mi \
    --cpu=1 \
    --set-env-vars="ASPNETCORE_ENVIRONMENT=Production,Agent__BaseUrl=${AGENT_URL}"
else
  echo "   [Subsequent Deploy] Deploying candidate revision for smoke test..."
  gcloud run deploy atelier-web \
    --image="$WEB_IMAGE" \
    --platform=managed \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --service-account="sa-atelier-web@${PROJECT_ID}.iam.gserviceaccount.com" \
    --no-traffic \
    --tag="candidate" \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=5 \
    --memory=512Mi \
    --cpu=1 \
    --set-env-vars="ASPNETCORE_ENVIRONMENT=Production,Agent__BaseUrl=${AGENT_URL}"

  # The candidate URL is the service host with the tag prefixed, which Cloud Run reports
  # itself. This used to prepend "candidate---atelier-web-" to a value that already
  # contained the service name, producing candidate---atelier-web-atelier-web-... and a
  # 404 that aborted every promotion. The gate was right to abort; it was reading the wrong door.
  CANDIDATE_WEB_URL="https://candidate---$(gcloud run services describe atelier-web --region="$REGION" --project="$PROJECT_ID" --format='value(status.address.url)' | sed 's|https://||')"
  echo "🧪 Running smoke test on candidate: ${CANDIDATE_WEB_URL}/api/health..."
  SMOKE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${CANDIDATE_WEB_URL}/api/health" || echo "000")
  if [ "$SMOKE_CODE" != "200" ]; then
    echo "❌ Smoke test failed on atelier-web candidate (HTTP $SMOKE_CODE). Aborting traffic promotion."
    exit 1
  fi
  echo "✅ Smoke test passed! Promoting traffic to latest revision..."
  gcloud run services update-traffic atelier-web --region="$REGION" --project="$PROJECT_ID" --to-latest
fi

WEB_URL=$(gcloud run services describe atelier-web --platform=managed --region="$REGION" --project="$PROJECT_ID" --format='value(status.url)')
echo "🎉 Deployment complete!"
echo "🌐 Atelier Web UI: $WEB_URL"
echo "🤖 Atelier Agent:  $AGENT_URL"
