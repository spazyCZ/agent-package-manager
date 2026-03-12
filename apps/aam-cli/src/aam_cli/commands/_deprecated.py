"""Deprecated CLI aliases for legacy top-level commands."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click

from aam_cli.utils.deprecation import print_deprecation_warning

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# REGISTRATION                                                                 #
#                                                                              #
################################################################################


def register_deprecated_aliases(cli: click.Group) -> None:
    """Register hidden deprecated aliases on the root CLI group."""

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
    @click.option(
        "--output-dir",
        type=click.Path(file_okay=False, resolve_path=True),
        default=None,
    )
    @click.option("-y", "--yes", is_flag=True)
    @click.option("--from-source", "from_source", default=None)
    @click.option("--artifacts", "artifact_names", multiple=True)
    @click.pass_context
    def deprecated_create_package(ctx: click.Context, /, **kwargs: object) -> None:
        """(Deprecated) Use 'aam pkg create' instead."""
        print_deprecation_warning("aam create-package", "aam pkg create")
        from aam_cli.commands.pkg.create import pkg_create

        ctx.invoke(pkg_create, **kwargs)

    @cli.command("validate", hidden=True)
    @click.argument("path", default=".", type=click.Path(exists=True))
    @click.pass_context
    def deprecated_validate(ctx: click.Context, path: str) -> None:
        """(Deprecated) Use 'aam pkg validate' instead."""
        print_deprecation_warning("aam validate", "aam pkg validate")
        from aam_cli.commands.pkg.validate import pkg_validate

        ctx.invoke(pkg_validate, path=path, permissions=False)

    @cli.command("pack", hidden=True)
    @click.argument("path", default=".", type=click.Path(exists=True))
    @click.pass_context
    def deprecated_pack(ctx: click.Context, path: str) -> None:
        """(Deprecated) Use 'aam pkg pack' instead."""
        print_deprecation_warning("aam pack", "aam pkg pack")
        from aam_cli.commands.pkg.pack import pkg_pack

        ctx.invoke(pkg_pack, path=path)

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
        from aam_cli.commands.pkg.publish import pkg_publish

        ctx.invoke(
            pkg_publish,
            registry_name=registry_name,
            tag=tag,
            dry_run=dry_run,
        )

    @cli.command("build", hidden=True)
    @click.option("--target", "-t", required=True)
    @click.option("--output", "-o", default="dist", type=click.Path())
    @click.pass_context
    def deprecated_build(ctx: click.Context, target: str, output: str) -> None:
        """(Deprecated) Use 'aam pkg build' instead."""
        print_deprecation_warning("aam build", "aam pkg build")
        from aam_cli.commands.pkg.build import pkg_build

        ctx.invoke(pkg_build, target=target, output=output)

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
        from aam_cli.commands.upgrade import upgrade

        ctx.invoke(upgrade, package=package, dry_run=dry_run, force=force)

