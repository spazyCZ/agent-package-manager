"""Package service for AAM.

Provides list, info, uninstall, and create-package operations.
Returns structured data for use by both CLI and MCP.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import shutil
from pathlib import Path
from typing import Any

from aam_cli.adapters.cursor import CursorAdapter
from aam_cli.core.config import AamConfig
from aam_cli.core.manifest import load_manifest
from aam_cli.core.workspace import (
    get_packages_dir,
    read_lock_file,
    write_lock_file,
)
from aam_cli.detection.scanner import scan_project
from aam_cli.utils.naming import parse_package_name, to_filesystem_name
from aam_cli.utils.yaml_utils import dump_yaml

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# LIST INSTALLED PACKAGES                                                      #
#                                                                              #
################################################################################


def list_installed_packages(
    project_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """List all installed packages with artifact counts.

    Reads the lock file and inspects installed package directories
    for artifact metadata.

    Args:
        project_dir: Project root directory. Defaults to cwd.

    Returns:
        List of InstalledPackageInfo dicts per data-model.md.
    """
    logger.info("Listing installed packages")

    effective_dir = project_dir or Path.cwd()
    lock = read_lock_file(effective_dir)

    if not lock.packages:
        logger.info("No packages installed")
        return []

    packages_dir = get_packages_dir(effective_dir)
    results: list[dict[str, Any]] = []

    for pkg_name, locked in lock.packages.items():
        # -----
        # Try to read manifest for artifact counts
        # -----
        artifact_counts: dict[str, int] = {}
        artifact_count = 0
        scope, base_name = parse_package_name(pkg_name)
        fs_name = to_filesystem_name(scope, base_name)
        pkg_dir = packages_dir / fs_name

        if pkg_dir.is_dir():
            try:
                manifest = load_manifest(pkg_dir)
                for atype, _ref in manifest.all_artifacts:
                    key = atype + "s"
                    artifact_counts[key] = artifact_counts.get(key, 0) + 1
                artifact_count = manifest.artifact_count
            except Exception as exc:
                logger.warning(
                    f"Could not read manifest for '{pkg_name}': {exc}"
                )

        results.append(
            {
                "name": pkg_name,
                "version": locked.version,
                "source": locked.source,
                "source_name": locked.source_name,
                "source_commit": locked.source_commit,
                "artifact_count": artifact_count,
                "artifacts": artifact_counts,
                "checksum": locked.checksum or None,
            }
        )

    logger.info(f"Listed {len(results)} installed packages")
    return results


################################################################################
#                                                                              #
# GET PACKAGE INFO                                                             #
#                                                                              #
################################################################################


def get_package_info(
    package_name: str,
    project_dir: Path | None = None,
    version: str | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Get detailed metadata about an installed package.

    Reads the installed manifest and lock file entry to build
    a comprehensive PackageDetail dict.

    Args:
        package_name: Full package name (scoped or unscoped).
        project_dir: Project root directory. Defaults to cwd.
        version: Optional version filter (reserved for future use).

    Returns:
        PackageDetail dict per data-model.md.

    Raises:
        ValueError: If the package is not installed.
    """
    logger.info(f"Getting package info: name='{package_name}'")

    effective_dir = project_dir or Path.cwd()
    lock = read_lock_file(effective_dir)
    locked = lock.packages.get(package_name)

    if not locked:
        raise ValueError(
            f"[AAM_PACKAGE_NOT_FOUND] Package '{package_name}' is not installed"
        )

    # -----
    # Load manifest from installed directory
    # -----
    scope, base_name = parse_package_name(package_name)
    fs_name = to_filesystem_name(scope, base_name)
    pkg_dir = get_packages_dir(effective_dir) / fs_name

    try:
        manifest = load_manifest(pkg_dir)
    except FileNotFoundError as exc:
        raise ValueError(
            f"[AAM_PACKAGE_NOT_FOUND] Package directory not found for "
            f"'{package_name}': {pkg_dir}"
        ) from exc

    # -----
    # Build artifact info grouped by type
    # -----
    artifacts: dict[str, list[dict[str, Any]]] = {}
    for artifact_type, ref in manifest.all_artifacts:
        key = artifact_type + "s"
        if key not in artifacts:
            artifacts[key] = []
        artifacts[key].append(
            {
                "name": ref.name,
                "path": str(ref.path),
                "description": getattr(ref, "description", None),
            }
        )

    return {
        "name": manifest.name,
        "version": manifest.version,
        "description": manifest.description,
        "author": manifest.author,
        "license": getattr(manifest, "license", None),
        "repository": getattr(manifest, "repository", None),
        "homepage": getattr(manifest, "homepage", None),
        "keywords": getattr(manifest, "keywords", []),
        "artifacts": artifacts,
        "dependencies": manifest.dependencies or {},
        "platforms": getattr(manifest, "platforms", {}),
        "installed": True,
        "installed_version": locked.version,
        "source": locked.source,
        "source_name": locked.source_name,
        "source_commit": locked.source_commit,
    }


################################################################################
#                                                                              #
# UNINSTALL PACKAGE                                                            #
#                                                                              #
################################################################################


