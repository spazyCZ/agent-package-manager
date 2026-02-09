#!/usr/bin/env bash
set -euo pipefail

################################################################################
#                                                                              #
#  AAM DOCS — DEPLOY TO GCP (CLOUD STORAGE)                                   #
#                                                                              #
################################################################################
#
# Builds the MkDocs documentation site and deploys it to a Google Cloud Storage
# bucket configured for static website hosting.
#
# Architecture:
#   docs/user_docs/ ──(mkdocs build)──▸ site/ ──(gsutil rsync)──▸ GCS bucket
#
# The bucket is configured for:
#   - Static website serving (index.html / 404.html)
#   - Public read access (allUsers objectViewer)
#   - Optional: place behind Cloud CDN / Global HTTPS LB for custom domain
#
# Defaults (match the rest of the AAM GCP infra):
#   - Project : aamregistry
#   - Region  : us-central1
#   - Bucket  : aam-docs-dev  (override with --bucket)
#
# Prerequisites:
#   - `gcloud` installed and authenticated (`gcloud auth login`)
#   - Python 3.11+ with MkDocs dependencies installed (or --install flag)
#   - Permissions:
#       storage.buckets.create (first run only)
#       storage.objects.create / delete
#       storage.buckets.setIamPolicy (first run, for public access)
#
# Usage:
#   ./deploy/gcp/deploy_docs.sh                         # Build + deploy (dev)
#   ./deploy/gcp/deploy_docs.sh --bucket aam-docs-prod  # Custom bucket name
#   ./deploy/gcp/deploy_docs.sh --install               # Install MkDocs first
#   ./deploy/gcp/deploy_docs.sh --build-only            # Build without deploy
#   ./deploy/gcp/deploy_docs.sh --dry-run               # Show what would sync
#
################################################################################

PROJECT="aamregistry"
REGION="us-central1"
BUCKET="aam-docs-dev"

INSTALL_DEPS="0"
BUILD_ONLY="0"
DRY_RUN="0"

# -----
# Resolve monorepo root (script lives at deploy/gcp/)
# -----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DOCS_DIR="${REPO_ROOT}/docs/user_docs"
SITE_DIR="${DOCS_DIR}/site"
REQUIREMENTS="${DOCS_DIR}/requirements-docs.txt"

################################################################################
#                                                                              #
#  ARGUMENT PARSING                                                            #
#                                                                              #
################################################################################

for arg in "$@"; do
  case "${arg}" in
    --bucket=*)
      BUCKET="${arg#*=}"
      ;;
    --bucket)
      echo "ERROR: --bucket requires a value (e.g. --bucket=aam-docs-prod)" >&2
      exit 2
      ;;
    --install)
      INSTALL_DEPS="1"
      ;;
    --build-only)
      BUILD_ONLY="1"
      ;;
    --dry-run)
      DRY_RUN="1"
      ;;
    -h|--help)
      echo "Usage:"
      echo "  ./deploy/gcp/deploy_docs.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --bucket=NAME   GCS bucket name (default: aam-docs-dev)"
      echo "  --install       Install MkDocs Python dependencies first"
      echo "  --build-only    Build site locally without deploying to GCS"
      echo "  --dry-run       Show what gsutil would sync (no writes)"
      echo "  -h, --help      Show this help message"
      exit 0
      ;;
    *)
      echo "ERROR: Unknown argument: ${arg}" >&2
      exit 2
      ;;
  esac
done

BUCKET_URL="gs://${BUCKET}"
PUBLIC_URL="https://storage.googleapis.com/${BUCKET}/index.html"

echo "AAM Docs deployment"
echo "  project  : ${PROJECT}"
echo "  bucket   : ${BUCKET}"
echo "  docs_dir : ${DOCS_DIR}"
echo "  install  : ${INSTALL_DEPS}"
echo "  build_only: ${BUILD_ONLY}"
echo "  dry_run  : ${DRY_RUN}"
echo ""

################################################################################
#                                                                              #
#  PRE-FLIGHT CHECKS                                                           #
#                                                                              #
################################################################################

# -----
# Verify gcloud is available and authenticated
# -----
if [[ "${BUILD_ONLY}" == "0" ]]; then
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
  echo "Authenticated as: ${ACTIVE_ACCOUNT}"
fi

# -----
# Verify Python and mkdocs are available
# -----
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is not installed or not on PATH." >&2
  exit 1
fi

################################################################################
#                                                                              #
#  INSTALL MKDOCS DEPENDENCIES (OPTIONAL)                                      #
#                                                                              #
################################################################################

