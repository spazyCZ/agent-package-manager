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

import click

from aam_cli.commands.init_package import init_package

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
@click.pass_context
def pkg_init(ctx: click.Context, name: str | None) -> None:
    """Scaffold a new AAM package interactively.

    Creates an ``aam.yaml`` manifest and artifact directories.

    Examples::

        aam pkg init
        aam pkg init my-package
        aam pkg init @author/my-package
    """
    logger.info(f"pkg init invoked: name='{name}'")

    # -----
    # Delegate to the existing init_package command handler
    # -----
    ctx.invoke(init_package, name=name)
