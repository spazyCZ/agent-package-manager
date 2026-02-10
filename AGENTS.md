# AGENTS.md — Project Context for AI Agents

> High-level project guide for AI coding agents operating in this repository.

---

## Project Overview

**AAM (Agent Artifact Manager)** is a package manager for AI agent artifacts — skills, agents, prompts, and instructions. It enables practitioners to package, share, and deploy these artifacts across platforms like Cursor, Claude, GitHub Copilot, and Codex.

Think of it as `pip` or `npm`, but for AI agent configurations.

- **Repository:** `agent-package-manager`
- **Version:** 0.1.0 (early development)
- **License:** MIT

---

## Monorepo Structure (Nx)

This is an **Nx monorepo** managed with `npm` as the package manager.

```
agent-package-manager/
├── apps/
│   ├── aam-backend/        # Python FastAPI REST API (registry service)
│   ├── aam-cli/            # Python CLI tool (Click + Rich)
│   └── aam-web/            # React TypeScript frontend (Vite + Tailwind)
├── libs/                   # Shared libraries (planned, not yet created)
├── deploy/                 # Deployment (Docker, Pulumi IaC)
│   ├── local/              #   Local Docker Compose (dev & prod-like)
│   ├── docker/             #   Dockerfiles (backend, web)
│   └── pulumi/             #   Pulumi IaC for GCP (dev, test, prod)
├── docs/                   # Design docs, API specs, user guide
├── specs/                  # Technical specifications & task plans
├── .cursor/                # Cursor AI rules and skills
├── nx.json                 # Nx workspace configuration
├── package.json            # Root package.json (@aam/monorepo)
├── tsconfig.base.json      # Shared TypeScript config
└── CONTRIBUTING.md         # Developer setup and guidelines
```

### Nx Conventions

- Run all tasks through Nx: `npx nx <target> <project>`
- Projects are tagged: `type:app`, `scope:{backend,cli,web}`, `lang:{python,typescript}`
- Caching is enabled for `build`, `test`, and `lint` targets
- Base branch: `main`

---

## Applications

### aam-backend (`apps/aam-backend/`)

The registry HTTP API service.

- **Language:** Python 3.11+
- **Framework:** FastAPI 0.115+ with Uvicorn
- **Database:** PostgreSQL 16 (asyncpg + SQLAlchemy 2.0)
- **Cache:** Redis 7
- **Storage:** MinIO (local) / GCS (cloud) for package archives
- **Migrations:** Alembic
- **Observability:** Structlog, Prometheus, OpenTelemetry
- **Auth:** JWT (python-jose) + Passlib

### aam-cli (`apps/aam-cli/`)

The end-user CLI tool (`aam` command).

- **Language:** Python 3.11+
- **Framework:** Click 8.1+ with Rich 13.0+
- **HTTP Client:** httpx
- **Entry point:** `aam_cli.main:cli`

### aam-web (`apps/aam-web/`)

The web-based registry UI.

- **Language:** TypeScript
- **Framework:** React 18 with React Router DOM 7
- **Build:** Vite 6
- **Styling:** Tailwind CSS
- **Port:** 3000 (dev)

---

## Deployment

### Deploy Directory Structure

