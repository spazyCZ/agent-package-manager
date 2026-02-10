"""Install command for AAM CLI.

Installs packages from registries, local directories, or ``.aam`` archives.
Resolves dependencies, verifies checksums, extracts to ``.aam/packages/``,
and deploys artifacts to the target platform.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import shutil
from pathlib import Path

import click
from rich.console import Console

from aam_cli.adapters.factory import create_adapter, is_supported_platform
from aam_cli.core.config import load_config
from aam_cli.core.installer import install_packages
from aam_cli.core.manifest import load_manifest
from aam_cli.core.resolver import resolve_dependencies
from aam_cli.core.workspace import (
    LockedPackage,
    ensure_workspace,
    get_packages_dir,
    is_package_installed,
    read_lock_file,
    write_lock_file,
)
from aam_cli.registry.factory import create_registry
from aam_cli.utils.archive import extract_archive
from aam_cli.utils.checksum import calculate_sha256
from aam_cli.utils.naming import parse_package_name, parse_package_spec, to_filesystem_name
from aam_cli.utils.paths import resolve_project_dir
from aam_cli.utils.yaml_utils import load_yaml_optional

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# UPGRADE WARNING                                                              #
#                                                                              #
################################################################################


def _handle_upgrade_warning(
    console: Console,
    package_name: str,
    project_dir: Path,
    force: bool,
) -> bool:
    """Check for local modifications and warn the user before overwriting.

    If modifications are detected, presents the user with interactive
    options: [b]ackup, [s]kip, [d]iff, [f]orce.

    Args:
        console: Rich console for output.
        package_name: Name of the package being upgraded.
        project_dir: Project root directory.
        force: If True, skip the interactive prompt and overwrite.

    Returns:
        True if the upgrade should proceed, False to abort.
    """
    from aam_cli.services.checksum_service import (
        check_modifications,
        create_backup,
    )

    mod_result = check_modifications(package_name, project_dir)

    # -----
    # No checksums or no modifications — proceed silently
    # -----
    if not mod_result["has_checksums"] or not mod_result["has_modifications"]:
        return True

    # -----
    # Show warning about local modifications
    # -----
    modified = mod_result["modified_files"]
    missing = mod_result["missing_files"]

    console.print(
        f"\n[yellow]⚠  Warning:[/yellow] Package [bold]{package_name}[/bold] "
        f"has local modifications:"
    )

    if modified:
        console.print(f"  [yellow]Modified:[/yellow] {len(modified)} file(s)")
        for f in modified[:5]:
            console.print(f"    • {f}")
        if len(modified) > 5:
            console.print(f"    [dim]... and {len(modified) - 5} more[/dim]")

    if missing:
        console.print(f"  [red]Missing:[/red] {len(missing)} file(s)")
        for f in missing[:5]:
            console.print(f"    • {f}")
        if len(missing) > 5:
            console.print(f"    [dim]... and {len(missing) - 5} more[/dim]")

    # -----
    # If --force, proceed without prompt
    # -----
    if force:
        console.print(
            "  [dim]--force flag set, proceeding with overwrite[/dim]"
        )
        return True

    # -----
    # Interactive prompt: [b]ackup / [s]kip / [d]iff / [f]orce
    # -----
    from rich.prompt import Prompt

    while True:
        choice = Prompt.ask(
            "\n  [b]ackup modified files, [s]kip upgrade, "
            "[d]iff to view changes, [f]orce overwrite",
            choices=["b", "s", "d", "f"],
            default="b",
        )

        if choice == "s":
            return False

        if choice == "f":
            return True

        if choice == "b":
            # -----
            # Create backup of modified files
            # -----
            backup_result = create_backup(
                package_name, modified, project_dir
            )
            console.print(
                f"  [green]✓[/green] Backed up {len(backup_result['backed_up_files'])} "
                f"file(s) to: {backup_result['backup_dir']}"
            )
            return True

        if choice == "d":
            # -----
            # Show diff of modified files
            # -----
            from aam_cli.commands.diff import diff_package

            diff_result = diff_package(package_name, project_dir)

            if diff_result.get("diffs"):
                from rich.syntax import Syntax

                for diff_entry in diff_result["diffs"]:
                    console.print(f"  [yellow]{diff_entry['file']}[/yellow]")
                    if diff_entry["diff"]:
                        syntax = Syntax(
                            diff_entry["diff"],
                            "diff",
                            theme="monokai",
                            line_numbers=False,
                        )
                        console.print(syntax)
                    console.print()
            else:
                console.print("  [dim]No detailed diff available[/dim]")
            # Loop back to prompt after showing diff


################################################################################
#                                                                              #
# CHECKSUM HELPERS                                                             #
#                                                                              #
################################################################################


def _read_file_checksums_from_package(
    package_dir: Path,
) -> "object | None":
    """Read file checksums from a package's aam.yaml if present.

    The ``file_checksums`` section is written by ``aam pack`` and
    embedded in the archive's ``aam.yaml``. When installing, we
    extract these and store them in the lock file for later verification.

    Args:
        package_dir: Root of the installed package directory.

    Returns:
        A :class:`FileChecksums` instance or ``None`` if the package
        does not contain per-file checksums.
    """
    from aam_cli.core.workspace import FileChecksums

    manifest_path = package_dir / "aam.yaml"
    if not manifest_path.is_file():
        return None

    data = load_yaml_optional(manifest_path)
    if not data:
        return None

    checksums_data = data.get("file_checksums")
    if not checksums_data or not isinstance(checksums_data, dict):
        return None

    files = checksums_data.get("files", {})
    if not files:
        return None

    algorithm = checksums_data.get("algorithm", "sha256")

    logger.info(
        f"Read file checksums from package: "
        f"algorithm='{algorithm}', files={len(files)}"
    )

    return FileChecksums(algorithm=algorithm, files=files)


################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command()
@click.argument("package")
@click.option("--platform", default=None, help="Deploy to specific platform")
@click.option("--no-deploy", is_flag=True, help="Download only, skip deployment")
@click.option("--force", "-f", is_flag=True, help="Reinstall even if present")
@click.option("--dry-run", is_flag=True, help="Preview without installing")
@click.option(
    "--global", "-g", "is_global", is_flag=True,
    help="Install to global ~/.aam/ directory",
)
@click.pass_context
def install(
    ctx: click.Context,
    package: str,
    platform: str | None,
    no_deploy: bool,
    force: bool,
    dry_run: bool,
    is_global: bool,
) -> None:
    """Install a package and deploy artifacts.

    Supports multiple source formats:
      - ``name`` — install latest from registry
      - ``name@version`` — install specific version
      - ``@scope/name`` — scoped package from registry
      - ``./path/`` — install from local directory
      - ``file.aam`` — install from archive file

    Use ``-g`` / ``--global`` to install into the user-wide ``~/.aam/``
    directory instead of the project-local ``.aam/`` workspace.

    Examples::

        aam install my-agent
        aam install my-agent@1.0.0
        aam install @author/my-agent
        aam install ./my-package/
        aam install my-package-1.0.0.aam
        aam install my-agent --no-deploy
        aam install my-agent --force
        aam install my-agent -g
    """
    console: Console = ctx.obj["console"]
    project_dir = resolve_project_dir(is_global)

    # -----
    # Visual indicator for global mode
    # -----
    if is_global:
        console.print("[dim]Operating in global mode (~/.aam/)[/dim]\n")

    if dry_run:
        console.print("[yellow]Dry run mode — no changes will be made[/yellow]\n")

    config = load_config(project_dir)
    platform_name = platform or config.default_platform

    # -----
    # Determine source type
    # -----
    if package.endswith(".aam") and Path(package).is_file():
        _install_from_archive(
            ctx,
            console,
            Path(package),
            project_dir,
            platform_name,
            no_deploy,
            force,
            dry_run,
        )
        return

    if package.startswith("./") or package.startswith("/"):
        local_path = Path(package).resolve()
        if local_path.is_dir():
            _install_from_directory(
                ctx,
                console,
                local_path,
                project_dir,
                platform_name,
                no_deploy,
                force,
                dry_run,
            )
            return

    # -----
    # Registry-based install (with source fallback)
    # -----
    _install_from_registry_or_source(
        ctx,
        console,
        package,
        project_dir,
        config,
        platform_name,
        no_deploy,
        force,
        dry_run,
    )


################################################################################
#                                                                              #
# INSTALL FROM REGISTRY                                                        #
#                                                                              #
################################################################################


def _install_from_registry_or_source(
    ctx: click.Context,
    console: Console,
    package_spec: str,
    project_dir: Path,
    config: "AamConfig",  # noqa: F821
    platform_name: str,
    no_deploy: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Install a package from registries, with source fallback.

    Resolution order per spec 004 research.md R3:
      1. Qualified name (contains "/"): try source index directly
      2. Registry lookup (unqualified): try configured registries
      3. Source fallback (unqualified): try source artifact index
    """
    # -----
    # Step 1: Parse package spec
    # -----
    try:
        pkg_name, pkg_version = parse_package_spec(package_spec)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return

    # -----
    # Check if already installed
    # -----
    if not force and is_package_installed(pkg_name, project_dir):
        lock = read_lock_file(project_dir)
        existing = lock.packages.get(pkg_name)
        if existing:
            console.print(
                f"{pkg_name}@{existing.version} is already installed. "
                f"Use --force to reinstall."
            )
            return

    # -----
    # Step 2: Try qualified name in source index (if contains "/")
    # -----
    if "/" in package_spec and not pkg_version:
        try:
            _try_install_from_source(
                ctx, console, package_spec, project_dir,
                config, platform_name, no_deploy, force, dry_run,
            )
            return
        except ValueError:
            pass  # Fall through to registry

    # -----
    # Step 3: Try registry resolution
    # -----
    registry_resolved = False

    if config.registries:
        constraint = pkg_version or "*"
        console.print(f"Resolving {pkg_name}@{constraint}...")

        registries = []
        for reg_source in config.registries:
            registries.append(create_registry(reg_source))

        try:
            resolved = resolve_dependencies(
                [(pkg_name, constraint)],
                registries,
            )

            for pkg in resolved:
                console.print(f"  + {pkg.name}@{pkg.version}")

            if dry_run:
                console.print(
                    "\n[yellow]\\[Dry run — no packages installed][/yellow]"
                )
                return

            adapter = None
            if not no_deploy:
                if not is_supported_platform(platform_name):
                    console.print(
                        f"[red]Error:[/red] Unsupported platform "
                        f"'{platform_name}'. "
                        "Supported: cursor, copilot, claude, codex"
                    )
                    ctx.exit(1)
                    return
                adapter = create_adapter(platform_name, project_dir)

            installed = install_packages(
                resolved,
                adapter,
                config,
                project_dir,
                no_deploy=no_deploy,
                force=force,
            )

            console.print(
                f"\n[green]✓[/green] Installed {len(installed)} packages"
            )
            registry_resolved = True

        except ValueError:
            # -----
            # Registry resolution failed — fall through to source
            # -----
            logger.debug(
                f"Registry resolution failed for '{pkg_name}', "
                f"trying source fallback"
            )

    # -----
    # Step 4: Source fallback for unqualified names
    # -----
    if not registry_resolved:
        try:
            _try_install_from_source(
                ctx, console, pkg_name, project_dir,
                config, platform_name, no_deploy, force, dry_run,
            )
        except ValueError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            ctx.exit(1)


