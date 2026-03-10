"""Upgrade service for outdated detection and package upgrades.

Provides business logic for comparing installed packages against
source HEAD commits, detecting outdated packages, and upgrading
them with the spec 003 modification warning flow.

Reference: spec 004 User Stories 4–5; data-model.md entities 4–6.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aam_cli.core.config import AamConfig
from aam_cli.core.workspace import LockFile
from aam_cli.services.checksum_service import check_modifications
from aam_cli.services.git_service import get_cache_dir, get_head_sha, validate_cache
from aam_cli.services.install_service import install_from_source
from aam_cli.services.source_service import build_source_index, resolve_artifact
from aam_cli.utils.git_url import parse as parse_git_url

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# DATA MODELS                                                                  #
#                                                                              #
################################################################################


@dataclass
class OutdatedPackage:
    """A package that has updates available from its source.

    Attributes:
        name: Package name.
        current_commit: Short SHA (7 chars) of the installed version.
        latest_commit: Short SHA (7 chars) of the source HEAD.
        source_name: Source display name.
        has_local_modifications: True if files differ from checksums.
        last_source_update: ISO 8601 of last source fetch, if available.
    """

    name: str
    current_commit: str
    latest_commit: str
    source_name: str
    has_local_modifications: bool
    last_source_update: str | None = None


@dataclass
class OutdatedResult:
    """Complete result of an outdated detection scan.

    Attributes:
        outdated: Packages with updates available.
        up_to_date: Package names that are current.
        no_source: Packages not installed from sources.
        total_outdated: Count of outdated packages.
        stale_sources: Sources not updated in 7+ days.
    """

    outdated: list[OutdatedPackage] = field(default_factory=list)
    up_to_date: list[str] = field(default_factory=list)
    no_source: list[str] = field(default_factory=list)
    total_outdated: int = 0
    stale_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to MCP-ready dict."""
        return {
            "outdated": [
                {
                    "name": o.name,
                    "current_commit": o.current_commit,
                    "latest_commit": o.latest_commit,
                    "source_name": o.source_name,
                    "has_local_modifications": o.has_local_modifications,
                }
                for o in self.outdated
            ],
            "up_to_date": self.up_to_date,
            "no_source": self.no_source,
            "stale_sources": self.stale_sources,
            "total_outdated": self.total_outdated,
        }


@dataclass
class UpgradeResult:
    """Result of upgrading packages from sources.

    Attributes:
        upgraded: List of dicts with ``name``, ``from_commit``,
            ``to_commit`` for each successfully upgraded package.
        skipped: List of dicts with ``name``, ``reason`` for
            packages that were skipped (e.g., local modifications).
        failed: List of dicts with ``name``, ``error`` for packages
            where the upgrade failed.
        total_upgraded: Count of successfully upgraded packages.
    """

    upgraded: list[dict[str, str]] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)
    failed: list[dict[str, str]] = field(default_factory=list)
    total_upgraded: int = 0


################################################################################
#                                                                              #
# OUTDATED CHECK LOGIC                                                         #
#                                                                              #
################################################################################