```
deploy/
├── local/                        # Local Docker Compose
│   ├── docker-compose.yml        #   Base compose (all services)
│   ├── docker-compose.dev.yml    #   Dev overrides (hot reload)
│   ├── .env.example              #   Environment variable template
│   ├── init-db.sql               #   PostgreSQL initialization
│   ├── nginx/                    #   Nginx configs
│   │   ├── nginx.conf            #     Reverse proxy
│   │   └── nginx-web.conf        #     Web SPA serving
│   └── ssl/                      #   SSL certs (local testing)
│
├── docker/                       # Dockerfiles (shared by local & cloud)
│   ├── backend/
│   │   ├── Dockerfile            #   Production (multi-stage, non-root)
│   │   └── Dockerfile.dev        #   Development (hot reload)
│   └── web/
│       ├── Dockerfile            #   Production (Node build → Nginx)
│       └── Dockerfile.dev        #   Development (Vite HMR)
│
└── pulumi/                       # Pulumi IaC for GCP
    ├── Pulumi.yaml               #   Project config
    ├── Pulumi.dev.yaml           #   Dev stack
    ├── Pulumi.test.yaml          #   Test stack
    ├── Pulumi.prod.yaml          #   Prod stack
    ├── __main__.py               #   Entry point
    ├── config.py                 #   Typed stack config loader
    ├── requirements.txt          #   Python deps (pulumi, pulumi-gcp)
    └── components/               #   Reusable ComponentResource modules
        ├── network.py            #     VPC, subnets, VPC connector
        ├── database.py           #     Cloud SQL (PostgreSQL 16)
        ├── cache.py              #     Memorystore (Redis 7)
        ├── storage.py            #     GCS bucket
        ├── registry.py           #     Artifact Registry
        ├── secrets.py            #     Secret Manager
        ├── backend_service.py    #     Cloud Run (FastAPI)
        ├── web_service.py        #     Cloud Run (React SPA)
        ├── domain_mapping.py     #     Cloud Run domain mappings + SSL
        └── monitoring.py         #     Uptime checks & alerting
```

### Local Development — Docker Compose

All local development runs via Docker Compose from `deploy/local/`.

```bash
# Copy environment file
cp deploy/local/.env.example deploy/local/.env

# Start all services (dev mode with hot reload)
docker compose -f deploy/local/docker-compose.yml \
  -f deploy/local/docker-compose.dev.yml up

# Start only infrastructure (DB, Redis, MinIO)
docker compose -f deploy/local/docker-compose.yml up postgres redis minio
```

**Local services:**

| Service    | Port(s)     | Image                |
|------------|-------------|----------------------|
| PostgreSQL | 5432        | postgres:16-alpine   |
| Redis      | 6379        | redis:7-alpine       |
| MinIO      | 9000, 9001  | minio/minio          |
| Backend    | 8000        | deploy/docker/backend |
| Web        | 3000        | deploy/docker/web     |
| Nginx      | 80, 443     | nginx:alpine         |

### Remote Environments — Google Cloud (Pulumi)

Deployment to GCP is managed with **Pulumi** (Python SDK) from `deploy/pulumi/`.

| Environment | Stack Config       | Purpose                          | Branch / Trigger           |
|-------------|--------------------|---------------------------------|---------------------------|
| **dev**     | `Pulumi.dev.yaml`  | Development / integration tests  | Feature branches           |
| **test**    | `Pulumi.test.yaml` | QA, staging, pre-release         | `develop` / release candidates |
| **prod**    | `Pulumi.prod.yaml` | Production                       | `main` / tagged releases   |

**GCP Project:** `aamregistry`

```bash
cd deploy/pulumi
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

pulumi stack select dev    # or test / prod
pulumi up
```

### GCP Resource Map

| Resource              | GCP Service              | Purpose                        |
|-----------------------|--------------------------|--------------------------------|
| API / Backend         | Cloud Run                | FastAPI container hosting      |
| Web Frontend          | Cloud Run                | React SPA hosting (Nginx)      |
| Database              | Cloud SQL (PostgreSQL 16)| Persistent storage             |
| Cache                 | Memorystore (Redis 7)    | Session / query caching        |
| Object Storage        | Cloud Storage (GCS)      | Package archive storage        |
| Container Registry    | Artifact Registry        | Docker image storage           |
| Domain Routing        | Cloud Run Domain Maps    | Custom domains + managed SSL   |
| Secrets               | Secret Manager           | API keys, DB credentials       |
| Monitoring            | Cloud Monitoring         | Uptime checks, alerting        |

### Pulumi Component Architecture

Each infrastructure concern is encapsulated in a `pulumi.ComponentResource`:

| Component          | File                             | Resources Created                    |
|--------------------|----------------------------------|--------------------------------------|
| Network            | `components/network.py`          | VPC, subnet, VPC connector           |
| Database           | `components/database.py`         | Cloud SQL instance, database, user   |
| Cache              | `components/cache.py`            | Memorystore Redis instance           |
| Storage            | `components/storage.py`          | GCS bucket with lifecycle rules      |
| ArtifactRegistry   | `components/registry.py`         | Docker image repository              |
| Secrets            | `components/secrets.py`          | Secret Manager entries               |
| BackendService     | `components/backend_service.py`  | Cloud Run service + IAM              |
| WebService         | `components/web_service.py`      | Cloud Run service + IAM              |
| DomainMapping      | `components/domain_mapping.py`   | Cloud Run domain mappings + SSL      |
| Monitoring         | `components/monitoring.py`       | Uptime checks                        |

