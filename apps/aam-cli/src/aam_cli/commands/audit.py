"""``aam audit`` — Audit installed packages for integrity issues.

Verifies installed package directory hashes against stored lock file
integrity checksums and reports any tampering or degradation.
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

from aam_cli.services.dependency_tree_service import audit_deps

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

# Valid severity levels in order from most to least severe
SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


@click.command()
@click.option(
    "--severity",
    type=click.Choice(["critical", "high", "medium", "low", "info", "all"]),
    default="all",
    show_default=True,
    help="Minimum severity level to report.",
)
@click.option(
    "--project",
    default=None,
    type=click.Path(exists=True),
    help="Project directory (defaults to current directory).",
)
@click.pass_context
def audit(
    ctx: click.Context,
    severity: str,
    project: str | None,
) -> None:
    """Audit installed packages for integrity issues.

    Computes directory hashes for all installed packages and compares
    against stored checksums in ``package.agent.lock``. Reports any
    mismatches as CRITICAL findings.

    Exit code 1 if any findings at or above the specified severity.

    Examples::

        aam audit
        aam audit --severity critical
        aam audit --severity high --project ./my-project
    """
    console: Console = ctx.obj["console"]
    project_dir = Path(project).resolve() if project else Path.cwd()

    logger.info(f"Running audit: severity='{severity}'")

    result = audit_deps(project_dir=project_dir, severity=severity)

    findings = result.get("findings", [])
    total_checked = result.get("total_checked", 0)

    if total_checked == 0:
        console.print("[dim]No packages installed to audit.[/dim]")
        return

    # -----
    # Build Rich findings table
    # -----
    if findings:
        table = Table(title=f"Audit Findings ({severity})")
        table.add_column("Package", style="bold")
        table.add_column("Version")
        table.add_column("Severity")
        table.add_column("Title")

        # Map severity to color
        severity_colors = {
            "critical": "red",
            "high": "orange3",
            "medium": "yellow",
            "low": "blue",
            "info": "dim",
        }

        for finding in findings:
            sev = finding.get("severity", "info")
            color = severity_colors.get(sev, "white")

            table.add_row(
                finding.get("package_name", "?"),
                finding.get("version", "?"),
                f"[{color}]{sev.upper()}[/{color}]",
                finding.get("title", ""),
            )

        console.print(table)
        console.print(
            f"\n[red]✗[/red] {len(findings)} finding(s) across "
            f"{total_checked} packages audited"
        )

        # -----
        # Exit code 1 if any findings — audit_deps() already filters
        # findings to those at or above the requested --severity
        # -----
        ctx.exit(1)
    else:
        console.print(
            f"[green]✓[/green] All {total_checked} packages passed integrity audit"
        )
