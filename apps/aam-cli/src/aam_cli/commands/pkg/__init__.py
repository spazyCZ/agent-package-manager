"""Package authoring command group (``aam pkg``).

Groups all creator/authoring commands under a single ``pkg`` prefix:
  - ``aam pkg init``       — Scaffold a new AAM package
  - ``aam pkg create``     — Create package from existing project or source
  - ``aam pkg validate``   — Validate package manifest and artifacts
  - ``aam pkg pack``       — Build distributable .aam archive
  - ``aam pkg publish``    — Publish archive to a registry
  - ``aam pkg build``      — Build portable bundle for a target platform

Reference: spec 004 US7; research.md R1, R2.
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
# COMMAND GROUP                                                                #
#                                                                              #
################################################################################


@click.group()
@click.pass_context
def pkg(ctx: click.Context) -> None:
    """Package authoring commands.

    Create, validate, pack, and publish AAM packages.
    For installing packages, use 'aam install'.
    """
    ctx.ensure_object(dict)


################################################################################
#                                                                              #
# SUBCOMMAND REGISTRATION                                                     #
#                                                                              #
################################################################################

# Import and register subcommands
from aam_cli.commands.pkg.build import pkg_build  # noqa: E402
from aam_cli.commands.pkg.create import pkg_create  # noqa: E402
from aam_cli.commands.pkg.init import pkg_init  # noqa: E402
from aam_cli.commands.pkg.pack import pkg_pack  # noqa: E402
from aam_cli.commands.pkg.publish import pkg_publish  # noqa: E402
from aam_cli.commands.pkg.validate import pkg_validate  # noqa: E402

pkg.add_command(pkg_init, "init")
pkg.add_command(pkg_create, "create")
pkg.add_command(pkg_validate, "validate")
pkg.add_command(pkg_pack, "pack")
pkg.add_command(pkg_publish, "publish")
pkg.add_command(pkg_build, "build")
