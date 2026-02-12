# AAM Deployment Review — GCP Infrastructure Analysis

> **Date:** February 9, 2026  
> **Scope:** Full review of Pulumi IaC components in `deploy/pulumi/`  
> **Project:** `aamregistry` (us-central1)

---

## Critical Issues (must fix before production)

### C1. Backend `GCS_BUCKET` env var is broken

- **Category:** Reliability
- **File:** `components/backend_service.py` (line 98-101)
- **Issue:** The `GCS_BUCKET` environment variable has `value_source: None`
  instead of the actual bucket name. The backend cannot write or read package
  archives.
- **Fix:** Replace the broken env entry with a proper value:

```python
{"name": "GCS_BUCKET", "value": storage_bucket},
```

  Pass `storage_bucket` as a parameter (already wired in `__main__.py` but
  not used in the env block).
- **Effort:** S

### C2. Backend missing database and Redis connection env vars

- **Category:** Reliability
- **File:** `components/backend_service.py`
- **Issue:** The Cloud Run backend container receives `APP_ENV`,
  `STORAGE_BACKEND`, and a broken `GCS_BUCKET` — but no database connection
  string, no Redis host/port, and no reference to the DB password secret. The
  application cannot connect to Cloud SQL or Memorystore.
- **Fix:** Add environment variables for the database (via Cloud SQL Auth
  Proxy or direct private IP) and Redis. Reference the DB password from
  Secret Manager using `value_source`:

```python
{"name": "DB_HOST", "value": "/cloudsql/" + db_connection_name},
{"name": "DB_NAME", "value": "aam"},
{"name": "DB_USER", "value": "aam"},
{
    "name": "DB_PASSWORD",
    "value_source": {
        "secret_key_ref": {
            "secret": db_password_secret_id,
            "version": "latest",
        },
    },
},
{"name": "REDIS_HOST", "value": redis_host},
{"name": "REDIS_PORT", "value": str(redis_port)},
```

  Also add the Cloud SQL Auth Proxy as a sidecar or use the Cloud SQL
  connector library (recommended for Cloud Run v2).
- **Effort:** M

### C3. No dedicated service accounts

- **Category:** Security
- **File:** `components/backend_service.py`, `components/web_service.py`
- **Issue:** Neither Cloud Run service specifies a `service_account`. Both
  use the default Compute Engine service account, which has overly broad
  permissions (`roles/editor` by default). This violates least-privilege.
- **Fix:** Create per-service IAM service accounts with minimal roles:

  **Backend SA** (`aam-backend-{env}@aamregistry.iam.gserviceaccount.com`):
  - `roles/cloudsql.client` (Cloud SQL access)
  - `roles/storage.objectAdmin` (GCS read/write on its bucket)
  - `roles/secretmanager.secretAccessor` (read secrets)

  **Web SA** (`aam-web-{env}@aamregistry.iam.gserviceaccount.com`):
  - No additional roles needed (serves static files)

  Add a new `ServiceAccounts` component or create them inline.
- **Effort:** M

### C4. Web `VITE_API_URL` points to raw Cloud Run URL

- **Category:** Networking / Security
- **File:** `components/web_service.py` (line 88)
- **Issue:** `VITE_API_URL` is set to `backend_service.url` (the Cloud Run
  `*.run.app` URL), not `https://api.{env}.aamregistry.io`. The SPA will
  make API calls directly to the Cloud Run URL, bypassing the load balancer,
  CDN, WAF, and the custom domain SSL certificate. This also causes CORS
  issues.
- **Fix:** Pass the `api_domain` from config and set:

```python
{"name": "VITE_API_URL", "value": f"https://{api_domain}"},
```

  **Important:** `VITE_*` variables are baked in at build time, so the
  Docker image must be built per environment or use runtime config injection
  via Nginx.
- **Effort:** M

---

## High-Priority Improvements

### H1. Restrict Cloud Run ingress to load balancer only

- **Category:** Security
- **File:** `components/backend_service.py`, `components/web_service.py`
- **Issue:** Both services use `INGRESS_TRAFFIC_ALL`, meaning anyone with
  the `*.run.app` URL can bypass the load balancer (and any future WAF).
