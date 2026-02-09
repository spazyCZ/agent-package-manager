# Hosting a Registry

## Overview

This guide covers deploying and operating an AAM HTTP registry in production for teams and organizations.

## Prerequisites

- Linux server (Ubuntu 22.04+ recommended)
- Docker and Docker Compose
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)
- PostgreSQL database (self-hosted or managed)
- S3-compatible storage (AWS S3, MinIO, etc.)

## Deployment Options

### Option 1: Docker Compose (Recommended for Small Teams)

Includes all services: API, PostgreSQL, MinIO, Redis.

### Option 2: Kubernetes (Recommended for Enterprise)

Scalable deployment with multiple replicas and external services.

### Option 3: Manual Installation

Direct installation on server for maximum control.

## Quick Start with Docker Compose

### 1. Clone Repository

```bash
git clone https://github.com/spazyCZ/agent-package-manager.git
cd agent-package-manager/deployment/docker
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

Edit `.env`:

```bash
# Domain
DOMAIN=registry.yourcompany.com

# Database
POSTGRES_USER=aam
POSTGRES_PASSWORD=<generate-strong-password>
POSTGRES_DB=aam

# MinIO (S3-compatible storage)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=<generate-strong-password>

# JWT Secret
JWT_SECRET=<generate-random-string>

# Admin user
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_PASSWORD=<generate-strong-password>

# Optional: Enable signing
REQUIRE_SIGNATURES=false

# Optional: Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<app-password>
```

### 3. Start Services

```bash
docker-compose up -d
```

Services:

- API: http://localhost:8000
- MinIO Console: http://localhost:9001
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 4. Run Migrations

```bash
docker-compose exec api alembic upgrade head
```

### 5. Create Admin User

```bash
docker-compose exec api python -m app.cli create-admin \
  --username admin \
  --email admin@yourcompany.com \
  --password <password>
```

### 6. Configure SSL

Use Nginx or Caddy as reverse proxy:

```nginx
# /etc/nginx/sites-available/aam-registry
server {
    listen 80;
    server_name registry.yourcompany.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name registry.yourcompany.com;

    ssl_certificate /etc/letsencrypt/live/registry.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/registry.yourcompany.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # File upload size limit
        client_max_body_size 100M;
    }
}
```

Enable and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/aam-registry /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Test Installation

```bash
# Health check
curl https://registry.yourcompany.com/health

# Register a user
aam registry add https://registry.yourcompany.com --name company --default
aam register
aam login
```

## Production Deployment

### Infrastructure Requirements

**Minimum specs (small team, <100 users):**

- 2 vCPUs
- 4 GB RAM
- 100 GB storage
- PostgreSQL 13+
- Redis 6+

**Recommended specs (medium team, <1000 users):**

- 4 vCPUs
- 8 GB RAM
- 500 GB storage
- Managed PostgreSQL (AWS RDS, etc.)
- Managed Redis (AWS ElastiCache, etc.)
- S3 or equivalent object storage

**Large scale (enterprise, 1000+ users):**

- Multiple API replicas (horizontal scaling)
- Managed database with read replicas
- CDN for package downloads
- Dedicated storage backend

### Kubernetes Deployment

#### 1. Create Namespace

```bash
kubectl create namespace aam-registry
```

#### 2. Configure Secrets

```bash
kubectl create secret generic aam-secrets \
  --from-literal=postgres-password=<password> \
  --from-literal=jwt-secret=<secret> \
  --from-literal=minio-access-key=<key> \
  --from-literal=minio-secret-key=<secret> \
  -n aam-registry
```

#### 3. Deploy PostgreSQL

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: aam-registry
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: aam
        - name: POSTGRES_USER
          value: aam
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: aam-secrets
              key: postgres-password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

#### 4. Deploy API

```yaml
# api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aam-api
  namespace: aam-registry
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aam-api
  template:
    metadata:
      labels:
        app: aam-api
    spec:
      containers:
      - name: api
        image: aam-registry:latest
        env:
        - name: DATABASE_URL
          value: postgresql://aam:$(POSTGRES_PASSWORD)@postgres:5432/aam
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: aam-secrets
              key: jwt-secret
        - name: STORAGE_BACKEND
          value: s3
        - name: S3_BUCKET
          value: aam-packages
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aam-secrets
              key: minio-access-key
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: aam-secrets
              key: minio-secret-key
        ports:
        - containerPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: aam-api
  namespace: aam-registry
spec:
  selector:
    app: aam-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### 5. Deploy Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aam-registry
  namespace: aam-registry
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - registry.yourcompany.com
    secretName: aam-registry-tls
  rules:
  - host: registry.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: aam-api
            port:
              number: 80
```

## Monitoring

### Health Checks

```bash
# API health
curl https://registry.yourcompany.com/health

# Database connection
curl https://registry.yourcompany.com/health/db

