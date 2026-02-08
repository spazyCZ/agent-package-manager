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

from aam_cli.adapters.cursor import CursorAdapter
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

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

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
@click.pass_context
def install(
    ctx: click.Context,
    package: str,
    platform: str | None,
    no_deploy: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Install a package and deploy artifacts.

    Supports multiple source formats:
      - ``name`` — install latest from registry
      - ``name@version`` — install specific version
      - ``@scope/name`` — scoped package from registry
      - ``./path/`` — install from local directory
      - ``file.aam`` — install from archive file

    Examples::

        aam install my-agent
        aam install my-agent@1.0.0
        aam install @author/my-agent
        aam install ./my-package/
        aam install my-package-1.0.0.aam
        aam install my-agent --no-deploy
        aam install my-agent --force
    """
    console: Console = ctx.obj["console"]
    project_dir = Path.cwd()

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
    # Registry-based install
    # -----
    _install_from_registry(
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


def _install_from_registry(
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
    """Install a package from configured registries."""
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
    # Check for configured registries
    # -----
    if not config.registries:
        console.print(
            "[red]Error:[/red] No registries configured. "
            "Run 'aam registry init' to create one, then "
            "'aam registry add' to register it."
        )
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
                f"{pkg_name}@{existing.version} is already installed. Use --force to reinstall."
            )
            return

    constraint = pkg_version or "*"
    console.print(f"Resolving {pkg_name}@{constraint}...")

    # -----
    # Step 2: Get registries
    # -----
    registries = []
    for reg_source in config.registries:
        registries.append(create_registry(reg_source))

    # -----
    # Step 3: Resolve dependencies
    # -----
    try:
        resolved = resolve_dependencies(
            [(pkg_name, constraint)],
            registries,
        )
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return

    for pkg in resolved:
        console.print(f"  + {pkg.name}@{pkg.version}")

    if dry_run:
        console.print("\n[yellow]\\[Dry run — no packages installed][/yellow]")
        return

    # -----
    # Step 4: Install
    # -----
    adapter = None
    if not no_deploy:
        adapter = CursorAdapter(project_dir) if platform_name == "cursor" else None

    installed = install_packages(
        resolved,
        adapter,
        config,
        project_dir,
        no_deploy=no_deploy,
        force=force,
    )

    # -----
    # Summary
    # -----
    console.print(f"\n[green]✓[/green] Installed {len(installed)} packages")


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
    _force: bool,
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
    if not no_deploy and platform_name == "cursor":
        adapter = CursorAdapter(project_dir)
        from aam_cli.core.installer import _deploy_package

        _deploy_package(dest, adapter)

    # -----
    # Update lock file
    # -----
    lock = read_lock_file(project_dir)
    lock.packages[manifest.name] = LockedPackage(
        version=manifest.version,
        source="local",
        checksum="",
        dependencies=manifest.dependencies,
    )
    write_lock_file(lock, project_dir)

    console.print(f"\n[green]✓[/green] Installed {manifest.name}@{manifest.version}")


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
    _force: bool,
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
    if not no_deploy and platform_name == "cursor":
        adapter = CursorAdapter(project_dir)
        from aam_cli.core.installer import _deploy_package

        _deploy_package(dest, adapter)

    # -----
    # Update lock file
    # -----
    checksum = calculate_sha256(archive_path)
    lock = read_lock_file(project_dir)
    lock.packages[manifest.name] = LockedPackage(
        version=manifest.version,
        source="local",
        checksum=checksum,
        dependencies=manifest.dependencies,
    )
    write_lock_file(lock, project_dir)

    console.print(f"\n[green]✓[/green] Installed {manifest.name}@{manifest.version}")
