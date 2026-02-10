"""``aam pkg publish`` — Publish archive to a registry.

Delegates to the existing publish command logic.

Reference: spec 004 US7.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click

from aam_cli.commands.publish import publish

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


@click.command("publish")
@click.option(
    "--registry",
    "registry_name",
    default=None,
    help="Target registry name (default: default registry)",
)
@click.option("--tag", default="latest", help="Distribution tag")
@click.option("--dry-run", is_flag=True, help="Preview without publishing")
@click.pass_context
def pkg_publish(
    ctx: click.Context,
    registry_name: str | None,
    tag: str,
    dry_run: bool,
) -> None:
    """Publish a packed archive to a registry.

    Must be run from the package directory containing ``aam.yaml``.

    Examples::

        aam pkg publish
        aam pkg publish --registry local
        aam pkg publish --tag beta
    """
    logger.info(f"pkg publish invoked: registry='{registry_name}'")

    # -----
    # Delegate to the existing publish command handler
    # -----
    ctx.invoke(
        publish,
        registry_name=registry_name,
        tag=tag,
        dry_run=dry_run,
    )
