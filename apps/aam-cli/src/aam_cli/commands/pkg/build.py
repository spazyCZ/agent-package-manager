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

from aam_cli.commands.build import build

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

SUPPORTED_TARGETS = ["cursor", "copilot", "claude", "codex", "all"]

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
    logger.info(f"pkg build invoked: target='{target}'")

    # -----
    # Delegate to the existing build command handler
    # -----
    ctx.invoke(build, target=target, output=output)
