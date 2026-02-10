# AAM Deployment

This directory contains everything needed to deploy AAM locally (Docker
Compose) and to Google Cloud Platform (Pulumi IaC, with optional `gcloud`
helpers).

## Deployment Model

AAM runs on Google Cloud Platform in the `aamregistry` project. Three
isolated environments share the same GCP project but use independent
resources. Each environment is provisioned by its own Pulumi stack.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          aamregistry.io (DNS)                           │
├───────────────────┬───────────────────┬──────────────────────────────────┤
│       DEV         │       TEST        │             PROD                 │
│ dev.aamregistry.io│test.aamregistry.io│ prod.aamregistry.io              │
├───────────────────┼───────────────────┼──────────────────────────────────┤
│  Cloud Run (web)  │  Cloud Run (web)  │  Cloud Run (web)                 │
│  Cloud Run (api)  │  Cloud Run (api)  │  Cloud Run (api)                 │
│  Cloud SQL        │  Cloud SQL        │  Cloud SQL (HA)                  │
│  Memorystore      │  Memorystore      │  Memorystore (HA)                │
│  GCS bucket       │  GCS bucket       │  GCS bucket                      │
└───────────────────┴───────────────────┴──────────────────────────────────┘
```

Each Cloud Run service uses **domain mappings** with Google-managed SSL
certificates. No load balancer is needed.

### Environment summary

| Property          | dev                   | test                   | prod                        |
|-------------------|-----------------------|------------------------|-----------------------------|
| Purpose           | Development / CI      | QA / staging           | Production                  |
| Branch trigger    | Feature branches      | `develop` / RC tags    | `main` / release tags       |
| Pulumi stack file | `Pulumi.dev.yaml`     | `Pulumi.test.yaml`     | `Pulumi.prod.yaml`          |
| Scale-to-zero     | Yes                   | No (min 1)             | No (min 2)                  |
| DB HA             | No                    | No                     | Yes (REGIONAL)              |
| DB backups        | Off                   | On                     | On + PITR                   |
| Redis HA          | BASIC                 | BASIC                  | STANDARD_HA                 |
| Deletion protect  | Off                   | Off                    | On                          |

## Domain Naming Conventions

Every environment follows the same pattern:

```
{env}.aamregistry.io           — public web (React SPA)
api.{env}.aamregistry.io       — backend API + HTTP registry API
{env}.aamregistry.io/docs      — documentation (MkDocs)
```

### Full domain matrix

| Service             | dev                           | test                           | prod                           |
|---------------------|-------------------------------|--------------------------------|--------------------------------|
| **Web (SPA)**       | `dev.aamregistry.io`          | `test.aamregistry.io`          | `prod.aamregistry.io`          |
| **Backend API**     | `api.dev.aamregistry.io`      | `api.test.aamregistry.io`      | `api.prod.aamregistry.io`      |
| **Documentation**   | GitHub Pages                  | GitHub Pages                   | GitHub Pages                   |

### DNS records

Each domain requires a single CNAME record pointing to `ghs.googlehosted.com`.
Cloud Run domain mappings handle SSL termination with Google-managed certificates.

| Record                           | Type  | Target                  | Notes       |
|----------------------------------|-------|-------------------------|-------------|
| `dev.aamregistry.io`             | CNAME | `ghs.googlehosted.com.` | Web SPA     |
| `api.dev.aamregistry.io`         | CNAME | `ghs.googlehosted.com.` | Backend API |
| `test.aamregistry.io`            | CNAME | `ghs.googlehosted.com.` | Web SPA     |
| `api.test.aamregistry.io`        | CNAME | `ghs.googlehosted.com.` | Backend API |
| `prod.aamregistry.io`            | CNAME | `ghs.googlehosted.com.` | Web SPA     |
| `api.prod.aamregistry.io`        | CNAME | `ghs.googlehosted.com.` | Backend API |

### Routing

Each domain maps directly to its Cloud Run service via **Cloud Run domain
mappings**. No load balancer or URL map is needed — DNS does the routing.

```
test.aamregistry.io       → CNAME → ghs.googlehosted.com → Cloud Run (web)
api.test.aamregistry.io   → CNAME → ghs.googlehosted.com → Cloud Run (backend)
```

### Managed SSL certificates

Cloud Run domain mappings automatically provision Google-managed SSL
certificates per domain. Certificates are renewed automatically.

### Adding a new service

To add a new service (e.g. `admin.{env}.aamregistry.io`):

1. Deploy the Cloud Run service
2. Create a domain mapping: `gcloud beta run domain-mappings create --service=<name> --domain=<domain> --region=us-central1`
3. Add a DNS CNAME record: `<domain>` → `ghs.googlehosted.com.`

### CLI registry URL

The `aam` CLI connects to the backend API. The default registry URL per
environment is:

```
aam source add default https://api.dev.aamregistry.io     # dev
aam source add default https://api.test.aamregistry.io    # test
aam source add default https://api.prod.aamregistry.io    # prod
```

### Resource naming conventions (GCP)

All GCP resources follow the pattern `aam-{resource}-{env}`:

| Resource                | dev                    | test                    | prod                    |
|-------------------------|------------------------|-------------------------|-------------------------|
| Cloud Run (web)         | `aam-web-dev`          | `aam-web-test`          | `aam-web-prod`          |
| Cloud Run (backend)     | `aam-backend-dev`      | `aam-backend-test`      | `aam-backend-prod`      |
| Cloud SQL instance      | `aam-db-dev`           | `aam-db-test`           | `aam-db-prod`           |
| Memorystore (Redis)     | `aam-redis-dev`        | `aam-redis-test`        | `aam-redis-prod`        |
| GCS bucket (packages)   | `aam-packages-dev`     | `aam-packages-test`     | `aam-packages-prod`     |
| VPC                     | `aam-vpc-dev`          | `aam-vpc-test`          | `aam-vpc-prod`          |
| VPC connector           | `aam-vpc-conn-dev`     | `aam-vpc-conn-test`     | `aam-vpc-conn-prod`     |
| Artifact Registry repo  | `aam` (shared)         | `aam` (shared)          | `aam` (shared)          |

> **Note:** Artifact Registry is shared across environments. Container images
> are differentiated by tag (`web:dev`, `web:test`, `web:latest`).

### Container image naming

Images live in a single Artifact Registry repository:

```
us-central1-docker.pkg.dev/aamregistry/aam/{service}:{tag}
```

| Image                   | dev tag  | test tag  | prod tag   |
|-------------------------|----------|-----------|------------|
| `aam/backend`           | `dev`    | `test`    | `latest`   |
| `aam/web`               | `dev`    | `test`    | `latest`   |

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
│   │   ├── backend_service.py # Cloud Run (FastAPI backend)
│   │   ├── web_service.py     # Cloud Run (React web frontend)
│   │   ├── domain_mapping.py  # Cloud Run domain mappings + SSL
│   │   └── monitoring.py      # Uptime checks & alerting
│   └── README.md             # Pulumi deployment guide
│
└── README.md                 # This file
```