def _try_install_from_source(
    ctx: click.Context,
    console: Console,
    artifact_name: str,
    project_dir: Path,
    config: "AamConfig",  # noqa: F821
    platform_name: str,
    no_deploy: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Attempt to install an artifact from source index.

    Args:
        artifact_name: Qualified or unqualified artifact name.

    Raises:
        ValueError: If the artifact cannot be found in sources.
    """
    from aam_cli.services.source_service import (
        build_source_index,
        resolve_artifact,
    )
    from aam_cli.services.install_service import install_from_source

    console.print(f"Searching sources for '{artifact_name}'...")

    index = build_source_index(config)
    virtual_package = resolve_artifact(artifact_name, index)

    console.print(
        f"  Found [bold]{virtual_package.name}[/bold] "
        f"({virtual_package.type}) in source "
        f"[cyan]{virtual_package.source_name}[/cyan]"
    )

    if dry_run:
        console.print(
            "\n[yellow]\\[Dry run — no packages installed][/yellow]"
        )
        return

    result = install_from_source(
        virtual_package=virtual_package,
        project_dir=project_dir,
        platform_name=platform_name,
        config=config,
        force=force,
        no_deploy=no_deploy,
    )

    if result["status"] == "already_installed":
        console.print(
            f"'{virtual_package.name}' is already installed. "
            f"Use --force to reinstall."
        )
        return

    console.print(
        f"\n[green]✓[/green] Installed [bold]{virtual_package.name}[/bold] "
        f"from source [cyan]{virtual_package.source_name}[/cyan] "
        f"@ {virtual_package.commit_sha[:8]}"
    )


################################################################################
#                                                                              #
# INSTALL FROM LOCAL DIRECTORY                                                 #
#                                                                              #
################################################################################


def _install_from_directory(
    ctx: click.Context,
    console: Console,
    source_dir: Path,
    project_dir: Path,
    platform_name: str,
    no_deploy: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Install a package from a local directory (FR-017)."""
    try:
        manifest = load_manifest(source_dir)
    except (FileNotFoundError, Exception) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return

    console.print(f"Installing {manifest.name}@{manifest.version} from {source_dir}...")

    if dry_run:
        console.print("[yellow]\\[Dry run — no changes][/yellow]")
        return

    # -----
    # Check for local modifications before overwriting (upgrade warning)
    # -----
    if (
        is_package_installed(manifest.name, project_dir)
        and not _handle_upgrade_warning(
            console, manifest.name, project_dir, force
        )
    ):
        console.print("[yellow]Aborted.[/yellow]")
        return

    # -----
    # Copy to .aam/packages/
    # -----
    ensure_workspace(project_dir)
    scope, base_name = parse_package_name(manifest.name)
    fs_name = to_filesystem_name(scope, base_name)
    dest = get_packages_dir(project_dir) / fs_name

    if dest.exists():
        shutil.rmtree(dest)

    shutil.copytree(source_dir, dest)

    # -----
    # Deploy if needed
    # -----
    if not no_deploy:
        if is_supported_platform(platform_name):
            adapter = create_adapter(platform_name, project_dir)
            from aam_cli.core.installer import _deploy_package

            _deploy_package(dest, adapter)
        else:
            console.print(
                f"[yellow]Warning:[/yellow] Unsupported platform '{platform_name}', "
                "skipping deployment."
            )

    # -----
    # Update lock file (with file checksums if available)
    # -----
    file_checksums = _read_file_checksums_from_package(dest)
    lock = read_lock_file(project_dir)
    lock.packages[manifest.name] = LockedPackage(
        version=manifest.version,
        source="local",
        checksum="",
        dependencies=manifest.dependencies,
        file_checksums=file_checksums,
    )
    write_lock_file(lock, project_dir)

    console.print(f"\n[green]✓[/green] Installed {manifest.name}@{manifest.version}")
    if file_checksums:
        console.print(
            f"  [dim]{len(file_checksums.files)} file checksum(s) "
            f"recorded for integrity verification[/dim]"
        )


################################################################################
#                                                                              #
# INSTALL FROM ARCHIVE                                                         #
#                                                                              #
################################################################################


def _install_from_archive(
    ctx: click.Context,
    console: Console,
    archive_path: Path,
    project_dir: Path,
    platform_name: str,
    no_deploy: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Install a package from a ``.aam`` archive file (FR-017)."""
    console.print(f"Installing from archive: {archive_path}...")

    if dry_run:
        console.print("[yellow]\\[Dry run — no changes][/yellow]")
        return

    # -----
    # Extract to temp, read manifest, then move to packages
    # -----
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        extract_archive(archive_path, tmp_path)

        try:
            manifest = load_manifest(tmp_path)
        except (FileNotFoundError, Exception) as exc:
            console.print(f"[red]Error:[/red] {exc}")
            ctx.exit(1)
            return

        # -----
        # Check for local modifications before overwriting
        # -----
        if (
            is_package_installed(manifest.name, project_dir)
            and not _handle_upgrade_warning(
                console, manifest.name, project_dir, force
            )
        ):
            console.print("[yellow]Aborted.[/yellow]")
            return

        # Move to .aam/packages/
        ensure_workspace(project_dir)
        scope, base_name = parse_package_name(manifest.name)
        fs_name = to_filesystem_name(scope, base_name)
        dest = get_packages_dir(project_dir) / fs_name

        if dest.exists():
            shutil.rmtree(dest)

        shutil.copytree(tmp_path, dest)

    # -----
    # Deploy if needed
    # -----
    if not no_deploy:
        if is_supported_platform(platform_name):
            adapter = create_adapter(platform_name, project_dir)
            from aam_cli.core.installer import _deploy_package

            _deploy_package(dest, adapter)
        else:
            console.print(
                f"[yellow]Warning:[/yellow] Unsupported platform '{platform_name}', "
                "skipping deployment."
            )

    # -----
    # Update lock file (with file checksums if available)
    # -----
    checksum = calculate_sha256(archive_path)
    file_checksums = _read_file_checksums_from_package(dest)
    lock = read_lock_file(project_dir)
    lock.packages[manifest.name] = LockedPackage(
        version=manifest.version,
        source="local",
        checksum=checksum,
        dependencies=manifest.dependencies,
        file_checksums=file_checksums,
    )
    write_lock_file(lock, project_dir)

    console.print(f"\n[green]✓[/green] Installed {manifest.name}@{manifest.version}")
    if file_checksums:
        console.print(
            f"  [dim]{len(file_checksums.files)} file checksum(s) "
            f"recorded for integrity verification[/dim]"
        )
