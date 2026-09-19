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

import hashlib
import logging
import os
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from aam_cli.adapters.base import PlatformAdapter
from aam_cli.core.autodiscovery import discover_artifacts
from aam_cli.core.config import AamConfig
from aam_cli.core.manifest import load_manifest_universal
from aam_cli.core.resolver import ResolvedPackage
from aam_cli.core.workspace import (
    LockedPackage,
    LockedPackageV2,
    ensure_workspace,
    get_packages_dir,
    read_lock_file,
    read_universal_lock_file,
    write_lock_file,
    write_universal_lock_file,
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
    skip_checks: bool = False,
    console: Console | None = None,
    install_mode: str | None = None,
) -> list[str]:
    """Install resolved packages: download, verify, extract, deploy.

    Includes UAAPS v0.4.0 pre-flight steps:
      - Env var prompting for each ``required=True`` env entry not in environment
      - Permissions confirmation if any capabilities declared

    Args:
        resolved_packages: Packages to install (from the resolver).
        adapter: Platform adapter for deployment (None if --no-deploy).
        config: AAM configuration.
        project_dir: Project root directory.
        no_deploy: If True, skip platform deployment.
        force: If True, reinstall even if already installed.
        skip_checks: If True, skip system dependency pre-flight checks
            (intended for CI environments where system deps are pre-provisioned).
        console: Optional Rich console for user-facing output.
        install_mode: Override install mode (``"uaaps"`` or ``"plugin"``).
            When ``None``, the mode is read from the package manifest or
            defaults to ``"uaaps"``.

    Returns:
        List of installed package names (including version).

    Raises:
        ValueError: If checksum verification fails.
    """
    logger.info(
        f"Installing {len(resolved_packages)} packages: no_deploy={no_deploy}, "
        f"force={force}, skip_checks={skip_checks}"
    )

    ensure_workspace(project_dir)
    packages_dir = get_packages_dir(project_dir)

    lock = read_lock_file(project_dir)
    installed_names: list[str] = []

    # -----
    # T016: Env var prompting — for each package that declares required env vars
    # -----
    _prompt_env_vars(resolved_packages, console)

    # -----
    # T017: Permissions confirmation — warn the user about declared capabilities
    # -----
    _confirm_permissions(resolved_packages, console)

    # -----
    # T020: System dependency pre-flight check (skipped when skip_checks=True)
    # -----
    system_check_results: dict[str, list[dict[str, object]]] = {}
    if not skip_checks:
        system_check_results = _run_system_preflight(
            resolved_packages, console
        )

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
        # Step 3b: Resolve effective install mode (UAAPS v0.5.0)
        # -----
        # CLI override takes highest precedence, then manifest, then default.
        # "uaaps" → deploy to .agent-packages/ layout
        # "plugin" → deploy via adapter's native deploy_* methods
        effective_mode = install_mode or "uaaps"
        if not install_mode:
            try:
                pkg_manifest = load_manifest_universal(extract_dir)
                if hasattr(pkg_manifest, 'install_mode') and pkg_manifest.install_mode:
                    if isinstance(pkg_manifest.install_mode, dict):
                        adapter_name = adapter.name if adapter else "unknown"
                        effective_mode = pkg_manifest.install_mode.get(
                            adapter_name, "uaaps"
                        )
                    elif isinstance(pkg_manifest.install_mode, str):
                        effective_mode = pkg_manifest.install_mode
            except FileNotFoundError:
                pass
        logger.info(f"Install mode for {pkg_label}: {effective_mode}")

        # -----
        # Step 4: Deploy via platform adapter
        # -----
        if not no_deploy and adapter is not None:
            _deploy_package(extract_dir, adapter)

        # -----
        # Step 5: Compute directory integrity hash
        # -----
        integrity_hash = _compute_dir_integrity(extract_dir)
        logger.debug(f"Directory hash for {pkg_label}: {integrity_hash}")

        # -----
        # Step 6: Update lock file entry
        # -----
        deps: dict[str, str] = {}
        try:
            manifest = load_manifest_universal(extract_dir)
            deps = dict(manifest.dependencies)
        except FileNotFoundError:
            pass

        lock.packages[pkg.name] = LockedPackage(
            version=pkg.version,
            source=pkg.source,
            checksum=pkg.checksum or "",
            dependencies=deps,
        )

        installed_names.append(pkg_label)
        logger.info(f"Installed {pkg_label}")

    # -----
    # Step 7: Persist the legacy lock file (backward compat)
    # -----
    write_lock_file(lock, project_dir)

    # -----
    # Step 8: Persist universal lock file (UAAPS v0.4.0) with
    #         system_checks and per-package integrity hashes
    # -----
    _write_universal_lock_update(
        project_dir=project_dir,
        resolved_packages=resolved_packages,
        packages_dir=packages_dir,
        system_check_results=system_check_results,
    )

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
# INTEGRITY & LOCK FILE HELPERS                                                #
#                                                                              #
################################################################################