## Deployment Targets

### Local development

Run the full stack locally using Docker Compose.

```bash
# Quick start (dev mode with hot reload)
cp deploy/local/.env.example deploy/local/.env
docker compose -f deploy/local/docker-compose.yml \
  -f deploy/local/docker-compose.dev.yml up -d
```

See [local/README.md](local/README.md) for full instructions.

### Google Cloud Platform

Deploy to GCP using Pulumi across three environments.

```bash
cd deploy/pulumi
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

pulumi stack select dev
pulumi up
```

Pulumi references container images in Artifact Registry. To build and push
the dev web image (`apps/aam-web`) with `gcloud`, run:

```bash
./deploy/gcp/deploy_web_dev.sh
```

See [pulumi/README.md](pulumi/README.md) for full instructions.

### Documentation

MkDocs documentation can be deployed to either GitHub Pages or GCP.

#### Option A: GitHub Pages

Automatic on pushes to `main` that touch `docs/user_docs/**` via the GitHub
Actions workflow (`.github/workflows/deploy-docs.yml`).

> **Prerequisite:** In the repository Settings, go to Pages, then Build and
> deployment, and set **Source** to **GitHub Actions**.

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

The script creates the bucket on first run, configures static website
serving, and syncs the built site. See [gcp/README.md](gcp/README.md) for
full details.

## GCP Resources Overview

| Resource              | GCP Service            | Purpose                       |
|-----------------------|------------------------|-------------------------------|
| API / Backend         | Cloud Run              | FastAPI container hosting     |
| Web Frontend          | Cloud Run              | React SPA via Nginx container |
| Domain Routing        | Cloud Run Domain Maps  | Custom domains + managed SSL  |
| Database              | Cloud SQL (PG 16)      | Persistent storage            |
| Cache                 | Memorystore (Redis 7)  | Session / query caching       |
| Package Storage       | Cloud Storage (GCS)    | Package archive storage       |
| Container Registry    | Artifact Registry      | Docker image storage          |
| Secrets               | Secret Manager         | Credentials, signing keys     |
| Documentation         | GitHub Pages           | MkDocs static site hosting    |
| Monitoring            | Cloud Monitoring       | Uptime checks, alerting       |