def check_outdated(
    lock: LockFile,
    config: AamConfig,
) -> OutdatedResult:
    """Compare installed source packages against source HEAD commits.

    Groups packages by source for efficient cache reads.

    Args:
        lock: Parsed lock file.
        config: AAM configuration.

    Returns:
        :class:`OutdatedResult` with categorized packages.
    """
    logger.info(f"Checking outdated: packages={len(lock.packages)}")

    result = OutdatedResult()

    # -----
    # Build source HEAD SHA cache (one read per source)
    # -----
    source_head_cache: dict[str, str] = {}
    stale_threshold_days = 7

    for source_entry in config.sources:
        try:
            parsed = parse_git_url(source_entry.url)
            cache_dir = get_cache_dir(parsed.host, parsed.owner, parsed.repo)

            if validate_cache(cache_dir):
                source_head_cache[source_entry.name] = get_head_sha(cache_dir)

            # -----
            # Check for stale sources
            # -----
            if source_entry.last_fetched:
                fetched_dt = datetime.fromisoformat(source_entry.last_fetched)
                now = datetime.now(UTC)
                if (now - fetched_dt).days > stale_threshold_days:
                    result.stale_sources.append(source_entry.name)

        except (ValueError, OSError) as e:
            logger.warning(
                f"Cannot read HEAD for source '{source_entry.name}': {e}"
            )

    # -----
    # Compare each installed package
    # -----
    for pkg_name, locked in lock.packages.items():
        if not locked.source_name or not locked.source_commit:
            result.no_source.append(pkg_name)
            continue

        head_sha = source_head_cache.get(locked.source_name)

        if not head_sha:
            result.no_source.append(pkg_name)
            continue

        if locked.source_commit == head_sha:
            result.up_to_date.append(pkg_name)
        else:
            # -----
            # Check for local modifications
            # -----
            has_mods = False
            try:
                mod_result = check_modifications(pkg_name)
                has_mods = mod_result.get("has_modifications", False)
            except Exception:
                pass

            result.outdated.append(
                OutdatedPackage(
                    name=pkg_name,
                    current_commit=locked.source_commit[:7],
                    latest_commit=head_sha[:7],
                    source_name=locked.source_name,
                    has_local_modifications=has_mods,
                )
            )

    result.total_outdated = len(result.outdated)

    logger.info(
        f"Outdated check complete: outdated={result.total_outdated}, "
        f"up_to_date={len(result.up_to_date)}, no_source={len(result.no_source)}"
    )

    return result


################################################################################
#                                                                              #
# UPGRADE LOGIC                                                                #
#                                                                              #
################################################################################


def upgrade_packages(
    targets: list[OutdatedPackage],
    config: AamConfig,
    project_dir: Path,
    force: bool,
    dry_run: bool,
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

    Returns:
        :class:`UpgradeResult` with outcomes.
    """
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


################################################################################
#                                                                              #
# RUN UPGRADE (FULL WORKFLOW)                                                  #
#                                                                              #
################################################################################


def run_upgrade(
    package_name: str | None = None,
    dry_run: bool = False,
    force: bool = False,
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the full upgrade workflow for outdated source packages.

    Loads config, reads lock file, checks for outdated packages,
    optionally filters to a specific package, and executes upgrades.

    Args:
        package_name: Specific package to upgrade. If None, upgrades all.
        dry_run: Preview changes without applying.
        force: Skip modification warnings and overwrite.
        project_dir: Project root directory. Defaults to cwd.

    Returns:
        Dict with upgraded, skipped, failed lists, total_upgraded,
        and an optional message.
    """
    from aam_cli.core.config import load_config
    from aam_cli.core.workspace import read_lock_file

    effective_dir = project_dir or Path.cwd()
    config = load_config(effective_dir)
    lock = read_lock_file(effective_dir)

    outdated_result = check_outdated(lock, config)

    if not outdated_result.outdated:
        return {
            "upgraded": [],
            "skipped": [],
            "failed": [],
            "total_upgraded": 0,
            "message": "All packages are up to date.",
        }

    targets = outdated_result.outdated
    if package_name:
        targets = [o for o in targets if o.name == package_name]
        if not targets:
            return {
                "upgraded": [],
                "skipped": [],
                "failed": [],
                "total_upgraded": 0,
                "message": (
                    f"Package '{package_name}' is not outdated "
                    f"or not installed from a source."
                ),
            }

    result = upgrade_packages(
        targets=targets,
        config=config,
        project_dir=effective_dir,
        force=force,
        dry_run=dry_run,
    )

    return {
        "upgraded": result.upgraded,
        "skipped": result.skipped,
        "failed": result.failed,
        "total_upgraded": result.total_upgraded,
    }
