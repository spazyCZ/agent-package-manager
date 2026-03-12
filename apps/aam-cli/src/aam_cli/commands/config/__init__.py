"""Configuration command group for AAM CLI."""

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
def config(ctx: click.Context) -> None:
    """Manage AAM configuration."""
    del ctx


################################################################################
#                                                                              #
# SUBCOMMAND REGISTRATION                                                      #
#                                                                              #
################################################################################

from aam_cli.commands.config.get import config_get  # noqa: E402
from aam_cli.commands.config.list import config_list  # noqa: E402
from aam_cli.commands.config.set import config_set  # noqa: E402

config.add_command(config_set, "set")
config.add_command(config_get, "get")
config.add_command(config_list, "list")
