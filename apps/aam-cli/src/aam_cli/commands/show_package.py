"""Show package command for AAM CLI.

Displays detailed metadata about an installed package.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import click
from rich.console import Console

from aam_cli.core.manifest import load_manifest
from aam_cli.core.workspace import get_packages_dir, read_lock_file
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
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command("info")
@click.argument("package")
@click.pass_context
def show_package(ctx: click.Context, package: str) -> None:
    """Show detailed information about an installed package.

    Examples::

        aam info my-package
        aam info @author/my-package
    """
    console: Console = ctx.obj["console"]
    project_dir = Path.cwd()

    # -----
    # Step 1: Check lock file
    # -----
    lock = read_lock_file(project_dir)
    locked = lock.packages.get(package)

    if not locked:
        console.print(f"[red]Error:[/red] '{package}' is not installed.")
        ctx.exit(1)
        return

    # -----
    # Step 2: Load manifest from installed directory
    # -----
    scope, base_name = parse_package_name(package)
    fs_name = to_filesystem_name(scope, base_name)
    pkg_dir = get_packages_dir(project_dir) / fs_name

    try:
        manifest = load_manifest(pkg_dir)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Package directory not found: {pkg_dir}")
        ctx.exit(1)
        return

    # -----
    # Step 3: Display metadata
    # -----
    console.print(f"[bold]{manifest.name}@{manifest.version}[/bold]")
    console.print(f"  Description: {manifest.description}")

    if manifest.author:
        console.print(f"  Author:      {manifest.author}")
    if manifest.license:
        console.print(f"  License:     {manifest.license}")
    if manifest.repository:
        console.print(f"  Repository:  {manifest.repository}")

    # -----
    # Artifacts
    # -----
    console.print("\n  [bold]Artifacts:[/bold]")
    for artifact_type, ref in manifest.all_artifacts:
        console.print(f"    {artifact_type}: [cyan]{ref.name}[/cyan]           — {ref.description}")

    # -----
    # Dependencies
    # -----
    console.print("\n  [bold]Dependencies:[/bold]")
    if manifest.dependencies:
        for dep_name, constraint in manifest.dependencies.items():
            dep_locked = lock.packages.get(dep_name)
            installed_str = f" (installed: {dep_locked.version})" if dep_locked else ""
            console.print(f"    {dep_name}  {constraint}{installed_str}")
    else:
        console.print("    None")

    # -----
    # Source info
    # -----
    console.print(f"\n  [bold]Source:[/bold] {locked.source}")
    if locked.checksum:
        console.print(f"  [bold]Checksum:[/bold] {locked.checksum}")
