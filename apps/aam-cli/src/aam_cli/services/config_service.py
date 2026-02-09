"""Config service for AAM.

Provides get/set/list operations on AAM configuration.
Returns structured data for use by both CLI and MCP.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from typing import Any

from aam_cli.core.config import AamConfig, load_config, save_global_config

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# SERVICE FUNCTIONS                                                            #
#                                                                              #
################################################################################


def get_config(
    key: str | None = None,
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Get a configuration value or the full merged config.

    Args:
        key: Dotted config key (e.g., "default_platform", "author.name").
            If None, returns the full config.
        project_dir: Project root directory. Defaults to cwd.

    Returns:
        ConfigData dict per data-model.md with key, value, and source.

    Raises:
        ValueError: If the specified key does not exist.
    """
    logger.info(f"Getting config: key={key}")

    cfg = load_config(project_dir)

    if key is None:
        # -----
        # Return full merged config
        # -----
        return {
            "key": None,
            "value": cfg.model_dump(mode="json"),
            "source": "merged",
        }

    # -----
    # Resolve dotted key
    # -----
    value = _resolve_config_key(cfg, key)

    if value is None:
        raise ValueError(
            f"[AAM_INVALID_ARGUMENT] Unknown config key: {key}"
        )

    return {
        "key": key,
        "value": value,
        "source": "config",
    }


def set_config(key: str, value: str) -> dict[str, Any]:
    """Set a global configuration value.

    Args:
        key: Dotted config key (e.g., "default_platform").
        value: Value to set (string, will be coerced to target type).

    Returns:
        Updated ConfigData dict.

    Raises:
        ValueError: If the key is unknown or the value cannot be set.
    """
    logger.info(f"Setting config: key='{key}', value='{value}'")

    cfg = load_config()
    parts = key.split(".")

    if len(parts) == 1:
        # -----
        # Top-level key
        # -----
        if not hasattr(cfg, key):
            raise ValueError(
                f"[AAM_INVALID_ARGUMENT] Unknown config key: {key}"
            )
        setattr(cfg, key, value)

    elif len(parts) == 2:
        # -----
        # Nested key (e.g., author.name, security.require_checksum)
        # -----
        section, field = parts
        section_obj = getattr(cfg, section, None)
        if section_obj is None or not hasattr(section_obj, field):
            raise ValueError(
                f"[AAM_INVALID_ARGUMENT] Unknown config key: {key}"
            )

        current = getattr(section_obj, field)
        if isinstance(current, bool):
            setattr(section_obj, field, value.lower() in ("true", "1", "yes"))
        elif isinstance(current, int):
            setattr(section_obj, field, int(value))
        else:
            setattr(section_obj, field, value)
    else:
        raise ValueError(
            f"[AAM_INVALID_ARGUMENT] Unsupported config key depth: {key}"
        )

    save_global_config(cfg)

    logger.info(f"Config updated: key='{key}', value='{value}'")

    return {
        "key": key,
        "value": value,
        "source": "global",
    }


def list_config(
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """List all configuration values as a flat key-value dict.

    Args:
        project_dir: Project root directory. Defaults to cwd.

    Returns:
        Full merged config as dict.
    """
    logger.info("Listing all config values")

    cfg = load_config(project_dir)
    return cfg.model_dump(mode="json")


################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _resolve_config_key(cfg: AamConfig, key: str) -> Any:
    """Resolve a dotted config key to its value.

    Args:
        cfg: AAM configuration instance.
        key: Dotted key path (e.g., "author.name").

    Returns:
        The resolved value, or None if not found.
    """
    parts = key.split(".")

    if len(parts) == 1:
        return getattr(cfg, key, None)

    if len(parts) == 2:
        section, field = parts
        section_obj = getattr(cfg, section, None)
        if section_obj is not None:
            return getattr(section_obj, field, None)

    return None
