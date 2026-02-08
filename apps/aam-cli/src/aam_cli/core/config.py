"""AAM CLI configuration loading with 4-level precedence.

Precedence (highest → lowest):
  1. CLI flags (passed via ``overrides`` dict)
  2. Project config (``.aam/config.yaml``)
  3. Global config (``~/.aam/config.yaml``)
  4. Defaults (Pydantic model defaults)

Decision reference: plan.md Key Decision 6.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from aam_cli.utils.paths import (
    get_global_config_path,
    get_project_config_path,
)
from aam_cli.utils.yaml_utils import dump_yaml, load_yaml_optional

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONFIGURATION MODELS                                                         #
#                                                                              #
################################################################################


class RegistrySource(BaseModel):
    """A configured registry source."""

    name: str
    url: str  # file:///path or https://...
    type: str = "local"  # local, git, http
    default: bool = False


class SecurityConfig(BaseModel):
    """Security settings."""

    require_checksum: bool = True
    require_signature: bool = False
    on_signature_failure: str = "warn"  # warn, error, ignore


class AuthorConfig(BaseModel):
    """Author defaults for ``aam init``."""

    name: str | None = None
    email: str | None = None


class PublishConfig(BaseModel):
    """Publishing defaults."""

    default_scope: str = ""


class AamConfig(BaseModel):
    """Complete AAM configuration (merged global + project + CLI overrides).

    All fields have sensible defaults so the CLI works out-of-the-box
    with zero configuration.
    """

    default_platform: str = "cursor"
    active_platforms: list[str] = ["cursor"]
    registries: list[RegistrySource] = []
    security: SecurityConfig = SecurityConfig()
    author: AuthorConfig = AuthorConfig()
    publish: PublishConfig = PublishConfig()

    # -----
    # Helper methods
    # -----

    def get_default_registry(self) -> RegistrySource | None:
        """Return the default registry, or the first one if none is default.

        Returns:
            The default ``RegistrySource``, or ``None`` if no registries
            are configured.
        """
        for reg in self.registries:
            if reg.default:
                return reg
        # Fallback to first registry if available
        if self.registries:
            return self.registries[0]
        return None

    def get_registry_by_name(self, name: str) -> RegistrySource | None:
        """Find a registry by its user-defined name.

        Args:
            name: Registry name to look up.

        Returns:
            Matching ``RegistrySource`` or ``None``.
        """
        for reg in self.registries:
            if reg.name == name:
                return reg
        return None


################################################################################
#                                                                              #
# CONFIGURATION LOADING                                                        #
#                                                                              #
################################################################################


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge *override* into *base*, returning a new dict.

    Lists and non-dict values are replaced entirely by the override.
    Nested dicts are merged recursively.

    Args:
        base: Base dictionary (lower precedence).
        override: Override dictionary (higher precedence).

    Returns:
        Merged dictionary.
    """
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(
    project_dir: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> AamConfig:
    """Load configuration with 4-level precedence.

    Args:
        project_dir: Project root directory (for ``.aam/config.yaml``).
            Defaults to the current working directory.
        overrides: CLI flag overrides (highest precedence).

    Returns:
        Fully merged :class:`AamConfig` instance.
    """
    logger.info("Loading AAM configuration")

    # -----
    # Layer 4: Defaults (from Pydantic model)
    # -----
    merged: dict[str, Any] = {}

    # -----
    # Layer 3: Global config (~/.aam/config.yaml)
    # -----
    global_path = get_global_config_path()
    global_data = load_yaml_optional(global_path)
    if global_data:
        logger.debug(f"Loaded global config: {global_path}")
        merged = _deep_merge(merged, global_data)

    # -----
    # Layer 2: Project config (.aam/config.yaml)
    # -----
    project_path = get_project_config_path(project_dir)
    project_data = load_yaml_optional(project_path)
    if project_data:
        logger.debug(f"Loaded project config: {project_path}")
        merged = _deep_merge(merged, project_data)

    # -----
    # Layer 1: CLI flag overrides
    # -----
    if overrides:
        logger.debug(f"Applying CLI overrides: {list(overrides.keys())}")
        merged = _deep_merge(merged, overrides)

    # -----
    # Build the config model (Pydantic fills in defaults for missing keys)
    # -----
    config = AamConfig(**merged)

    logger.info(
        f"Config loaded: platform='{config.default_platform}', registries={len(config.registries)}"
    )
    return config


def save_global_config(config: AamConfig) -> None:
    """Save the configuration to the global config file.

    Only persists fields that differ from defaults, but for simplicity
    in v1 we write the full model.

    Args:
        config: Configuration to save.
    """
    global_path = get_global_config_path()
    logger.info(f"Saving global config: path='{global_path}'")

    data = config.model_dump(mode="json")
    # Convert RegistrySource list of models to list of dicts
    dump_yaml(data, global_path)

    logger.info("Global config saved successfully")
