# =============================================================================
# Web Dockerfile — Production (multi-stage)
# =============================================================================
# Stage 1: Node 20-alpine  → build React SPA
# Stage 2: Nginx alpine    → serve static assets
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder
# ---------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
COPY apps/aam-web/package.json ./apps/aam-web/

RUN npm ci --legacy-peer-deps

COPY . .

RUN npm run web:build

# ---------------------------------------------------------------------------
# Stage 2: Nginx — serve built assets
# ---------------------------------------------------------------------------
FROM nginx:alpine

COPY --from=builder /app/dist/apps/aam-web /usr/share/nginx/html
COPY deploy/local/nginx/nginx-web.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
