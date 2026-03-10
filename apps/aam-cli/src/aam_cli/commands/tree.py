"""``aam tree`` — Display the resolved dependency tree.

Reads ``package.agent.lock`` and renders a nested dependency tree
using Rich's tree rendering.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.tree import Tree

from aam_cli.services.dependency_tree_service import get_tree

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
@click.option(
    "--depth",
    "-d",
    default=0,
    type=int,
    show_default=True,
    help="Maximum tree depth to display (0 = unlimited).",
)
@click.option(
    "--project",
    default=None,
    type=click.Path(exists=True),
    help="Project directory (defaults to current directory).",
)
@click.pass_context
def tree(ctx: click.Context, depth: int, project: str | None) -> None:
    """Display the resolved dependency tree.

    Reads ``package.agent.lock`` and shows all installed packages
    with their transitive dependencies.

    Examples::

        aam tree
        aam tree --depth 2
        aam tree --project ./my-project
    """
    console: Console = ctx.obj["console"]
    project_dir = Path(project).resolve() if project else Path.cwd()

    logger.info(f"Rendering dependency tree: depth={depth}")

    result = get_tree(project_dir=project_dir, depth=depth)

    if result["total_packages"] == 0:
        console.print("[dim]No packages installed.[/dim]")
        return

    # -----
    # Build Rich tree from returned dict
    # -----
    root_tree = Tree(
        f"[bold]project[/bold] [dim]({result['total_packages']} packages)[/dim]"
    )

    def _add_children(
        rich_node: Tree,
        node_dict: dict[str, Any],
    ) -> None:
        """Recursively add children to a Rich tree node.

        Args:
            rich_node: Rich tree node to attach children to.
            node_dict: Serialized DependencyTreeNode dict.
        """
        for child in node_dict.get("children", []):
            label = f"[green]{child['name']}[/green]@[cyan]{child['version']}[/cyan]"
            if child.get("optional"):
                label += " [dim](optional)[/dim]"
            child_node = rich_node.add(label)
            _add_children(child_node, child)

    _add_children(root_tree, result["tree"])

    console.print(root_tree)
    console.print(
        f"\n[dim]{result['total_packages']} packages total[/dim]"
    )
