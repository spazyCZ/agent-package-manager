"""Client initialization command for AAM CLI.

``aam init`` guides new users through platform selection and default
source configuration. When called with a ``[name]`` argument, it
detects the old usage pattern and delegates to ``aam pkg init``.

Reference: spec 004 US1; research.md R2, R4.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console

from aam_cli.services.client_init_service import (
    SUPPORTED_PLATFORMS,
    ClientInitResult,
    detect_platform,
    orchestrate_init,
    orchestrate_project_init,
)
from aam_cli.utils.deprecation import print_deprecation_warning

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
    "-y",
    "--yes",
    is_flag=True,
    help="Non-interactive: use defaults for all prompts",
)
@click.option(
    "--project",
    is_flag=True,
    help="Create a project-level .aam/config.yaml instead of the global config",
)
@click.pass_context
def client_init(ctx: click.Context, name: str | None, yes: bool, project: bool) -> None:
    """Set up AAM for your project.

    Configures the default AI platform and registers community
    artifact sources. Run this once in a new project to get started.

    Use ``--project`` to create a project-level ``.aam/config.yaml``
    that overrides the global configuration for this directory.

    If called with a NAME argument, delegates to ``aam pkg init``
    for backward compatibility (deprecated).

    Examples::

        aam init
        aam init --yes
        aam init --project
        aam init --project --yes
    """
    console: Console = ctx.obj["console"]

    # -----
    # Backward compatibility: "aam init <name>" means old package init
    # Delegate to pkg init with deprecation warning
    # -----
    if name:
        print_deprecation_warning(
            "aam init <name>",
            "aam pkg init <name>",
        )
        from aam_cli.commands.pkg.init import pkg_init

        ctx.invoke(pkg_init, name=name)
        return

    logger.info(f"Client init invoked: yes={yes}, project={project}")

    if project:
        _init_project(ctx, console, yes)
    else:
        _init_global(ctx, console, yes)


def _init_project(
    ctx: click.Context,
    console: Console,
    yes: bool,
) -> None:
    """Handle ``aam init --project`` to create a project-level config."""
    from aam_cli.utils.paths import get_project_config_path

    config_path = get_project_config_path()

    # -----
    # Step 1: Check for existing project config
    # -----
    if config_path.exists() and not yes:
        console.print(
            "[yellow]Project config already exists.[/yellow] "
            f"Config: {config_path}"
        )
        if not click.confirm("Overwrite?", default=False):
            console.print("[dim]Aborted.[/dim]")
            return

    # -----
    # Step 2: Detect or ask for platform
    # -----
    detected = detect_platform()

    if yes:
        platform = detected or "cursor"
    else:
        if detected:
            console.print(
                f"\n  Detected platform: [bold cyan]{detected}[/bold cyan]"
            )

        platform = click.prompt(
            "Choose default platform",
            type=click.Choice(SUPPORTED_PLATFORMS, case_sensitive=False),
            default=detected or "cursor",
        )

    # -----
    # Step 3: Ask for active platforms
    # -----
    if yes:
        active_platforms = [platform]
    else:
        console.print(
            f"\n  Active platforms (comma-separated, default: {platform}):"
        )
        raw = click.prompt(
            "Active platforms",
            default=platform,
        )
        active_platforms = [p.strip() for p in raw.split(",") if p.strip()]

    console.print(f"\n  Platform:         [bold]{platform}[/bold]")
    console.print(f"  Active platforms: [bold]{', '.join(active_platforms)}[/bold]")

    # -----
    # Step 4: Orchestrate
    # -----
    result: ClientInitResult = orchestrate_project_init(
        platform=platform,
        active_platforms=active_platforms,
    )

    # -----
    # Step 5: Display summary
    # -----
    console.print()

    if result.is_reconfigure:
        console.print("[green]✓[/green] Project config updated.")
    else:
        console.print("[green]✓[/green] Project config created.")

    console.print(f"  Config: {result.config_path}")

    logger.info("Project init flow completed")


def _init_global(
    ctx: click.Context,
    console: Console,
    yes: bool,
) -> None:
    """Handle ``aam init`` (global config initialization)."""

    # -----
    # Step 1: Check for existing config
    # -----
    from aam_cli.utils.paths import get_global_aam_dir

    config_path = get_global_aam_dir() / "config.yaml"

    if config_path.exists() and not yes:
        console.print(
            "[yellow]AAM is already configured.[/yellow] "
            f"Config: {config_path}"
        )
        if not click.confirm("Reconfigure?", default=False):
            console.print("[dim]Aborted.[/dim]")
            return

    # -----
    # Step 2: Detect or ask for platform
    # -----
    detected = detect_platform()

    if yes:
        platform = detected or "cursor"
    else:
        if detected:
            console.print(
                f"\n  Detected platform: [bold cyan]{detected}[/bold cyan]"
            )

        platform = click.prompt(
            "Choose platform",
            type=click.Choice(SUPPORTED_PLATFORMS, case_sensitive=False),
            default=detected or "cursor",
        )

    console.print(f"\n  Platform: [bold]{platform}[/bold]")

    # -----
    # Step 3: Sources setup
    # -----
    skip_sources = False
    if not yes:
        skip_sources = not click.confirm(
            "Register community artifact sources?",
            default=True,
        )

    # -----
    # Step 4: Orchestrate
    # -----
    result: ClientInitResult = orchestrate_init(
        platform=platform,
        skip_sources=skip_sources,
    )

    # -----
    # Step 5: Display summary
    # -----
    console.print()

    if result.is_reconfigure:
        console.print("[green]✓[/green] AAM reconfigured successfully.")
    else:
        console.print("[green]✓[/green] AAM initialized successfully.")

    console.print(f"  Platform:  [bold]{result.platform}[/bold]")
    console.print(f"  Config:    {result.config_path}")

    if result.sources_added:
        console.print(
            f"  Sources:   {len(result.sources_added)} community source(s) added"
        )
        for src_name in result.sources_added:
            console.print(f"    • {src_name}")

    # -----
    # Next steps
    # -----
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  [cyan]aam search <query>[/cyan]   — Find packages to install")
    console.print("  [cyan]aam install <pkg>[/cyan]     — Install a package")
    console.print("  [cyan]aam list --available[/cyan]  — Browse source artifacts")
    console.print("  [cyan]aam pkg init[/cyan]          — Create a new package")

    logger.info("Client init flow completed")
