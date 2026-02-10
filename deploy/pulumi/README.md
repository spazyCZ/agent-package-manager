# AAM Infrastructure — Pulumi (GCP)

Infrastructure as Code for deploying AAM to Google Cloud Platform across three environments: **dev**, **test**, and **prod**.

## Architecture

```
   test.aamregistry.io          api.test.aamregistry.io
          │                              │
          ▼                              ▼
   ┌────────────┐                ┌────────────┐
   │ Cloud Run  │                │ Cloud Run  │
   │ Web (SPA)  │                │ Backend    │
   │ (Nginx)    │                │ (FastAPI)  │
   └────────────┘                └─────┬──────┘
                                       │
                             ┌─────────┼──────────┐
                             ▼         ▼          ▼
                        ┌────────┐ ┌───────┐ ┌────────┐
                        │Cloud   │ │Memory-│ │  GCS   │
                        │SQL     │ │store  │ │Bucket  │
                        │(PG 16) │ │(Redis)│ │(pkgs)  │
                        └────────┘ └───────┘ └────────┘

   ┌────────────┐  ┌──────────────┐  ┌───────────┐
   │ Artifact   │  │  Secret      │  │  Cloud    │
   │ Registry   │  │  Manager     │  │ Monitoring│
   └────────────┘  └──────────────┘  └───────────┘
```

Each Cloud Run service has its own **domain mapping** with a Google-managed
SSL certificate. No load balancer is needed — routing is done via DNS
(one CNAME per domain pointing to `ghs.googlehosted.com`).

## Prerequisites

1. **Pulumi CLI** >= 3.0 ([install](https://www.pulumi.com/docs/install/))
2. **Python** >= 3.11
3. **Google Cloud SDK** (`gcloud`) authenticated with the `aamregistry` project
4. A **GCS bucket** for Pulumi state (e.g. `gs://aam-pulumi-state`)

## Quick Start

```bash
cd deploy/pulumi

# 1. Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Login to Pulumi state backend (GCS)
pulumi login gs://aam-pulumi-state

# 3. Initialize a stack (one-time per environment)
pulumi stack init dev    # or test / prod

# 4. Preview changes
pulumi preview

# 5. Apply changes
pulumi up

# 6. View outputs
pulumi stack output
```

## Environments

| Stack    | Config File         | Purpose                          | Trigger                   |
|----------|---------------------|----------------------------------|---------------------------|
| **dev**  | `Pulumi.dev.yaml`   | Development / integration tests  | Feature branches          |
| **test** | `Pulumi.test.yaml`  | QA, staging, pre-release         | `develop` / release candidates |
| **prod** | `Pulumi.prod.yaml`  | Production                       | `main` / tagged releases  |

### Domain naming conventions

Every environment uses the same subdomain pattern under `aamregistry.io`:

```
{env}.aamregistry.io           — public web (React SPA)
api.{env}.aamregistry.io       — backend API + HTTP registry API
```

| Service         | dev                          | test                          | prod                          |
|-----------------|------------------------------|-------------------------------|-------------------------------|
| Web (SPA)       | `dev.aamregistry.io`         | `test.aamregistry.io`         | `prod.aamregistry.io`         |
| Backend API     | `api.dev.aamregistry.io`     | `api.test.aamregistry.io`     | `api.prod.aamregistry.io`     |
| Documentation   | GitHub Pages                 | GitHub Pages                  | GitHub Pages                  |

Each domain is mapped directly to its Cloud Run service using **Cloud Run
domain mappings**. DNS is a CNAME record per domain pointing to
`ghs.googlehosted.com`. Google provisions and renews SSL certificates
automatically.

#### Adding a new service

To add a new service (e.g. `aam-admin`) at `admin.{env}.aamregistry.io`:

1. Create the Cloud Run service (via Pulumi or `gcloud`)
2. Add a domain mapping: `gcloud beta run domain-mappings create --service=aam-{env}-admin --domain=admin.{env}.aamregistry.io --region=us-central1`
3. Add a DNS CNAME: `admin.{env}.aamregistry.io` → `ghs.googlehosted.com.`

### Key differences between environments

| Resource            | dev            | test              | prod                 |
|---------------------|----------------|-------------------|----------------------|
| Cloud Run min inst. | 0 (scale to 0) | 1                 | 2                    |
| Cloud SQL tier      | db-f1-micro    | db-custom-1-3840  | db-custom-2-7680     |
| Cloud SQL HA        | No             | No                | Yes (REGIONAL)       |
| Cloud SQL backups   | Off            | On                | On + PITR            |
| Redis tier          | BASIC          | BASIC             | STANDARD_HA          |
| Deletion protection | Off            | Off               | On                   |

## Components

Each component is a reusable `pulumi.ComponentResource`:

| Component          | File                           | GCP Resources                        |
|--------------------|--------------------------------|--------------------------------------|
| Network            | `components/network.py`        | VPC, subnet, VPC connector           |
| Database           | `components/database.py`       | Cloud SQL instance, database, user   |
| Cache              | `components/cache.py`          | Memorystore Redis                    |
| Storage            | `components/storage.py`        | GCS bucket                           |
| ArtifactRegistry   | `components/registry.py`       | Artifact Registry repo               |
| Secrets            | `components/secrets.py`        | Secret Manager secrets               |
| BackendService     | `components/backend_service.py`| Cloud Run (FastAPI)                  |
| WebService         | `components/web_service.py`    | Cloud Run (React SPA)                |
| DomainMapping      | `components/domain_mapping.py` | Cloud Run domain mappings + SSL      |
| Monitoring         | `components/monitoring.py`     | Uptime checks                        |

## Managing Secrets

```bash
# Set a secret value (encrypted in state)
pulumi config set --secret jwt_signing_key "your-secret-key"

# DB password is auto-generated — retrieve it
pulumi stack output db_password --show-secrets
```

## Destroying Infrastructure

```bash
# Destroy a non-production stack
pulumi destroy

# Remove the stack entirely
pulumi stack rm dev
```

> **WARNING:** The `prod` stack has `deletion_protection` enabled on Cloud SQL.
> You must disable it manually before `pulumi destroy` will succeed.

## Troubleshooting

```bash
# Check stack state
pulumi stack

# View detailed resource state
pulumi stack export

# Refresh state from cloud (detect drift)
pulumi refresh

# Cancel a stuck update
pulumi cancel
```
