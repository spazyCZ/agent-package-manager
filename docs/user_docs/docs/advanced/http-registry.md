# HTTP Registry

## Overview

The HTTP Registry is a centralized server for publishing and discovering AAM packages. It provides features beyond local/Git registries, including authentication, package signing verification, download statistics, and governance controls.

**Key features:**

- RESTful API for package operations
- User authentication with API tokens
- Package signing with Sigstore or GPG
- Download statistics and metrics
- Governance approvals for enterprise use
- Audit logging for all mutations
- Scoped package namespaces

## Architecture

```
┌─────────────┐
│  AAM CLI    │
│   Client    │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────┐
│   HTTP Registry Server      │
│  ┌────────────────────────┐ │
│  │    FastAPI Service     │ │
│  │  - Authentication      │ │
│  │  - Package Management  │ │
│  │  - Signing Verification│ │
│  └────────┬───────────────┘ │
│           │                  │
│  ┌────────▼───────────────┐ │
│  │    PostgreSQL DB       │ │
│  │  - Package metadata    │ │
│  │  - Users & tokens      │ │
│  │  - Audit logs          │ │
│  └────────────────────────┘ │
│  ┌────────────────────────┐ │
│  │  S3/MinIO Storage      │ │
│  │  - Package archives    │ │
│  │  - Signatures          │ │
│  └────────────────────────┘ │
└─────────────────────────────┘
```

## When to Use HTTP Registry

### Use HTTP Registry if you:

- Need centralized package sharing across teams
- Want user authentication and access control
- Require package signing verification
- Need download statistics and usage metrics
- Want governance approvals (enterprise)
- Need audit trails for compliance

### Use Local/Git Registry if you:

- Work solo or on a small team
- Want zero infrastructure setup
- Prefer filesystem or Git-based sharing
- Don't need authentication
- Want maximum simplicity

## Setting Up HTTP Registry

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- S3-compatible storage (AWS S3, MinIO, etc.)
- Redis (optional, for caching)

### Installation

```bash
# Clone the registry
git clone https://github.com/spazyCZ/agent-package-manager.git
cd agent-package-manager/aam-backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and storage credentials

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Configuration

Edit `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/aam

# Storage
STORAGE_BACKEND=s3
S3_BUCKET=aam-packages
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Optional: MinIO (local S3-compatible storage)
# STORAGE_BACKEND=minio
# MINIO_ENDPOINT=localhost:9000
# MINIO_ACCESS_KEY=minioadmin
# MINIO_SECRET_KEY=minioadmin

# Authentication
JWT_SECRET=your-secret-key-here
TOKEN_EXPIRE_HOURS=24

# Optional: Redis cache
REDIS_URL=redis://localhost:6379

# Optional: Signing
REQUIRE_SIGNATURES=false  # Set to true to enforce signing
```

## Using HTTP Registry

### Register and Login

```bash
# Register a new account
aam register
# Username: alice
# Email: alice@example.com
# Password: ****

# Login
aam login
# Username: alice
# Password: ****
# Token saved to ~/.aam/credentials.json
```

### Configure Registry

```bash
# Add the HTTP registry
aam registry add https://registry.aam.dev --name central --default

# Verify configuration
aam registry list
# central (default): https://registry.aam.dev (HTTP)
```

### Publish to HTTP Registry

```bash
# Publish package (requires authentication)
aam pkg publish

# Publish with signing
aam pkg publish --sign

# Publish to specific registry
aam pkg publish --registry central
```

### Install from HTTP Registry

```bash
# Install package (authentication not required for public packages)
aam install @author/my-package

# Install with signature verification
aam install @author/my-package --verify-signature
```

## API Overview

### Authentication

Most write operations require authentication via API token:

```bash
# Create API token
aam token create --name "ci-token" --expires 90d

# Token is saved in ~/.aam/credentials.json
# Use in CI/CD:
export AAM_TOKEN=your-token-here
aam pkg publish
```

### Package Operations

```bash
# Search packages
GET /api/v1/packages?q=audit&type=agent

# Get package metadata
GET /api/v1/packages/@author/my-package

# Download package
GET /api/v1/packages/@author/my-package/1.0.0/download

# Publish package (requires auth)
POST /api/v1/packages

