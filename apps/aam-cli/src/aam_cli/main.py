"""Main entry point for AAM CLI.

Registers all CLI commands and configures the root Click group.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console

from aam_cli import __version__
from aam_cli.commands import (
    build,
    config,
    create_package,
    install,
    publish,
    registry,
    search,
)
from aam_cli.commands.diff import diff_cmd
from aam_cli.commands.doctor import doctor
from aam_cli.commands.init_package import init_package
from aam_cli.commands.list_packages import list_packages
from aam_cli.commands.mcp_serve import mcp
from aam_cli.commands.pack import pack
from aam_cli.commands.show_package import show_package
from aam_cli.commands.source import source
from aam_cli.commands.uninstall import uninstall
from aam_cli.commands.validate import validate
from aam_cli.commands.verify import verify

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CLI GROUP                                                                    #
#                                                                              #
################################################################################

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="aam")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """AAM - Agent Package Manager.

    A package manager for AI agents, skills, and tools.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["console"] = console

    # -----
    # Configure logging level based on verbose flag
    # -----
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    else:
        logging.basicConfig(
            level=logging.WARNING,
            format="%(levelname)s: %(message)s",
        )


################################################################################
#                                                                              #
# COMMAND REGISTRATION                                                         #
#                                                                              #
################################################################################

# -----
# Existing commands
# -----
cli.add_command(build.build)
cli.add_command(create_package.create_package)
cli.add_command(install.install)
cli.add_command(registry.registry)
cli.add_command(search.search)
cli.add_command(publish.publish)
cli.add_command(config.config)

# -----
# New commands for local-repository feature
# -----
cli.add_command(init_package)
cli.add_command(validate)
cli.add_command(pack)
cli.add_command(list_packages)
cli.add_command(show_package)
cli.add_command(uninstall)

# -----
# Source management commands (spec 003)
# -----
cli.add_command(source)
cli.add_command(verify)
cli.add_command(diff_cmd)

# -----
# MCP server and diagnostic commands
# -----
cli.add_command(mcp)
cli.add_command(doctor)


if __name__ == "__main__":
    cli()
