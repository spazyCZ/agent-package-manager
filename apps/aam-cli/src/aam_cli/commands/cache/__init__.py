"""Cache command group for AAM CLI."""

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
def cache() -> None:
    """Manage the package download cache."""


################################################################################
#                                                                              #
# SUBCOMMAND REGISTRATION                                                      #
#                                                                              #
################################################################################

from aam_cli.commands.cache.clean import cache_clean  # noqa: E402
from aam_cli.commands.cache.ls import cache_ls  # noqa: E402

cache.add_command(cache_clean, "clean")
cache.add_command(cache_ls, "ls")
