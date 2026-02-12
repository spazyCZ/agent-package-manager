"""Deprecation warning utilities for CLI command migration.

Provides standardized deprecation messages for old root-level
commands that have moved under ``aam pkg``.

Reference: spec 004 research.md R2; contracts/cli-commands.md
deprecated aliases section.
"""

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

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# DEPRECATION WARNING                                                          #
#                                                                              #
################################################################################


def print_deprecation_warning(
    old_cmd: str,
    new_cmd: str,
    removal_version: str = "0.3.0",
) -> None:
    """Print a styled deprecation warning to stderr.

    Warns the user that a CLI command has been moved and suggests
    the new command path. The warning is written to stderr so it
    does not interfere with stdout piping.

    Args:
        old_cmd: The deprecated command name (e.g., ``aam validate``).
        new_cmd: The replacement command name (e.g., ``aam pkg validate``).
        removal_version: The version when the old command will be removed.
    """
    logger.info(
        f"Deprecated command invoked: old='{old_cmd}', new='{new_cmd}'"
    )

    warning = click.style(
        f"Warning: '{old_cmd}' is deprecated and will be removed in "
        f"v{removal_version}. Use '{new_cmd}' instead.",
        fg="yellow",
        bold=True,
    )
    click.echo(warning, err=True)