if [[ "${INSTALL_DEPS}" == "1" ]]; then
  echo "Installing MkDocs dependencies from ${REQUIREMENTS}..."

  if [[ -f "${REPO_ROOT}/.venv/bin/activate" ]]; then
    # Use existing project venv if available
    # shellcheck disable=SC1091
    source "${REPO_ROOT}/.venv/bin/activate"
  fi

  pip install -r "${REQUIREMENTS}"
  echo "Dependencies installed."
  echo ""
fi

# -----
# Verify mkdocs command is available after optional install
# -----
if ! command -v mkdocs >/dev/null 2>&1; then
  echo "ERROR: mkdocs is not on PATH." >&2
  echo "       Run with --install flag, or activate your venv first:" >&2
  echo "       source .venv/bin/activate" >&2
  exit 1
fi

################################################################################
#                                                                              #
#  BUILD MKDOCS SITE                                                           #
#                                                                              #
################################################################################

echo "Building MkDocs site (strict mode)..."
cd "${DOCS_DIR}"
mkdocs build --strict
echo "Site built: ${SITE_DIR}"
echo ""

# -----
# Count output files for the summary
# -----
FILE_COUNT="$(find "${SITE_DIR}" -type f | wc -l | tr -d ' ')"
SITE_SIZE="$(du -sh "${SITE_DIR}" | cut -f1)"
echo "  files : ${FILE_COUNT}"
echo "  size  : ${SITE_SIZE}"
echo ""

if [[ "${BUILD_ONLY}" == "1" ]]; then
  echo "Build complete (--build-only). Site is at:"
  echo "  ${SITE_DIR}"
  exit 0
fi

################################################################################
#                                                                              #
#  GCS BUCKET SETUP                                                            #
#                                                                              #
################################################################################

# -----
# Create the bucket if it does not exist
# -----
if ! gcloud storage buckets describe "${BUCKET_URL}" \
  --project="${PROJECT}" >/dev/null 2>&1; then

  echo "Creating GCS bucket '${BUCKET}' in ${REGION}..."
  gcloud storage buckets create "${BUCKET_URL}" \
    --project="${PROJECT}" \
    --location="${REGION}" \
    --uniform-bucket-level-access \
    --public-access-prevention=inherited

  # -----
  # Configure static website serving
  # -----
  echo "Configuring bucket for static website hosting..."
  gcloud storage buckets update "${BUCKET_URL}" \
    --web-main-page-suffix=index.html \
    --web-error-page=404.html

  # -----
  # Grant public read access (allUsers as objectViewer)
  # -----
  echo "Granting public read access..."
  gcloud storage buckets add-iam-policy-binding "${BUCKET_URL}" \
    --member=allUsers \
    --role=roles/storage.objectViewer

  echo "Bucket '${BUCKET}' created and configured."
  echo ""
else
  echo "Bucket '${BUCKET}' already exists."
  echo ""
fi

################################################################################
#                                                                              #
#  UPLOAD SITE TO GCS                                                          #
#                                                                              #
################################################################################

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "Dry run — showing what would be synced:"
  echo ""
  gcloud storage rsync "${SITE_DIR}" "${BUCKET_URL}" \
    --recursive \
    --delete-unmatched-destination-objects \
    --dry-run
  echo ""
  echo "No changes were made (--dry-run)."
  exit 0
fi

echo "Uploading site to ${BUCKET_URL}..."
gcloud storage rsync "${SITE_DIR}" "${BUCKET_URL}" \
  --recursive \
  --delete-unmatched-destination-objects \
  --cache-control="public, max-age=300"

################################################################################
#                                                                              #
#  SET CACHE HEADERS FOR HTML FILES                                            #
#                                                                              #
################################################################################

# -----
# HTML files get a shorter cache TTL so updates are picked up quickly.
# Static assets (CSS/JS/images) keep the default 5-minute cache.
# -----
echo "Setting short cache TTL on HTML files..."
gcloud storage objects update "${BUCKET_URL}/**/*.html" \
  --cache-control="public, max-age=60" 2>/dev/null || true

################################################################################
#                                                                              #
#  SUMMARY                                                                     #
#                                                                              #
################################################################################

echo ""
echo "Docs deployed successfully!"
echo ""
echo "  Bucket  : ${BUCKET_URL}"
echo "  URL     : ${PUBLIC_URL}"
echo "  Files   : ${FILE_COUNT}"
echo "  Size    : ${SITE_SIZE}"
echo ""
echo "Direct URL (GCS static hosting):"
echo "  https://storage.googleapis.com/${BUCKET}/index.html"
echo ""
echo "If you have a load balancer with a custom domain, the docs are"
echo "served from the bucket backend. Update the URL map to route"
echo "/docs/* to this bucket if not already configured."
echo ""
echo "Verify:"
echo "  curl -fsS \"https://storage.googleapis.com/${BUCKET}/index.html\" | head -5"
