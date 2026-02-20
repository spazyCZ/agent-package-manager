"""``aam pkg create`` — Create package from existing project or source.

Delegates to the existing create_package command logic.

Reference: spec 004 US7.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click

from aam_cli.commands.create_package import create_package
from aam_cli.detection.scanner import KNOWN_PLATFORMS

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


@click.command("create")
@click.argument(
    "path",
    default=".",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
)
@click.option("--all", "include_all", is_flag=True, help="Include all detected artifacts")
@click.option(
    "--type",
    "-t",
    "artifact_types",
    multiple=True,
    type=click.Choice(["skill", "agent", "prompt", "instruction"], case_sensitive=False),
    help="Filter detection to specific artifact types",
)
@click.option(
    "--platform",
    "-p",
    "platforms",
    multiple=True,
    type=click.Choice(sorted(KNOWN_PLATFORMS), case_sensitive=False),
    help="Filter to artifacts from a specific platform",
)
@click.option(
    "--organize",
    type=click.Choice(["copy", "reference", "move"], case_sensitive=False),
    default="copy",
    help="File organization mode",
)
@click.option(
    "--include", "includes", multiple=True, type=click.Path(), help="Manually include file/dir"
)
@click.option(
    "--include-as",
    type=click.Choice(["skill", "agent", "prompt", "instruction"], case_sensitive=False),
    default=None,
    help="Artifact type for --include",
)
@click.option("--name", "pkg_name", default=None, help="Package name (e.g. my-pkg, @scope/my-pkg)")
@click.option("--scope", "pkg_scope", default=None, help="Scope prefix")
@click.option("--version", "pkg_version", default=None, help="Package version")
@click.option("--description", "pkg_description", default=None, help="Package description")
@click.option("--author", "pkg_author", default=None, help="Package author")
@click.option("--dry-run", is_flag=True, help="Preview without writing")
@click.option("--output-dir", type=click.Path(file_okay=False, resolve_path=True), default=None)
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompts")
@click.option(
    "--from-source",
    "from_source",
    default=None,
    help="Create package from a registered remote source",
)
@click.option(
    "--artifacts",
    "artifact_names",
    multiple=True,
    help="Select specific artifacts by name when using --from-source",
)
@click.pass_context
def pkg_create(
    ctx: click.Context,
    path: str,
    include_all: bool,
    artifact_types: tuple[str, ...],
    platforms: tuple[str, ...],
    organize: str,
    includes: tuple[str, ...],
    include_as: str | None,
    pkg_name: str | None,
    pkg_scope: str | None,
    pkg_version: str | None,
    pkg_description: str | None,
    pkg_author: str | None,
    dry_run: bool,
    output_dir: str | None,
    yes: bool,
    from_source: str | None,
    artifact_names: tuple[str, ...],
) -> None:
    """Create an AAM package from an existing project or remote source.

    Scans the project for artifacts, lets you pick which to include,
    then generates ``aam.yaml`` and copies files into an AAM package.

    Examples::

        aam pkg create
        aam pkg create ./my-project/
        aam pkg create --from-source openai/skills --all
    """
    logger.info(f"pkg create invoked: path='{path}'")

    # -----
    # Delegate to the existing create_package command handler
    # -----
    ctx.invoke(
        create_package,
        path=path,
        include_all=include_all,
        artifact_types=artifact_types,
        platforms=platforms,
        organize=organize,
        includes=includes,
        include_as=include_as,
        pkg_name=pkg_name,
        pkg_scope=pkg_scope,
        pkg_version=pkg_version,
        pkg_description=pkg_description,
        pkg_author=pkg_author,
        dry_run=dry_run,
        output_dir=output_dir,
        yes=yes,
        from_source=from_source,
        artifact_names=artifact_names,
    )
