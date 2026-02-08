"""
Stack configuration helper.

Reads typed configuration values from the active Pulumi stack
(Pulumi.<stack>.yaml) and exposes them as a single dataclass
so that every component can import ``from config import cfg``.
"""

################################################################################
#                                                                              #
#  IMPORTS & DEPENDENCIES                                                      #
#                                                                              #
################################################################################

import logging
from dataclasses import dataclass

import pulumi

################################################################################
#                                                                              #
#  LOGGER                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
#  STACK CONFIGURATION                                                         #
#                                                                              #
################################################################################


@dataclass(frozen=True)
class StackConfig:
    """Typed representation of the active Pulumi stack configuration."""

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------
    environment: str
    gcp_project: str
    gcp_region: str

    # -------------------------------------------------------------------------
    # Cloud Run — Backend
    # -------------------------------------------------------------------------
    backend_image: str
    backend_cpu: str
    backend_memory: str
    backend_min_instances: int
    backend_max_instances: int
    backend_concurrency: int

    # -------------------------------------------------------------------------
    # Cloud Run — Web
    # -------------------------------------------------------------------------
    web_image: str
    web_cpu: str
    web_memory: str
    web_min_instances: int
    web_max_instances: int

    # -------------------------------------------------------------------------
    # Cloud SQL — PostgreSQL
    # -------------------------------------------------------------------------
    db_tier: str
    db_disk_size_gb: int
    db_high_availability: bool
    db_backup_enabled: bool

    # -------------------------------------------------------------------------
    # Memorystore — Redis
    # -------------------------------------------------------------------------
    redis_tier: str
    redis_memory_size_gb: int

    # -------------------------------------------------------------------------
    # GCS — Package Storage
    # -------------------------------------------------------------------------
    storage_location: str
    storage_class: str

    # -------------------------------------------------------------------------
    # Domain / Networking
    # -------------------------------------------------------------------------
    domain: str
    enable_cdn: bool


def load_config() -> StackConfig:
    """
    Load and validate configuration from the active Pulumi stack.

    Returns:
        StackConfig: Fully-typed configuration dataclass.

    Raises:
        pulumi.ConfigMissingError: If a required key is absent.
    """
    logger.info("Loading Pulumi stack configuration")
    config = pulumi.Config()

    stack_cfg = StackConfig(
        # General
        environment=config.require("environment"),
        gcp_project=config.require("gcp_project"),
        gcp_region=config.require("gcp_region"),
        # Backend
        backend_image=config.require("backend_image"),
        backend_cpu=config.require("backend_cpu"),
        backend_memory=config.require("backend_memory"),
        backend_min_instances=config.require_int("backend_min_instances"),
        backend_max_instances=config.require_int("backend_max_instances"),
        backend_concurrency=config.require_int("backend_concurrency"),
        # Web
        web_image=config.require("web_image"),
        web_cpu=config.require("web_cpu"),
        web_memory=config.require("web_memory"),
        web_min_instances=config.require_int("web_min_instances"),
        web_max_instances=config.require_int("web_max_instances"),
        # Database
        db_tier=config.require("db_tier"),
        db_disk_size_gb=config.require_int("db_disk_size_gb"),
        db_high_availability=config.require_bool("db_high_availability"),
        db_backup_enabled=config.require_bool("db_backup_enabled"),
        # Redis
        redis_tier=config.require("redis_tier"),
        redis_memory_size_gb=config.require_int("redis_memory_size_gb"),
        # Storage
        storage_location=config.require("storage_location"),
        storage_class=config.require("storage_class"),
        # Networking
        domain=config.require("domain"),
        enable_cdn=config.require_bool("enable_cdn"),
    )

    logger.info(
        "Stack configuration loaded: env=%s, project=%s, region=%s",
        stack_cfg.environment,
        stack_cfg.gcp_project,
        stack_cfg.gcp_region,
    )
    return stack_cfg
