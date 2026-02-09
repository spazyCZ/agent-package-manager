"""Doctor command for AAM CLI.

Provides ``aam doctor`` to run environment diagnostics and identify
configuration, registry, and package integrity issues.
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

from aam_cli.services.doctor_service import run_diagnostics

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# STATUS SYMBOLS                                                               #
#                                                                              #
################################################################################

STATUS_SYMBOLS = {
    "pass": "[green]✓[/green]",
    "warn": "[yellow]⚠[/yellow]",
    "fail": "[red]✗[/red]",
}

################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command()
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Run AAM environment diagnostics.

    Checks Python version, configuration validity, registry accessibility,
    installed package integrity, and detects incomplete installations.

    Examples::

        aam doctor
    """
    console: Console = ctx.obj["console"]
    project_dir = Path.cwd()

    logger.info("Running aam doctor")

    console.print("\n[bold]AAM Environment Diagnostics[/bold]\n")

    # -----
    # Run diagnostics
    # -----
    report = run_diagnostics(project_dir)

    # -----
    # Display individual check results
    # -----
    for check in report["checks"]:
        symbol = STATUS_SYMBOLS.get(check["status"], "?")
        console.print(f"  {symbol} {check['message']}")

        if check.get("suggestion"):
            console.print(f"      [dim]{check['suggestion']}[/dim]")

    # -----
    # Display summary
    # -----
    console.print()
    if report["healthy"]:
        console.print(f"[green]✓[/green] {report['summary']}")
    else:
        console.print(f"[red]✗[/red] {report['summary']}")
        ctx.exit(1)
