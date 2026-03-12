"""``aam pkg build`` — Build portable bundle for a target platform.

Delegates to the existing build command logic.

Reference: spec 004 US7.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console

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

SUPPORTED_TARGETS = ["cursor", "copilot", "claude-code", "codex", "all"]

################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command("build")
@click.option(
    "--target",
    "-t",
    required=True,
    type=click.Choice(SUPPORTED_TARGETS, case_sensitive=False),
    help="Target platform to build for (or 'all').",
)
@click.option(
    "--output",
    "-o",
    default="dist",
    type=click.Path(),
    help="Output directory for the bundle archive.",
)
@click.pass_context
def pkg_build(ctx: click.Context, target: str, output: str) -> None:
    """Build a portable bundle for a target platform.

    Produces a self-contained ``.bundle.aam`` archive containing all
    artifacts pre-compiled for the specified platform.

    Examples::

        aam pkg build --target cursor
        aam pkg build --target copilot --output ./releases/
        aam pkg build --target all
    """
    console: Console = ctx.obj["console"]

    # -----
    # Log command invocation
    # -----
    logger.info(f"Building portable bundle: target='{target}', output='{output}'")

    # -----
    # Step 1: Validate that we are inside a valid AAM package
    # -----
    console.print(f"[bold blue]Building bundle[/bold blue] for target: [bold]{target}[/bold]")

    # TODO: Parse aam.yaml from current directory
    # TODO: Resolve all dependencies
    # TODO: Run platform adapter to compile artifacts for the target
    # TODO: Package compiled artifacts + bundle.json into .bundle.aam
    # TODO: Write output to the specified directory

    console.print(
        f"\n[dim]Bundle build is not yet implemented. Output would be written to: {output}/[/dim]"
    )
