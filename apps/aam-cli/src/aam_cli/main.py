"""Main entry point for AAM CLI.

Registers all CLI commands and configures the root Click group
with categorized help output using :class:`OrderedGroup`.

Reference: spec 004 US7, US8; research.md R1, R2.
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

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# ORDERED GROUP                                                                #
#                                                                              #
################################################################################


class OrderedGroup(click.Group):
    """Click group that renders commands in categorized sections.

    Overrides ``format_commands()`` to render ``aam --help`` with
    labeled sections instead of a flat alphabetical list.

    The SECTIONS dict defines the display order. Commands not listed
    in any section (e.g., hidden deprecated aliases) are omitted.
    """

    SECTIONS: dict[str, list[str]] = {
        "Getting Started": ["init"],
        "Package Management": [
            "install",
            "uninstall",
            "upgrade",
            "outdated",
            "search",
            "list",
            "info",
        ],
        "Package Integrity": ["verify", "diff"],
        "Dependency Management": ["tree", "why", "check", "audit", "dedupe", "prune"],
        "Testing": ["test", "eval"],
        "Package Authoring": ["pkg"],
        "Source Management": ["source"],
        "Configuration": ["config", "registry"],
        "Authentication": ["login", "logout", "whoami"],
        "Utilities": ["mcp", "doctor", "convert", "cache"],
    }

    def format_commands(
        self,
        ctx: click.Context,
        formatter: click.HelpFormatter,
    ) -> None:
        """Render commands grouped by section with labeled headers.

        Args:
            ctx: Click context.
            formatter: Click help formatter.
        """
        for section_name, cmd_names in self.SECTIONS.items():
            commands: list[tuple[str, click.Command]] = []
            for name in cmd_names:
                cmd = self.commands.get(name)
                if cmd and not cmd.hidden:
                    commands.append((name, cmd))

            if commands:
                with formatter.section(section_name):
                    formatter.write_dl(
                        [
                            (name, cmd.get_short_help_str(limit=150))
                            for name, cmd in commands
                        ]
                    )


################################################################################
#                                                                              #
# CLI GROUP                                                                    #
#                                                                              #
################################################################################

console = Console()


@click.group(cls=OrderedGroup)
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
    ctx.obj["err_console"] = Console(stderr=True)

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
# COMMAND IMPORTS                                                              #
#                                                                              #
################################################################################

# Groups (from package __init__)
from aam_cli.commands.pkg import pkg  # noqa: E402
from aam_cli.commands.source import source  # noqa: E402
from aam_cli.commands.config import config  # noqa: E402
from aam_cli.commands.registry import registry  # noqa: E402
from aam_cli.commands.auth import login, logout, whoami  # noqa: E402
from aam_cli.commands._deprecated import register_deprecated_aliases  # noqa: E402
from aam_cli.commands.cache import cache  # noqa: E402
from aam_cli.commands.mcp import mcp  # noqa: E402

# Top-level commands (direct function imports)
from aam_cli.commands.init import client_init  # noqa: E402
from aam_cli.commands.install import install  # noqa: E402
from aam_cli.commands.uninstall import uninstall  # noqa: E402
from aam_cli.commands.upgrade import upgrade  # noqa: E402
from aam_cli.commands.outdated import outdated  # noqa: E402
from aam_cli.commands.search import search  # noqa: E402
from aam_cli.commands.list import list_packages  # noqa: E402
from aam_cli.commands.info import show_package  # noqa: E402
from aam_cli.commands.verify import verify  # noqa: E402
from aam_cli.commands.diff import diff_cmd  # noqa: E402
from aam_cli.commands.tree import tree  # noqa: E402
from aam_cli.commands.why import why  # noqa: E402
from aam_cli.commands.check import check  # noqa: E402
from aam_cli.commands.audit import audit  # noqa: E402
from aam_cli.commands.dedupe import dedupe  # noqa: E402
from aam_cli.commands.prune import prune  # noqa: E402
from aam_cli.commands.test import test  # noqa: E402
from aam_cli.commands.eval import eval_cmd  # noqa: E402
from aam_cli.commands.doctor import doctor  # noqa: E402
from aam_cli.commands.convert import convert  # noqa: E402

################################################################################
#                                                                              #
# GETTING STARTED                                                             #
#                                                                              #
################################################################################

cli.add_command(client_init)

################################################################################
#                                                                              #
# PACKAGE MANAGEMENT                                                           #
#                                                                              #
################################################################################

cli.add_command(install)
cli.add_command(uninstall)
cli.add_command(upgrade)
cli.add_command(outdated)
cli.add_command(search)
cli.add_command(list_packages)
cli.add_command(show_package)

################################################################################
#                                                                              #
# PACKAGE INTEGRITY                                                            #
#                                                                              #
################################################################################

cli.add_command(verify)
cli.add_command(diff_cmd)
cli.add_command(check)
cli.add_command(audit)
cli.add_command(tree)
cli.add_command(why)
cli.add_command(dedupe)
cli.add_command(prune)

################################################################################
#                                                                              #
# TESTING                                                                      #
#                                                                              #
################################################################################

cli.add_command(test)
cli.add_command(eval_cmd)

################################################################################
#                                                                              #
# PACKAGE AUTHORING (pkg group)                                                #
#                                                                              #
################################################################################

cli.add_command(pkg)

################################################################################
#                                                                              #
# SOURCE MANAGEMENT                                                            #
#                                                                              #
################################################################################

cli.add_command(source)

################################################################################
#                                                                              #
# CONFIGURATION                                                                #
#                                                                              #
################################################################################

cli.add_command(config)
cli.add_command(registry)

################################################################################
#                                                                              #
# AUTHENTICATION                                                               #
#                                                                              #
################################################################################

cli.add_command(login)
cli.add_command(logout)
cli.add_command(whoami)

################################################################################
#                                                                              #
# UTILITIES                                                                    #
#                                                                              #
################################################################################

cli.add_command(mcp)
cli.add_command(doctor)
cli.add_command(convert)
cli.add_command(cache)

################################################################################
#                                                                              #
# DEPRECATED ALIASES (hidden from --help)                                      #
# These delegate to `aam pkg <subcmd>` with a deprecation warning.            #
# Scheduled for removal in v0.3.0.                                             #
#                                                                              #
################################################################################

register_deprecated_aliases(cli)


################################################################################
#                                                                              #
# ENTRY POINT                                                                  #
#                                                                              #
################################################################################

if __name__ == "__main__":
    cli()
