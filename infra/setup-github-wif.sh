#!/usr/bin/env bash
# ==============================================================================
# Setup Workload Identity Federation (WIF) for GitHub Actions
# Usage: ./infra/setup-github-wif.sh [PROJECT_ID] [GITHUB_REPO]
# Example: ./infra/setup-github-wif.sh atelier-hack hvaler/atelier
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project)}"
GITHUB_REPO="${2:-hvaler/atelier}"
POOL_NAME="github-pool"
PROVIDER_NAME="github-provider"
SA_NAME="github-deployer"

echo "🔐 Setting up Workload Identity Federation for GitHub Actions..."
echo "   Project: $PROJECT_ID | Repo: $GITHUB_REPO"

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

# 1. Create Workload Identity Pool if not exists
if ! gcloud iam workload-identity-pools describe "$POOL_NAME" --location="global" &>/dev/null; then
  gcloud iam workload-identity-pools create "$POOL_NAME" \
    --project="$PROJECT_ID" \
    --location="global" \
    --display-name="GitHub Actions Pool"
  echo "✅ Workload Identity Pool created."
else
  echo "✅ Workload Identity Pool already exists."
fi

# 2. Create OIDC Provider if not exists
if ! gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
    --workload-identity-pool="$POOL_NAME" \
    --location="global" &>/dev/null; then
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
    --project="$PROJECT_ID" \
    --location="global" \
    --workload-identity-pool="$POOL_NAME" \
    --display-name="GitHub Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"
  echo "✅ OIDC Provider created."
else
  echo "✅ OIDC Provider already exists."
fi

# 3. Create Service Account for GitHub Actions deployment
if ! gcloud iam service-accounts describe "${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" &>/dev/null; then
  gcloud iam service-accounts create "$SA_NAME" \
    --project="$PROJECT_ID" \
    --display-name="GitHub Actions Deployer SA"
  echo "✅ Service Account created."
else
  echo "✅ Service Account already exists."
fi

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# 4. Assign least-privilege roles to Service Account
ROLES=(
  "roles/run.admin"
  "roles/artifactregistry.writer"
  "roles/iam.serviceAccountUser"
  "roles/storage.admin"
)

for role in "${ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$role" \
    --condition=None --quiet
done

# 5. Bind GitHub Repo to Service Account via WIF
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${GITHUB_REPO}" \
  --quiet

WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"

echo ""
echo "🎉 WIF setup complete! Add these values to GitHub Repository Secrets/Variables:"
echo "--------------------------------------------------------------------------------"
echo "WIF_PROVIDER: $WIF_PROVIDER"
echo "WIF_SERVICE_ACCOUNT: $SA_EMAIL"
echo "GCP_PROJECT: $PROJECT_ID"
echo "--------------------------------------------------------------------------------"
