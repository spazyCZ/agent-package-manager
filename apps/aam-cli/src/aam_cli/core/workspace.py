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
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aam_cli.utils.paths import (
    ensure_project_workspace,
    get_lock_file_path,
    get_packages_dir,
    get_project_workspace,
    get_universal_lock_file_path,
    resolve_lock_path,
)
from aam_cli.utils.yaml_utils import dump_yaml, load_yaml_optional

################################################################################
#                                                                              #
# PUBLIC API                                                                   #
#                                                                              #
################################################################################

__all__ = [
    "FileChecksums",
    "LockedPackage",
    "LockedPackageV2",
    "LockFile",
    "UniversalLockFile",
    "ensure_workspace",
    "get_packages_dir",
    "get_workspace_path",
    "read_lock_file",
    "read_lock_file_resolved",
    "read_universal_lock_file",
    "write_lock_file",
    "write_lock_file_resolved",
    "write_universal_lock_file",
    "get_installed_packages",
    "get_installed_packages_universal",
    "is_package_installed",
]

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


class FileChecksums(BaseModel):
    """Per-file integrity checksums for an installed package.

    Stored in the lock file to enable verification of installed
    files against their original state.
    """

    algorithm: str = "sha256"  # Hash algorithm used
    files: dict[str, str] = {}  # {relative_path: hex_digest}


class LockedPackage(BaseModel):
    """A single resolved package in the lock file."""

    version: str
    source: str  # Registry name or "local"
    checksum: str  # "sha256:<hex>"
    dependencies: dict[str, str] = {}  # name -> resolved version

    # -----
    # Per-file integrity data (spec 003)
    # Backward compatible: None for packages installed before this feature
    # -----
    file_checksums: FileChecksums | None = None

    # -----
    # Source tracking fields (spec 004)
    # Enables outdated detection and upgrade from git sources.
    # Co-presence rule: both None or both set.
    # -----
    source_name: str | None = None
    source_commit: str | None = None

    @model_validator(mode="after")
    def _validate_source_fields(self) -> "LockedPackage":
        """Ensure source_name and source_commit are either both set or both None.

        Raises:
            ValueError: If only one of the pair is set.
        """
        has_name = self.source_name is not None
        has_commit = self.source_commit is not None

        if has_name != has_commit:
            raise ValueError(
                "source_name and source_commit must both be set or both be None. "
                f"Got source_name={self.source_name!r}, source_commit={self.source_commit!r}"
            )

        return self


class LockFile(BaseModel):
    """Complete lock file model (``.aam/aam-lock.yaml``)."""

    lockfile_version: int = 1
    resolved_at: str = ""  # ISO 8601 timestamp
    packages: dict[str, LockedPackage] = {}  # package name -> locked info


################################################################################
#                                                                              #
# UAAPS v0.4.0 LOCK FILE MODELS                                               #
#                                                                              #
################################################################################


class LockedPackageV2(BaseModel):
    """A single package entry in the universal lock file (``package.agent.lock``)."""

    version: str
    source: str  # Registry name, "local", or "git"
    integrity: str  # "sha256-<hex>" format (directory tree hash)
    dependencies: dict[str, str] = {}  # name -> resolved version
    optional: bool = False  # True if from optionalDependencies
    peer: bool = False  # True if peer dep (verified, not installed)

    # Legacy fields (preserved for aam-lock.yaml compat)
    source_name: str | None = None
    source_commit: str | None = None


class UniversalLockFile(BaseModel):
    """``package.agent.lock`` — universal JSON lock file (UAAPS v0.4.0).

    JSON field names use camelCase per UAAPS §13.3. Use
    ``model.model_dump(by_alias=True)`` for serialization and
    ``UniversalLockFile.model_validate(data)`` for deserialization.
    """

    model_config = ConfigDict(populate_by_name=True)

    lock_version: int = Field(
        1, validation_alias="lockVersion", serialization_alias="lockVersion"
    )
    resolved_at: str = ""
    packages: dict[str, LockedPackageV2] = Field(
        default_factory=dict,
        validation_alias="resolved",
        serialization_alias="resolved",
    )
    system_checks: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="systemChecks",
        serialization_alias="systemChecks",
    )


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
# UNIVERSAL LOCK FILE OPERATIONS (UAAPS v0.4.0)                               #
#                                                                              #
################################################################################


