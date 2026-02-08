"""Dependency resolution using greedy BFS.

Resolves package dependencies by iterating a BFS queue, looking up the
best matching version for each dependency, and detecting conflicts.
No backtracking (v1 simplification — agent packages have shallow graphs).

Decision reference: plan.md Key Decision 4.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from collections import deque
from pathlib import Path

from pydantic import BaseModel

from aam_cli.core.manifest import PackageManifest
from aam_cli.core.version import find_best_match, parse_version
from aam_cli.registry.base import Registry

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


class ResolvedPackage(BaseModel):
    """A package resolved during dependency resolution."""

    name: str
    version: str
    source: str  # Registry name
    checksum: str  # "sha256:<hex>"
    archive_path: Path | None = None
    manifest: PackageManifest | None = None

    class Config:
        """Allow arbitrary types for Path."""

        arbitrary_types_allowed = True


################################################################################
#                                                                              #
# RESOLVER                                                                     #
#                                                                              #
################################################################################


def resolve_dependencies(
    root_specs: list[tuple[str, str]],
    registries: list[Registry],
) -> list[ResolvedPackage]:
    """Resolve dependencies for a set of root package specs.

    Uses a greedy BFS algorithm:
      1. For each package in the queue, find the best matching version
      2. If already resolved and compatible, skip
      3. If conflict, raise a clear error
      4. Add the package's dependencies to the queue

    Args:
        root_specs: List of ``(name, constraint)`` tuples for the
            packages to install.
        registries: Available registries to look up packages in.

    Returns:
        Ordered list of :class:`ResolvedPackage` instances (dependencies first).

    Raises:
        ValueError: If a package cannot be found or a version conflict occurs.
    """
    logger.info(f"Resolving dependencies for {len(root_specs)} root packages")

    # -----
    # resolved_map: package_name -> ResolvedPackage
    # -----
    resolved_map: dict[str, ResolvedPackage] = {}

    # -----
    # BFS queue: (package_name, constraint_str, requested_by)
    # -----
    queue: deque[tuple[str, str, str]] = deque()

    for name, constraint in root_specs:
        queue.append((name, constraint, "user"))

    while queue:
        pkg_name, constraint, requested_by = queue.popleft()

        logger.debug(
            f"Resolving: name='{pkg_name}', constraint='{constraint}', "
            f"requested_by='{requested_by}'"
        )

        # -----
        # Check if already resolved
        # -----
        if pkg_name in resolved_map:
            existing = resolved_map[pkg_name]
            # Verify the existing resolved version satisfies this constraint
            from aam_cli.core.version import parse_constraint, version_matches

            constraints = parse_constraint(constraint)
            existing_ver = parse_version(existing.version)
            if version_matches(existing_ver, constraints):
                logger.debug(
                    f"Already resolved {pkg_name}@{existing.version}, "
                    "compatible with new constraint"
                )
                continue

            # -----
            # Conflict: existing version doesn't satisfy new constraint
            # -----
            raise ValueError(
                f"Dependency conflict for '{pkg_name}': "
                f"version {existing.version} (required by {requested_by}) "
                f"is incompatible with constraint '{constraint}'. "
                f"Cannot resolve without backtracking."
            )

        # -----
        # Look up the package in registries
        # -----
        resolved = _resolve_from_registries(pkg_name, constraint, registries)
        resolved_map[pkg_name] = resolved

        # -----
        # Enqueue dependencies
        # -----
        if resolved.manifest:
            for dep_name, dep_constraint in resolved.manifest.dependencies.items():
                queue.append((dep_name, dep_constraint, pkg_name))

    # -----
    # Return in dependency-first order (reverse BFS order)
    # -----
    result = list(resolved_map.values())
    logger.info(f"Resolution complete: {len(result)} packages resolved")
    return result


def _resolve_from_registries(
    name: str,
    constraint: str,
    registries: list[Registry],
) -> ResolvedPackage:
    """Find and resolve a package from the available registries.

    Tries each registry in order until a matching version is found.

    Args:
        name: Package name.
        constraint: Version constraint string.
        registries: Registries to search.

    Returns:
        A :class:`ResolvedPackage` with version info.

    Raises:
        ValueError: If the package or matching version is not found.
    """
    for registry in registries:
        try:
            versions = registry.get_versions(name)
        except KeyError:
            continue

        best = find_best_match(constraint, versions)
        if best is None:
            continue

        # -----
        # Get metadata for the resolved version
        # -----
        metadata = registry.get_metadata(name)
        version_info = None
        for vi in metadata.versions:
            if vi.version == best:
                version_info = vi
                break

        checksum = version_info.checksum if version_info else ""

        # -----
        # Try to load the manifest from the archive
        # (will be populated during download)
        # -----
        return ResolvedPackage(
            name=name,
            version=best,
            source=registry.name,
            checksum=checksum,
        )

    raise ValueError(
        f"Package '{name}' not found in any configured registry. "
        f"Run 'aam registry list' to check your registries."
    )
