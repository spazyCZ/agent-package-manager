# AAM Infrastructure — Pulumi (GCP)

Infrastructure as Code for deploying AAM to Google Cloud Platform across three environments: **dev**, **test**, and **prod**.

## Architecture

```
                     ┌──────────────────────────┐
                     │  Global HTTPS LB          │
                     │  (managed SSL, CDN)       │
                     └────────┬─────────────────┘
                              │
               ┌──────────────┼──────────────┐
               │ /api/*       │ /*           │
               ▼              ▼              │
        ┌────────────┐  ┌────────────┐       │
        │ Cloud Run  │  │ Cloud Run  │       │
        │ Backend    │  │ Web (SPA)  │       │
        │ (FastAPI)  │  │ (Nginx)    │       │
        └─────┬──────┘  └────────────┘       │
              │                              │
    ┌─────────┼──────────┐                   │
    ▼         ▼          ▼                   │
┌────────┐ ┌───────┐ ┌────────┐              │
│Cloud   │ │Memory-│ │  GCS   │              │
│SQL     │ │store  │ │Bucket  │              │
│(PG 16) │ │(Redis)│ │(pkgs)  │              │
└────────┘ └───────┘ └────────┘              │
                                             │
         ┌──────────────────────────────────┘
         │
    ┌────────────┐  ┌──────────────┐  ┌───────────┐
    │ Artifact   │  │  Secret      │  │  Cloud    │
    │ Registry   │  │  Manager     │  │ Monitoring│
    └────────────┘  └──────────────┘  └───────────┘
```

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

### Key Differences Between Environments

| Resource            | dev            | test              | prod                 |
|---------------------|----------------|-------------------|----------------------|
| Cloud Run min inst. | 0 (scale to 0) | 1                 | 2                    |
| Cloud SQL tier      | db-f1-micro    | db-custom-1-3840  | db-custom-2-7680     |
| Cloud SQL HA        | No             | No                | Yes (REGIONAL)       |
| Cloud SQL backups   | Off            | On                | On + PITR            |
| Redis tier          | BASIC          | BASIC             | STANDARD_HA          |
| CDN                 | Off            | Off               | On                   |
| Deletion protection | Off            | Off               | On                   |

## Components

Each component is a reusable `pulumi.ComponentResource`:

| Component          | File                        | GCP Resources                        |
|--------------------|-----------------------------|--------------------------------------|
| Network            | `components/network.py`     | VPC, subnet, VPC connector           |
| Database           | `components/database.py`    | Cloud SQL instance, database, user   |
| Cache              | `components/cache.py`       | Memorystore Redis                    |
| Storage            | `components/storage.py`     | GCS bucket                           |
| ArtifactRegistry   | `components/registry.py`    | Artifact Registry repo               |
| Secrets            | `components/secrets.py`     | Secret Manager secrets               |
| BackendService     | `components/backend_service.py` | Cloud Run (FastAPI)              |
| WebService         | `components/web_service.py` | Cloud Run (React SPA)                |
| LoadBalancer       | `components/load_balancer.py` | GLB, SSL cert, URL map             |
| Monitoring         | `components/monitoring.py`  | Uptime checks                        |

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
