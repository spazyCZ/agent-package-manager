"""Workspace management for ``.aam/`` directory and lock files.

Handles creation and maintenance of the project-level workspace that
stores installed packages and the lock file.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from aam_cli.utils.paths import (
    ensure_project_workspace,
    get_lock_file_path,
    get_packages_dir,
    get_project_workspace,
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
# LOCK FILE MODELS                                                             #
#                                                                              #
################################################################################


class LockedPackage(BaseModel):
    """A single resolved package in the lock file."""

    version: str
    source: str  # Registry name or "local"
    checksum: str  # "sha256:<hex>"
    dependencies: dict[str, str] = {}  # name -> resolved version


class LockFile(BaseModel):
    """Complete lock file model (``.aam/aam-lock.yaml``)."""

    lockfile_version: int = 1
    resolved_at: str = ""  # ISO 8601 timestamp
    packages: dict[str, LockedPackage] = {}  # package name -> locked info


################################################################################
#                                                                              #
# WORKSPACE FUNCTIONS                                                          #
#                                                                              #
################################################################################


def ensure_workspace(project_dir: Path | None = None) -> Path:
    """Create the project workspace and packages directory.

    Ensures ``.aam/`` and ``.aam/packages/`` exist.

    Args:
        project_dir: Project root. Defaults to cwd.

    Returns:
        Path to the workspace directory.
    """
    workspace = ensure_project_workspace(project_dir)

    # Ensure packages subdirectory
    packages_dir = get_packages_dir(project_dir)
    packages_dir.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Workspace ensured: {workspace}")
    return workspace


def get_workspace_path(project_dir: Path | None = None) -> Path:
    """Return the workspace path without creating it.

    Args:
        project_dir: Project root. Defaults to cwd.

    Returns:
        Path to ``.aam/``.
    """
    return get_project_workspace(project_dir)


################################################################################
#                                                                              #
# LOCK FILE OPERATIONS                                                         #
#                                                                              #
################################################################################


def read_lock_file(project_dir: Path | None = None) -> LockFile:
    """Read the lock file, returning an empty model if not found.

    Args:
        project_dir: Project root directory.

    Returns:
        Parsed :class:`LockFile`.
    """
    lock_path = get_lock_file_path(project_dir)
    logger.debug(f"Reading lock file: path='{lock_path}'")

    data = load_yaml_optional(lock_path)
    if not data:
        logger.debug("No existing lock file found, returning empty")
        return LockFile()

    # -----
    # Parse packages into LockedPackage models
    # -----
    packages_raw = data.get("packages", {})
    packages: dict[str, LockedPackage] = {}
    for pkg_name, pkg_data in packages_raw.items():
        if isinstance(pkg_data, dict):
            packages[pkg_name] = LockedPackage(**pkg_data)

    return LockFile(
        lockfile_version=data.get("lockfile_version", 1),
        resolved_at=data.get("resolved_at", ""),
        packages=packages,
    )


def write_lock_file(
    lock_file: LockFile,
    project_dir: Path | None = None,
) -> None:
    """Write the lock file to disk.

    Args:
        lock_file: Lock file model to persist.
        project_dir: Project root directory.
    """
    lock_path = get_lock_file_path(project_dir)
    logger.info(f"Writing lock file: path='{lock_path}'")

    # -----
    # Update the resolved_at timestamp
    # -----
    lock_file.resolved_at = datetime.now(UTC).isoformat()

    # -----
    # Serialize to dict for YAML output
    # -----
    data = lock_file.model_dump(mode="json")

    ensure_workspace(project_dir)
    dump_yaml(data, lock_path)

    logger.info(f"Lock file written: packages={len(lock_file.packages)}")


################################################################################
#                                                                              #
# INSTALLED PACKAGES                                                           #
#                                                                              #
################################################################################


def get_installed_packages(
    project_dir: Path | None = None,
) -> dict[str, LockedPackage]:
    """Return a mapping of installed package names to their lock entries.

    Args:
        project_dir: Project root directory.

    Returns:
        Dict mapping package names to :class:`LockedPackage` instances.
    """
    lock = read_lock_file(project_dir)
    return lock.packages


def is_package_installed(
    package_name: str,
    project_dir: Path | None = None,
) -> bool:
    """Check if a package is currently installed.

    Args:
        package_name: Full package name (scoped or unscoped).
        project_dir: Project root directory.

    Returns:
        ``True`` if the package appears in the lock file.
    """
    packages = get_installed_packages(project_dir)
    return package_name in packages
