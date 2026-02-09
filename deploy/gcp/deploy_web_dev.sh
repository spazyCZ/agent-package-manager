#!/usr/bin/env bash
set -euo pipefail

################################################################################
#                                                                              #
#  AAM WEB — DEV BUILD (GCP)                                                   #
#                                                                              #
################################################################################
#
# This script builds and pushes the production web container for `apps/aam-web`
# into the DEV environment using `gcloud`:
#
# - Build+push image via Cloud Build (Artifact Registry)
# - Optional: deploy to Cloud Run (public)
#
# Naming and image tags match the Pulumi dev stack:
# - Project : aamregistry
# - Region  : us-central1
# - AR Repo : aam
# - Image   : us-central1-docker.pkg.dev/aamregistry/aam/web:dev
# - Service : aam-dev-web
#
# Prerequisites:
# - `gcloud` installed and authenticated (`gcloud auth login`)
# - Permissions to:
#   - create/read Artifact Registry repo (or repo pre-created)
#   - run Cloud Build builds that push to Artifact Registry
#   - if deploying Cloud Run: deploy services and set IAM (allow unauthenticated)
#
# Usage:
# - Build and push only (safe with Pulumi-managed infra):
#     ./deploy/gcp/deploy_web_dev.sh
# - Build and push with local Docker (no Cloud Build):
#     ./deploy/gcp/deploy_web_dev.sh --local-docker
# - Build, push, and deploy ONLY the web service with gcloud:
#     ./deploy/gcp/deploy_web_dev.sh --deploy-cloud-run
#
################################################################################

PROJECT="aamregistry"
REGION="us-central1"

AR_REPO="aam"
IMAGE_NAME="web"
IMAGE_TAG="dev"

SERVICE="aam-dev-web"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${AR_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"

DEPLOY_CLOUD_RUN="0"
BUILD_METHOD="cloud-build"

for arg in "$@"; do
  case "${arg}" in
    --deploy-cloud-run)
      DEPLOY_CLOUD_RUN="1"
      ;;
    --local-docker)
      BUILD_METHOD="local-docker"
      ;;
    -h|--help)
      echo "Usage:"
      echo "  ./deploy/gcp/deploy_web_dev.sh [--local-docker] [--deploy-cloud-run]"
      exit 0
      ;;
    *)
      echo "ERROR: Unknown argument: ${arg}" >&2
      exit 2
      ;;
  esac
done

################################################################################
#                                                                              #
#  PRE-FLIGHT CHECKS                                                           #
#                                                                              #
################################################################################

if ! command -v gcloud >/dev/null 2>&1; then
  echo "ERROR: gcloud is not installed or not on PATH." >&2
  exit 1
fi

ACTIVE_ACCOUNT="$(
  gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null || true
)"
if [[ -z "${ACTIVE_ACCOUNT}" ]]; then
  echo "ERROR: No active gcloud account. Run: gcloud auth login" >&2
  exit 1
fi

echo "Building AAM web image (dev)"
echo "  project : ${PROJECT}"
echo "  region  : ${REGION}"
echo "  service : ${SERVICE}"
echo "  image   : ${IMAGE}"
echo "  method  : ${BUILD_METHOD}"
echo "  deploy  : ${DEPLOY_CLOUD_RUN}"

################################################################################
#                                                                              #
#  ARTIFACT REGISTRY (DOCKER REPO)                                             #
#                                                                              #
################################################################################

if ! gcloud artifacts repositories describe "${AR_REPO}" \
  --location="${REGION}" \
  --project="${PROJECT}" \
  >/dev/null 2>&1; then
  echo "Creating Artifact Registry repo '${AR_REPO}' in ${REGION}"
  gcloud artifacts repositories create "${AR_REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="AAM container images" \
    --project="${PROJECT}"
fi

################################################################################
#                                                                              #
#  BUILD + PUSH                                                                #
#                                                                              #
################################################################################

if [[ "${BUILD_METHOD}" == "cloud-build" ]]; then
  # Best-effort: ensure Cloud Build can push to this repo.
  # If your org manages IAM elsewhere, this may fail (and that's OK).
  PROJECT_NUMBER="$(gcloud projects describe "${PROJECT}" --format='value(projectNumber)')"
  CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

  if ! gcloud artifacts repositories add-iam-policy-binding "${AR_REPO}" \
    --location="${REGION}" \
    --member="serviceAccount:${CLOUDBUILD_SA}" \
    --role="roles/artifactregistry.writer" \
    --project="${PROJECT}" \
    >/dev/null 2>&1; then
    echo "WARNING: Could not grant Cloud Build SA Artifact Registry writer role." >&2
    echo "         Ensure '${CLOUDBUILD_SA}' has roles/artifactregistry.writer." >&2
  fi

  gcloud builds submit \
    --project="${PROJECT}" \
    --config="deploy/gcp/cloudbuild-web.yaml" \
    --substitutions="_IMAGE=${IMAGE}" \
    .
elif [[ "${BUILD_METHOD}" == "local-docker" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker is not installed or not on PATH." >&2
    exit 1
  fi

  gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

  docker build \
    -f "deploy/docker/web/Dockerfile" \
    -t "${IMAGE}" \
    .

  docker push "${IMAGE}"
else
  echo "ERROR: Unknown build method: ${BUILD_METHOD}" >&2
  exit 2
fi

if [[ "${DEPLOY_CLOUD_RUN}" != "1" ]]; then
  echo
  echo "Built and pushed image:"
  echo "  ${IMAGE}"
  echo
  echo "Next steps:"
  echo "  - If you deploy infrastructure with Pulumi, run:"
  echo "      cd deploy/pulumi"
  echo "      pulumi stack select dev"
  echo "      pulumi up"
  echo
  echo "  - If you want to deploy ONLY the web service with gcloud, run:"
  echo "      ./deploy/gcp/deploy_web_dev.sh --deploy-cloud-run"
  exit 0
fi

################################################################################
#                                                                              #
#  DEPLOY (CLOUD RUN)                                                          #
#                                                                              #
################################################################################

gcloud run deploy "${SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --allow-unauthenticated \
  --port=80 \
  --cpu=1 \
  --memory=256Mi \
  --min-instances=0 \
  --max-instances=2 \
  --set-env-vars="VITE_API_URL=/api"

WEB_URL="$(gcloud run services describe "${SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format='value(status.url)')"

echo "Deployed web service:"
echo "  ${WEB_URL}"
echo
echo "Verify:"
echo "  curl -fsS \"${WEB_URL}/health\" && echo"