### Environment Sizing

| Resource            | dev            | test              | prod                 |
|---------------------|----------------|-------------------|----------------------|
| Cloud Run min inst. | 0 (scale to 0) | 1                 | 2                    |
| Cloud SQL tier      | db-f1-micro    | db-custom-1-3840  | db-custom-2-7680     |
| Cloud SQL HA        | No             | No                | Yes (REGIONAL)       |
| Cloud SQL backups   | Off            | On                | On + PITR            |
| Redis tier          | BASIC          | BASIC             | STANDARD_HA          |
| CDN                 | Off            | Off               | On                   |
| Deletion protection | Off            | Off               | On (Cloud SQL)       |

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   aam-cli   │────▶│ aam-backend  │◀────│   aam-web   │
│  (Python)   │     │  (FastAPI)   │     │  (React)    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │PostgreSQL│ │  Redis   │ │MinIO/GCS │
        │  (data)  │ │ (cache)  │ │(packages)│
        └──────────┘ └──────────┘ └──────────┘
```

- **CLI -> Backend:** HTTP REST API (see `docs/HTTP_REGISTRY_SPEC.md`)
- **Web -> Backend:** Same REST API, consumed from the browser
- **Local:** Nginx reverse proxy sits in front of Backend and Web
- **Cloud:** Cloud Run domain mappings route custom domains to services (no load balancer)

---

## Key Documentation

| Document                         | Description                                   |
|----------------------------------|-----------------------------------------------|
| `README.md`                      | Project overview, quick start, CLI reference   |
| `CONTRIBUTING.md`                | Developer setup, code style, PR process        |
| `docs/DESIGN.md`                 | Architecture, package format, registry design  |
| `docs/HTTP_REGISTRY_SPEC.md`     | Registry HTTP API specification                |
| `docs/USER_GUIDE.md`            | End-user walkthrough                           |
| `deploy/README.md`              | Deployment overview (local + cloud)            |
| `deploy/local/README.md`        | Local Docker Compose guide                     |
| `deploy/pulumi/README.md`       | Pulumi IaC guide for GCP                       |

### User Documentation — MkDocs (MANDATORY)

User-facing documentation is published via **MkDocs** (Material theme) from the `docs/` directory. Keeping the docs aligned with the codebase is a **mandatory part of every change**.

- **Any PR that modifies CLI commands, API endpoints, package format, configuration options, or user-visible behavior MUST include corresponding updates to the relevant MkDocs pages** (`docs/USER_GUIDE.md`, `docs/HTTP_REGISTRY_SPEC.md`, `docs/DESIGN.md`, or new pages as needed).
- Documentation updates are a **quality gate** — PRs with user-facing changes that lack doc updates MUST NOT be merged.
- When adding new features, create or update the appropriate doc page and ensure the MkDocs `nav` structure in `mkdocs.yml` includes it.
- CLI `--help` text, API spec, and MkDocs pages MUST stay in sync — if one changes, the others MUST be updated in the same PR.
- Use clear examples, code blocks, and step-by-step instructions in all user-facing docs.

---

## Development Workflow

### Prerequisites

- Node.js >= 20
- Python >= 3.11
- Docker & Docker Compose
- `npm` (workspace-level package manager)
- Pulumi CLI >= 3.0 (for cloud deployments)
- Google Cloud SDK (`gcloud`) (for cloud deployments)

### Common Commands

```bash
# Install all dependencies
npm install

# Backend
npx nx serve aam-backend          # Start backend dev server
npx nx test aam-backend           # Run backend tests
npx nx lint aam-backend           # Lint backend code
npx nx migrate aam-backend        # Run DB migrations

# CLI
npx nx serve aam-cli              # Run CLI in dev mode
npx nx test aam-cli               # Run CLI tests

