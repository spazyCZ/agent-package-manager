"""Test command for AAM CLI.

Runs deterministic assert tests for skills and hooks in an AAM package.

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

from aam_cli.services.test_service import (
    TestSuiteResult,
    run_hook_tests,
    run_skill_tests,
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


@click.command("test")
@click.argument("skill_name", required=False)
@click.option("--hooks", is_flag=True, help="Run hook tests instead of skill tests")
@click.option("--event", default=None, help="Filter hook tests by event name")
@click.option("--case", default=None, help="Run a specific test case by name")
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
@click.pass_context
def test(
    ctx: click.Context,
    skill_name: str | None,
    hooks: bool,
    event: str | None,
    case: str | None,
    output_json: bool,
) -> None:
    """Run deterministic tests for skills or hooks.

    Examples::

        aam test                    # Test all skills
        aam test my-skill           # Test a specific skill
        aam test --hooks            # Test all hooks
        aam test --hooks --event pre_tool_use
    """
    console: Console = ctx.obj["console"]
    package_dir = Path.cwd().resolve()

    logger.info(f"Running tests in {package_dir}")

    if hooks:
        suites = run_hook_tests(package_dir, event_name=event, case_name=case)
    else:
        suites = run_skill_tests(package_dir, skill_name=skill_name)

    if not suites:
        console.print("[yellow]No test suites found.[/yellow]")
        ctx.exit(0)
        return

    if output_json:
        console.print(json.dumps([s.to_dict() for s in suites], indent=2))
    else:
        _render_results(console, suites)

    total_failed = sum(s.failed for s in suites)
    if total_failed > 0:
        ctx.exit(1)


def _render_results(console: Console, suites: list[TestSuiteResult]) -> None:
    """Render test results to the console.

    Args:
        console: Rich console instance.
        suites: Test suite results to render.
    """
    total_passed = 0
    total_failed = 0

    for suite in suites:
        console.print(f"\n[bold]{suite.suite_name}[/bold]")

        for case_result in suite.cases:
            if case_result.passed:
                console.print(
                    f"  [green]✓[/green] {case_result.name} "
                    f"[dim]({case_result.duration_ms:.0f}ms)[/dim]"
                )
            else:
                console.print(
                    f"  [red]✗[/red] {case_result.name} "
                    f"[dim]({case_result.duration_ms:.0f}ms)[/dim]"
                )
                if case_result.error:
                    console.print(f"    [red]{case_result.error}[/red]")

        total_passed += suite.passed
        total_failed += suite.failed

    console.print(
        f"\n[bold]Results:[/bold] "
        f"[green]{total_passed} passed[/green], "
        f"[red]{total_failed} failed[/red], "
        f"{total_passed + total_failed} total"
    )
