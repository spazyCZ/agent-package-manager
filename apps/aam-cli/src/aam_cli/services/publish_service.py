"""Publish service for AAM.

Orchestrates package publishing to configured registries.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from typing import Any

from aam_cli.core.config import load_config
from aam_cli.core.manifest import load_manifest
from aam_cli.registry.factory import create_registry
from aam_cli.utils.checksum import calculate_sha256

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


def publish_package(
    registry_name: str | None = None,
    tag: str = "latest",
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Publish a packed ``.aam`` archive to a configured registry.

    Must be run from (or pointed at) a directory containing ``aam.yaml``
    and at least one ``.aam`` archive.

    Args:
        registry_name: Target registry name. Uses default if None.
        tag: Distribution tag (e.g., "latest", "beta").
        project_dir: Package directory. Defaults to cwd.

    Returns:
        PublishResult dict per data-model.md.

    Raises:
        ValueError: If no manifest, no archive, or registry errors.
    """
    logger.info(
        f"Publishing package: registry='{registry_name}', tag='{tag}'"
    )

    pkg_path = project_dir or Path.cwd()

    # -----
    # Step 1: Load manifest
    # -----
    try:
        manifest = load_manifest(pkg_path)
    except FileNotFoundError as exc:
        raise ValueError(
            "[AAM_MANIFEST_NOT_FOUND] No aam.yaml found. "
            "Run 'aam init' or 'aam create-package' first."
        ) from exc

    # -----
    # Step 2: Find the .aam archive
    # -----
    archive_candidates = list(pkg_path.glob("*.aam"))
    if not archive_candidates:
        raise ValueError(
            "[AAM_MANIFEST_INVALID] No .aam archive found. "
            "Run 'aam pack' first."
        )

    archive_path = archive_candidates[0]

    # -----
    # Step 3: Get the target registry
    # -----
    config = load_config()

    if registry_name:
        reg_source = config.get_registry_by_name(registry_name)
        if not reg_source:
            raise ValueError(
                f"[AAM_REGISTRY_NOT_FOUND] Registry '{registry_name}' "
                f"not found. Run 'aam registry list'."
            )
    else:
        reg_source = config.get_default_registry()
        if not reg_source:
            raise ValueError(
                "[AAM_REGISTRY_NOT_CONFIGURED] No registries configured. "
                "Run 'aam registry init' to create one."
            )

    # -----
    # Step 4: Verify checksum
    # -----
    checksum = calculate_sha256(archive_path)

    # -----
    # Step 5: Publish
    # -----
    reg = create_registry(reg_source)
    reg.publish(archive_path)

    archive_size = archive_path.stat().st_size

    logger.info(
        f"Published {manifest.name}@{manifest.version} "
        f"to registry '{reg_source.name}'"
    )

    return {
        "package_name": manifest.name,
        "version": manifest.version,
        "registry": reg_source.name,
        "archive_size": archive_size,
        "checksum": checksum,
    }
