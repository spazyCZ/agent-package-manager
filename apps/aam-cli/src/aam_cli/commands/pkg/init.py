"""``aam pkg init`` — Scaffold a new AAM package.

Delegates to the existing init_package scaffolding logic.

Reference: spec 004 US7.
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

from aam_cli.commands.init_package import init_package
from aam_cli.core.manifest import load_manifest_universal

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


@click.command("init")
@click.argument("name", required=False)
@click.option(
    "--migrate",
    is_flag=True,
    default=False,
    help="Migrate an existing aam.yaml to package.agent.json format.",
)
@click.pass_context
def pkg_init(ctx: click.Context, name: str | None, migrate: bool) -> None:
    """Scaffold a new AAM package (generates ``package.agent.json``).

    Creates a ``package.agent.json`` manifest and artifact directories.
    Use ``--migrate`` to convert an existing ``aam.yaml`` to the new
    ``package.agent.json`` format.

    Examples::

        aam pkg init
        aam pkg init my-package
        aam pkg init @author/my-package
        aam pkg init --migrate
    """
    import json

    logger.info(f"pkg init invoked: name='{name}', migrate={migrate}")

    # -----
    # Handle --migrate: read existing manifest and rewrite as JSON
    # -----
    if migrate:
        console: Console = ctx.obj["console"]
        cwd = Path.cwd()
        try:
            manifest = load_manifest_universal(cwd)
        except FileNotFoundError:
            console.print(
                "[red]Error:[/red] No manifest found to migrate. "
                "Run 'aam pkg init' to create a new package."
            )
            ctx.exit(1)
            return

        json_path = cwd / "package.agent.json"
        json_path.write_text(
            json.dumps(manifest.model_dump(by_alias=True), indent=2) + "\n",
            encoding="utf-8",
        )
        console.print(
            f"[green]Migrated[/green] manifest to "
            f"[bold]package.agent.json[/bold] "
            f"(format: {manifest.manifest_format} -> json)"
        )
        return

    # -----
    # Delegate to the existing init_package command handler
    # -----
    ctx.invoke(init_package, name=name)