def uninstall_package(
    package_name: str,
    config: AamConfig | None = None,  # noqa: ARG001
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Uninstall a package and remove its deployed artifacts.

    Removes the package from ``.aam/packages/``, undeploys artifacts
    from the platform, and updates the lock file.

    Args:
        package_name: Full package name.
        config: AAM configuration (reserved for future platform selection).
        project_dir: Project root directory. Defaults to cwd.

    Returns:
        UninstallResult dict per data-model.md.

    Raises:
        ValueError: If the package is not installed.
    """
    logger.info(f"Uninstalling package: name='{package_name}'")

    effective_dir = project_dir or Path.cwd()
    lock = read_lock_file(effective_dir)
    locked = lock.packages.get(package_name)

    if not locked:
        raise ValueError(
            f"[AAM_PACKAGE_NOT_INSTALLED] Package '{package_name}' is not installed"
        )

    # -----
    # Check for dependents
    # -----
    dependents: list[str] = []
    for other_name, other_locked in lock.packages.items():
        if other_name == package_name:
            continue
        if package_name in other_locked.dependencies:
            dependents.append(other_name)

    # -----
    # Undeploy artifacts
    # -----
    scope, base_name = parse_package_name(package_name)
    fs_name = to_filesystem_name(scope, base_name)
    pkg_dir = get_packages_dir(effective_dir) / fs_name
    files_removed = 0

    if pkg_dir.is_dir():
        try:
            manifest = load_manifest(pkg_dir)
            adapter = CursorAdapter(effective_dir)

            for artifact_type, ref in manifest.all_artifacts:
                adapter.undeploy(ref.name, artifact_type)
                files_removed += 1

        except Exception as exc:
            logger.warning(
                f"Could not undeploy artifacts for '{package_name}': {exc}"
            )

        # -----
        # Remove package directory
        # -----
        shutil.rmtree(pkg_dir)

    # -----
    # Update lock file
    # -----
    version = locked.version
    del lock.packages[package_name]
    write_lock_file(lock, effective_dir)

    logger.info(f"Uninstalled package: {package_name}@{version}")

    return {
        "package_name": package_name,
        "version": version,
        "files_removed": files_removed,
        "dependents_warning": dependents,
    }


################################################################################
#                                                                              #
# CREATE PACKAGE                                                               #
#                                                                              #
################################################################################


def create_package(
    path: Path,
    name: str | None = None,
    version: str | None = None,
    description: str | None = None,
    artifact_types: list[str] | None = None,
    platforms: list[str] | None = None,
    include_all: bool = False,  # noqa: ARG001
) -> dict[str, Any]:
    """Create an AAM package manifest from an existing project directory.

    Scans for artifacts and generates ``aam.yaml`` non-interactively.

    Args:
        path: Project directory to scan.
        name: Package name (defaults to directory name).
        version: Package version (defaults to "1.0.0").
        description: Package description.
        artifact_types: Optional filter for artifact types to include.
        platforms: Optional list of platform names to filter results
            (cursor, copilot, claude, codex).
        include_all: Whether to include all detected artifacts (reserved).

    Returns:
        CreatePackageResult dict per data-model.md.
    """
    logger.info(f"Creating package from path: {path}")

    project_path = Path(path).resolve()

    # -----
    # Step 1: Detect artifacts (with optional platform filter)
    # -----
    artifacts = scan_project(project_path, platforms=platforms)

    if artifact_types:
        type_set = set(artifact_types)
        artifacts = [a for a in artifacts if a.type in type_set]

    selected = artifacts

    # -----
    # Step 2: Generate metadata
    # -----
    pkg_name = name or project_path.name
    pkg_version = version or "1.0.0"
    pkg_description = description or ""

    # -----
    # Step 3: Build artifact sections
    # -----
    grouped: dict[str, list[dict[str, str]]] = {
        "agents": [],
        "skills": [],
        "prompts": [],
        "instructions": [],
    }

    for art in selected:
        ref = {
            "name": art.name,
            "path": str(art.source_path),
            "description": art.description or f"{art.type.capitalize()} {art.name}",
        }
        grouped[art.type + "s"].append(ref)

    # -----
    # Step 4: Build and write manifest
    # -----
    manifest_data: dict[str, Any] = {
        "name": pkg_name,
        "version": pkg_version,
        "description": pkg_description,
        "artifacts": grouped,
        "dependencies": {},
        "platforms": {
            "cursor": {
                "skill_scope": "project",
                "deploy_instructions_as": "rules",
            },
        },
    }

    manifest_path = project_path / "aam.yaml"
    dump_yaml(manifest_data, manifest_path)

    # -----
    # Step 5: Build result
    # -----
    type_counts: dict[str, int] = {}
    for art in selected:
        key = art.type + "s"
        type_counts[key] = type_counts.get(key, 0) + 1

    logger.info(
        f"Package created: name='{pkg_name}', "
        f"version='{pkg_version}', artifacts={len(selected)}"
    )

    return {
        "manifest_path": str(manifest_path),
        "package_name": pkg_name,
        "version": pkg_version,
        "artifacts_included": type_counts,
        "total_artifacts": len(selected),
    }
