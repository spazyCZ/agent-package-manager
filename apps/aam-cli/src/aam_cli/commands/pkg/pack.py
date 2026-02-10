"""``aam pkg pack`` — Build distributable .aam archive.

Delegates to the existing pack command logic.

Reference: spec 004 US7.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click

from aam_cli.commands.pack import pack

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


@click.command("pack")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.pass_context
def pkg_pack(ctx: click.Context, path: str) -> None:
    """Build a distributable ``.aam`` archive.

    Validates the package first, then creates a gzipped tar archive.

    Examples::

        aam pkg pack
        aam pkg pack ./my-package/
    """
    logger.info(f"pkg pack invoked: path='{path}'")

    # -----
    # Delegate to the existing pack command handler
    # -----
    ctx.invoke(pack, path=path)
