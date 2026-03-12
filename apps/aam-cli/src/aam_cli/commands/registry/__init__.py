"""Registry command group for AAM CLI."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click

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
def registry(ctx: click.Context) -> None:
    """Manage registry connections."""
    del ctx


################################################################################
#                                                                              #
# SUBCOMMAND REGISTRATION                                                      #
#                                                                              #
################################################################################

from aam_cli.commands.registry.add import registry_add  # noqa: E402
from aam_cli.commands.registry.init import registry_init  # noqa: E402
from aam_cli.commands.registry.list import registry_list  # noqa: E402
from aam_cli.commands.registry.remove import registry_remove  # noqa: E402

registry.add_command(registry_init, "init")
registry.add_command(registry_add, "add")
registry.add_command(registry_list, "list")
registry.add_command(registry_remove, "remove")
