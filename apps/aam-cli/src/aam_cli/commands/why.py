"""``aam why`` — Show why a package is installed.

Traces dependency provenance to explain which packages require
a given package.
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
from rich.panel import Panel

from aam_cli.services.dependency_tree_service import get_why

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
@click.argument("package_name")
@click.option(
    "--project",
    default=None,
    type=click.Path(exists=True),
    help="Project directory (defaults to current directory).",
)
@click.pass_context
def why(ctx: click.Context, package_name: str, project: str | None) -> None:
    """Show why a package is installed.

    Traces all packages that directly depend on PACKAGE_NAME and
    explains whether it is a direct or transitive dependency.

    Examples::

        aam why my-package
        aam why @scope/some-dep --project ./my-project
    """
    console: Console = ctx.obj["console"]
    project_dir = Path(project).resolve() if project else Path.cwd()

    logger.info(f"Tracing dependency provenance: package='{package_name}'")

    result = get_why(package_name=package_name, project_dir=project_dir)

    if not result["found"]:
        console.print(
            f"[red]Package '[bold]{package_name}[/bold]' "
            f"is not in the lock file.[/red]"
        )
        ctx.exit(1)
        return

    # -----
    # Build display content
    # -----
    version = result.get("version", "?")
    required_by = result.get("required_by", [])
    is_direct = result.get("is_direct", False)

    lines: list[str] = [
        f"[bold]{package_name}[/bold]@[cyan]{version}[/cyan]",
        "",
    ]

    if is_direct:
        lines.append("[green]Direct dependency[/green] (not required by any other package)")
    elif required_by:
        lines.append(f"[dim]Required by {len(required_by)} package(s):[/dim]")
        for dep in required_by:
            constraint = dep.get("constraint", "*")
            lines.append(
                f"  • [green]{dep['name']}[/green]@[cyan]{dep['version']}[/cyan] "
                f"([dim]{constraint}[/dim])"
            )

    console.print(
        Panel(
            "\n".join(lines),
            title=f"[bold]aam why {package_name}[/bold]",
        )
    )
