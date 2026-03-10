"""Eval command for AAM CLI.

Runs LLM-judged evaluations for skills in an AAM package.
Supports dry-run mode to preview what would be executed.

Reference: UAAPS v0.5.0 spec §15 validation.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
from pathlib import Path

import click
from rich.console import Console

from aam_cli.services.eval_service import (
    DEFAULT_ENGINE,
    EvalSuiteResult,
    SUPPORTED_ENGINES,
    run_evals,
)

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


@click.command("eval")
@click.option("--target", default=None, help="Specific skill to evaluate")
@click.option(
    "--engine",
    default=DEFAULT_ENGINE,
    type=click.Choice(SUPPORTED_ENGINES),
    help="Eval engine to use",
)
@click.option("--dry-run", is_flag=True, help="Parse cases without executing")
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
@click.pass_context
def eval_cmd(
    ctx: click.Context,
    target: str | None,
    engine: str,
    dry_run: bool,
    output_json: bool,
) -> None:
    """Run LLM-judged evaluations for skills.

    Examples::

        aam eval --dry-run          # Preview eval cases
        aam eval                    # Run all evals
        aam eval --target my-skill  # Eval a specific skill
        aam eval --engine claude-code --json
    """
    console: Console = ctx.obj["console"]
    package_dir = Path.cwd().resolve()

    logger.info(f"Running evals in {package_dir}")

    suites = run_evals(
        package_dir,
        target=target,
        engine=engine,
        dry_run=dry_run,
    )

    if not suites:
        console.print("[yellow]No eval suites found.[/yellow]")
        ctx.exit(0)
        return

    if output_json:
        console.print(json.dumps([s.to_dict() for s in suites], indent=2))
    else:
        _render_results(console, suites, dry_run=dry_run)

    total_failed = sum(s.failed for s in suites)
    if total_failed > 0 and not dry_run:
        ctx.exit(1)


def _render_results(
    console: Console,
    suites: list[EvalSuiteResult],
    dry_run: bool = False,
) -> None:
    """Render eval results to the console.

    Args:
        console: Rich console instance.
        suites: Eval suite results to render.
        dry_run: Whether this was a dry-run.
    """
    for suite in suites:
        console.print(f"\n[bold]{suite.suite_name}[/bold] [dim](engine: {suite.engine})[/dim]")

        for case_result in suite.cases:
            if case_result.status == "dry-run":
                console.print(f"  [blue]⊘[/blue] {case_result.name} [dim](dry-run)[/dim]")
            elif case_result.status == "pass":
                score_str = f" score={case_result.score}" if case_result.score else ""
                console.print(
                    f"  [green]✓[/green] {case_result.name}{score_str} "
                    f"[dim]({case_result.duration_ms:.0f}ms)[/dim]"
                )
            else:
                console.print(
                    f"  [red]✗[/red] {case_result.name} "
                    f"[dim]({case_result.duration_ms:.0f}ms)[/dim]"
                )
                if case_result.error:
                    console.print(f"    [red]{case_result.error}[/red]")

    if dry_run:
        total = sum(s.total for s in suites)
        console.print(f"\n[bold]Dry run:[/bold] {total} eval cases discovered")
    else:
        total_passed = sum(s.passed for s in suites)
        total_failed = sum(s.failed for s in suites)
        console.print(
            f"\n[bold]Results:[/bold] "
            f"[green]{total_passed} passed[/green], "
            f"[red]{total_failed} failed[/red], "
            f"{total_passed + total_failed} total"
        )
