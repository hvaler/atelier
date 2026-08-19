#!/usr/bin/env bash
# ==============================================================================
# Setup script for Atelier GCP infrastructure
# Usage: ./infra/setup.sh [PROJECT_ID] [REGION]
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project)}"
REGION="${2:-europe-west3}"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: Project ID not specified and no default project set in gcloud."
  exit 1
fi

echo "🚀 Setting up GCP infrastructure for Atelier..."
echo "   Project: $PROJECT_ID"
echo "   Region:  $REGION"

# 1. Set current project
gcloud config set project "$PROJECT_ID"

# 2. Enable Required APIs
echo "📦 Enabling required Google Cloud APIs..."
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  eventarc.googleapis.com \
  cloudscheduler.googleapis.com \
  pubsub.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  iam.googleapis.com

# 3. Create Firestore database if not exists
echo "💾 Initializing Firestore in $REGION (eur3)..."
if ! gcloud firestore databases list --format="value(name)" | grep -q "projects/$PROJECT_ID/databases/(default)"; then
  gcloud firestore databases create --location=eur3
  echo "✅ Firestore (default) database created."
else
  echo "✅ Firestore database already exists."
fi

# 4. Create Artifact Registry repository for containers
echo "🐳 Creating Artifact Registry repository 'atelier-repo'..."
if ! gcloud artifacts repositories describe atelier-repo --location="$REGION" &>/dev/null; then
  gcloud artifacts repositories create atelier-repo \
    --repository-format=docker \
    --location="$REGION" \
    --description="Docker repository for Atelier services"
  echo "✅ Artifact Registry repository created."
else
  echo "✅ Artifact Registry repository already exists."
fi

# 5. Create GCS buckets
# One name, everywhere. It appeared as atelier-inbox, atelier-inbox-$PROJECT_ID and
# atelier-hack-inbox across code, scripts and docs; only the last one exists.
INBOX_BUCKET="atelier-hack-inbox"
echo "🪣 Creating private GCS bucket '$INBOX_BUCKET'..."
if ! gcloud storage buckets describe "gs://${INBOX_BUCKET}" &>/dev/null; then
  gcloud storage buckets create "gs://${INBOX_BUCKET}" \
    --location="$REGION" \
    --uniform-bucket-level-access
  echo "✅ GCS inbox bucket created."
else
  echo "✅ GCS inbox bucket already exists."
fi

echo "🎉 Setup complete! All services, APIs, and buckets are ready."