# Storage connection
curl https://registry.yourcompany.com/health/storage
```

### Metrics

The registry exposes Prometheus metrics:

```
https://registry.yourcompany.com/metrics
```

Key metrics:

- `aam_requests_total` - Total API requests
- `aam_request_duration_seconds` - Request latency
- `aam_packages_total` - Total packages
- `aam_downloads_total` - Total downloads
- `aam_storage_bytes` - Storage usage

### Logging

Structured JSON logging to stdout:

```json
{
  "timestamp": "2026-02-09T14:30:00Z",
  "level": "info",
  "event": "package_published",
  "user_id": 42,
  "package": "@author/my-agent",
  "version": "1.0.0",
  "duration_ms": 1250
}
```

Forward logs to your logging system (ELK, Splunk, CloudWatch, etc.).

## Backup and Disaster Recovery

### Database Backups

```bash
# Automated daily backups
0 2 * * * docker-compose exec postgres pg_dump -U aam aam > /backups/aam-$(date +\%Y\%m\%d).sql
```

### Storage Backups

Enable S3 versioning and replication:

```bash
# Enable S3 versioning
aws s3api put-bucket-versioning \
  --bucket aam-packages \
  --versioning-configuration Status=Enabled

# Enable cross-region replication
aws s3api put-bucket-replication \
  --bucket aam-packages \
  --replication-configuration file://replication.json
```

### Disaster Recovery Plan

1. **Backup frequency:** Daily database, continuous S3 replication
2. **Retention:** 30 days for database, indefinite for packages
3. **Recovery time objective (RTO):** 1 hour
4. **Recovery point objective (RPO):** 24 hours

## Maintenance

### Update Registry

```bash
# Pull latest image
docker-compose pull

# Run migrations
docker-compose exec api alembic upgrade head

# Restart services
docker-compose up -d
```

### Database Maintenance

```bash
# Vacuum database
docker-compose exec postgres psql -U aam -d aam -c "VACUUM ANALYZE;"

# Check database size
docker-compose exec postgres psql -U aam -d aam -c "SELECT pg_size_pretty(pg_database_size('aam'));"
```

### Storage Cleanup

```bash
# List orphaned packages (not in database)
docker-compose exec api python -m app.cli storage cleanup --dry-run

# Delete orphaned packages
docker-compose exec api python -m app.cli storage cleanup
```

## Security

### Authentication

- Use strong passwords
- Enable 2FA for admin accounts
- Rotate JWT secrets annually
- Use short-lived tokens (24 hours)

### Network Security

- Use HTTPS only (enforce with HSTS)
- Firewall rules: Allow only 80/443 from internet
- Private network for database and storage
- VPN for admin access

### Package Security

- Enable package signing verification
- Scan packages for malware (optional)
- Implement rate limiting
- Monitor for suspicious activity

### Audit Logging

Enable audit logging for compliance:

```yaml
# config.yaml
audit:
  enabled: true
  retention_days: 90
  log_all_reads: false  # Only log mutations by default
```

## Troubleshooting

### API Not Starting

Check logs:

```bash
docker-compose logs api
```

Common issues:

- Database connection failed
- Missing environment variables
- Port already in use

### High Latency

Check database query performance:

```sql
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

Add indexes if needed:

```sql
CREATE INDEX idx_packages_name ON packages(name);
CREATE INDEX idx_versions_package_id ON versions(package_id);
```

### Storage Full

Check storage usage:

```bash
df -h  # Disk space
aws s3 ls s3://aam-packages --recursive --summarize  # S3 usage
```

Clean up old versions:

```bash
# Delete versions older than 1 year with no downloads
docker-compose exec api python -m app.cli cleanup-old-versions --days 365
```

## Scaling

### Horizontal Scaling

Add more API replicas:

```yaml
# docker-compose.yml
services:
  api:
    # ...
    deploy:
      replicas: 5
```

Or in Kubernetes:

```bash
kubectl scale deployment aam-api --replicas=10 -n aam-registry
```

### Caching

Enable Redis caching:

```yaml
# config.yaml
cache:
  enabled: true
  redis_url: redis://localhost:6379
  ttl_seconds: 300
```

### CDN

Use CDN for package downloads:

```yaml
# config.yaml
cdn:
  enabled: true
  base_url: https://cdn.yourcompany.com
  provider: cloudflare  # or "cloudfront", "fastly"
```

## Cost Optimization

**Compute:** Start with 1-2 replicas, scale based on load

**Database:** Use managed service with automated backups

**Storage:** S3 lifecycle policies to move old packages to Glacier

**CDN:** Cache package archives to reduce S3 costs

## Next Steps

- [HTTP Registry](http-registry.md) - Registry features and API
- [Package Signing](signing.md) - Enable signing verification
- [Security](../concepts/security.md) - Security best practices
- [Troubleshooting](../troubleshooting/index.md) - Common issues
