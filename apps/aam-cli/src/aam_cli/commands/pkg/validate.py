"""``aam pkg validate`` — Validate package manifest and artifacts.

Delegates to the existing validate command logic.

Reference: spec 004 US7.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click

from aam_cli.commands.validate import validate

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


@click.command("validate")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.pass_context
def pkg_validate(ctx: click.Context, path: str) -> None:
    """Validate the package manifest and artifacts.

    Checks that ``aam.yaml`` is syntactically correct, all required fields
    are present, and all artifact paths exist.

    Examples::

        aam pkg validate
        aam pkg validate ./my-package/
    """
    logger.info(f"pkg validate invoked: path='{path}'")

    # -----
    # Delegate to the existing validate command handler
    # -----
    ctx.invoke(validate, path=path)
