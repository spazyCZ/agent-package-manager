# =============================================================================
# Backend Dockerfile — Production (multi-stage)
# =============================================================================
# Image: Python 3.12-slim
# User:  non-root "app"
# Port:  8000
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder — install Python dependencies
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/aam-backend/pyproject.toml .
RUN pip install --no-cache-dir build && \
    pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Stage 2: Runtime — minimal production image
# ---------------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY apps/aam-backend/src/aam_backend ./aam_backend
COPY apps/aam-backend/alembic ./alembic
COPY apps/aam-backend/alembic.ini .

# Set ownership to non-root user
RUN chown -R app:app /app

USER app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "aam_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
