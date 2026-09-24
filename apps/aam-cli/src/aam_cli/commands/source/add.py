"""Add a remote git artifact source."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging

import click
from rich.console import Console

from aam_cli.services.source_service import add_source

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command()
@click.argument("source_url")
@click.option("--ref", default=None, help="Git reference (branch, tag, or commit SHA)")
@click.option("--path", "scan_path", default=None, help="Subdirectory to scan within the repo")
@click.option("--name", default=None, help="Custom display name for the source")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def add(
    ctx: click.Context,
    source_url: str,
    ref: str | None,
    scan_path: str | None,
    name: str | None,
    output_json: bool,
) -> None:
    """Add a remote git repository as an artifact source."""
    console: Console = ctx.obj["console"]
    err_console: Console = ctx.obj["err_console"]
    logger.info(f"CLI source add: url='{source_url}'")

    try:
        result = add_source(
            source_str=source_url,
            ref=ref,
            path=scan_path,
            name=name,
        )
    except ValueError as error:
        err_console.print(f"[red]Error:[/red] {error}")
        ctx.exit(1)
        return
    except Exception as error:
        err_console.print(f"[red]Error:[/red] Failed to add source: {error}")
        logger.error(f"Source add failed: {error}", exc_info=True)
        ctx.exit(1)
        return

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    console.print()
    console.print(f"[green]✓[/green] Source '[bold]{result['name']}[/bold]' added successfully")
    console.print()
    console.print(f"  Repository:  {result['url']}")
    console.print(f"  Ref:         {result['ref']}")
    if result["path"]:
        console.print(f"  Path:        {result['path']}")
    console.print(f"  Commit:      {result['commit'][:12]}")
    console.print()

    by_type = result["artifacts_by_type"]
    console.print(f"  Artifacts found: [bold]{result['artifact_count']}[/bold]")
    if by_type["skills"]:
        console.print(f"    Skills:       {by_type['skills']}")
    if by_type["agents"]:
        console.print(f"    Agents:       {by_type['agents']}")
    if by_type["prompts"]:
        console.print(f"    Prompts:      {by_type['prompts']}")
    if by_type["instructions"]:
        console.print(f"    Instructions: {by_type['instructions']}")
    console.print()
