"""Shared naming utilities for package name validation and parsing.

Centralises all regex patterns and helpers for scoped package names
(``@scope/name``) and unscoped package names (``name``).

This module mirrors ``aam_backend.core.naming`` to keep CLI and backend
naming rules consistent.

Scope format: ``@scope/name`` where
  - Scope: ``^[a-z0-9][a-z0-9_-]{0,63}$`` (underscores allowed for org names)
  - Name:  ``^[a-z0-9][a-z0-9-]{0,63}$``  (no underscores, stricter)
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import re

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

# -----
# Regex patterns for validating package names
# -----
# Scope part: lowercase alphanumeric, hyphens, and underscores (npm convention)
SCOPE_REGEX: str = r"^[a-z0-9][a-z0-9_-]{0,63}$"

# Name part: lowercase alphanumeric and hyphens only (stricter than scope)
NAME_REGEX: str = r"^[a-z0-9][a-z0-9-]{0,63}$"

# Full name: optional @scope/ prefix followed by the name
FULL_NAME_REGEX: str = r"^(@[a-z0-9][a-z0-9_-]{0,63}/)?[a-z0-9][a-z0-9-]{0,63}$"

# Pre-compiled patterns for performance
_SCOPE_PATTERN: re.Pattern[str] = re.compile(SCOPE_REGEX)
_NAME_PATTERN: re.Pattern[str] = re.compile(NAME_REGEX)
_FULL_NAME_PATTERN: re.Pattern[str] = re.compile(FULL_NAME_REGEX)

# -----
# Filesystem mapping separator
# -----
# Scoped packages use double-hyphen to create filesystem-safe names.
# Example: @author/asvc-report -> author--asvc-report
FS_SEPARATOR: str = "--"

################################################################################
#                                                                              #
# FUNCTIONS                                                                    #
#                                                                              #
################################################################################


def parse_package_name(full_name: str) -> tuple[str, str]:
    """Parse a full package name into ``(scope, name)`` components.

    Args:
        full_name: The full package name, e.g. ``"@author/my-pkg"`` or
            ``"my-pkg"``.

    Returns:
        A tuple of ``(scope, name)`` where ``scope`` is an empty string
        for unscoped packages.

    Raises:
        ValueError: If the full name does not match the expected format.
    """
    logger.debug(f"Parsing package name: full_name='{full_name}'")

    if not full_name:
        raise ValueError("Package name must not be empty")

    # -----
    # Step 1: Check if this is a scoped name
    # -----
    if full_name.startswith("@"):
        # Must contain exactly one '/' separating scope from name
        slash_idx = full_name.find("/")
        if slash_idx == -1:
            raise ValueError(f"Scoped package name '{full_name}' missing '/' separator")

        scope = full_name[1:slash_idx]
        name = full_name[slash_idx + 1 :]

        # Validate scope
        if not scope:
            raise ValueError("Scope must not be empty in scoped package name")
        if not _SCOPE_PATTERN.match(scope):
            raise ValueError(f"Invalid scope '{scope}': must match {SCOPE_REGEX}")

        # Validate name
        if not name:
            raise ValueError("Name must not be empty in scoped package name")
        if not _NAME_PATTERN.match(name):
            raise ValueError(f"Invalid name '{name}': must match {NAME_REGEX}")

        logger.debug(f"Parsed scoped package: scope='{scope}', name='{name}'")
        return scope, name

    # -----
    # Step 2: Unscoped name — validate directly
    # -----
    if not _NAME_PATTERN.match(full_name):
        raise ValueError(f"Invalid package name '{full_name}': must match {NAME_REGEX}")

    logger.debug(f"Parsed unscoped package: name='{full_name}'")
    return "", full_name


def validate_package_name(full_name: str) -> bool:
    """Validate whether a full package name is syntactically correct.

    Args:
        full_name: The full package name to validate.

    Returns:
        ``True`` if the name is valid, ``False`` otherwise.
    """
    return bool(_FULL_NAME_PATTERN.match(full_name))


def format_package_name(scope: str, name: str) -> str:
    """Format scope and name into a full package name string.

    Args:
        scope: The scope (without ``@``), or empty string for unscoped.
        name: The package name.

    Returns:
        The full package name, e.g. ``"@author/my-pkg"`` or ``"my-pkg"``.
    """
    if scope:
        return f"@{scope}/{name}"
    return name


def to_filesystem_name(scope: str, name: str) -> str:
    """Convert scope and name to a filesystem-safe directory/file name.

    Uses the double-hyphen convention: ``@author/asvc-report`` becomes
    ``author--asvc-report``.

    Args:
        scope: The scope (without ``@``), or empty string for unscoped.
        name: The package name.

    Returns:
        A filesystem-safe name string.
    """
    if scope:
        return f"{scope}{FS_SEPARATOR}{name}"
    return name


def parse_package_spec(spec: str) -> tuple[str, str | None]:
    """Parse a CLI package spec into ``(full_name, version)``.

    Handles the following formats:
      - ``my-pkg``               -> ``("my-pkg", None)``
      - ``my-pkg@1.0.0``        -> ``("my-pkg", "1.0.0")``
      - ``@author/my-pkg``      -> ``("@author/my-pkg", None)``
      - ``@author/my-pkg@1.0.0``-> ``("@author/my-pkg", "1.0.0")``

    Args:
        spec: The raw CLI argument (e.g. ``"@author/pkg@1.0.0"``).

    Returns:
        A tuple of ``(full_name, version)`` where version is ``None``
        when not specified.

    Raises:
        ValueError: If the spec is malformed (empty scope, empty version,
            invalid name, etc.).
    """
    logger.debug(f"Parsing package spec: spec='{spec}'")

    if not spec:
        raise ValueError("Package spec must not be empty")

    # -----
    # Step 1: No '@' at all — unscoped, no version
    # -----
    if "@" not in spec:
        # Validate the name
        parse_package_name(spec)
        return spec, None

    # -----
    # Step 2: Scoped package — starts with '@'
    # -----
    if spec.startswith("@"):
        # Find the '/' that separates scope from name
        slash_idx = spec.find("/")
        if slash_idx == -1:
            raise ValueError(f"Scoped package spec '{spec}' missing '/' separator")

        # Everything after the slash may contain a version after the last '@'
        remainder = spec[slash_idx + 1 :]

        # Check if there's a version after the name
        if "@" in remainder:
            # Split on the last '@' to separate name from version
            name_part, version = remainder.rsplit("@", 1)
            if not version:
                raise ValueError(f"Empty version in package spec '{spec}'")
            full_name = spec[: slash_idx + 1] + name_part
        else:
            full_name = spec
            version = None

        # Validate the full name
        parse_package_name(full_name)

        logger.debug(f"Parsed scoped spec: full_name='{full_name}', version='{version}'")
        return full_name, version

    # -----
    # Step 3: Unscoped with version — contains '@' but doesn't start with '@'
    # -----
    name_part, version = spec.rsplit("@", 1)
    if not version:
        raise ValueError(f"Empty version in package spec '{spec}'")

    # Validate the name
    parse_package_name(name_part)

    logger.debug(f"Parsed unscoped spec: full_name='{name_part}', version='{version}'")
    return name_part, version
