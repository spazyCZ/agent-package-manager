"""Convert command for AAM CLI.

Provides ``aam convert`` to convert AI agent configurations between
platforms (Cursor, Copilot, Claude, Codex).

Reference: docs/specs/SPEC-convert-command.md
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

from aam_cli.converters.mappings import PLATFORMS, VERBOSE_WORKAROUNDS
from aam_cli.services.convert_service import ConversionResult, run_conversion

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

ARTIFACT_TYPES = ("instruction", "agent", "prompt", "skill")

################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command("convert")
@click.option(
    "--source-platform", "-s",
    required=True,
    type=click.Choice(PLATFORMS, case_sensitive=False),
    help="Source platform to convert from.",
)
@click.option(
    "--target-platform", "-t",
    required=True,
    type=click.Choice(PLATFORMS, case_sensitive=False),
    help="Target platform to convert to.",
)
@click.option(
    "--type",
    "artifact_type",
    type=click.Choice(ARTIFACT_TYPES, case_sensitive=False),
    default=None,
    help="Filter by artifact type.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be converted without writing files.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing target files (creates .bak backup).",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Show detailed conversion notes and workarounds.",
)
@click.pass_context
def convert(
    ctx: click.Context,
    source_platform: str,
    target_platform: str,
    artifact_type: str | None,
    dry_run: bool,
    force: bool,
    verbose: bool,
) -> None:
    """Convert AI agent configurations between platforms.

    Reads artifacts from one platform's format and writes them in
    another's format. Supports Cursor, Copilot, Claude, and Codex.

    Examples::

        aam convert -s cursor -t copilot
        aam convert -s copilot -t claude --type instruction --dry-run
        aam convert -s codex -t cursor --force
    """
    console: Console = ctx.obj["console"]
    project_dir = Path.cwd()

    # -----
    # Validate platforms are different
    # -----
    if source_platform.lower() == target_platform.lower():
        console.print(
            "[red]Error:[/red] Source and target platform cannot be the same."
        )
        ctx.exit(1)
        return

    # -----
    # Display header
    # -----
    prefix = "[DRY RUN] " if dry_run else ""
    console.print(
        f"\n{prefix}Converting [bold]{source_platform.title()}[/bold] "
        f"→ [bold]{target_platform.title()}[/bold]...\n"
    )

    # -----
    # Run conversion
    # -----
    report = run_conversion(
        project_root=project_dir,
        source_platform=source_platform.lower(),
        target_platform=target_platform.lower(),
        artifact_type=artifact_type.lower() if artifact_type else None,
        dry_run=dry_run,
        force=force,
    )

    # -----
    # Display results grouped by type
    # -----
    if not report.results:
        console.print(
            f"  No {source_platform} artifacts found to convert."
        )
        console.print()
        return

    # Group results by artifact type
    grouped: dict[str, list[ConversionResult]] = {}
    for result in report.results:
        grouped.setdefault(result.artifact_type.upper() + "S", []).append(result)

    for section_name, results in grouped.items():
        console.print(f"[bold]{section_name}:[/bold]")

        for result in results:
            if result.error:
                console.print(
                    f"  [red]✗[/red] {result.source_path}"
                )
                console.print(f"    [red]{result.error}[/red]")
            elif result.skipped:
                console.print(
                    f"  [yellow]⊘[/yellow] {result.source_path} → {result.target_path}"
                )
                for warning in result.warnings:
                    console.print(f"    [yellow]⚠ {warning}[/yellow]")
            else:
                console.print(
                    f"  [green]✓[/green] {result.source_path} → {result.target_path}"
                )
                for warning in result.warnings:
                    console.print(f"    [yellow]⚠ {warning}[/yellow]")
                    if verbose:
                        _print_verbose_workaround(console, warning)

        console.print()

    # -----
    # Display summary
    # -----
    summary_parts = [
        f"{report.converted_count} converted",
        f"{report.failed_count} failed",
        f"{report.warning_count} warnings",
    ]
    if report.skipped_count:
        summary_parts.append(f"{report.skipped_count} skipped")

    console.print(f"[bold]SUMMARY:[/bold] {', '.join(summary_parts)}")

    if report.warning_count and not verbose:
        console.print(
            "\nWarnings indicate metadata that could not be converted."
        )
        console.print(
            "Run with [bold]--verbose[/bold] for detailed workaround instructions."
        )

    console.print()

    if report.failed_count:
        ctx.exit(1)


################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _print_verbose_workaround(console: Console, warning: str) -> None:
    """Print verbose workaround text for a warning if available."""
    warning_lower = warning.lower()

    for key, workaround in VERBOSE_WORKAROUNDS.items():
        if key.replace("_", " ").replace("removed", "").strip() in warning_lower:
            console.print(f"      [dim]{workaround}[/dim]")
            return