# Yank version (requires auth, owner only)
DELETE /api/v1/packages/@author/my-package/1.0.0
```

### Dist-Tags

```bash
# List tags
GET /api/v1/packages/@author/my-package/tags

# Set tag (requires auth, owner only)
PUT /api/v1/packages/@author/my-package/tags/stable
{"version": "1.2.0"}

# Remove tag (requires auth, owner only)
DELETE /api/v1/packages/@author/my-package/tags/stable
```

### Governance

```bash
# Approve version (requires auth, approver role)
POST /api/v1/packages/@author/my-package/1.0.0/approve
{"comment": "Reviewed and approved"}

# List approvals
GET /api/v1/packages/@author/my-package/1.0.0/approvals
```

## Advanced Features

### Package Signing

Enable package signing to verify artifact integrity:

```bash
# Configure signing requirement
# In .env:
REQUIRE_SIGNATURES=true

# Publish with signature
aam pkg publish --sign

# Install with verification
aam install @author/my-package --verify-signature
```

See [Package Signing](signing.md) for details.

### Dist-Tags

Create named aliases for versions:

```bash
# Tag a version as stable
aam dist-tag add @author/my-package@1.2.0 stable

# Install using tag
aam install @author/my-package@stable
```

See [Dist-Tags](dist-tags.md) for details.

### Governance Approvals

Require approvals before installation (enterprise):

```bash
# Configure approval requirement
aam config set security.require_approval true

# Designated approvers can approve versions
aam approve @author/my-package@1.0.0

# Only approved versions can be installed
aam install @author/my-package  # Uses latest approved version
```

### Audit Logs

Query audit logs for compliance:

```bash
# View audit log (admin only)
GET /api/v1/audit-log?action=publish&start_date=2026-01-01

# View package-specific log
GET /api/v1/packages/@author/my-package/audit-log
```

### Quality Metrics

Upload and view quality metrics:

```bash
# Run evals and publish results
aam eval --publish

# View results
aam info @author/my-package
# Quality Metrics:
#   accuracy-eval: 94.2%
#   latency_p95: 245ms
```

See [Quality & Evals](quality-evals.md) for details.

## Security

### Authentication

- User passwords are hashed with bcrypt
- API tokens are JWT-based and revocable
- HTTPS required for all traffic in production

### Authorization

- Package owners can publish new versions
- Package owners can yank versions
- Package owners can manage dist-tags
- Approvers can approve versions
- Admins can access audit logs

### Package Verification

- SHA-256 checksums for all packages
- Optional Sigstore or GPG signatures
- Signature verification on install

## Monitoring

### Health Check

```bash
GET /health
# Response: {"status": "ok", "version": "0.1.0"}
```

### Metrics

The registry exposes metrics for monitoring:

- Package downloads
- User registrations
- Publish operations
- Storage usage
- API latency

### Logging

All operations are logged with structured logging:

```json
{
  "timestamp": "2026-02-09T14:30:00Z",
  "level": "info",
  "event": "package_published",
  "user": "alice",
  "package": "@author/my-package",
  "version": "1.0.0",
  "size_bytes": 12847
}
```

## Troubleshooting

### Authentication Failed

**Symptom:** `401 Unauthorized` when publishing.

**Solution:**

```bash
# Check if logged in
aam config get token

# Login again
aam login
```

### Package Not Found

**Symptom:** `404 Not Found` when installing.

**Solution:**

```bash
# Check registry configuration
aam registry list

# Search for package
aam search my-package
```

### Signature Verification Failed

**Symptom:** Signature verification fails on install.

**Solution:**

```bash
# Check package signature
aam info @author/my-package

# Install without verification (not recommended)
aam install @author/my-package --no-verify
```

### Storage Backend Error

**Symptom:** `500 Internal Server Error` when publishing.

**Cause:** S3/MinIO connection issue.

**Solution:**

Check storage configuration in `.env`:

```bash
# Test S3 connection
aws s3 ls s3://aam-packages

# Test MinIO connection
mc ls myminio/aam-packages
```

## Next Steps

- [Package Signing](signing.md) - Sign and verify packages
- [Hosting a Registry](hosting-registry.md) - Production deployment
- [Dist-Tags](dist-tags.md) - Version aliasing
- [Quality & Evals](quality-evals.md) - Quality metrics