- **Fix:** Change to `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` for both:

```python
ingress="INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER",
```

  This ensures traffic only flows through the Global HTTPS LB.
- **Effort:** S
- **Impact:** High — closes a direct access bypass

### H2. Add Cloud Armor WAF policy

- **Category:** Security
- **File:** `components/load_balancer.py`
- **Issue:** No Cloud Armor security policy protects the load balancer.
  There is no DDoS protection, rate limiting, geo-blocking, or OWASP
  ModSecurity CRS rules.
- **Fix:** Create a `gcp.compute.SecurityPolicy` with:
  - OWASP ModSecurity CRS rules (preconfigured `evaluatePreconfiguredWaf`)
  - Rate limiting rule (e.g. 1000 req/min per IP)
  - Optional geo-restriction

  Attach the policy to both backend services in the load balancer:

```python
security_policy = gcp.compute.SecurityPolicy(
    f"{name}-waf",
    project=project,
    rules=[...],
)
# Then on BackendService:
# security_policy=security_policy.id,
```

- **Effort:** M
- **Impact:** High — required for production security posture

### H3. Add monitoring for the API domain

- **Category:** Observability
- **File:** `components/monitoring.py`
- **Issue:** The uptime check only monitors `{env}.aamregistry.io/health`
  (the web domain). The API domain (`api.{env}.aamregistry.io`) has no
  uptime monitoring.
- **Fix:** Accept `api_domain` as a parameter and create a second uptime
  check:

```python
self.api_uptime_check = gcp.monitoring.UptimeCheckConfig(
    f"{name}-api-health-check",
    display_name=f"AAM Backend API Health ({environment})",
    monitored_resource={
        "type": "uptime_url",
        "labels": {"project_id": project, "host": api_domain},
    },
    http_check={"path": "/health", "port": 443, "use_ssl": True, "validate_ssl": True},
    period="60s",
    timeout="10s",
)
```

- **Effort:** S
- **Impact:** High — essential for prod incident detection

### H4. Add alerting policies and notification channels

- **Category:** Observability
- **File:** `components/monitoring.py`
- **Issue:** Uptime checks exist but there are no alerting policies or
  notification channels. Nobody gets paged when the service goes down.
- **Fix:** Add:
  1. A notification channel (email, Slack, PagerDuty)
  2. Alerting policies for: uptime check failure, Cloud Run error rate > 1%,
     Cloud Run latency P95 > 2s, Cloud SQL CPU > 80%, Redis memory > 80%

```python
notification_channel = gcp.monitoring.NotificationChannel(
    f"{name}-email",
    type="email",
    labels={"email_address": "ops@example.com"},  # Replace with your alerting email
)
alert_policy = gcp.monitoring.AlertPolicy(
    f"{name}-uptime-alert",
    display_name=f"AAM Uptime Alert ({environment})",
    conditions=[...],
    notification_channels=[notification_channel.name],
    alert_strategy={"auto_close": "1800s"},
)
```

- **Effort:** M
- **Impact:** High — no alerting = no incident response

### H5. Reduce uvicorn workers to 1 on Cloud Run

- **Category:** Performance / Cost
- **File:** `deploy/docker/backend/Dockerfile` (line 60)
- **Issue:** The backend starts with `--workers 4`, but Cloud Run scales by
  adding container instances, not by having multiple workers per instance.
  Running 4 workers in a 1-CPU container causes contention and wastes
  memory.
- **Fix:** Change to `--workers 1` or use `--workers 1 --loop uvloop` for
  better async performance. Cloud Run's concurrency setting
  (`max_instance_request_concurrency`) handles load distribution.
- **Effort:** S
- **Impact:** Medium — reduces memory per instance, improves cold start time

---

## Medium-Priority Improvements

### M1. Project-per-environment isolation

- **Category:** Security / Compliance
- **Issue:** All three environments (dev, test, prod) run in a single GCP
  project. A misconfiguration in dev could affect prod resources. IAM
  boundaries are not enforced between environments.
- **Fix:** Create separate GCP projects: `aamregistry-dev`,
  `aamregistry-test`, `aamregistry-prod` under an organization. Share the
  Artifact Registry repo via cross-project IAM.