def _compute_dir_integrity(directory: Path) -> str:
    """Compute a deterministic SHA-256 hash of a package directory tree.

    Algorithm: sorted file list → per-file SHA-256 → SHA-256 of the
    concatenated intermediate hashes. Returns ``sha256-<hex>``.

    Args:
        directory: Root directory to hash.

    Returns:
        Hash string in ``sha256-<hex>`` format.
    """
    # -----
    # Collect all files in sorted order for determinism
    # -----
    file_hashes: list[str] = []
    for file_path in sorted(directory.rglob("*")):
        if not file_path.is_file():
            continue
        # -----
        # Skip .lock and __pycache__ for stability (must match
        # _compute_dir_hash in dependency_tree_service.py for audit)
        # -----
        if file_path.name in (".lock",) or "__pycache__" in file_path.parts:
            continue
        file_digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        # Include relative path so renames are detected
        rel_path = file_path.relative_to(directory)
        file_hashes.append(f"{rel_path}:{file_digest}")

    combined = "\n".join(file_hashes)
    final_hash = hashlib.sha256(combined.encode()).hexdigest()
    return f"sha256-{final_hash}"


def _write_universal_lock_update(
    project_dir: Path | None,
    resolved_packages: list[ResolvedPackage],
    packages_dir: Path,
    system_check_results: dict[str, list[dict[str, object]]],
) -> None:
    """Write / update the universal lock file after installation.

    Reads the existing ``package.agent.lock`` (or creates a new one),
    adds / updates :class:`LockedPackageV2` entries with computed directory
    integrity hashes, and persists ``system_checks``.

    Args:
        project_dir: Project root directory.
        resolved_packages: Packages that were installed in this run.
        packages_dir: Path to the ``.agent-packages/`` directory.
        system_check_results: Aggregated system check results keyed by dep name.
    """
    effective_dir = project_dir or Path.cwd()
    universal_lock = read_universal_lock_file(effective_dir)

    # -----
    # Update or add each package entry
    # -----
    for pkg in resolved_packages:
        scope, base_name = parse_package_name(pkg.name)
        from aam_cli.utils.naming import to_filesystem_name as _tfn
        fs_name = _tfn(scope, base_name)
        pkg_dir = packages_dir / fs_name

        # -----
        # Compute integrity hash if directory exists
        # -----
        integrity = ""
        if pkg_dir.is_dir():
            integrity = _compute_dir_integrity(pkg_dir)

        # -----
        # Read dependencies from installed manifest
        # -----
        deps: dict[str, str] = {}
        try:
            from aam_cli.core.manifest import load_manifest_universal as _lmu
            inst_manifest = _lmu(pkg_dir)
            deps = dict(inst_manifest.dependencies)
        except (FileNotFoundError, Exception):
            pass

        universal_lock.packages[pkg.name] = LockedPackageV2(
            version=pkg.version,
            source=pkg.source,
            integrity=integrity,
            dependencies=deps,
        )

    # -----
    # Persist system check results (keyed by dep name)
    # -----
    if system_check_results:
        universal_lock.system_checks.update(system_check_results)

    write_universal_lock_file(universal_lock, effective_dir)
    logger.info(
        f"Universal lock file updated: {len(universal_lock.packages)} packages, "
        f"{len(universal_lock.system_checks)} system checks"
    )


################################################################################
#                                                                              #
# HELPER FUNCTIONS                                                             #
#                                                                              #
################################################################################


