"""Check command for AAM CLI.

Provides ``aam check`` to verify package installation status and
system dependency availability. The ``--system`` flag runs pre-flight
checks against system dependencies declared in installed packages.
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
from rich.table import Table

from aam_cli.core.manifest import (
    SystemDependencies,
    SystemPackages,
    load_manifest_universal,
)
from aam_cli.services.dependency_tree_service import check_deps
from aam_cli.services.system_deps_service import check_system_deps
from aam_cli.utils.paths import get_packages_dir

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _collect_system_deps_from_installed(
    project_dir: Path,
) -> SystemDependencies:
    """Aggregate system dependencies from all installed package manifests.

    Iterates every package directory in ``.agent-packages/``, loads
    each manifest via ``load_manifest_universal()``, and merges all
    ``system_dependencies`` into a single :class:`SystemDependencies`
    object (union of all pip/npm/binary/MCP requirements).

    Args:
        project_dir: Project root directory.

    Returns:
        Merged :class:`SystemDependencies` containing the union of
        all installed packages' system requirements.
    """
    packages_dir = get_packages_dir(project_dir)

    # -----
    # Accumulate unique entries across all packages
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

    if not packages_dir.is_dir():
        logger.debug(f"Packages directory not found: {packages_dir}")
        return SystemDependencies()

    for pkg_dir in packages_dir.iterdir():
        if not pkg_dir.is_dir():
            continue

        try:
            manifest = load_manifest_universal(pkg_dir)
        except (FileNotFoundError, ValueError, Exception) as exc:
            logger.debug(
                f"Could not load manifest from '{pkg_dir}': {exc}"
            )
            continue

        sys_deps = manifest.system_dependencies
        if sys_deps is None:
            continue

        # -----
        # Merge: use first non-None version constraint encountered
        # -----
        if sys_deps.python and not python_version:
            python_version = sys_deps.python
        if sys_deps.node and not node_version:
            node_version = sys_deps.node

        for pkg in sys_deps.packages.pip:
            if pkg not in pip_packages:
                pip_packages.append(pkg)
        for pkg in sys_deps.packages.npm:
            if pkg not in npm_packages:
                npm_packages.append(pkg)
        for pkg in sys_deps.packages.brew:
            if pkg not in brew_packages:
                brew_packages.append(pkg)
        for pkg in sys_deps.packages.apt:
            if pkg not in apt_packages:
                apt_packages.append(pkg)
        for pkg in sys_deps.packages.cargo:
            if pkg not in cargo_packages:
                cargo_packages.append(pkg)
        for binary in sys_deps.binaries:
            if binary not in binaries:
                binaries.append(binary)
        for server in sys_deps.mcp_servers:
            if server not in mcp_servers:
                mcp_servers.append(server)

    return SystemDependencies(
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


################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command()
@click.option(
    "--system",
    "system_only",
    is_flag=True,
    help="Check system dependencies declared by installed packages.",
)
@click.option(
    "--project",
    default=None,
    type=click.Path(exists=True),
    help="Project directory (defaults to current directory).",
)
@click.pass_context
def check(
    ctx: click.Context,
    system_only: bool,
    project: str | None,
) -> None:
    """Check package installation status and system dependencies.

    Without flags, checks that all packages in the lock file have
    corresponding directories in ``.agent-packages/``.

    With ``--system``, runs pre-flight checks against system dependencies
    (python, node, binaries, pip/npm/cargo packages, MCP servers) declared
    by all currently installed packages.

    Examples::

        aam check
        aam check --system
        aam check --system --project ./my-project
    """
    console: Console = ctx.obj["console"]
    project_dir = Path(project).resolve() if project else Path.cwd()

    if system_only:
        _run_system_check(ctx, console, project_dir)
    else:
        _run_package_check(ctx, console, project_dir)


################################################################################
#                                                                              #
# PACKAGE CHECK                                                                #
#                                                                              #
################################################################################


def _run_package_check(
    ctx: click.Context,
    console: Console,
    project_dir: Path,
) -> None:
    """Check all lock-file entries have corresponding directories.

    Calls :func:`dependency_tree_service.check_deps` and renders a
    Rich table showing each package's presence status.

    Args:
        ctx: Click context for exit code management.
        console: Rich console for output.
        project_dir: Project root directory.
    """
    logger.info("Running package presence check")

    # -----
    # Delegate to dependency_tree_service
    # -----
    result = check_deps(project_dir=project_dir, system_only=False)

    # check_deps returns "results" key with package checks
    results = result.get("results", [])
    if not results:
        console.print("[dim]No packages in lock file[/dim]")
        return

    # -----
    # Render results table
    # -----
    table = Table(title="Package Installation Check")
    table.add_column("Package", style="bold")
    table.add_column("Version")
    table.add_column("Status")
    table.add_column("Directory")

    all_ok = result.get("all_passed", True)
    for entry in results:
        name = entry.get("name", "")
        version = entry.get("version", "")
        present = entry.get("present", False)
        directory = entry.get("directory", "")

        status_str = "[green]✓ present[/green]" if present else "[red]✗ missing[/red]"

        table.add_row(name, version, status_str, directory)

    console.print(table)

    # -----
    # Summary and exit code
    # -----
    present_count = sum(1 for e in results if e.get("present"))
    console.print(f"\n{present_count}/{len(results)} packages present")

    if not all_ok:
        missing_count = len(results) - present_count
        console.print(
            f"[red]✗[/red] {missing_count} package(s) missing from "
            "`.agent-packages/`. Run `aam install` to restore."
        )
        ctx.exit(1)
    else:
        console.print("[green]✓[/green] All packages present")


################################################################################
#                                                                              #
# SYSTEM CHECK                                                                 #
#                                                                              #
################################################################################


def _run_system_check(
    ctx: click.Context,
    console: Console,
    project_dir: Path,
) -> None:
    """Run system dependency checks and display results.

    Loads all installed package manifests, merges their system
    dependencies, and runs pre-flight checks via
    :func:`check_system_deps`.

    Args:
        ctx: Click context for exit code management.
        console: Rich console for output.
        project_dir: Project root directory.
    """
    logger.info("Running system dependency check")

    # -----
    # Collect system deps from all installed packages
    # -----
    merged_deps = _collect_system_deps_from_installed(project_dir)

    # -----
    # Check for empty deps (no packages declare system dependencies)
    # -----
    has_any_deps = (
        merged_deps.python is not None
        or merged_deps.node is not None
        or merged_deps.binaries
        or merged_deps.packages.pip
        or merged_deps.packages.npm
        or merged_deps.packages.cargo
        or merged_deps.mcp_servers
    )

    if not has_any_deps:
        console.print(
            "[green]✓[/green] No system dependencies declared "
            "by installed packages"
        )
        return

    # -----
    # Run checks
    # -----
    results = check_system_deps(merged_deps)

    # -----
    # Display results as a Rich table
    # -----
    table = Table(title="System Dependency Check")
    table.add_column("Name", style="bold")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Version")
    table.add_column("Hint")

    for result in results.passed:
        table.add_row(
            result.name,
            result.dep_type,
            "[green]✓ found[/green]",
            result.found_version or "",
            "",
        )

    for result in results.failed:
        table.add_row(
            result.name,
            result.dep_type,
            "[red]✗ missing[/red]",
            "",
            result.install_hint or "",
        )

    for result in results.optional_failed:
        table.add_row(
            result.name,
            result.dep_type,
            "[yellow]⚠ missing (optional)[/yellow]",
            "",
            result.install_hint or "",
        )

    console.print(table)

    # -----
    # Summary
    # -----
    total = len(results.passed) + len(results.failed) + len(results.optional_failed)
    console.print(
        f"\n{len(results.passed)}/{total} checks passed"
    )

    if not results.all_required_passed:
        console.print(
            f"[red]✗[/red] {len(results.failed)} required "
            f"dependencies missing"
        )
        ctx.exit(1)
    else:
        console.print("[green]✓[/green] All required dependencies satisfied")
