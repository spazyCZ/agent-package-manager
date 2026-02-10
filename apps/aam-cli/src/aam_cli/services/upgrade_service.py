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
