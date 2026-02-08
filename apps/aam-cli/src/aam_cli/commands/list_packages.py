"""List packages command for AAM CLI.

Lists installed packages from the lock file and ``.aam/packages/``.
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
from rich.tree import Tree

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


@click.command("list")
@click.option("--tree", is_flag=True, help="Show dependency tree")
@click.pass_context
def list_packages(ctx: click.Context, tree: bool) -> None:
    """List installed packages.

    Shows a table of installed packages with version and artifact counts.
    Use ``--tree`` to see the dependency tree.

    Examples::

        aam list
        aam list --tree
    """
    console: Console = ctx.obj["console"]
    project_dir = Path.cwd()

    lock = read_lock_file(project_dir)

    if not lock.packages:
        console.print("No packages installed.")
        return

    if tree:
        _show_tree(console, lock, project_dir)
    else:
        _show_table(console, lock, project_dir)


def _show_table(
    console: Console,
    lock: "LockFile",  # noqa: F821
    project_dir: Path,
) -> None:
    """Display packages as a flat table."""
    console.print("[bold]Installed packages:[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Artifacts")

    packages_dir = get_packages_dir(project_dir)

    for pkg_name, locked in lock.packages.items():
        # -----
        # Try to read the manifest for artifact counts
        # -----
        artifact_info = ""
        scope, base_name = parse_package_name(pkg_name)
        fs_name = to_filesystem_name(scope, base_name)
        pkg_dir = packages_dir / fs_name

        if pkg_dir.is_dir():
            try:
                manifest = load_manifest(pkg_dir)
                counts: dict[str, int] = {}
                for atype, _ref in manifest.all_artifacts:
                    counts[atype] = counts.get(atype, 0) + 1
                parts = [f"{c} {t}" for t, c in counts.items()]
                total = manifest.artifact_count
                artifact_info = f"{total} ({', '.join(parts)})"
            except Exception:
                artifact_info = "?"

        table.add_row(pkg_name, locked.version, artifact_info)

    console.print(table)


def _show_tree(
    console: Console,
    lock: "LockFile",  # noqa: F821
    _project_dir: Path,
) -> None:
    """Display packages as a dependency tree."""
    # -----
    # Find root packages (not depended on by anything)
    # -----
    all_deps: set[str] = set()
    for locked in lock.packages.values():
        all_deps.update(locked.dependencies.keys())

    roots = [name for name in lock.packages if name not in all_deps]

    for root_name in roots:
        locked = lock.packages[root_name]
        tree = Tree(f"{root_name}@{locked.version}")

        _add_deps_to_tree(tree, locked, lock)
        console.print(tree)


def _add_deps_to_tree(
    parent: Tree,
    locked: "LockedPackage",  # noqa: F821
    lock: "LockFile",  # noqa: F821
) -> None:
    """Recursively add dependencies to a Rich Tree."""
    for dep_name in locked.dependencies:
        dep_locked = lock.packages.get(dep_name)
        if dep_locked:
            branch = parent.add(f"{dep_name}@{dep_locked.version}")
            _add_deps_to_tree(branch, dep_locked, lock)
        else:
            parent.add(f"{dep_name} [dim](not installed)[/dim]")
