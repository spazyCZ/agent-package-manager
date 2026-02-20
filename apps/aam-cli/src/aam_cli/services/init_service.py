"""Package initialization (scaffolding) service.

Non-interactive package scaffolding logic shared between the CLI ``aam init``
command and the ``aam_init_package`` MCP tool. Creates a directory structure
with ``aam.yaml`` manifest and artifact subdirectories.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from typing import Any

from aam_cli.utils.naming import format_invalid_package_name_message, validate_package_name
from aam_cli.utils.yaml_utils import dump_yaml

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

VALID_ARTIFACT_TYPES: list[str] = ["skills", "agents", "prompts", "instructions"]
VALID_PLATFORMS: list[str] = ["cursor", "claude", "copilot", "codex"]

# Default platform-specific configurations
DEFAULT_PLATFORM_CONFIGS: dict[str, dict[str, Any]] = {
    "cursor": {
        "skill_scope": "project",
        "deploy_instructions_as": "rules",
    },
    "claude": {"merge_instructions": True},
    "copilot": {"merge_instructions": True},
    "codex": {"skill_scope": "project"},
}

################################################################################
#                                                                              #
# SERVICE FUNCTION                                                             #
#                                                                              #
################################################################################


def init_package(
    name: str,
    path: str | None = None,
    version: str = "1.0.0",
    description: str | None = None,
    author: str | None = None,
    license_name: str = "Apache-2.0",
    artifact_types: list[str] | None = None,
    platforms: list[str] | None = None,
) -> dict[str, Any]:
    """Scaffold a brand-new AAM package with directory structure and manifest.

    Creates the package directory (if needed), artifact subdirectories,
    and an ``aam.yaml`` manifest populated with the provided metadata.
    This is the non-interactive equivalent of ``aam init``.

    Args:
        name: Package name (e.g., "my-skills" or "@org/my-skills").
            Must be lowercase with optional ``@scope/`` prefix.
        path: Parent directory in which to create the package folder.
            Defaults to the current working directory. When ``path``
            is provided the package folder is created as
            ``<path>/<bare-name>/``.
        version: Semantic version string. Defaults to "1.0.0".
        description: One-line package description.
        author: Package author or organisation.
        license_name: SPDX licence identifier. Defaults to "Apache-2.0".
        artifact_types: Which artifact directories to scaffold.
            Defaults to all four: skills, agents, prompts, instructions.
            Invalid types are rejected.
        platforms: Target platforms to configure.
            Defaults to ["cursor"]. Invalid platforms are rejected.

    Returns:
        InitResult dict with ``package_name``, ``package_dir``,
        ``manifest_path``, ``artifact_types``, ``platforms``,
        and ``directories_created``.

    Raises:
        ValueError: If *name* is invalid or *artifact_types* / *platforms*
            contain unrecognised values.
    """
    logger.info(f"Initializing package: name='{name}', path='{path}'")

    # -----
    # Step 1: Validate package name
    # -----
    if not validate_package_name(name):
        raise ValueError(
            f"[AAM_INVALID_ARGUMENT] {format_invalid_package_name_message(name)}"
        )

    # -----
    # Step 2: Validate and default artifact types
    # -----
    if artifact_types is None:
        selected_types = list(VALID_ARTIFACT_TYPES)
    else:
        invalid = [t for t in artifact_types if t not in VALID_ARTIFACT_TYPES]
        if invalid:
            raise ValueError(
                f"[AAM_INVALID_ARGUMENT] Invalid artifact types: {invalid}. "
                f"Valid types: {VALID_ARTIFACT_TYPES}"
            )
        selected_types = list(artifact_types)

    # -----
    # Step 3: Validate and default platforms
    # -----
    if platforms is None:
        selected_platforms = ["cursor"]
    else:
        invalid = [p for p in platforms if p not in VALID_PLATFORMS]
        if invalid:
            raise ValueError(
                f"[AAM_INVALID_ARGUMENT] Invalid platforms: {invalid}. "
                f"Valid platforms: {VALID_PLATFORMS}"
            )
        selected_platforms = list(platforms)

    # -----
    # Step 4: Determine package directory
    # -----
    # The bare name is the part after the optional @scope/ prefix.
    bare_name = name.split("/")[-1] if "/" in name else name
    parent = Path(path) if path else Path.cwd()
    pkg_dir = parent / bare_name

    # -----
    # Step 5: Create directory structure
    # -----
    directories_created: list[str] = []

    pkg_dir.mkdir(parents=True, exist_ok=True)
    directories_created.append(str(pkg_dir))

    for atype in selected_types:
        artifact_dir = pkg_dir / atype
        artifact_dir.mkdir(parents=True, exist_ok=True)
        directories_created.append(str(artifact_dir))

    logger.info(
        f"Created {len(directories_created)} directories for package '{name}'"
    )

    # -----
    # Step 6: Build manifest data
    # -----
    manifest_data: dict[str, Any] = {
        "name": name,
        "version": version,
    }

    if description:
        manifest_data["description"] = description
    if author:
        manifest_data["author"] = author
    if license_name:
        manifest_data["license"] = license_name

    # Artifact stubs — empty lists ready for the user to populate
    manifest_data["artifacts"] = {atype: [] for atype in VALID_ARTIFACT_TYPES}

    manifest_data["dependencies"] = {}

    # Platform-specific configuration
    platforms_config: dict[str, Any] = {}
    for plat in selected_platforms:
        if plat in DEFAULT_PLATFORM_CONFIGS:
            platforms_config[plat] = dict(DEFAULT_PLATFORM_CONFIGS[plat])
    manifest_data["platforms"] = platforms_config

    # -----
    # Step 7: Write aam.yaml
    # -----
    manifest_path = pkg_dir / "aam.yaml"
    dump_yaml(manifest_data, manifest_path)

    logger.info(f"Package initialized successfully: manifest='{manifest_path}'")

    return {
        "package_name": name,
        "package_dir": str(pkg_dir),
        "manifest_path": str(manifest_path),
        "artifact_types": selected_types,
        "platforms": selected_platforms,
        "directories_created": directories_created,
    }