def _prompt_env_vars(
    resolved_packages: list[ResolvedPackage],
    console: Console | None,
) -> None:
    """Prompt for required environment variables declared in package manifests.

    For each package whose manifest declares ``env`` entries with
    ``required=True``, prompts the user for the value if not already
    set in the current process environment.

    Values are stored in the process environment via ``os.environ`` and
    are NOT persisted to disk.

    Args:
        resolved_packages: Resolved packages being installed.
        console: Optional Rich console for output.
    """
    for pkg in resolved_packages:
        if not pkg.manifest:
            continue

        for var_name, env_cfg in pkg.manifest.env.items():
            if not env_cfg.required:
                continue
            if os.environ.get(var_name):
                logger.debug(
                    f"Env var '{var_name}' already set for "
                    f"'{pkg.name}', skipping prompt"
                )
                continue

            # -----
            # Prompt the user for the missing required env var
            # -----
            description = env_cfg.description or var_name
            prompt_text = (
                f"[{pkg.name}] Enter value for {var_name} ({description})"
            )
            logger.info(
                f"Prompting for required env var: "
                f"name='{var_name}', package='{pkg.name}'"
            )
            try:
                value = click.prompt(prompt_text, hide_input=True)
                os.environ[var_name] = value
                logger.debug(f"Set env var '{var_name}' for '{pkg.name}'")
            except click.exceptions.Abort:
                logger.warning(
                    f"User aborted env var prompt for '{var_name}'"
                )


def _confirm_permissions(
    resolved_packages: list[ResolvedPackage],
    console: Console | None,
) -> None:
    """Prompt the user to confirm declared capability permissions.

    If any package in ``resolved_packages`` declares a non-empty
    ``permissions`` block, displays a Rich panel listing all requested
    capabilities and calls :func:`click.confirm` with ``abort=True``.

    Args:
        resolved_packages: Resolved packages being installed.
        console: Optional Rich console for output.
    """
    permission_lines: list[str] = []

    for pkg in resolved_packages:
        if not pkg.manifest or not pkg.manifest.permissions:
            continue

        perms = pkg.manifest.permissions
        pkg_lines: list[str] = []

        # v0.5.0 structured permissions: shell.allow + shell.binaries
        if perms.shell and perms.shell.allow:
            pkg_lines.append(f"  [{pkg.name}] shell execution")
            for binary in perms.shell.binaries:
                pkg_lines.append(f"  [{pkg.name}] shell binary: {binary}")

        # v0.5.0 structured permissions: fs.read + fs.write
        if perms.fs:
            for read_path in perms.fs.read:
                pkg_lines.append(
                    f"  [{pkg.name}] filesystem read: {read_path}"
                )
            for write_path in perms.fs.write:
                pkg_lines.append(
                    f"  [{pkg.name}] filesystem write: {write_path}"
                )

        # v0.5.0 structured permissions: network.hosts + network.schemes
        if perms.network:
            for host in perms.network.hosts:
                pkg_lines.append(f"  [{pkg.name}] network host: {host}")
            for scheme in perms.network.schemes:
                pkg_lines.append(
                    f"  [{pkg.name}] network scheme: {scheme}"
                )

        if pkg_lines:
            permission_lines.extend(pkg_lines)

    if not permission_lines:
        return

    # -----
    # Display permissions panel and request confirmation
    # -----
    perm_text = "\n".join(permission_lines)
    msg = f"The following capabilities are requested:\n\n{perm_text}"

    if console:
        console.print(Panel(msg, title="[yellow]Package Permissions[/yellow]"))
    else:
        logger.warning(f"Permission confirmation required:\n{msg}")

    logger.info(
        f"Requesting permissions confirmation for "
        f"{len(permission_lines)} capability entries"
    )
    click.confirm("Proceed with these permissions?", abort=True)


