"""Source management command group for AAM CLI."""

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

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# COMMAND GROUP                                                                #
#                                                                              #
################################################################################


@click.group()
@click.pass_context
def source(ctx: click.Context) -> None:
    """Manage remote git artifact sources."""
    # -----
    # Ensure console handles exist for all subcommands.
    # -----
    ctx.ensure_object(dict)
    if "console" not in ctx.obj:
        ctx.obj["console"] = Console()
    if "err_console" not in ctx.obj:
        ctx.obj["err_console"] = Console(stderr=True)


################################################################################
#                                                                              #
# SUBCOMMAND REGISTRATION                                                      #
#                                                                              #
################################################################################

from aam_cli.commands.source.add import add  # noqa: E402
from aam_cli.commands.source.candidates import candidates  # noqa: E402
from aam_cli.commands.source.enable_defaults import enable_defaults  # noqa: E402
from aam_cli.commands.source.list import list_cmd  # noqa: E402
from aam_cli.commands.source.remove import remove  # noqa: E402
from aam_cli.commands.source.scan import scan  # noqa: E402
from aam_cli.commands.source.update import update  # noqa: E402

source.add_command(add, "add")
source.add_command(scan, "scan")
source.add_command(update, "update")
source.add_command(list_cmd, "list")
source.add_command(remove, "remove")
source.add_command(candidates, "candidates")
source.add_command(enable_defaults, "enable-defaults")
