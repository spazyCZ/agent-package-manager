"""Uninstall command for AAM CLI.

Removes an installed package and its deployed artifacts.
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
from rich.prompt import Confirm

from aam_cli.adapters.factory import create_adapter
from aam_cli.core.config import load_config
from aam_cli.core.manifest import load_manifest
from aam_cli.core.workspace import (
    get_packages_dir,
    read_lock_file,
    write_lock_file,
)
from aam_cli.utils.naming import parse_package_name, to_filesystem_name
from aam_cli.utils.paths import resolve_project_dir

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
@click.option(
    "--global", "-g", "is_global", is_flag=True,
    help="Uninstall from global ~/.aam/ directory",
)
@click.pass_context
def uninstall(ctx: click.Context, package: str, is_global: bool) -> None:
    """Uninstall a package and remove deployed artifacts.

    Removes the package from ``.aam/packages/``, undeploys artifacts
    from the platform, and updates the lock file.

    Use ``-g`` / ``--global`` to uninstall from the user-wide ``~/.aam/``
    directory instead of the project-local ``.aam/`` workspace.

    Examples::

        aam uninstall my-package
        aam uninstall @author/my-package
        aam uninstall my-package -g
    """
    console: Console = ctx.obj["console"]
    project_dir = resolve_project_dir(is_global)

    # -----
    # Visual indicator for global mode
    # -----
    if is_global:
        console.print("[dim]Operating in global mode (~/.aam/)[/dim]\n")

    # -----
    # Step 1: Check if installed
    # -----
    lock = read_lock_file(project_dir)
    locked = lock.packages.get(package)

    if not locked:
        console.print(f"[red]Error:[/red] '{package}' is not installed.")
        ctx.exit(1)
        return

    # -----
    # Step 2: Check for dependents
    # -----
    dependents: list[str] = []
    for other_name, other_locked in lock.packages.items():
        if other_name == package:
            continue
        if package in other_locked.dependencies:
            dependents.append(other_name)

    if dependents:
        dep_list = ", ".join(dependents)
        console.print(f"[yellow]Warning:[/yellow] '{package}' is required by: {dep_list}.")
        if not Confirm.ask("Uninstall anyway?", default=False):
            console.print("[yellow]Aborted.[/yellow]")
            return

    console.print(f"Uninstalling [bold]{package}@{locked.version}[/bold]...")

    # -----
    # Step 3: Undeploy artifacts from platform
    # -----
    scope, base_name = parse_package_name(package)
    fs_name = to_filesystem_name(scope, base_name)
    pkg_dir = get_packages_dir(project_dir) / fs_name

    config = load_config(project_dir)

    if pkg_dir.is_dir():
        try:
            manifest = load_manifest(pkg_dir)
            adapter = create_adapter(config.default_platform, project_dir)

            console.print(f"\nRemoving deployed artifacts from {config.default_platform}...")

            for artifact_type, ref in manifest.all_artifacts:
                adapter.undeploy(ref.name, artifact_type)
                console.print(f"  [green]✓[/green] Removed {artifact_type}: {ref.name}")

        except Exception as exc:
            logger.warning(f"Could not undeploy artifacts for '{package}': {exc}")

        # -----
        # Step 4: Remove package directory
        # -----
        shutil.rmtree(pkg_dir)

    # -----
    # Step 5: Update lock file
    # -----
    del lock.packages[package]
    write_lock_file(lock, project_dir)

    console.print(f"\n[green]✓[/green] Uninstalled {package}")

    logger.info(f"Uninstalled package: {package}")
