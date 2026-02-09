# AAM Deployment

This directory contains everything needed to deploy AAM locally (Docker Compose)
and to Google Cloud Platform (Pulumi IaC, with optional `gcloud` helpers).

## Directory Structure

```
deploy/
├── local/                    # Local Docker Compose deployment
│   ├── docker-compose.yml    # Base compose (all services)
│   ├── docker-compose.dev.yml# Dev overrides (hot reload, debug)
│   ├── .env.example          # Environment variable template
│   ├── init-db.sql           # PostgreSQL initialization script
│   ├── nginx/                # Nginx configuration files
│   │   ├── nginx.conf        # Reverse proxy config
│   │   └── nginx-web.conf    # Web SPA serving config
│   ├── ssl/                  # SSL certificates (local testing)
│   └── README.md             # Local deployment guide
│
├── docker/                   # Dockerfiles (shared by local & cloud)
│   ├── backend/
│   │   ├── Dockerfile        # Production (multi-stage)
│   │   └── Dockerfile.dev    # Development (hot reload)
│   └── web/
│       ├── Dockerfile        # Production (multi-stage → Nginx)
│       └── Dockerfile.dev    # Development (Vite HMR)
│
├── gcp/                      # Optional `gcloud` helpers (GCP)
│   ├── README.md             # gcloud-based build and deploy helpers
│   ├── cloudbuild-web.yaml   # Cloud Build config for web image
│   ├── deploy_web_dev.sh     # Build web image (optional Cloud Run deploy)
│   └── deploy_docs.sh        # Build & deploy MkDocs to GCS bucket
│
├── pulumi/                   # Pulumi IaC for Google Cloud
│   ├── Pulumi.yaml           # Pulumi project config
│   ├── Pulumi.dev.yaml       # Dev stack config
│   ├── Pulumi.test.yaml      # Test stack config
│   ├── Pulumi.prod.yaml      # Prod stack config
│   ├── __main__.py           # Entry point — provisions all resources
│   ├── config.py             # Typed stack configuration loader
│   ├── requirements.txt      # Python dependencies (pulumi, pulumi-gcp)
│   ├── components/           # Reusable ComponentResource modules
│   │   ├── network.py        # VPC, subnets, VPC connector
│   │   ├── database.py       # Cloud SQL (PostgreSQL 16)
│   │   ├── cache.py          # Memorystore (Redis 7)
│   │   ├── storage.py        # GCS bucket (package archives)
│   │   ├── registry.py       # Artifact Registry (Docker images)
│   │   ├── secrets.py        # Secret Manager
│   │   ├── backend_service.py# Cloud Run (FastAPI backend)
│   │   ├── web_service.py    # Cloud Run (React web frontend)
│   │   ├── load_balancer.py  # Global HTTPS Load Balancer
│   │   └── monitoring.py     # Uptime checks & alerting
│   └── README.md             # Pulumi deployment guide
│
└── README.md                 # This file
```

## Deployment Targets

### Local Development

Run the full stack locally using Docker Compose.

```bash
# Quick start (dev mode with hot reload)
cp deploy/local/.env.example deploy/local/.env
docker compose -f deploy/local/docker-compose.yml \
  -f deploy/local/docker-compose.dev.yml up -d
```

See [local/README.md](local/README.md) for full instructions.

### Google Cloud Platform

Deploy to GCP using Pulumi across three environments:

| Environment | Stack Config         | Trigger                        |
|-------------|----------------------|--------------------------------|
| **dev**     | `Pulumi.dev.yaml`    | Feature branches               |
| **test**    | `Pulumi.test.yaml`   | `develop` / release candidates |
| **prod**    | `Pulumi.prod.yaml`   | `main` / tagged releases       |

```bash
cd deploy/pulumi
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

pulumi stack select dev
pulumi up
```

Pulumi references container images in Artifact Registry. If you want to build
and push the dev web image (`apps/aam-web`) with `gcloud`, run:

```bash
./deploy/gcp/deploy_web_dev.sh
```

See [pulumi/README.md](pulumi/README.md) for full instructions.

### Documentation

MkDocs documentation can be deployed to either GitHub Pages or GCP.

#### Option A: GitHub Pages

Automatic on pushes to `main` that touch `docs/user_docs/**` via the GitHub
Actions workflow (`.github/workflows/deploy-docs.yml`).

> **Prerequisite:** In the repository Settings → Pages → Build and deployment,
> set **Source** to **GitHub Actions**.

Manual deployment from your machine:

```bash
npm run docs:install   # one-time
npm run docs:deploy    # pushes to gh-pages branch
```

#### Option B: Google Cloud Storage

Deploy the static site to a GCS bucket with public access.

```bash
# Deploy to the dev docs bucket (aam-docs-dev)
npm run docs:deploy:gcp

# Or run the script directly with options
./deploy/gcp/deploy_docs.sh --bucket=aam-docs-prod
./deploy/gcp/deploy_docs.sh --dry-run
./deploy/gcp/deploy_docs.sh --install  # install MkDocs deps first
```

The script creates the bucket on first run, configures static website serving,
and syncs the built site. See [gcp/README.md](gcp/README.md) for full details.

## GCP Resources Overview

| Resource              | GCP Service            | Purpose                       |
|-----------------------|------------------------|-------------------------------|
| API / Backend         | Cloud Run              | FastAPI container hosting     |
| Web Frontend          | Cloud Run              | React SPA via Nginx container |
| Database              | Cloud SQL (PG 16)      | Persistent storage            |
| Cache                 | Memorystore (Redis 7)  | Session / query caching       |
| Package Storage       | Cloud Storage (GCS)    | Package archive storage       |
| Container Registry    | Artifact Registry      | Docker image storage          |
| Load Balancer         | Global HTTPS LB        | SSL termination, routing      |
| Secrets               | Secret Manager         | Credentials, signing keys     |
| Documentation         | Cloud Storage (GCS)    | MkDocs static site hosting    |
| Monitoring            | Cloud Monitoring       | Uptime checks, alerting       |
