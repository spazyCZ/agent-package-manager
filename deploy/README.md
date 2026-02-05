# AAM Deployment

Docker Compose deployment for the Agent Package Manager.

## Quick Start

### Development

```bash
# Copy environment file
cp .env.example .env

# Start all services in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production

```bash
# Copy and configure environment file
cp .env.example .env
# Edit .env with secure passwords and your domain

# Build and start services
docker-compose up -d --build

# Run database migrations
docker-compose exec backend alembic upgrade head

# View logs
docker-compose logs -f
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80, 443 | Reverse proxy |
| web | 3000 | React frontend |
| backend | 8000 | FastAPI backend |
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Redis cache |
| minio | 9000, 9001 | S3-compatible storage |

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
      │ :3000   │   │   :8000   │   │  :9000  │
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

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key variables:

- `SECRET_KEY`: JWT signing key (must be secure in production)
- `POSTGRES_PASSWORD`: Database password
- `REDIS_PASSWORD`: Redis password
- `MINIO_ROOT_PASSWORD`: MinIO admin password

### SSL/TLS

For HTTPS support:

1. Place SSL certificates in the `ssl/` directory:
   - `ssl/cert.pem`
   - `ssl/key.pem`

2. Uncomment the HTTPS server block in `nginx.conf`

3. Update the HTTP server to redirect to HTTPS

### Scaling

For high availability, consider:

- Running multiple backend instances behind a load balancer
- Using managed PostgreSQL (RDS, Cloud SQL, etc.)
- Using managed Redis (ElastiCache, etc.)
- Using S3 instead of MinIO

## Maintenance

### Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Rollback
docker-compose exec backend alembic downgrade -1
```

### Backups

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U aam aam > backup.sql

# Restore PostgreSQL
docker-compose exec -T postgres psql -U aam aam < backup.sql
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail 100 backend
```

## Troubleshooting

### Services not starting

```bash
# Check service status
docker-compose ps

# Check logs for errors
docker-compose logs backend

# Restart a service
docker-compose restart backend
```

### Database connection issues

```bash
# Check if PostgreSQL is healthy
docker-compose exec postgres pg_isready -U aam

# Connect to database
docker-compose exec postgres psql -U aam aam
```

### Clear all data and restart

```bash
# Stop and remove containers, volumes
docker-compose down -v

# Rebuild and start
docker-compose up -d --build
```
