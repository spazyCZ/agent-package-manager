"""Upgrade command for AAM CLI.

Upgrades outdated source-installed packages to the latest version
from the source cache, with spec 003 modification warning flow.

Reference: spec 004 US5; contracts/cli-commands.md.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import click
from rich.console import Console

from aam_cli.commands.outdated import check_outdated
from aam_cli.core.config import load_config
from aam_cli.core.workspace import read_lock_file
from aam_cli.services.upgrade_service import UpgradeResult

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


@click.command()
@click.argument("package", required=False)
@click.option("--dry-run", is_flag=True, help="Preview without making changes")
@click.option("--force", "-f", is_flag=True, help="Skip modification warnings")
@click.pass_context
def upgrade(
    ctx: click.Context,
    package: str | None,
    dry_run: bool,
    force: bool,
) -> None:
    """Upgrade outdated source-installed packages.

    Without arguments, upgrades all outdated packages. Specify a
    PACKAGE name to upgrade a single package.

    Checks for local modifications before overwriting. Use ``--force``
    to skip modification warnings.

    Examples::

        aam upgrade
        aam upgrade code-review
        aam upgrade --dry-run
        aam upgrade --force
    """
    console: Console = ctx.obj["console"]
    project_dir = Path.cwd()

    logger.info(
        f"Upgrade invoked: package='{package}', dry_run={dry_run}, force={force}"
    )

    config = load_config(project_dir)
    lock = read_lock_file(project_dir)

    if not lock.packages:
        console.print("No packages installed.")
        return

    # -----
    # Step 1: Check what's outdated
    # -----
    outdated_result = check_outdated(lock, config)

    if not outdated_result.outdated:
        console.print("[green]✓[/green] All packages are up to date.")
        return

    # -----
    # Step 2: Filter to requested package if specified
    # -----
    targets = outdated_result.outdated
    if package:
        targets = [o for o in targets if o.name == package]
        if not targets:
            console.print(
                f"Package '{package}' is not outdated or not installed "
                f"from a source."
            )
            return

    # -----
    # Step 3: Execute upgrades
    # -----
    result = upgrade_packages(
        targets=targets,
        config=config,
        project_dir=project_dir,
        force=force,
        dry_run=dry_run,
        console=console,
    )

    # -----
    # Step 4: Summary
    # -----
    console.print()

    if dry_run:
        console.print("[yellow]DRY RUN[/yellow] — No changes applied")
        console.print()
        for u in result.upgraded:
            console.print(
                f"  Would upgrade [cyan]{u['name']}[/cyan] "
                f"({u['from_commit']} → {u['to_commit']})"
            )
        return

    if result.upgraded:
        for u in result.upgraded:
            console.print(
                f"  [green]✓[/green] Upgraded [cyan]{u['name']}[/cyan] "
                f"({u['from_commit']} → {u['to_commit']})"
            )

    if result.skipped:
        for s in result.skipped:
            console.print(
                f"  [yellow]⊘[/yellow] Skipped [cyan]{s['name']}[/cyan]: "
                f"{s['reason']}"
            )

    if result.failed:
        for f in result.failed:
            console.print(
                f"  [red]✗[/red] Failed [cyan]{f['name']}[/cyan]: "
                f"{f['error']}"
            )

    console.print()
    console.print(
        f"  {result.total_upgraded} upgraded, "
        f"{len(result.skipped)} skipped, "
        f"{len(result.failed)} failed"
    )


################################################################################
#                                                                              #
# UPGRADE LOGIC                                                                #
#                                                                              #
################################################################################


def upgrade_packages(
    targets: list,
    config: "AamConfig",  # noqa: F821
    project_dir: Path,
    force: bool,
    dry_run: bool,
    console: Console,
) -> UpgradeResult:
    """Upgrade a list of outdated packages from sources.

    For each target, reinstalls from the source cache using the
    existing install_from_source flow.

    Args:
        targets: List of OutdatedPackage instances to upgrade.
        config: AAM configuration.
        project_dir: Project root directory.
        force: Skip modification warnings.
        dry_run: Preview without making changes.
        console: Rich console for output.

    Returns:
        :class:`UpgradeResult` with outcomes.
    """
    from aam_cli.services.install_service import install_from_source
    from aam_cli.services.source_service import build_source_index, resolve_artifact

    logger.info(f"Upgrading {len(targets)} package(s)")

    result = UpgradeResult()

    if dry_run:
        # -----
        # Dry run: just report what would be upgraded
        # -----
        for target in targets:
            result.upgraded.append({
                "name": target.name,
                "from_commit": target.current_commit,
                "to_commit": target.latest_commit,
            })
        result.total_upgraded = len(result.upgraded)
        return result

    # -----
    # Build source index for resolution
    # -----
    index = build_source_index(config)

    for target in targets:
        try:
            # -----
            # Check for local modifications
            # -----
            if target.has_local_modifications and not force:
                result.skipped.append({
                    "name": target.name,
                    "reason": "Local modifications detected. Use --force to overwrite.",
                })
                continue

            # -----
            # Resolve the artifact from source index
            # -----
            virtual_package = resolve_artifact(target.name, index)

            # -----
            # Reinstall from source with force=True (overwrite existing)
            # -----
            install_from_source(
                virtual_package=virtual_package,
                project_dir=project_dir,
                platform_name=config.default_platform,
                config=config,
                force=True,
                no_deploy=False,
            )

            result.upgraded.append({
                "name": target.name,
                "from_commit": target.current_commit,
                "to_commit": target.latest_commit,
            })

        except Exception as e:
            logger.error(
                f"Failed to upgrade '{target.name}': {e}", exc_info=True
            )
            result.failed.append({
                "name": target.name,
                "error": str(e),
            })

    result.total_upgraded = len(result.upgraded)

    logger.info(
        f"Upgrade complete: upgraded={result.total_upgraded}, "
        f"skipped={len(result.skipped)}, failed={len(result.failed)}"
    )

    return result