def _run_system_preflight(
    resolved_packages: list[ResolvedPackage],
    console: Console | None,
) -> dict[str, list[dict[str, object]]]:
    """Run system dependency pre-flight checks for all resolved packages.

    Aggregates all ``systemDependencies`` from the resolved package manifests,
    runs checks, displays a Rich table, and prompts the user if any required
    deps are missing.

    Args:
        resolved_packages: Resolved packages whose manifests declare
            system dependencies.
        console: Optional Rich console for output.

    Returns:
        Dict of package name → serialized SystemCheckResults dict,
        used for storing in the lock file.
    """
    from aam_cli.core.manifest import SystemDependencies, SystemPackages
    from aam_cli.services.system_deps_service import check_system_deps

    # -----
    # Aggregate system deps across all packages
    # -----
    python_version: str | None = None
    node_version: str | None = None
    pip_packages: list[str] = []
    npm_packages: list[str] = []
    brew_packages: list[str] = []
    apt_packages: list[str] = []
    cargo_packages: list[str] = []
    binaries: list[str] = []
    mcp_servers: list[str] = []

    for pkg in resolved_packages:
        if not pkg.manifest or not pkg.manifest.system_dependencies:
            continue
        sys_deps = pkg.manifest.system_dependencies
        if sys_deps.python and not python_version:
            python_version = sys_deps.python
        if sys_deps.node and not node_version:
            node_version = sys_deps.node
        for item in sys_deps.packages.pip:
            if item not in pip_packages:
                pip_packages.append(item)
        for item in sys_deps.packages.npm:
            if item not in npm_packages:
                npm_packages.append(item)
        for item in sys_deps.packages.brew:
            if item not in brew_packages:
                brew_packages.append(item)
        for item in sys_deps.packages.apt:
            if item not in apt_packages:
                apt_packages.append(item)
        for item in sys_deps.packages.cargo:
            if item not in cargo_packages:
                cargo_packages.append(item)
        for item in sys_deps.binaries:
            if item not in binaries:
                binaries.append(item)
        for item in sys_deps.mcp_servers:
            if item not in mcp_servers:
                mcp_servers.append(item)

    merged = SystemDependencies(
        python=python_version,
        node=node_version,
        packages=SystemPackages(
            pip=pip_packages,
            npm=npm_packages,
            brew=brew_packages,
            apt=apt_packages,
            cargo=cargo_packages,
        ),
        binaries=binaries,
        mcp_servers=mcp_servers,
    )

    has_any = (
        python_version is not None
        or node_version is not None
        or pip_packages
        or npm_packages
        or cargo_packages
        or binaries
        or mcp_servers
    )

    if not has_any:
        logger.debug("No system dependencies declared — skipping pre-flight")
        return {}

    results = check_system_deps(merged)

    # -----
    # Display results table via console or log
    # -----
    if results.failed or results.passed:
        total = len(results.passed) + len(results.failed) + len(results.optional_failed)
        logger.info(
            f"System pre-flight: {len(results.passed)}/{total} passed, "
            f"{len(results.failed)} failed"
        )

    if results.failed:
        failed_names = ", ".join(r.name for r in results.failed)
        msg = (
            f"System dependency pre-flight failed for: {failed_names}. "
            f"Use --install-system-deps to attempt auto-install, "
            f"or --skip-checks to bypass."
        )
        if console:
            console.print(f"[yellow]Warning:[/yellow] {msg}")
        else:
            logger.warning(msg)

    return {
        "passed": [r.model_dump() for r in results.passed],
        "failed": [r.model_dump() for r in results.failed],
        "optional_failed": [r.model_dump() for r in results.optional_failed],
    }


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


def migrate_install_dir(project_dir: Path | None = None) -> bool:
    """Migrate the legacy ``.aam/packages/`` to ``.agent-packages/``.

    Detects the old packages directory, prompts the user for confirmation,
    and moves the contents to the new location if accepted.

    Args:
        project_dir: Project root directory. Defaults to cwd.

    Returns:
        True if migration was performed, False if skipped or not needed.
    """
    import shutil

    import click

    from aam_cli.utils.paths import get_legacy_packages_dir

    legacy_packages = get_legacy_packages_dir(project_dir)

    if not legacy_packages.is_dir() or not any(legacy_packages.iterdir()):
        logger.debug("No legacy packages directory — migration not needed")
        return False

    new_packages = get_packages_dir(project_dir)
    if new_packages.is_dir() and any(new_packages.iterdir()):
        logger.debug(
            "New packages directory already has content — migration not needed"
        )
        return False

    # -----
    # Prompt user (Constitution VII: no silent migration)
    # -----
    confirmed = click.confirm(
        f"Found legacy packages at '{legacy_packages}'. "
        f"Migrate to '{new_packages}'?",
        default=True,
    )
    if not confirmed:
        logger.info("Install directory migration declined by user")
        return False

    logger.info(
        f"Migrating install dir: '{legacy_packages}' → '{new_packages}'"
    )

    new_packages.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(legacy_packages), str(new_packages))

    logger.info("Install directory migration complete")
    return True