# Web
npx nx serve aam-web              # Start web dev server (port 3000)
npx nx test aam-web               # Run web tests
npx nx build aam-web              # Production build

# All projects
npx nx run-many -t test           # Test all projects
npx nx run-many -t lint           # Lint all projects
npx nx run-many -t build          # Build all projects

# Local Docker deployment
docker compose -f deploy/local/docker-compose.yml \
  -f deploy/local/docker-compose.dev.yml up

# Cloud deployment (Pulumi)
cd deploy/pulumi && pulumi up
```

### Python Projects

Python apps (`aam-backend`, `aam-cli`) use:

- **pyproject.toml** for dependency declaration
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Pytest** for testing

### TypeScript Projects

TypeScript apps (`aam-web`) use:

- **Vite** for build and dev server
- **ESLint 9** for linting
- **Prettier** for formatting
- **Vitest** for testing

---

## Coding Standards

### Universal Rules

- Max **600 lines** per file, **100 lines** per function
- All public functions/classes must have **docstrings**
- All function signatures must have **type hints** (Python) or **type annotations** (TypeScript)
- No `print()` in Python — use `logging` module
- Catch **specific exceptions**, log with context, re-raise with `raise ... from e`

### Python Style

- Visual separation with 80-char `#` block headers between sections
- Extensive commenting (explain the *why*, not just the *what*)
- Google-style docstrings
- Module-level `logger = logging.getLogger(__name__)` in every file
- Naming: `snake_case` (variables/functions), `PascalCase` (classes), `UPPER_CASE` (constants)

### Testing Conventions

- Unit tests: `test_unit_*`
- Mocked tests: `test_mocked_*`
- Integration tests: `test_integration_*`
- End-to-end tests: `test_e2e_*`

### Logging Requirements

Every module must include logging at:

- Function entry/exit (critical paths)
- External service calls (API, DB, file I/O)
- All exceptions (with `exc_info=True`)
- Performance-critical operations (with timing)
- Security events (auth, access control)

---

## Environment Variables

Key environment variables (see `deploy/local/.env.example` for full list):

| Variable           | Purpose                        |
|--------------------|--------------------------------|
| `APP_ENV`          | Environment: dev, test, prod   |
| `DEBUG`            | Enable debug mode              |
| `SECRET_KEY`       | Application secret key         |
| `POSTGRES_*`       | Database connection            |
| `REDIS_PASSWORD`   | Redis authentication           |
| `MINIO_*`          | Object storage credentials     |
| `BACKEND_PORT`     | Backend service port (8000)    |
| `CORS_ORIGINS`     | Allowed CORS origins           |

---

## CI/CD

> **Status:** CI/CD pipelines are not yet configured.

When implemented, the pipeline should:

1. Run `nx affected -t lint,test,build` on PRs
2. Build Docker images on merge to `main` / `develop`
3. Push images to GCP Artifact Registry (`aamregistry`)
4. Deploy to the appropriate environment via Pulumi
5. Run integration / e2e tests post-deploy

---

## Important Notes for AI Agents

1. **Never import LLM libraries directly** — always use `src.common.llm.providers` (see Cursor rules)
2. **No `print()` statements** — use `logging` everywhere in Python code
3. **No bare `except:`** — always catch specific exceptions
4. **No try-except for imports** — imports should fail loudly
5. **No fallback logic unless explicitly tasked** — do not add defensive fallbacks unprompted
6. **All Nx commands should be run via `npx nx`** (or through the scripts in `package.json`)
7. **The `libs/` directory does not exist yet** — it is planned for shared code (`@aam/shared`)
8. **Pulumi IaC lives in `deploy/pulumi/`** — use `pulumi.ComponentResource` for new infrastructure. Each component is a separate module in `deploy/pulumi/components/`.
9. **Dockerfiles live in `deploy/docker/`** — referenced by both local compose and cloud CI/CD builds
10. **Local Docker Compose lives in `deploy/local/`** — not in the deploy root
11. **Keep MkDocs user documentation aligned** — when changing CLI commands, API endpoints, package format, config options, or any user-visible behavior, you MUST update the corresponding pages in `docs/` in the same change. CLI `--help` text, API spec, and MkDocs pages MUST stay in sync.
