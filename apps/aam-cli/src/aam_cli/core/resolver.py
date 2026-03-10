"""Dependency resolution using greedy BFS.

Resolves package dependencies by iterating a BFS queue, looking up the
best matching version for each dependency, and detecting conflicts.
No backtracking (v1 simplification — agent packages have shallow graphs).

Includes v2 resolver with support for optional/peer dependencies, cycle
detection, resolution strategies, and resolutions enforcement (FR-012).

Decision reference: plan.md Key Decision 4.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from collections import deque
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from aam_cli.core.manifest import PackageManifest
from aam_cli.core.version import find_best_match, find_lowest_match, parse_version
from aam_cli.core.workspace import UniversalLockFile
from aam_cli.registry.base import Registry
from aam_cli.services.system_deps_service import SystemCheckResults

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# ENUMS                                                                        #
#                                                                              #
################################################################################


class DependencyType(StrEnum):
    """Type of dependency relationship."""

    DIRECT = "direct"
    OPTIONAL = "optional"
    PEER = "peer"
    SYSTEM = "system"


class ResolutionStrategy(StrEnum):
    """Strategy for dependency version resolution."""

    DEFAULT = "default"
    FROZEN = "frozen"
    MINIMAL = "minimal"
    LATEST = "latest"
    DRY_RUN = "dry_run"


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

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ResolvedGraph(BaseModel):
    """Complete dependency resolution result."""

    direct: list[ResolvedPackage] = Field(default_factory=list)
    optional_resolved: list[ResolvedPackage] = Field(default_factory=list)
    optional_failed: list[str] = Field(default_factory=list)
    peer_satisfied: list[str] = Field(default_factory=list)
    peer_unsatisfied: list[str] = Field(default_factory=list)
    all_packages: list[ResolvedPackage] = Field(
        default_factory=list
    )  # hoisted, deduped, install order
    system_check_results: SystemCheckResults | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


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


def detect_cycles(
    root_specs: list[tuple[str, str]],
    registries: list[Registry],
) -> list[str] | None:
    """Detect circular dependencies using DFS.

    Traverses the dependency graph starting from each root spec and looks
    for back-edges that indicate a cycle.

    Args:
        root_specs: List of (name, constraint) tuples.
        registries: Available registries.

    Returns:
        List of package names forming a cycle, or None if acyclic.
    """
    logger.info(f"Checking for cycles in {len(root_specs)} root packages")

    # -----
    # Track DFS state across all root specs
    # -----
    visited: set[str] = set()
    visiting: set[str] = set()

    def _dfs(name: str, constraint: str, path: list[str]) -> list[str] | None:
        """Recursive DFS traversal for cycle detection.

        Args:
            name: Current package name.
            constraint: Version constraint string.
            path: Current DFS path (ancestor stack).

        Returns:
            Cycle path if found, None otherwise.
        """
        # -----
        # Cycle detected: package is already being visited in this path
        # -----
        if name in visiting:
            cycle_start = path.index(name)
            cycle = path[cycle_start:] + [name]
            logger.warning(f"Cycle detected: {' -> '.join(cycle)}")
            return cycle

        # -----
        # Already fully explored — no cycle through this node
        # -----
        if name in visited:
            return None

        # -----
        # Mark as currently visiting and add to path
        # -----
        visiting.add(name)
        path.append(name)

        # -----
        # Look up the package to get its dependencies
        # -----
        try:
            resolved = _resolve_from_registries(name, constraint, registries)
        except ValueError:
            # Package not found — cannot have downstream cycles
            visiting.discard(name)
            path.pop()
            visited.add(name)
            return None

        # -----
        # Recurse into dependencies
        # -----
        if resolved.manifest:
            for dep_name, dep_constraint in resolved.manifest.dependencies.items():
                dep_cycle = _dfs(dep_name, dep_constraint, path)
                if dep_cycle is not None:
                    return dep_cycle

        # -----
        # Done visiting — move to fully visited
        # -----
        visiting.discard(name)
        path.pop()
        visited.add(name)
        return None

    # -----
    # Run DFS from each root spec
    # -----
    for name, constraint in root_specs:
        cycle = _dfs(name, constraint, [])
        if cycle is not None:
            return cycle

    logger.info("No cycles detected")
    return None


def resolve_dependencies_v2(
    root_manifest: PackageManifest,
    registries: list[Registry],
    strategy: ResolutionStrategy,
    lock_file: UniversalLockFile | None = None,
) -> ResolvedGraph:
    """Resolve dependencies using the v2 resolver with full dep-type support.

    Handles direct, optional, and peer dependencies with configurable
    resolution strategies.

    Implementation:
      1. BFS for ``root_manifest.dependencies`` — fail on conflict
      2. BFS for ``root_manifest.optional_dependencies`` — swallow
         ``ValueError`` (PackageNotFound) per package
      3. Verify ``root_manifest.peer_dependencies`` — check if already
         resolved in graph or lock file
      4. Apply resolution strategy (frozen, minimal, latest, default)
      5. Enforce ``root_manifest.resolutions`` overrides (FR-012)
      6. Combine all resolved packages into ``all_packages``

    Args:
        root_manifest: The root package's manifest.
        registries: Available registries to look up packages in.
        strategy: Resolution strategy to use.
        lock_file: Existing lock file for frozen strategy.

    Returns:
        A :class:`ResolvedGraph` with all resolution results.

    Raises:
        ValueError: If a package cannot be found (non-optional), a version
            conflict occurs, or frozen strategy encounters an unlocked package.
    """
    from aam_cli.core.version import parse_constraint, version_matches

    logger.info(
        f"Resolving dependencies v2: strategy='{strategy}', "
        f"direct={len(root_manifest.dependencies)}, "
        f"optional={len(root_manifest.optional_dependencies)}, "
        f"peer={len(root_manifest.peer_dependencies)}"
    )

    graph = ResolvedGraph()

    # -----
    # Shared resolved map across all dependency types (hoisted/flat)
    # -----
    resolved_map: dict[str, ResolvedPackage] = {}

    # =====================================================================
    # Step 1: BFS for direct dependencies
    # =====================================================================

    direct_specs = list(root_manifest.dependencies.items())
    _bfs_resolve(
        specs=direct_specs,
        registries=registries,
        resolved_map=resolved_map,
        strategy=strategy,
        lock_file=lock_file,
        requested_by="root",
    )

    # -----
    # Collect direct resolved packages
    # -----
    for name, _constraint in direct_specs:
        if name in resolved_map:
            graph.direct.append(resolved_map[name])

    # =====================================================================
    # Step 2: BFS for optional dependencies (swallow PackageNotFound)
    # =====================================================================

    for opt_name, opt_constraint in root_manifest.optional_dependencies.items():
        try:
            _bfs_resolve(
                specs=[(opt_name, opt_constraint)],
                registries=registries,
                resolved_map=resolved_map,
                strategy=strategy,
                lock_file=lock_file,
                requested_by="root (optional)",
            )
            if opt_name in resolved_map:
                graph.optional_resolved.append(resolved_map[opt_name])
        except ValueError as exc:
            logger.info(
                f"Optional dependency '{opt_name}' not resolved: {exc}"
            )
            graph.optional_failed.append(opt_name)

    # =====================================================================
    # Step 3: Verify peer dependencies (verify-only, do not install)
    # =====================================================================

    for peer_name, peer_constraint in root_manifest.peer_dependencies.items():
        # -----
        # Check if peer is already in the resolved graph
        # -----
        if peer_name in resolved_map:
            existing = resolved_map[peer_name]
            constraints = parse_constraint(peer_constraint)
            existing_ver = parse_version(existing.version)
            if version_matches(existing_ver, constraints):
                graph.peer_satisfied.append(peer_name)
                logger.debug(
                    f"Peer dependency '{peer_name}' satisfied by "
                    f"resolved version {existing.version}"
                )
            else:
                graph.peer_unsatisfied.append(peer_name)
                logger.warning(
                    f"Peer dependency '{peer_name}' version "
                    f"{existing.version} does not satisfy "
                    f"constraint '{peer_constraint}'"
                )
            continue

        # -----
        # Check if peer is in the existing lock file
        # -----
        if lock_file and peer_name in lock_file.packages:
            locked = lock_file.packages[peer_name]
            constraints = parse_constraint(peer_constraint)
            locked_ver = parse_version(locked.version)
            if version_matches(locked_ver, constraints):
                graph.peer_satisfied.append(peer_name)
                logger.debug(
                    f"Peer dependency '{peer_name}' satisfied by "
                    f"locked version {locked.version}"
                )
            else:
                graph.peer_unsatisfied.append(peer_name)
                logger.warning(
                    f"Peer dependency '{peer_name}' locked version "
                    f"{locked.version} does not satisfy "
                    f"constraint '{peer_constraint}'"
                )
            continue

        # -----
        # Peer not found anywhere
        # -----
        graph.peer_unsatisfied.append(peer_name)
        logger.warning(
            f"Peer dependency '{peer_name}' ({peer_constraint}) "
            f"is not installed or resolved"
        )

    # =====================================================================
    # Step 4: Resolutions enforcement (FR-012)
    # =====================================================================

    if root_manifest.resolutions:
        logger.info(
            f"Applying {len(root_manifest.resolutions)} resolution overrides"
        )

        for res_name, forced_version in root_manifest.resolutions.items():
            # -----
            # Validate tree membership
            # -----
            if res_name not in resolved_map:
                raise ValueError(
                    f"resolutions entry '{res_name}' does not reference "
                    f"any package in the dependency tree"
                )

            # -----
            # Apply override — replace version regardless of constraints
            # -----
            existing = resolved_map[res_name]
            old_version = existing.version

            if old_version != forced_version:
                logger.warning(
                    f"Resolution override: '{res_name}' "
                    f"{old_version} -> {forced_version}"
                )

                # -----
                # Check if forced version violates any constraint
                # (log warning, never silently drop)
                # -----
                _warn_if_violates_constraints(
                    res_name, forced_version, root_manifest
                )

                # -----
                # Create updated resolved package with forced version
                # -----
                resolved_map[res_name] = ResolvedPackage(
                    name=existing.name,
                    version=forced_version,
                    source=existing.source,
                    checksum=existing.checksum,
                    archive_path=existing.archive_path,
                    manifest=existing.manifest,
                )

    # =====================================================================
    # Step 5: Combine all packages into all_packages (install order)
    # =====================================================================

    graph.all_packages = list(resolved_map.values())

    logger.info(
        f"Resolution v2 complete: "
        f"direct={len(graph.direct)}, "
        f"optional_resolved={len(graph.optional_resolved)}, "
        f"optional_failed={len(graph.optional_failed)}, "
        f"peer_satisfied={len(graph.peer_satisfied)}, "
        f"peer_unsatisfied={len(graph.peer_unsatisfied)}, "
        f"all_packages={len(graph.all_packages)}"
    )

    return graph


def _bfs_resolve(
    specs: list[tuple[str, str]],
    registries: list[Registry],
    resolved_map: dict[str, ResolvedPackage],
    strategy: ResolutionStrategy,
    lock_file: UniversalLockFile | None,
    requested_by: str,
) -> None:
    """BFS resolution loop shared by direct and optional dependency passes.

    Resolves packages into ``resolved_map`` in-place, following the given
    resolution strategy.

    Args:
        specs: List of (name, constraint) tuples to resolve.
        registries: Available registries.
        resolved_map: Shared resolved map (mutated in-place).
        strategy: Resolution strategy.
        lock_file: Existing lock file (for frozen strategy).
        requested_by: Label for the requester (for error messages).

    Raises:
        ValueError: If a package cannot be found or version conflict occurs.
    """
    from aam_cli.core.version import parse_constraint, version_matches

    queue: deque[tuple[str, str, str]] = deque()

    for name, constraint in specs:
        queue.append((name, constraint, requested_by))

    while queue:
        pkg_name, constraint, req_by = queue.popleft()

        logger.debug(
            f"BFS resolving: name='{pkg_name}', constraint='{constraint}', "
            f"requested_by='{req_by}', strategy='{strategy}'"
        )

        # -----
        # Check if already resolved
        # -----
        if pkg_name in resolved_map:
            existing = resolved_map[pkg_name]
            constraints = parse_constraint(constraint)
            existing_ver = parse_version(existing.version)
            if version_matches(existing_ver, constraints):
                logger.debug(
                    f"Already resolved {pkg_name}@{existing.version}, "
                    "compatible with new constraint"
                )
                continue

            raise ValueError(
                f"Dependency conflict for '{pkg_name}': "
                f"version {existing.version} (required by {req_by}) "
                f"is incompatible with constraint '{constraint}'. "
                f"Cannot resolve without backtracking."
            )

        # -----
        # Strategy: frozen — use exact version from lock file
        # -----
        if strategy == ResolutionStrategy.FROZEN:
            if lock_file is None or pkg_name not in lock_file.packages:
                raise ValueError(
                    f"Frozen strategy: package '{pkg_name}' not found in "
                    f"lock file. Run a full resolve first."
                )
            locked = lock_file.packages[pkg_name]
            resolved_map[pkg_name] = ResolvedPackage(
                name=pkg_name,
                version=locked.version,
                source=locked.source,
                checksum=locked.integrity,
            )
            # -----
            # Enqueue locked dependencies
            # -----
            for dep_name, dep_version in locked.dependencies.items():
                queue.append((dep_name, dep_version, pkg_name))
            continue

        # -----
        # Strategy: latest — ignore constraints, use latest version
        # -----
        if strategy == ResolutionStrategy.LATEST:
            resolved = _resolve_from_registries(pkg_name, "*", registries)
            resolved_map[pkg_name] = resolved
            if resolved.manifest:
                for dep_name, dep_constraint in resolved.manifest.dependencies.items():
                    queue.append((dep_name, dep_constraint, pkg_name))
            continue

        # -----
        # Strategy: minimal — use lowest satisfying version
        # -----
        if strategy == ResolutionStrategy.MINIMAL:
            resolved = _resolve_minimal_from_registries(
                pkg_name, constraint, registries
            )
            resolved_map[pkg_name] = resolved
            if resolved.manifest:
                for dep_name, dep_constraint in resolved.manifest.dependencies.items():
                    queue.append((dep_name, dep_constraint, pkg_name))
            continue

        # -----
        # Strategy: default — use best match (highest satisfying version)
        # -----
        resolved = _resolve_from_registries(pkg_name, constraint, registries)
        resolved_map[pkg_name] = resolved

        if resolved.manifest:
            for dep_name, dep_constraint in resolved.manifest.dependencies.items():
                queue.append((dep_name, dep_constraint, pkg_name))


def _warn_if_violates_constraints(
    name: str,
    forced_version: str,
    root_manifest: PackageManifest,
) -> None:
    """Log a warning if a forced resolution version violates constraints.

    Checks if the forced version violates the constraint declared in the
    root manifest's dependencies, optional dependencies, or peer dependencies.

    Args:
        name: Package name.
        forced_version: The version being forced via resolutions.
        root_manifest: The root manifest to check constraints against.
    """
    from aam_cli.core.version import parse_constraint, version_matches

    # -----
    # Collect all constraints for this package from the root manifest
    # -----
    constraint_sources: dict[str, str] = {}
    if name in root_manifest.dependencies:
        constraint_sources["dependencies"] = root_manifest.dependencies[name]
    if name in root_manifest.optional_dependencies:
        constraint_sources["optionalDependencies"] = (
            root_manifest.optional_dependencies[name]
        )
    if name in root_manifest.peer_dependencies:
        constraint_sources["peerDependencies"] = (
            root_manifest.peer_dependencies[name]
        )

    forced_ver = parse_version(forced_version)
    for source_label, constraint_str in constraint_sources.items():
        constraints = parse_constraint(constraint_str)
        if not version_matches(forced_ver, constraints):
            logger.warning(
                f"Resolution override for '{name}': forced version "
                f"'{forced_version}' violates constraint "
                f"'{constraint_str}' from {source_label}"
            )


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


def _resolve_minimal_from_registries(
    name: str,
    constraint: str,
    registries: list[Registry],
) -> ResolvedPackage:
    """Find and resolve the lowest satisfying version from registries.

    Identical to :func:`_resolve_from_registries` except it picks the
    lowest matching version instead of the highest. Used by the
    ``MINIMAL`` resolution strategy for conservative dependency
    resolution.

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

        lowest = find_lowest_match(constraint, versions)
        if lowest is None:
            continue

        # -----
        # Get metadata for the resolved version
        # -----
        metadata = registry.get_metadata(name)
        version_info = None
        for vi in metadata.versions:
            if vi.version == lowest:
                version_info = vi
                break

        checksum = version_info.checksum if version_info else ""

        return ResolvedPackage(
            name=name,
            version=lowest,
            source=registry.name,
            checksum=checksum,
        )

    raise ValueError(
        f"Package '{name}' not found in any configured registry. "
        f"Run 'aam registry list' to check your registries."
    )