def _deploy_package(
    package_dir: Path,
    adapter: PlatformAdapter,
) -> None:
    """Deploy all artifacts from an extracted package.

    Deploys path-based artifacts (skills, agents, prompts, instructions,
    commands, rules) via the platform adapter.  Also deploys lifecycle hooks
    and MCP server configuration when declared in the manifest or discovered.

    Args:
        package_dir: Path to the extracted package directory.
        adapter: Platform adapter for deployment.
    """
    manifest = load_manifest_universal(package_dir)

    # Include package name so adapters can namespace deployed artifacts
    config_dict: dict[str, str] = {"package_name": manifest.name}

    # -----
    # Pass skill_scope from package manifest platforms.<adapter.name>
    # Default remains "project" when the platform block is missing.
    # -----
    platform_cfg = manifest.platforms.get(adapter.name)
    if platform_cfg is not None:
        config_dict["skill_scope"] = platform_cfg.skill_scope
    else:
        config_dict["skill_scope"] = "project"

    logger.debug(
        f"Deploy config for {adapter.name}: "
        f"skill_scope={config_dict['skill_scope']}"
    )

    # -----
    # Resolve artifacts via auto-discovery if not explicitly declared
    # -----
    resolved_artifacts = discover_artifacts(package_dir, manifest)

    # -----
    # Deploy path-based artifact types
    # -----
    for artifact_type, artifact_ref in resolved_artifacts.all_artifacts:
        artifact_path = package_dir / artifact_ref.path

        if artifact_type == "skill":
            adapter.deploy_skill(artifact_path, artifact_ref, config_dict)
        elif artifact_type == "agent":
            adapter.deploy_agent(artifact_path, artifact_ref, config_dict)
        elif artifact_type == "prompt":
            # v0.5.0: prompts merged into commands
            adapter.deploy_command(artifact_path, artifact_ref, config_dict)
        elif artifact_type == "instruction":
            adapter.deploy_instruction(artifact_path, artifact_ref, config_dict)
        elif artifact_type == "command":
            adapter.deploy_command(artifact_path, artifact_ref, config_dict)
        elif artifact_type == "rule":
            adapter.deploy_rule(artifact_path, artifact_ref, config_dict)
        else:
            logger.debug(f"Unknown artifact type '{artifact_type}' — skipping")

    # -----
    # Deploy hooks from hooks_path if declared/discovered
    # -----
    if resolved_artifacts.hooks_path:
        hooks_json = package_dir / resolved_artifacts.hooks_path / "hooks.json"
        if not hooks_json.is_file():
            # Fall back to the path itself if it directly points to a JSON file
            hooks_json = package_dir / resolved_artifacts.hooks_path
        if hooks_json.is_file():
            logger.info(f"Deploying hooks from {hooks_json}")
            adapter.deploy_hook(hooks_json, config_dict)
        else:
            logger.warning(f"hooks_path '{resolved_artifacts.hooks_path}' has no hooks.json")

    # -----
    # Deploy MCP servers from mcp_path if declared/discovered
    # -----
    if resolved_artifacts.mcp_path:
        servers_json = package_dir / resolved_artifacts.mcp_path / "servers.json"
        if not servers_json.is_file():
            servers_json = package_dir / resolved_artifacts.mcp_path
        if servers_json.is_file():
            logger.info(f"Deploying MCP servers from {servers_json}")
            adapter.deploy_mcp(servers_json, config_dict)
        else:
            logger.warning(f"mcp_path '{resolved_artifacts.mcp_path}' has no servers.json")

    logger.info(
        f"Deployed {manifest.artifact_count} artifacts from {manifest.name}@{manifest.version}"
    )
