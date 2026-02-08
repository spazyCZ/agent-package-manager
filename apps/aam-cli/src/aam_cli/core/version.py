"""Semantic version constraint parsing and matching.

Wraps the ``packaging`` library's ``Version`` class and adds custom support
for caret (``^``) and tilde (``~``) operators that are not native to PEP 440.

Supported constraint formats:
  - ``1.0.0``            → exact match
  - ``>=1.0.0``          → minimum version
  - ``^1.0.0``           → compatible (>=1.0.0, <2.0.0)
  - ``~1.0.0``           → approximate (>=1.0.0, <1.1.0)
  - ``*``                → any version
  - ``>=1.0.0,<2.0.0``   → range (comma-separated)

Decision reference: R-003 in research.md.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import re
from typing import NamedTuple

from packaging.version import InvalidVersion, Version

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

# Pattern for matching version strings (MAJOR.MINOR.PATCH with optional pre-release)
_SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)")

################################################################################
#                                                                              #
# DATA MODELS                                                                  #
#                                                                              #
################################################################################


class VersionConstraint(NamedTuple):
    """A parsed version constraint with a lower and optional upper bound."""

    lower: Version | None
    lower_inclusive: bool
    upper: Version | None
    upper_inclusive: bool


################################################################################
#                                                                              #
# FUNCTIONS                                                                    #
#                                                                              #
################################################################################


def parse_version(version_str: str) -> Version:
    """Parse a version string into a ``packaging.version.Version``.

    Args:
        version_str: A semver-compatible version string (e.g. ``"1.2.3"``).

    Returns:
        Parsed ``Version`` object.

    Raises:
        ValueError: If the string is not a valid version.
    """
    try:
        return Version(version_str)
    except InvalidVersion as exc:
        raise ValueError(
            f"'{version_str}' is not valid semver (expected MAJOR.MINOR.PATCH): {exc}"
        ) from exc


def _expand_caret(version_str: str) -> tuple[str, str]:
    """Expand a caret constraint into a range.

    ``^1.2.3`` → ``>=1.2.3, <2.0.0``
    ``^0.2.3`` → ``>=0.2.3, <0.3.0``  (bump minor when major is 0)
    ``^0.0.3`` → ``>=0.0.3, <0.0.4``  (bump patch when major+minor are 0)

    Args:
        version_str: The version portion after the ``^`` prefix.

    Returns:
        Tuple of (lower_bound, upper_bound) as version strings.
    """
    match = _SEMVER_PATTERN.match(version_str)
    if not match:
        raise ValueError(
            f"Cannot parse caret constraint '^{version_str}': expected MAJOR.MINOR.PATCH"
        )

    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))

    if major != 0:
        upper = f"{major + 1}.0.0"
    elif minor != 0:
        upper = f"0.{minor + 1}.0"
    else:
        upper = f"0.0.{patch + 1}"

    return version_str, upper


def _expand_tilde(version_str: str) -> tuple[str, str]:
    """Expand a tilde constraint into a range.

    ``~1.2.3`` → ``>=1.2.3, <1.3.0``

    Args:
        version_str: The version portion after the ``~`` prefix.

    Returns:
        Tuple of (lower_bound, upper_bound) as version strings.
    """
    match = _SEMVER_PATTERN.match(version_str)
    if not match:
        raise ValueError(
            f"Cannot parse tilde constraint '~{version_str}': expected MAJOR.MINOR.PATCH"
        )

    major, minor, _patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    upper = f"{major}.{minor + 1}.0"

    return version_str, upper


def parse_constraint(constraint_str: str) -> list[VersionConstraint]:
    """Parse a version constraint string into a list of constraints.

    All sub-constraints (comma-separated) must be satisfied simultaneously.

    Args:
        constraint_str: Version constraint string (e.g. ``"^1.0.0"``,
            ``">=1.0.0,<2.0.0"``, ``"*"``).

    Returns:
        List of :class:`VersionConstraint` objects.

    Raises:
        ValueError: If the constraint string is malformed.
    """
    logger.debug(f"Parsing version constraint: '{constraint_str}'")

    stripped = constraint_str.strip()

    # -----
    # Wildcard: matches any version
    # -----
    if stripped == "*":
        return [
            VersionConstraint(lower=None, lower_inclusive=True, upper=None, upper_inclusive=True)
        ]

    # -----
    # Caret operator: ^X.Y.Z
    # -----
    if stripped.startswith("^"):
        lower_str, upper_str = _expand_caret(stripped[1:])
        return [
            VersionConstraint(
                lower=parse_version(lower_str),
                lower_inclusive=True,
                upper=parse_version(upper_str),
                upper_inclusive=False,
            )
        ]

    # -----
    # Tilde operator: ~X.Y.Z
    # -----
    if stripped.startswith("~"):
        lower_str, upper_str = _expand_tilde(stripped[1:])
        return [
            VersionConstraint(
                lower=parse_version(lower_str),
                lower_inclusive=True,
                upper=parse_version(upper_str),
                upper_inclusive=False,
            )
        ]

    # -----
    # Comma-separated sub-constraints (e.g. ">=1.0.0,<2.0.0")
    # -----
    constraints: list[VersionConstraint] = []
    parts = [p.strip() for p in stripped.split(",") if p.strip()]

    for part in parts:
        constraints.append(_parse_single_constraint(part))

    if not constraints:
        raise ValueError(f"Empty version constraint: '{constraint_str}'")

    return constraints


def _parse_single_constraint(part: str) -> VersionConstraint:
    """Parse a single constraint expression (e.g. ``>=1.0.0``, ``1.0.0``).

    Args:
        part: Single constraint string.

    Returns:
        A :class:`VersionConstraint`.
    """
    # -----
    # Comparison operators
    # -----
    if part.startswith(">="):
        ver = parse_version(part[2:].strip())
        return VersionConstraint(lower=ver, lower_inclusive=True, upper=None, upper_inclusive=True)

    if part.startswith(">"):
        ver = parse_version(part[1:].strip())
        return VersionConstraint(lower=ver, lower_inclusive=False, upper=None, upper_inclusive=True)

    if part.startswith("<="):
        ver = parse_version(part[2:].strip())
        return VersionConstraint(lower=None, lower_inclusive=True, upper=ver, upper_inclusive=True)

    if part.startswith("<"):
        ver = parse_version(part[1:].strip())
        return VersionConstraint(lower=None, lower_inclusive=True, upper=ver, upper_inclusive=False)

    if part.startswith("==") or part.startswith("="):
        ver_str = part.lstrip("=").strip()
        ver = parse_version(ver_str)
        return VersionConstraint(lower=ver, lower_inclusive=True, upper=ver, upper_inclusive=True)

    # -----
    # No operator: exact match
    # -----
    ver = parse_version(part)
    return VersionConstraint(lower=ver, lower_inclusive=True, upper=ver, upper_inclusive=True)


def version_matches(version: Version, constraints: list[VersionConstraint]) -> bool:
    """Check whether a version satisfies all constraints.

    Args:
        version: The version to test.
        constraints: List of constraints that must all be satisfied.

    Returns:
        ``True`` if *version* satisfies every constraint in the list.
    """
    for c in constraints:
        # -----
        # Check lower bound
        # -----
        if c.lower is not None:
            if c.lower_inclusive and version < c.lower:
                return False
            if not c.lower_inclusive and version <= c.lower:
                return False

        # -----
        # Check upper bound
        # -----
        if c.upper is not None:
            if c.upper_inclusive and version > c.upper:
                return False
            if not c.upper_inclusive and version >= c.upper:
                return False

    return True


def find_best_match(
    constraint_str: str,
    available_versions: list[str],
) -> str | None:
    """Find the highest version that satisfies a constraint.

    Args:
        constraint_str: Version constraint string.
        available_versions: List of available version strings.

    Returns:
        The best matching version string, or ``None`` if no version matches.
    """
    logger.debug(
        f"Finding best match: constraint='{constraint_str}', available={available_versions}"
    )

    constraints = parse_constraint(constraint_str)

    # -----
    # Parse and filter matching versions, then sort descending
    # -----
    matching: list[Version] = []
    for ver_str in available_versions:
        try:
            ver = parse_version(ver_str)
        except ValueError:
            logger.warning(f"Skipping unparseable version: '{ver_str}'")
            continue

        if version_matches(ver, constraints):
            matching.append(ver)

    if not matching:
        logger.debug(f"No matching version found for constraint '{constraint_str}'")
        return None

    # -----
    # Return the highest matching version
    # -----
    best = max(matching)
    logger.debug(f"Best match: {best}")
    return str(best)