def read_universal_lock_file(
    project_dir: Path | None = None,
) -> UniversalLockFile:
    """Read the UAAPS v0.4.0 lock file (``package.agent.lock``).

    Returns an empty model if the file does not exist.

    Args:
        project_dir: Project root directory.

    Returns:
        Parsed :class:`UniversalLockFile`.
    """
    import json

    lock_path = get_universal_lock_file_path(project_dir)
    logger.debug(f"Reading universal lock file: path='{lock_path}'")

    if not lock_path.is_file():
        logger.debug("No universal lock file found, returning empty")
        return UniversalLockFile()  # type: ignore[call-arg]

    text = lock_path.read_text(encoding="utf-8")
    data = json.loads(text)

    return UniversalLockFile.model_validate(data)


def write_universal_lock_file(
    lock_file: UniversalLockFile,
    project_dir: Path | None = None,
) -> None:
    """Write the UAAPS v0.4.0 lock file atomically.

    Writes to a ``.tmp`` file first, then renames to ensure atomicity.
    Also creates a symlink/copy at ``.agent-packages/.lock`` per UAAPS §13.11.

    Args:
        lock_file: Universal lock file model to persist.
        project_dir: Project root directory.
    """
    import json
    import shutil

    lock_path = get_universal_lock_file_path(project_dir)
    logger.info(f"Writing universal lock file: path='{lock_path}'")

    # -----
    # Update the resolved_at timestamp
    # -----
    lock_file.resolved_at = datetime.now(UTC).isoformat()

    # -----
    # Serialize with aliases (camelCase per UAAPS §13.3)
    # -----
    data = lock_file.model_dump(mode="json", by_alias=True)

    # -----
    # Atomic write: tmp file + rename
    # -----
    tmp_path = lock_path.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp_path.rename(lock_path)

    # -----
    # Secondary copy at .agent-packages/.lock (UAAPS §13.11)
    # -----
    packages_dir = get_packages_dir(project_dir)
    if packages_dir.is_dir():
        secondary_path = packages_dir / ".lock"
        shutil.copy2(lock_path, secondary_path)
        logger.debug(f"Lock file secondary copy: path='{secondary_path}'")

    logger.info(f"Universal lock file written: packages={len(lock_file.packages)}")


################################################################################
#                                                                              #
# RESOLVED LOCK FILE OPERATIONS (GLOBAL / LOCAL)                               #
#                                                                              #
################################################################################


def read_lock_file_resolved(
    is_global: bool = False,
    project_dir: Path | None = None,
) -> UniversalLockFile:
    """Read the lock file from the resolved path (global or local).

    Args:
        is_global: If True, read from ``~/.aam/global.lock``.
        project_dir: Project root (for local installs).

    Returns:
        Parsed lock file model.
    """
    import json

    lock_path = resolve_lock_path(is_global=is_global, project_dir=project_dir)
    logger.debug(f"Reading resolved lock file: path='{lock_path}'")

    if not lock_path.is_file():
        logger.debug("No lock file found at resolved path, returning empty")
        return UniversalLockFile()  # type: ignore[call-arg]

    text = lock_path.read_text(encoding="utf-8")
    data = json.loads(text)
    return UniversalLockFile.model_validate(data)