- **Effort:** L
- **Impact:** Medium — significantly improves security boundary

### M2. Add CORS configuration to the backend

- **Category:** Security
- **File:** Backend application code (not Pulumi)
- **Issue:** With separate domains for web (`{env}.aamregistry.io`) and API
  (`api.{env}.aamregistry.io`), the browser will enforce CORS. The backend
  must send correct `Access-Control-Allow-Origin` headers.
- **Fix:** Configure FastAPI CORS middleware:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"https://{env}.aamregistry.io"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
```

  Pass the allowed origin via an env var from Pulumi config.
- **Effort:** S
- **Impact:** Medium — API calls from the SPA will fail without this

### M3. Add GCS object lifecycle rules for non-prod

- **Category:** Cost
- **File:** `components/storage.py`
- **Issue:** Dev and test package archives accumulate indefinitely. Only
  multipart upload cleanup exists.
- **Fix:** Add a lifecycle rule to delete objects older than 90 days in
  non-prod:

```python
if environment != "prod":
    lifecycle_rules.append({
        "action": {"type": "Delete"},
        "condition": {"age": 90},
    })
```

- **Effort:** S
- **Impact:** Low-Medium — prevents cost creep in non-prod

### M4. Scale VPC connector to zero in dev

- **Category:** Cost
- **File:** `components/network.py` (line 113-116)
- **Issue:** The VPC connector runs `min_instances=2` in all environments,
  including dev. VPC connector instances cost ~$0.01/hr each.
- **Fix:** Make `min_instances` configurable per environment:
  - dev: `min_instances=2` (minimum allowed, cannot go lower)
  - test: `min_instances=2`
  - prod: `min_instances=3`

  **Note:** VPC Access connector minimum is 2, so this is already at the
  floor. Consider migrating to **Direct VPC Egress** (Cloud Run v2 feature)
  which eliminates VPC connectors entirely:

```python
"vpc_access": {
    "egress": "PRIVATE_RANGES_ONLY",
    "network_interfaces": [{"network": network_id, "subnetwork": subnet_id}],
},
```

- **Effort:** M
- **Impact:** Medium — reduces cost and removes a bottleneck

### M5. Separate SSL certificates per domain

- **Category:** Networking
- **File:** `components/load_balancer.py`
- **Issue:** A single managed SSL certificate covers all domains (web, api,
  and apex). Google-managed certs have a limit of 100 domains per
  certificate but can be slow to provision when multiple domains are
  pending DNS validation simultaneously.
- **Fix:** Create separate certificates for the web domain and API domain.
  For prod, create a third certificate for the apex domain. This improves
  provisioning reliability.
- **Effort:** S
- **Impact:** Low-Medium — improves SSL provisioning reliability

### M6. Enable Cloud Run request logging and trace sampling

- **Category:** Observability
- **File:** `components/backend_service.py`, application code
- **Issue:** No explicit structured logging or trace configuration. Cloud
  Run logs go to Cloud Logging by default, but without correlation to
  traces or custom labels.
- **Fix:** Set environment variables for OpenTelemetry auto-instrumentation:

```python
{"name": "OTEL_EXPORTER_OTLP_ENDPOINT", "value": "https://otel-collector..."},
{"name": "OTEL_SERVICE_NAME", "value": f"aam-backend-{environment}"},
{"name": "OTEL_TRACES_SAMPLER", "value": "parentbased_traceidratio"},
{"name": "OTEL_TRACES_SAMPLER_ARG", "value": "0.1"},
```

  Or use the built-in Cloud Trace integration.
- **Effort:** M
- **Impact:** Medium — essential for debugging production issues

### M7. Add Cloud SQL connection limits and pgbouncer

- **Category:** Reliability
- **Issue:** Cloud Run can scale to many instances (up to 10 in prod), each
  potentially opening multiple DB connections. With `db-f1-micro` (dev) the
  connection limit is ~25. With 4 uvicorn workers each might open a pool.
- **Fix:**
  1. Reduce uvicorn workers to 1 (see H5)
  2. Use Cloud SQL Auth Proxy sidecar with connection pooling
  3. Or use the `cloud-sql-python-connector` library with SQLAlchemy's
     built-in pool (pool_size=5, max_overflow=2)
  4. Set `max_connections` flag on Cloud SQL for prod
- **Effort:** M
- **Impact:** Medium — prevents connection exhaustion under load

---

## Low-Priority / Future Enhancements

### L1. Add Cloud Build triggers to IaC

- **Category:** CI/CD
- **Issue:** Container images are built manually or via helper scripts. No
  automated CI/CD pipeline exists in the Pulumi IaC.
- **Fix:** Add `gcp.cloudbuild.Trigger` resources that:
  1. Build + push images on merge to `develop` (test) and `main` (prod)
  2. Run `pulumi up` via a Cloud Build step after image push
  3. Use Artifact Registry image digest (not just tag) for immutability
- **Effort:** L

### L2. Add Artifact Registry vulnerability scanning

- **Category:** Security
- **Issue:** No container image scanning configured. Vulnerabilities in base
  images or dependencies go undetected.
- **Fix:** Enable Container Analysis on the Artifact Registry repository
  (automatic on-push scanning) and create an alerting policy for CRITICAL
  CVEs.
- **Effort:** S

### L3. Add GCS signed URLs for package downloads

- **Category:** Security
- **Issue:** The package storage bucket access model is not defined. If
  packages are served directly, the bucket would need public access.
- **Fix:** Generate short-lived signed URLs in the backend for package
  downloads. Never expose the bucket publicly.
- **Effort:** M

### L4. Add Cloud SQL automated maintenance notifications

- **Category:** Reliability
- **Issue:** Maintenance window is set (Sunday 4am) but no notification
  channel is configured for maintenance events.
- **Fix:** Set `maintenance_window.notifications_enabled = true` once
  notification channels (H4) are in place.
- **Effort:** S

### L5. Add budget alerts

- **Category:** Cost
- **Issue:** No GCP billing budget or alerts configured. Unexpected spend
  can go unnoticed.
- **Fix:** Create a `gcp.billing.Budget` resource with thresholds at 50%,
  80%, and 100% of expected monthly spend per environment.
- **Effort:** M

### L6. Consider Cloud Run Jobs for migrations

- **Category:** CI/CD / Reliability
- **Issue:** Database migrations (`alembic upgrade head`) are run manually
  via `docker compose exec`. In cloud environments, there is no defined
  migration strategy.
- **Fix:** Create a Cloud Run Job for Alembic migrations that runs as a
  pre-deploy step. This ensures migrations run in the correct network
  context with proper IAM.
- **Effort:** M

### L7. Add Artifact Registry cleanup policy

- **Category:** Cost
- **Issue:** Old container images accumulate in Artifact Registry.
- **Fix:** Add a cleanup policy to delete untagged images older than 30 days
  and keep only the last 10 tagged versions per image.
- **Effort:** S

### L8. Enable Cloud SQL query insights

- **Category:** Observability
- **Issue:** No query-level performance monitoring for the database.
- **Fix:** Enable Query Insights on the Cloud SQL instance:

```python
"insights_config": {
    "query_insights_enabled": True,
    "query_plans_per_minute": 5,
    "record_application_tags": True,
    "record_client_address": True,
},
```

- **Effort:** S

---

## Summary

| Priority | Count | Key Theme                                    |
|----------|-------|----------------------------------------------|
| Critical | 4     | Broken env vars, missing SA, bypassed LB     |
| High     | 5     | Ingress lockdown, WAF, alerting, monitoring  |
| Medium   | 7     | CORS, cost, VPC egress, observability        |
| Low      | 8     | CI/CD, scanning, budgets, query insights     |

**Recommended order of execution:**
1. Fix C1 + C2 (broken env vars) — backend cannot function
2. Fix C3 (service accounts) + H1 (ingress lockdown) — security baseline
3. Fix C4 (VITE_API_URL) + M2 (CORS) — SPA cannot talk to API
4. Add H2 (Cloud Armor) + H3/H4 (monitoring + alerting)
5. Optimize H5 (workers) + M4 (VPC connector)
6. Tackle medium and low items incrementally
