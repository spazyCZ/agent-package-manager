"""
AAM Infrastructure — Pulumi Entry Point.

Provisions all GCP resources for the active stack (dev / test / prod).
Each component is self-contained and idempotent.

Usage:
    cd deploy/pulumi
    pulumi stack select dev   # or test / prod
    pulumi up
"""

################################################################################
#                                                                              #
#  IMPORTS & DEPENDENCIES                                                      #
#                                                                              #
################################################################################

import logging

import pulumi

from config import load_config
from components.network import Network
from components.database import Database
from components.cache import Cache
from components.storage import Storage
from components.registry import ArtifactRegistry
from components.secrets import Secrets
from components.backend_service import BackendService
from components.web_service import WebService
from components.domain_mapping import DomainMapping
from components.monitoring import Monitoring

################################################################################
#                                                                              #
#  LOGGER                                                                      #
#                                                                              #
################################################################################

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
#  MAIN                                                                        #
#                                                                              #
################################################################################

# -------------------------------------------------------------------------
# Load typed configuration from the active stack
# -------------------------------------------------------------------------
cfg = load_config()
prefix = f"aam-{cfg.environment}"

logger.info(
    "Provisioning AAM infrastructure: env=%s, project=%s, region=%s",
    cfg.environment,
    cfg.gcp_project,
    cfg.gcp_region,
)

# -------------------------------------------------------------------------
# 1. VPC Network & VPC Connector
# -------------------------------------------------------------------------
network = Network(
    prefix,
    project=cfg.gcp_project,
    region=cfg.gcp_region,
    environment=cfg.environment,
)

# -------------------------------------------------------------------------
# 2. Cloud SQL (PostgreSQL 16)
# -------------------------------------------------------------------------
database = Database(
    prefix,
    project=cfg.gcp_project,
    region=cfg.gcp_region,
    environment=cfg.environment,
    network_id=network.network.id,
    private_connection=network.private_connection,
    tier=cfg.db_tier,
    disk_size_gb=cfg.db_disk_size_gb,
    high_availability=cfg.db_high_availability,
    backup_enabled=cfg.db_backup_enabled,
)

# -------------------------------------------------------------------------
# 3. Memorystore (Redis 7)
# -------------------------------------------------------------------------
cache = Cache(
    prefix,
    project=cfg.gcp_project,
    region=cfg.gcp_region,
    environment=cfg.environment,
    network_id=network.network.id,
    tier=cfg.redis_tier,
    memory_size_gb=cfg.redis_memory_size_gb,
)

# -------------------------------------------------------------------------
# 4. GCS Bucket (package archives)
# -------------------------------------------------------------------------
storage = Storage(
    prefix,
    project=cfg.gcp_project,
    environment=cfg.environment,
    location=cfg.storage_location,
    storage_class=cfg.storage_class,
)

# -------------------------------------------------------------------------
# 5. Artifact Registry (Docker images)
# -------------------------------------------------------------------------
artifact_registry = ArtifactRegistry(
    prefix,
    project=cfg.gcp_project,
    region=cfg.gcp_region,
)

# -------------------------------------------------------------------------
# 6. Secret Manager
# -------------------------------------------------------------------------
secrets = Secrets(
    prefix,
    project=cfg.gcp_project,
    environment=cfg.environment,
    db_password=database.password.result,
)

# -------------------------------------------------------------------------
# 7. Cloud Run — Backend (FastAPI)
# -------------------------------------------------------------------------
backend_service = BackendService(
    prefix,
    project=cfg.gcp_project,
    region=cfg.gcp_region,
    environment=cfg.environment,
    image=cfg.backend_image,
    cpu=cfg.backend_cpu,
    memory=cfg.backend_memory,
    min_instances=cfg.backend_min_instances,
    max_instances=cfg.backend_max_instances,
    concurrency=cfg.backend_concurrency,
    vpc_connector_id=network.vpc_connector.id,
    db_connection_name=database.connection_name,
    db_password_secret_id=secrets.db_password_secret.secret_id,
    redis_host=cache.host,
    redis_port=cache.port,
    storage_bucket=storage.bucket.name,
)

# -------------------------------------------------------------------------
# 8. Cloud Run — Web (React SPA)
# -------------------------------------------------------------------------
web_service = WebService(
    prefix,
    project=cfg.gcp_project,
    region=cfg.gcp_region,
    environment=cfg.environment,
    image=cfg.web_image,
    cpu=cfg.web_cpu,
    memory=cfg.web_memory,
    min_instances=cfg.web_min_instances,
    max_instances=cfg.web_max_instances,
    backend_url=backend_service.url,
)

# -------------------------------------------------------------------------
# 9. Cloud Run Domain Mappings (custom domains with managed SSL)
# -------------------------------------------------------------------------
domain_mappings = DomainMapping(
    prefix,
    project=cfg.gcp_project,
    region=cfg.gcp_region,
    services={
        cfg.domain: web_service.service,
        cfg.api_domain: backend_service.service,
    },
)

# -------------------------------------------------------------------------
# 10. Cloud Monitoring (uptime checks)
# -------------------------------------------------------------------------
monitoring = Monitoring(
    prefix,
    project=cfg.gcp_project,
    environment=cfg.environment,
    domain=cfg.domain,
)

# -------------------------------------------------------------------------
# Stack outputs
# -------------------------------------------------------------------------
pulumi.export("environment", cfg.environment)
pulumi.export("gcp_project", cfg.gcp_project)
pulumi.export("gcp_region", cfg.gcp_region)
pulumi.export("domain", cfg.domain)
pulumi.export("api_domain", cfg.api_domain)
pulumi.export("backend_url", backend_service.url)
pulumi.export("web_url", web_service.url)
pulumi.export("db_connection_name", database.connection_name)
pulumi.export("redis_host", cache.host)
pulumi.export("storage_bucket", storage.bucket.name)