def write_lock_file_resolved(
    lock_file: UniversalLockFile,
    is_global: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Write the lock file to the resolved path (global or local).

    Args:
        lock_file: Lock file model to persist.
        is_global: If True, write to ``~/.aam/global.lock``.
        project_dir: Project root (for local installs).
    """
    import json

    lock_path = resolve_lock_path(is_global=is_global, project_dir=project_dir)
    logger.info(f"Writing resolved lock file: path='{lock_path}'")

    lock_file.resolved_at = datetime.now(UTC).isoformat()
    data = lock_file.model_dump(mode="json", by_alias=True)

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = lock_path.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp_path.rename(lock_path)

    logger.info(f"Lock file written to: {lock_path}")


################################################################################
#                                                                              #
# INSTALLED PACKAGES                                                           #
#                                                                              #
################################################################################


def get_installed_packages_universal(
    project_dir: Path | None = None,
) -> dict[str, LockedPackageV2]:
    """Return installed packages from the universal lock file, falling back to legacy.

    Prefers ``package.agent.lock``; if absent, reads ``aam-lock.yaml`` and
    converts entries to :class:`LockedPackageV2` for a unified return type.

    Args:
        project_dir: Project root directory.

    Returns:
        Dict mapping package names to :class:`LockedPackageV2` instances.
    """
    universal = read_universal_lock_file(project_dir)
    if universal.packages:
        return universal.packages

    # -----
    # Fall back to legacy lock file with type conversion
    # -----
    legacy = read_lock_file(project_dir)
    if not legacy.packages:
        return {}

    converted: dict[str, LockedPackageV2] = {}
    for pkg_name, locked in legacy.packages.items():
        converted[pkg_name] = LockedPackageV2(
            version=locked.version,
            source=locked.source,
            integrity=locked.checksum or "",
            dependencies=locked.dependencies,
            source_name=locked.source_name,
            source_commit=locked.source_commit,
        )
    return converted


def get_installed_packages(
    project_dir: Path | None = None,
) -> dict[str, LockedPackage]:
    """Return a mapping of installed package names to their lock entries.

    Reads from the universal lock file first, then falls back to the
    legacy ``aam-lock.yaml``.

    Args:
        project_dir: Project root directory.

    Returns:
        Dict mapping package names to :class:`LockedPackage` instances.
    """
    # -----
    # Try universal lock file first
    # -----
    universal = read_universal_lock_file(project_dir)
    if universal.packages:
        converted: dict[str, LockedPackage] = {}
        for pkg_name, v2 in universal.packages.items():
            converted[pkg_name] = LockedPackage(
                version=v2.version,
                source=v2.source,
                checksum=v2.integrity,
                dependencies=v2.dependencies,
                source_name=v2.source_name,
                source_commit=v2.source_commit,
            )
        return converted

    # -----
    # Fall back to legacy lock file
    # -----
    lock = read_lock_file(project_dir)
    return lock.packages


################################################################################
#                                                                              #
# MIGRATION HELPERS (UAAPS v0.4.0)                                            #
#                                                                              #
################################################################################


def migrate_lock_file(project_dir: Path | None = None) -> bool:
    """Migrate the legacy ``aam-lock.yaml`` to ``package.agent.lock``.

    Detects ``.aam/aam-lock.yaml``, prompts the user, and if accepted
    converts ``LockFile`` → ``UniversalLockFile``, writes
    ``package.agent.lock``, and renames the old file to
    ``aam-lock.yaml.bak``.

    Args:
        project_dir: Project root directory. Defaults to cwd.

    Returns:
        True if migration was performed, False if skipped or not needed.
    """
    import click

    from aam_cli.utils.paths import get_lock_file_path

    old_lock_path = get_lock_file_path(project_dir)

    if not old_lock_path.is_file():
        logger.debug("No legacy lock file found — migration not needed")
        return False

    universal_path = get_universal_lock_file_path(project_dir)
    if universal_path.is_file():
        logger.debug(
            "Universal lock file already exists — migration not needed"
        )
        return False

    # -----
    # Prompt user for confirmation (Constitution VII: no silent migration)
    # -----
    confirmed = click.confirm(
        f"Found legacy lock file at '{old_lock_path}'. "
        f"Migrate to '{universal_path.name}'?",
        default=True,
    )
    if not confirmed:
        logger.info("Lock file migration declined by user")
        return False

    logger.info(f"Migrating lock file: '{old_lock_path}' → '{universal_path}'")

    # -----
    # Load legacy lock file
    # -----
    legacy = read_lock_file(project_dir)

    # -----
    # Convert to UniversalLockFile
    # -----
    converted_packages: dict[str, LockedPackageV2] = {}
    for pkg_name, locked in legacy.packages.items():
        converted_packages[pkg_name] = LockedPackageV2(
            version=locked.version,
            source=locked.source,
            integrity=locked.checksum or "",
            dependencies=locked.dependencies,
            source_name=locked.source_name,
            source_commit=locked.source_commit,
        )

    universal = UniversalLockFile(packages=converted_packages)  # type: ignore[call-arg]
    write_universal_lock_file(universal, project_dir)

    # -----
    # Rename legacy file to .bak (do not delete — allow rollback)
    # -----
    bak_path = old_lock_path.with_suffix(".bak")
    old_lock_path.rename(bak_path)
    logger.info(f"Legacy lock file backed up to: '{bak_path}'")

    return True


def is_package_installed(
    package_name: str,
    project_dir: Path | None = None,
) -> bool:
    """Check if a package is currently installed.

    Checks the universal lock file first, then falls back to the legacy
    ``aam-lock.yaml``.

    Args:
        package_name: Full package name (scoped or unscoped).
        project_dir: Project root directory.

    Returns:
        ``True`` if the package appears in either lock file.
    """
    # -----
    # Check universal lock file first
    # -----
    universal = read_universal_lock_file(project_dir)
    if universal.packages:
        return package_name in universal.packages

    # -----
    # Fall back to legacy lock file
    # -----
    legacy = read_lock_file(project_dir)
    return package_name in legacy.packages
