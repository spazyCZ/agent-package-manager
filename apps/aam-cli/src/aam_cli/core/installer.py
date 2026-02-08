"""Package installer — download, extract, verify, and deploy.

Orchestrates the full install flow:
  1. Download archives from registries
  2. Verify checksums
  3. Extract to ``.aam/packages/``
  4. Deploy via platform adapter
  5. Write lock file
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

from aam_cli.adapters.base import PlatformAdapter
from aam_cli.core.config import AamConfig
from aam_cli.core.manifest import load_manifest
from aam_cli.core.resolver import ResolvedPackage
from aam_cli.core.workspace import (
    LockedPackage,
    ensure_workspace,
    get_packages_dir,
    read_lock_file,
    write_lock_file,
)
from aam_cli.registry.base import Registry
from aam_cli.registry.factory import create_registry
from aam_cli.utils.checksum import verify_sha256
from aam_cli.utils.naming import parse_package_name, to_filesystem_name

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# INSTALLER                                                                    #
#                                                                              #
################################################################################


def install_packages(
    resolved_packages: list[ResolvedPackage],
    adapter: PlatformAdapter | None,
    config: AamConfig,
    project_dir: Path | None = None,
    no_deploy: bool = False,
    force: bool = False,
) -> list[str]:
    """Install resolved packages: download, verify, extract, deploy.

    Args:
        resolved_packages: Packages to install (from the resolver).
        adapter: Platform adapter for deployment (None if --no-deploy).
        config: AAM configuration.
        project_dir: Project root directory.
        no_deploy: If True, skip platform deployment.
        force: If True, reinstall even if already installed.

    Returns:
        List of installed package names (including version).

    Raises:
        ValueError: If checksum verification fails.
    """
    logger.info(
        f"Installing {len(resolved_packages)} packages: no_deploy={no_deploy}, force={force}"
    )

    ensure_workspace(project_dir)
    packages_dir = get_packages_dir(project_dir)

    lock = read_lock_file(project_dir)
    installed_names: list[str] = []

    for pkg in resolved_packages:
        pkg_label = f"{pkg.name}@{pkg.version}"

        # -----
        # Check if already installed (skip unless --force)
        # -----
        if pkg.name in lock.packages and not force:
            existing = lock.packages[pkg.name]
            if existing.version == pkg.version:
                logger.info(f"Already installed: {pkg_label}, skipping")
                continue

        # -----
        # Step 1: Download the archive
        # -----
        logger.info(f"Downloading {pkg_label} from '{pkg.source}'")

        registry = _get_registry(pkg.source, config)
        archive_dest = packages_dir / ".downloads"
        archive_path = registry.download(pkg.name, pkg.version, archive_dest)

        # -----
        # Step 2: Verify checksum
        # -----
        if pkg.checksum and config.security.require_checksum:
            if not verify_sha256(archive_path, pkg.checksum):
                raise ValueError(
                    f"Checksum verification failed for {pkg_label}. The archive may be corrupted."
                )
            logger.info(f"Checksum verified: {pkg_label}")

        # -----
        # Step 3: Extract to .aam/packages/<fs-name>/
        # -----
        scope, base_name = parse_package_name(pkg.name)
        fs_name = to_filesystem_name(scope, base_name)
        extract_dir = packages_dir / fs_name

        from aam_cli.utils.archive import extract_archive

        if extract_dir.exists():
            import shutil

            shutil.rmtree(extract_dir)

        extract_archive(archive_path, extract_dir)
        logger.info(f"Extracted {pkg_label} to {extract_dir}")

        # -----
        # Step 4: Deploy via platform adapter
        # -----
        if not no_deploy and adapter is not None:
            _deploy_package(extract_dir, adapter)

        # -----
        # Step 5: Update lock file entry
        # -----
        deps: dict[str, str] = {}
        manifest_path = extract_dir / "aam.yaml"
        if manifest_path.is_file():
            manifest = load_manifest(extract_dir)
            deps = dict(manifest.dependencies)

        lock.packages[pkg.name] = LockedPackage(
            version=pkg.version,
            source=pkg.source,
            checksum=pkg.checksum,
            dependencies=deps,
        )

        installed_names.append(pkg_label)
        logger.info(f"Installed {pkg_label}")

    # -----
    # Step 6: Persist the lock file
    # -----
    write_lock_file(lock, project_dir)

    # -----
    # Clean up download directory
    # -----
    downloads_dir = packages_dir / ".downloads"
    if downloads_dir.exists():
        import shutil

        shutil.rmtree(downloads_dir, ignore_errors=True)

    logger.info(f"Installation complete: {len(installed_names)} packages installed")
    return installed_names


################################################################################
#                                                                              #
# HELPER FUNCTIONS                                                             #
#                                                                              #
################################################################################


def _get_registry(source_name: str, config: AamConfig) -> Registry:
    """Get a registry instance by name from the config.

    Args:
        source_name: Registry name.
        config: AAM configuration.

    Returns:
        Registry instance.

    Raises:
        ValueError: If the registry is not configured.
    """
    source = config.get_registry_by_name(source_name)
    if source is None:
        raise ValueError(
            f"Registry '{source_name}' not found. "
            "Run 'aam registry list' to see configured registries."
        )
    return create_registry(source)


def _deploy_package(
    package_dir: Path,
    adapter: PlatformAdapter,
) -> None:
    """Deploy all artifacts from an extracted package.

    Args:
        package_dir: Path to the extracted package directory.
        adapter: Platform adapter for deployment.
    """
    manifest = load_manifest(package_dir)

    config_dict: dict[str, str] = {}

    # -----
    # Deploy each artifact type
    # -----
    for artifact_type, artifact_ref in manifest.all_artifacts:
        artifact_path = package_dir / artifact_ref.path

        if artifact_type == "skill":
            adapter.deploy_skill(artifact_path, artifact_ref, config_dict)
        elif artifact_type == "agent":
            adapter.deploy_agent(artifact_path, artifact_ref, config_dict)
        elif artifact_type == "prompt":
            adapter.deploy_prompt(artifact_path, artifact_ref, config_dict)
        elif artifact_type == "instruction":
            adapter.deploy_instruction(artifact_path, artifact_ref, config_dict)

    logger.info(
        f"Deployed {manifest.artifact_count} artifacts from {manifest.name}@{manifest.version}"
    )
