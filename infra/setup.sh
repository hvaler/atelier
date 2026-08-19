#!/usr/bin/env bash
# ==============================================================================
# Setup script for Atelier GCP infrastructure
# Usage: ./infra/setup.sh [PROJECT_ID] [REGION]
#
# Idempotent: every step checks before it creates, so running it twice is safe.
#
# This script used to stop after enabling APIs and creating a bucket. It never created the two
# service accounts `deploy.sh` requires, granted no IAM at all, and enabled the Eventarc and
# Cloud Scheduler APIs without creating either resource — both of those existed in the live
# project only because somebody typed them once. A clean-room `setup.sh && deploy.sh` failed on
# a missing service account, which meant the infrastructure was hand-built and these scripts
# were decoration.
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project)}"
# europe-west1, matching deploy.sh. These disagreed — setup.sh said west3, deploy.sh said west1 —
# so a fresh run created an Artifact Registry in one region and pushed to another.
REGION="${2:-europe-west1}"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: Project ID not specified and no default project set in gcloud."
  exit 1
fi

AGENT_SA="sa-atelier-agent@${PROJECT_ID}.iam.gserviceaccount.com"
EVENTARC_SA="sa-eventarc@${PROJECT_ID}.iam.gserviceaccount.com"
INBOX_BUCKET="atelier-hack-inbox"

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
echo "💾 Initializing Firestore (eur3)..."
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

# 5. Create the private GCS inbox
# One name, everywhere. It appeared as atelier-inbox, atelier-inbox-$PROJECT_ID and
# atelier-hack-inbox across code, scripts and docs; only the last one exists.
echo "🪣 Creating private GCS bucket '$INBOX_BUCKET'..."
if ! gcloud storage buckets describe "gs://${INBOX_BUCKET}" &>/dev/null; then
  gcloud storage buckets create "gs://${INBOX_BUCKET}" \
    --location="$REGION" \
    --uniform-bucket-level-access
  echo "✅ GCS inbox bucket created."
else
  echo "✅ GCS inbox bucket already exists."
fi

# 6. Runtime identities
# deploy.sh passes --service-account for both services and fails without these.
echo "👤 Creating runtime service accounts..."
create_sa() {
  local name="$1" display="$2"
  if ! gcloud iam service-accounts describe "${name}@${PROJECT_ID}.iam.gserviceaccount.com" &>/dev/null; then
    gcloud iam service-accounts create "$name" --display-name="$display"
    echo "   ✅ ${name} created."
  else
    echo "   ✅ ${name} already exists."
  fi
}
create_sa "sa-atelier-agent" "Atelier Agent (Cloud Run)"
create_sa "sa-atelier-web"   "Atelier Web (Cloud Run)"
create_sa "sa-eventarc"      "Eventarc delivery to atelier-agent"

# 7. Least privilege, stated rather than assumed
# The agent calls Vertex AI, writes student history to Firestore, reads uploaded drawings from
# the bucket, and reads one secret. The web service gets nothing: it only talks HTTP to the agent.
echo "🔐 Granting IAM roles..."
grant() {
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$1" --role="$2" --condition=None --quiet >/dev/null
  echo "   ✅ $2 -> ${1%%@*}"
}
grant "$AGENT_SA"    "roles/aiplatform.user"
grant "$AGENT_SA"    "roles/datastore.user"
grant "$AGENT_SA"    "roles/storage.objectUser"
grant "$EVENTARC_SA" "roles/eventarc.eventReceiver"
grant "$EVENTARC_SA" "roles/run.invoker"

# The Cloud Storage service agent must be able to publish to Pub/Sub for Eventarc to deliver
# object-finalized events at all. Missing this is the classic silent Eventarc failure.
# tr, because this command prints a leading blank line and the IAM binding would be
# rejected for a malformed member — a failure that only appears on a fresh project.
GCS_SA="$(gcloud storage service-agent --project="$PROJECT_ID" | tr -d '[:space:]')"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${GCS_SA}" --role="roles/pubsub.publisher" --condition=None --quiet >/dev/null
echo "   ✅ roles/pubsub.publisher -> Cloud Storage service agent"

# 8. The Gemini API key, for the Gemma router
# Gemma is not a publisher model on Vertex AI, so the router reaches it through the Gemini API,
# which authenticates with a key rather than ADC. The value is NOT in this repository: create the
# key in AI Studio and pipe it in without it ever touching a terminal history:
#
#   gcloud services api-keys get-key-string <KEY_ID> --format='value(keyString)' \
#     | gcloud secrets create gemini-api-key --data-file=- --project="$PROJECT_ID"
#
echo "🔑 Checking the gemini-api-key secret..."
if gcloud secrets describe gemini-api-key --project="$PROJECT_ID" &>/dev/null; then
  gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:${AGENT_SA}" --role=roles/secretmanager.secretAccessor \
    --project="$PROJECT_ID" --quiet >/dev/null
  echo "   ✅ secret exists and the agent may read it."
else
  echo "   ⚠️  gemini-api-key does not exist. The Gemma router will fall back to the profile"
  echo "      level and label itself 'fallback' until you create it (see the comment above)."
fi

# 9. Eventarc: a drawing dropped in the bucket runs the whole pipeline
echo "⚡ Creating the Eventarc trigger..."
if ! gcloud eventarc triggers describe gcs-inbox-trigger --location="$REGION" &>/dev/null; then
  gcloud eventarc triggers create gcs-inbox-trigger \
    --location="$REGION" \
    --destination-run-service=atelier-agent \
    --destination-run-region="$REGION" \
    --destination-run-path="/api/async/gcs-upload" \
    --event-filters="type=google.cloud.storage.object.v1.finalized" \
    --event-filters="bucket=${INBOX_BUCKET}" \
    --service-account="$EVENTARC_SA"
  echo "   ✅ Trigger created."
else
  echo "   ✅ Trigger already exists."
fi

# 10. Cloud Scheduler: the weekly digest, Mondays at 09:00 UTC
echo "📅 Creating the weekly digest schedule..."
if ! gcloud scheduler jobs describe weekly-digest-job --location="$REGION" &>/dev/null; then
  AGENT_URL="$(gcloud run services describe atelier-agent --region="$REGION" \
    --format='value(status.url)' 2>/dev/null || true)"
  if [ -z "$AGENT_URL" ]; then
    echo "   ⚠️  atelier-agent is not deployed yet; run ./infra/deploy.sh first, then re-run this."
  else
    gcloud scheduler jobs create http weekly-digest-job \
      --location="$REGION" \
      --schedule="0 9 * * 1" \
      --time-zone="UTC" \
      --uri="${AGENT_URL}/api/digest/weekly" \
      --http-method=POST
    echo "   ✅ weekly-digest-job created."
  fi
else
  echo "   ✅ weekly-digest-job already exists."
fi

echo ""
echo "🎉 Setup complete."
echo "   Next: ./infra/deploy.sh ${PROJECT_ID} ${REGION}"
echo ""
echo "   Not validated against a fresh project. This reproduces what the live project contains,"
echo "   step by step, but nobody has yet run it end to end on an empty one — see the known"
echo "   limitations in README.md rather than assuming otherwise."
