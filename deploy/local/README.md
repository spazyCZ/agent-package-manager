# AAM Local Deployment

Docker Compose deployment for local development and production-like testing.

## Quick Start

### Development (recommended)

```bash
# 1. Copy environment file
cp deploy/local/.env.example deploy/local/.env

# 2. Start all services with hot reload
docker compose -f deploy/local/docker-compose.yml \
  -f deploy/local/docker-compose.dev.yml up -d

# 3. Run database migrations
docker compose -f deploy/local/docker-compose.yml exec backend alembic upgrade head

# 4. View logs
docker compose -f deploy/local/docker-compose.yml logs -f
```

### Infrastructure Only

Start only the backing services (useful when running backend/web natively):

```bash
docker compose -f deploy/local/docker-compose.yml up -d postgres redis minio
```

### Production-Like

```bash
# Copy and configure environment file with secure values
cp deploy/local/.env.example deploy/local/.env
# Edit .env — set real SECRET_KEY, passwords, domain, etc.

# Build and start all services including Nginx
docker compose -f deploy/local/docker-compose.yml up -d --build

# Run database migrations
docker compose -f deploy/local/docker-compose.yml exec backend alembic upgrade head
```

## Services

| Service    | Port(s)     | Description              |
|------------|-------------|--------------------------|
| Nginx      | 80, 443     | Reverse proxy            |
| Web        | 3000        | React frontend           |
| Backend    | 8000        | FastAPI backend          |
| PostgreSQL | 5432        | PostgreSQL 16 database   |
| Redis      | 6379        | Redis 7 cache            |
| MinIO      | 9000, 9001  | S3-compatible storage    |

## Architecture

```
                    ┌─────────────┐
                    │   Nginx     │ :80/:443
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
      ┌─────────┐   ┌───────────┐   ┌─────────┐
      │   Web   │   │  Backend  │   │  MinIO  │
      │  :3000  │   │   :8000   │   │  :9000  │
      └─────────┘   └─────┬─────┘   └─────────┘
                          │
                ┌─────────┴─────────┐
                │                   │
                ▼                   ▼
          ┌──────────┐       ┌───────────┐
          │ Postgres │       │   Redis   │
          │  :5432   │       │   :6379   │
          └──────────┘       └───────────┘
```

## Database Maintenance

```bash
# Run migrations
docker compose -f deploy/local/docker-compose.yml exec backend alembic upgrade head

# Create a new migration
docker compose -f deploy/local/docker-compose.yml exec backend \
  alembic revision --autogenerate -m "description"

# Rollback one migration
docker compose -f deploy/local/docker-compose.yml exec backend alembic downgrade -1

# Backup PostgreSQL
docker compose -f deploy/local/docker-compose.yml exec postgres \
  pg_dump -U aam aam > backup.sql

# Restore PostgreSQL
docker compose -f deploy/local/docker-compose.yml exec -T postgres \
  psql -U aam aam < backup.sql
```

## SSL/TLS (local production-like testing)

1. Place certificates in `deploy/local/ssl/`:
   - `ssl/cert.pem`
   - `ssl/key.pem`
2. Uncomment the HTTPS server block in `nginx/nginx.conf`
3. Update the HTTP server to redirect to HTTPS

## Troubleshooting

```bash
# Check service status
docker compose -f deploy/local/docker-compose.yml ps

# View logs for a specific service
docker compose -f deploy/local/docker-compose.yml logs -f backend

# Restart a service
docker compose -f deploy/local/docker-compose.yml restart backend

# Clear all data and restart from scratch
docker compose -f deploy/local/docker-compose.yml down -v
docker compose -f deploy/local/docker-compose.yml up -d --build
```
