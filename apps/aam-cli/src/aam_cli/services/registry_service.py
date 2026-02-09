"""Registry service for AAM.

Provides list and add operations for AAM registry sources.
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

from aam_cli.core.config import (
    RegistrySource,
    load_config,
    save_global_config,
)

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


def list_registries(
    project_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """List all configured registries with accessibility info.

    Args:
        project_dir: Project root directory. Defaults to cwd.

    Returns:
        List of RegistryInfo dicts per data-model.md.
    """
    logger.info("Listing configured registries")

    cfg = load_config(project_dir)

    results: list[dict[str, Any]] = []
    for reg in cfg.registries:
        # -----
        # Check accessibility for local registries
        # -----
        accessible: bool | None = None
        if reg.url.startswith("file://"):
            from aam_cli.utils.paths import parse_file_url

            local_path = parse_file_url(reg.url)
            accessible = local_path.is_dir()

        results.append(
            {
                "name": reg.name,
                "url": reg.url,
                "type": reg.type,
                "is_default": reg.default,
                "accessible": accessible,
            }
        )

    logger.info(f"Listed {len(results)} registries")
    return results


def add_registry(
    name: str,
    url: str,
    set_default: bool = False,
) -> dict[str, Any]:
    """Add a new registry source to the global configuration.

    Validates name uniqueness and local path accessibility.

    Args:
        name: User-defined registry name.
        url: Registry URL (``file:///path`` or ``https://...``).
        set_default: Whether to set this as the default registry.

    Returns:
        RegistryInfo dict for the newly added registry.

    Raises:
        ValueError: If name already exists or local path is inaccessible.
    """
    logger.info(
        f"Adding registry: name='{name}', url='{url}', default={set_default}"
    )

    cfg = load_config()

    # -----
    # Validate name uniqueness
    # -----
    if cfg.get_registry_by_name(name):
        raise ValueError(
            f"[AAM_INVALID_ARGUMENT] Registry '{name}' already configured. "
            f"Remove it first with 'aam registry remove {name}'."
        )

    # -----
    # Validate local URL path exists
    # -----
    if url.startswith("file://"):
        from aam_cli.utils.paths import parse_file_url

        local_path = parse_file_url(url)
        if not local_path.is_dir():
            raise ValueError(
                f"[AAM_REGISTRY_NOT_FOUND] Registry path does not exist: "
                f"{local_path}"
            )

    # -----
    # Set as default if requested
    # -----
    if set_default:
        for existing_reg in cfg.registries:
            existing_reg.default = False

    reg_type = "local" if url.startswith("file://") else "http"

    cfg.registries.append(
        RegistrySource(
            name=name,
            url=url,
            type=reg_type,
            default=set_default,
        )
    )

    save_global_config(cfg)

    logger.info(f"Registry added: name='{name}'")

    return {
        "name": name,
        "url": url,
        "type": reg_type,
        "is_default": set_default,
        "accessible": None,
    }
