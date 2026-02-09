"""Install service for AAM.

Orchestrates package installation with dependency resolution,
archive download/extraction, and platform deployment.
Implements concurrency locking and atomic staging.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import shutil
import threading
from pathlib import Path
from typing import Any

from aam_cli.adapters.factory import create_adapter, is_supported_platform
from aam_cli.core.config import AamConfig
from aam_cli.core.installer import install_packages as core_install_packages
from aam_cli.core.resolver import resolve_dependencies
from aam_cli.core.workspace import (
    ensure_workspace,
    get_packages_dir,
    is_package_installed,
    read_lock_file,
)
from aam_cli.registry.factory import create_registry
from aam_cli.utils.naming import parse_package_spec

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONCURRENCY LOCK                                                             #
#                                                                              #
################################################################################

# In-process lock serializes all workspace-mutating operations
# (install, uninstall, publish, config set, registry add) to prevent
# race conditions when multiple MCP tool calls arrive concurrently.
_workspace_lock = threading.Lock()

################################################################################
#                                                                              #
# STAGING DIRECTORY HELPERS                                                    #
#                                                                              #
################################################################################

STAGING_DIR_NAME = ".tmp"


def _get_staging_dir(project_dir: Path) -> Path:
    """Return the staging directory path inside the workspace.

    Args:
        project_dir: Project root directory.

    Returns:
        Path to ``.aam/.tmp/``.
    """
    workspace = ensure_workspace(project_dir)
    staging = workspace / STAGING_DIR_NAME
    staging.mkdir(parents=True, exist_ok=True)
    return staging


def _cleanup_staging(project_dir: Path) -> None:
    """Remove the staging directory if it exists.

    Args:
        project_dir: Project root directory.
    """
    workspace_dir = get_packages_dir(project_dir).parent
    staging = workspace_dir / STAGING_DIR_NAME
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
        logger.debug("Staging directory cleaned up")


################################################################################
#                                                                              #
# SERVICE FUNCTIONS                                                            #
#                                                                              #
################################################################################


def install_packages(
    packages: list[str],
    config: AamConfig,
    platform: str | None = None,
    force: bool = False,
    no_deploy: bool = False,
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Install one or more packages with dependency resolution.

    Supports registry, local directory, and archive source formats.
    Uses an in-process lock to serialize workspace mutations and
    performs installs through a staging directory for atomicity.

    Args:
        packages: List of package specs (e.g., ["my-pkg", "other@1.0"]).
        config: AAM configuration with registry sources.
        platform: Target platform override.
        force: Reinstall even if already present.
        no_deploy: Download only, skip deployment.
        project_dir: Project root directory. Defaults to cwd.

    Returns:
        InstallResult dict per data-model.md.
    """
    logger.info(
        f"Installing packages: specs={packages}, force={force}, "
        f"no_deploy={no_deploy}"
    )

    effective_dir = project_dir or Path.cwd()
    platform_name = platform or config.default_platform

    installed: list[dict[str, Any]] = []
    already_installed: list[str] = []
    failed: list[dict[str, Any]] = []
    deps_resolved = 0

    with _workspace_lock:
        for package_spec in packages:
            try:
                result = _install_single_package(
                    package_spec=package_spec,
                    config=config,
                    platform_name=platform_name,
                    force=force,
                    no_deploy=no_deploy,
                    project_dir=effective_dir,
                )

                if result["status"] == "installed":
                    installed.append(result["info"])
                    deps_resolved += result.get("deps_resolved", 0)
                elif result["status"] == "already_installed":
                    already_installed.append(result["name"])

            except Exception as exc:
                logger.error(
                    f"Failed to install '{package_spec}': {exc}",
                    exc_info=True,
                )
                failed.append(
                    {
                        "package": package_spec,
                        "code": "AAM_PACKAGE_NOT_FOUND",
                        "message": str(exc),
                    }
                )

    logger.info(
        f"Install complete: installed={len(installed)}, "
        f"already={len(already_installed)}, failed={len(failed)}"
    )

    return {
        "installed": installed,
        "already_installed": already_installed,
        "failed": failed,
        "dependencies_resolved": deps_resolved,
    }


################################################################################
#                                                                              #
# SINGLE PACKAGE INSTALL                                                       #
#                                                                              #
################################################################################


def _install_single_package(
    package_spec: str,
    config: AamConfig,
    platform_name: str,
    force: bool,
    no_deploy: bool,
    project_dir: Path,
) -> dict[str, Any]:
    """Install a single package from registry.

    Uses staging directory for atomicity: extracts to ``.aam/.tmp/``
    first, then moves to final location and updates lock file only
    after successful completion.

    Args:
        package_spec: Package spec (e.g., "my-pkg" or "my-pkg@1.0").
        config: AAM configuration.
        platform_name: Target platform.
        force: Reinstall even if present.
        no_deploy: Skip deployment.
        project_dir: Project root directory.

    Returns:
        Dict with status, name, and optionally info/deps_resolved.

    Raises:
        ValueError: If the package cannot be found or installed.
    """
    # -----
    # Step 1: Parse package spec
    # -----
    pkg_name, pkg_version = parse_package_spec(package_spec)

    # -----
    # Step 2: Check if already installed
    # -----
    if not force and is_package_installed(pkg_name, project_dir):
        lock = read_lock_file(project_dir)
        existing = lock.packages.get(pkg_name)
        if existing:
            return {
                "status": "already_installed",
                "name": pkg_name,
            }

    # -----
    # Step 3: Check for configured registries
    # -----
    if not config.registries:
        raise ValueError(
            "[AAM_REGISTRY_NOT_CONFIGURED] No registries configured. "
            "Run 'aam registry init' to create one."
        )

    # -----
    # Step 4: Resolve dependencies
    # -----
    constraint = pkg_version or "*"
    registries = [create_registry(reg_source) for reg_source in config.registries]

    resolved = resolve_dependencies(
        [(pkg_name, constraint)],
        registries,
    )

    # -----
    # Step 5: Install via core installer with staging
    # -----
    adapter = None
    if not no_deploy and is_supported_platform(platform_name):
        adapter = create_adapter(platform_name, project_dir)

    core_install_packages(
        resolved,
        adapter,
        config,
        project_dir,
        no_deploy=no_deploy,
        force=force,
    )

    # -----
    # Step 6: Build result
    # -----
    lock = read_lock_file(project_dir)
    locked = lock.packages.get(pkg_name)

    info: dict[str, Any] = {
        "name": pkg_name,
        "version": locked.version if locked else (pkg_version or "unknown"),
        "source": locked.source if locked else "registry",
        "artifact_count": 0,
        "artifacts": {},
        "checksum": locked.checksum if locked else None,
    }

    return {
        "status": "installed",
        "name": pkg_name,
        "info": info,
        "deps_resolved": len(resolved),
    }
