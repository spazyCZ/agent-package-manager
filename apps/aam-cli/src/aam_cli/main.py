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
from aam_cli.utils.deprecation import print_deprecation_warning

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
        "Package Authoring": ["pkg"],
        "Source Management": ["source"],
        "Configuration": ["config", "registry"],
        "Utilities": ["mcp", "doctor", "convert"],
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

from aam_cli.commands import (  # noqa: E402
    build,
    config,
    create_package,
    install,
    publish,
    registry,
    search,
)
from aam_cli.commands.client_init import client_init  # noqa: E402
from aam_cli.commands.convert import convert  # noqa: E402
from aam_cli.commands.diff import diff_cmd  # noqa: E402
from aam_cli.commands.doctor import doctor  # noqa: E402
from aam_cli.commands.list_packages import list_packages  # noqa: E402
from aam_cli.commands.mcp_serve import mcp  # noqa: E402
from aam_cli.commands.outdated import outdated  # noqa: E402
from aam_cli.commands.pack import pack  # noqa: E402
from aam_cli.commands.pkg import pkg  # noqa: E402
from aam_cli.commands.show_package import show_package  # noqa: E402
from aam_cli.commands.source import source  # noqa: E402
from aam_cli.commands.uninstall import uninstall  # noqa: E402
from aam_cli.commands.upgrade import upgrade  # noqa: E402
from aam_cli.commands.validate import validate  # noqa: E402
from aam_cli.commands.verify import verify  # noqa: E402

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

cli.add_command(install.install)
cli.add_command(uninstall)
cli.add_command(upgrade)
cli.add_command(outdated)
cli.add_command(search.search)
cli.add_command(list_packages)
cli.add_command(show_package)

################################################################################
#                                                                              #
# PACKAGE INTEGRITY                                                            #
#                                                                              #
################################################################################

cli.add_command(verify)
cli.add_command(diff_cmd)

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

cli.add_command(config.config)
cli.add_command(registry.registry)

################################################################################
#                                                                              #
# UTILITIES                                                                    #
#                                                                              #
################################################################################

cli.add_command(mcp)
cli.add_command(doctor)
cli.add_command(convert)

################################################################################
#                                                                              #
# DEPRECATED ALIASES (hidden from --help)                                      #
# These delegate to `aam pkg <subcmd>` with a deprecation warning.            #
# Scheduled for removal in v0.3.0.                                             #
#                                                                              #
################################################################################


@cli.command("create-package", hidden=True)
@click.argument(
    "path",
    default=".",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
)
@click.option("--all", "include_all", is_flag=True)
@click.option("--type", "-t", "artifact_types", multiple=True)
@click.option("--platform", "-p", "platforms", multiple=True)
@click.option("--organize", default="copy")
@click.option("--include", "includes", multiple=True, type=click.Path())
@click.option("--include-as", default=None)
@click.option("--name", "pkg_name", default=None)
@click.option("--scope", "pkg_scope", default=None)
@click.option("--version", "pkg_version", default=None)
@click.option("--description", "pkg_description", default=None)
@click.option("--author", "pkg_author", default=None)
@click.option("--dry-run", is_flag=True)
@click.option("--output-dir", type=click.Path(file_okay=False, resolve_path=True), default=None)
@click.option("-y", "--yes", is_flag=True)
@click.option("--from-source", "from_source", default=None)
@click.option("--artifacts", "artifact_names", multiple=True)
@click.pass_context
def deprecated_create_package(ctx: click.Context, /, **kwargs: object) -> None:
    """(Deprecated) Use 'aam pkg create' instead."""
    print_deprecation_warning("aam create-package", "aam pkg create")
    ctx.invoke(create_package.create_package, **kwargs)


@cli.command("validate", hidden=True)
@click.argument("path", default=".", type=click.Path(exists=True))
@click.pass_context
def deprecated_validate(ctx: click.Context, path: str) -> None:
    """(Deprecated) Use 'aam pkg validate' instead."""
    print_deprecation_warning("aam validate", "aam pkg validate")
    ctx.invoke(validate, path=path)


@cli.command("pack", hidden=True)
@click.argument("path", default=".", type=click.Path(exists=True))
@click.pass_context
def deprecated_pack(ctx: click.Context, path: str) -> None:
    """(Deprecated) Use 'aam pkg pack' instead."""
    print_deprecation_warning("aam pack", "aam pkg pack")
    ctx.invoke(pack, path=path)


@cli.command("publish", hidden=True)
@click.option("--registry", "registry_name", default=None)
@click.option("--tag", default="latest")
@click.option("--dry-run", is_flag=True)
@click.pass_context
def deprecated_publish(
    ctx: click.Context,
    registry_name: str | None,
    tag: str,
    dry_run: bool,
) -> None:
    """(Deprecated) Use 'aam pkg publish' instead."""
    print_deprecation_warning("aam publish", "aam pkg publish")
    ctx.invoke(publish.publish, registry_name=registry_name, tag=tag, dry_run=dry_run)


@cli.command("build", hidden=True)
@click.option("--target", "-t", required=True)
@click.option("--output", "-o", default="dist", type=click.Path())
@click.pass_context
def deprecated_build(ctx: click.Context, target: str, output: str) -> None:
    """(Deprecated) Use 'aam pkg build' instead."""
    print_deprecation_warning("aam build", "aam pkg build")
    ctx.invoke(build.build, target=target, output=output)


@cli.command("update", hidden=True)
@click.argument("package", required=False)
@click.option("--dry-run", is_flag=True)
@click.option("--force", "-f", is_flag=True)
@click.pass_context
def update_alias(
    ctx: click.Context,
    package: str | None,
    dry_run: bool,
    force: bool,
) -> None:
    """(Hidden alias) Synonym for 'aam upgrade' — npm convention."""
    ctx.invoke(upgrade, package=package, dry_run=dry_run, force=force)


################################################################################
#                                                                              #
# ENTRY POINT                                                                  #
#                                                                              #
################################################################################

if __name__ == "__main__":
    cli()
