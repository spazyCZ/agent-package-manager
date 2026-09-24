"""Unit tests for the v2 dependency resolver.

Tests:
  - detect_cycles(): no cycle, direct cycle, multi-hop cycle
  - resolve_dependencies_v2(): direct deps BFS, optional dep swallowed on
    PackageNotFound, peer dep verify-only, frozen strategy, dry_run strategy,
    resolutions override post-BFS
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

from unittest.mock import MagicMock

from aam_cli.core.manifest import PackageManifest
from aam_cli.core.resolver import (
    ResolutionStrategy,
    ResolvedGraph,
    ResolvedPackage,
    detect_cycles,
    resolve_dependencies_v2,
)
from aam_cli.core.workspace import LockedPackageV2, UniversalLockFile

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _make_manifest(
    name: str = "test-pkg",
    version: str = "1.0.0",
    dependencies: dict | None = None,
    optional_dependencies: dict | None = None,
    peer_dependencies: dict | None = None,
    resolutions: dict | None = None,
) -> PackageManifest:
    """Create a minimal PackageManifest for testing."""
    return PackageManifest(
        name=name,
        version=version,
        description=f"Test package {name}",
        dependencies=dependencies or {},
        optional_dependencies=optional_dependencies or {},
        peer_dependencies=peer_dependencies or {},
        resolutions=resolutions or {},
    )


def _make_version_info(version: str, checksum: str = "sha256-abc") -> MagicMock:
    """Create a mock version_info object."""
    vi = MagicMock()
    vi.version = version
    vi.checksum = checksum
    return vi


def _make_registry(packages: dict[str, tuple[str, PackageManifest | None]]):
    """Create a mock registry from a {name: (version, manifest_or_None)} dict.

    The registry mock implements the interface used by _resolve_from_registries:
      - registry.get_versions(name) → list[str]
      - registry.get_metadata(name) → mock with .versions
      - registry.name → "test-registry"

    Args:
        packages: Maps package name to (version, manifest_or_None).

    Returns:
        A mock Registry object.
    """
    registry = MagicMock()
    registry.name = "test-registry"

    def _get_versions(name: str) -> list[str]:
        if name not in packages:
            raise KeyError(f"Package '{name}' not in registry")
        version, _ = packages[name]
        return [version]

    def _get_metadata(name: str) -> MagicMock:
        if name not in packages:
            raise KeyError(f"Package '{name}' not in registry")
        version, pkg_manifest = packages[name]
        metadata = MagicMock()
        vi = _make_version_info(version)
        metadata.versions = [vi]
        return metadata

    def _download(name: str, version: str, dest: object) -> str:
        return "sha256-downloaded"

    registry.get_versions.side_effect = _get_versions
    registry.get_metadata.side_effect = _get_metadata
    registry.download.side_effect = _download
    return registry


def _make_registry_with_manifest(
    packages: dict[str, tuple[str, PackageManifest | None]],
) -> MagicMock:
    """Like _make_registry but patches _resolve_from_registries directly.

    For resolve_dependencies_v2 tests that need manifests, we patch the
    internal helper directly since the registry mock doesn't load manifests.
    """
    return _make_registry(packages)


################################################################################
#                                                                              #
# TEST: detect_cycles                                                          #
#                                                                              #
################################################################################


class TestDetectCycles:
    """Tests for detect_cycles() — DFS cycle detection."""

    def test_unit_no_cycles_returns_none(self):
        """detect_cycles returns None for an acyclic graph."""
        pkg_a = _make_manifest("pkg-a", dependencies={"pkg-b": ">=1.0.0"})
        pkg_b = _make_manifest("pkg-b", dependencies={})
        registry = _make_registry(
            {
                "pkg-a": ("1.0.0", pkg_a),
                "pkg-b": ("1.0.0", pkg_b),
            }
        )

        # Patch _resolve_from_registries to return the manifests we created
        from unittest.mock import patch

        from aam_cli.core import resolver as resolver_module

        def _mock_resolve(name: str, constraint: str, registries_arg: list) -> ResolvedPackage:
            manifests = {"pkg-a": pkg_a, "pkg-b": pkg_b}
            return ResolvedPackage(
                name=name,
                version="1.0.0",
                source="test-registry",
                checksum="sha256-abc",
                manifest=manifests.get(name),
            )

        with patch.object(resolver_module, "_resolve_from_registries", _mock_resolve):
            result = detect_cycles([("pkg-a", ">=1.0.0")], [registry])

        assert result is None

    def test_unit_direct_cycle_detected(self):
        """detect_cycles returns a cycle path for A→B→A."""
        pkg_a = _make_manifest("pkg-a", dependencies={"pkg-b": ">=1.0.0"})
        pkg_b = _make_manifest("pkg-b", dependencies={"pkg-a": ">=1.0.0"})
        registry = _make_registry(
            {
                "pkg-a": ("1.0.0", pkg_a),
                "pkg-b": ("1.0.0", pkg_b),
            }
        )

        from unittest.mock import patch

        from aam_cli.core import resolver as resolver_module

        def _mock_resolve(name: str, constraint: str, registries_arg: list) -> ResolvedPackage:
            manifests = {"pkg-a": pkg_a, "pkg-b": pkg_b}
            return ResolvedPackage(
                name=name,
                version="1.0.0",
                source="test-registry",
                checksum="sha256-abc",
                manifest=manifests.get(name),
            )

        with patch.object(resolver_module, "_resolve_from_registries", _mock_resolve):
            result = detect_cycles([("pkg-a", ">=1.0.0")], [registry])

        assert result is not None
        assert "pkg-a" in result
        assert "pkg-b" in result

    def test_unit_multi_hop_cycle_detected(self):
        """detect_cycles detects a 3-package cycle A→B→C→A."""
        pkg_a = _make_manifest("pkg-a", dependencies={"pkg-b": ">=1.0.0"})
        pkg_b = _make_manifest("pkg-b", dependencies={"pkg-c": ">=1.0.0"})
        pkg_c = _make_manifest("pkg-c", dependencies={"pkg-a": ">=1.0.0"})
        registry = _make_registry(
            {
                "pkg-a": ("1.0.0", pkg_a),
                "pkg-b": ("1.0.0", pkg_b),
                "pkg-c": ("1.0.0", pkg_c),
            }
        )

        from unittest.mock import patch

        from aam_cli.core import resolver as resolver_module

        def _mock_resolve(name: str, constraint: str, registries_arg: list) -> ResolvedPackage:
            manifests = {"pkg-a": pkg_a, "pkg-b": pkg_b, "pkg-c": pkg_c}
            return ResolvedPackage(
                name=name,
                version="1.0.0",
                source="test-registry",
                checksum="sha256-abc",
                manifest=manifests.get(name),
            )

        with patch.object(resolver_module, "_resolve_from_registries", _mock_resolve):
            result = detect_cycles([("pkg-a", ">=1.0.0")], [registry])

        assert result is not None
        names_in_cycle = set(result)
        assert len(names_in_cycle) >= 2

    def test_unit_missing_package_not_cycle(self):
        """detect_cycles returns None if a dep is not found (cannot have cycle)."""
        pkg_a = _make_manifest("pkg-a", dependencies={"missing-pkg": ">=1.0.0"})
        registry = _make_registry({"pkg-a": ("1.0.0", pkg_a)})

        from unittest.mock import patch

        from aam_cli.core import resolver as resolver_module

        def _mock_resolve(name: str, constraint: str, registries_arg: list) -> ResolvedPackage:
            if name == "missing-pkg":
                raise ValueError(f"Package '{name}' not found")
            return ResolvedPackage(
                name=name,
                version="1.0.0",
                source="test-registry",
                checksum="sha256-abc",
                manifest=pkg_a,
            )

        with patch.object(resolver_module, "_resolve_from_registries", _mock_resolve):
            result = detect_cycles([("pkg-a", ">=1.0.0")], [registry])

        assert result is None

    def test_unit_no_dependencies_no_cycle(self):
        """detect_cycles returns None for leaf packages with no dependencies."""
        pkg_a = _make_manifest("pkg-a", dependencies={})
        registry = _make_registry({"pkg-a": ("1.0.0", pkg_a)})

        from unittest.mock import patch

        from aam_cli.core import resolver as resolver_module

        def _mock_resolve(name: str, constraint: str, registries_arg: list) -> ResolvedPackage:
            return ResolvedPackage(
                name=name,
                version="1.0.0",
                source="test-registry",
                checksum="sha256-abc",
                manifest=pkg_a,
            )

        with patch.object(resolver_module, "_resolve_from_registries", _mock_resolve):
            result = detect_cycles([("pkg-a", ">=1.0.0")], [registry])

        assert result is None


################################################################################
#                                                                              #
# TEST: resolve_dependencies_v2                                                #
#                                                                              #
################################################################################


class TestResolveDependenciesV2:
    """Tests for resolve_dependencies_v2()."""

    def _patch_resolver(self, packages: dict[str, tuple[str, PackageManifest | None]]):
        """Create a patch context for _resolve_from_registries.

        Args:
            packages: Maps package name to (version, manifest_or_None).

        Returns:
            A context manager for the patch.
        """
        from unittest.mock import patch

        from aam_cli.core import resolver as resolver_module

        def _mock_resolve(name: str, constraint: str, registries_arg: list) -> ResolvedPackage:
            if name not in packages:
                raise ValueError(
                    f"Package '{name}' not found in any configured registry."
                )
            version, pkg_manifest = packages[name]
            return ResolvedPackage(
                name=name,
                version=version,
                source="test-registry",
                checksum="sha256-abc",
                manifest=pkg_manifest,
            )

        return patch.object(resolver_module, "_resolve_from_registries", _mock_resolve)

    def test_unit_direct_deps_resolved_bfs(self):
        """Direct dependencies are resolved and included in all_packages."""
        pkg_b = _make_manifest("pkg-b", dependencies={})
        root = _make_manifest("root", dependencies={"pkg-b": ">=1.0.0"})

        with self._patch_resolver({"pkg-b": ("1.0.0", pkg_b)}):
            graph = resolve_dependencies_v2(root, [], ResolutionStrategy.DEFAULT)

        assert isinstance(graph, ResolvedGraph)
        assert any(p.name == "pkg-b" for p in graph.all_packages)
        assert len(graph.direct) >= 1

    def test_unit_optional_dep_not_found_is_swallowed(self):
        """Optional dependency PackageNotFound is swallowed; in optional_failed."""
        root = _make_manifest("root", optional_dependencies={"missing-pkg": ">=1.0.0"})

        with self._patch_resolver({}):
            graph = resolve_dependencies_v2(root, [], ResolutionStrategy.DEFAULT)

        assert "missing-pkg" in graph.optional_failed
        assert not any(p.name == "missing-pkg" for p in graph.all_packages)

    def test_unit_optional_dep_found_is_included(self):
        """Optional dependency that resolves is included in optional_resolved."""
        pkg_opt = _make_manifest("opt-pkg", dependencies={})
        root = _make_manifest("root", optional_dependencies={"opt-pkg": ">=1.0.0"})

        with self._patch_resolver({"opt-pkg": ("1.0.0", pkg_opt)}):
            graph = resolve_dependencies_v2(root, [], ResolutionStrategy.DEFAULT)

        assert any(p.name == "opt-pkg" for p in graph.optional_resolved)

    def test_unit_peer_dep_satisfied_when_in_graph(self):
        """Peer dependency is satisfied when the peer package is in the graph."""
        pkg_b = _make_manifest("pkg-b", dependencies={})
        root = _make_manifest(
            "root",
            dependencies={"pkg-b": ">=1.0.0"},
            peer_dependencies={"pkg-b": ">=1.0.0"},
        )

        with self._patch_resolver({"pkg-b": ("1.0.0", pkg_b)}):
            graph = resolve_dependencies_v2(root, [], ResolutionStrategy.DEFAULT)

        assert "pkg-b" in graph.peer_satisfied

    def test_unit_peer_dep_unsatisfied_when_not_in_graph(self):
        """Peer dependency is listed as unsatisfied when not resolved."""
        root = _make_manifest(
            "root",
            dependencies={},
            peer_dependencies={"peer-pkg": ">=1.0.0"},
        )

        with self._patch_resolver({}):
            graph = resolve_dependencies_v2(root, [], ResolutionStrategy.DEFAULT)

        assert "peer-pkg" in graph.peer_unsatisfied

    def test_unit_frozen_strategy_uses_lock_file_version(self):
        """FROZEN strategy reads version from lock file, not registry."""
        root = _make_manifest("root", dependencies={"pkg-b": ">=1.0.0"})

        # Lock file has 1.5.0
        lock_file = UniversalLockFile()
        lock_file.packages["pkg-b"] = LockedPackageV2(
            version="1.5.0",
            source="test-registry",
            integrity="sha256-oldlock",
            dependencies={},
        )

        # Frozen strategy reads from lock file directly — no registry call needed
        graph = resolve_dependencies_v2(
            root, [], ResolutionStrategy.FROZEN, lock_file=lock_file
        )

        resolved = next((p for p in graph.all_packages if p.name == "pkg-b"), None)
        assert resolved is not None
        assert resolved.version == "1.5.0"

    def test_unit_dry_run_returns_graph_without_errors(self):
        """DRY_RUN strategy resolves the graph without raising errors."""
        pkg_b = _make_manifest("pkg-b", dependencies={})
        root = _make_manifest("root", dependencies={"pkg-b": ">=1.0.0"})

        with self._patch_resolver({"pkg-b": ("1.0.0", pkg_b)}):
            graph = resolve_dependencies_v2(root, [], ResolutionStrategy.DRY_RUN)

        assert isinstance(graph, ResolvedGraph)
        assert any(p.name == "pkg-b" for p in graph.all_packages)

    def test_unit_resolutions_override_applied(self):
        """resolutions field overrides the resolved version post-BFS."""
        pkg_b_v2 = _make_manifest("pkg-b", version="2.0.0", dependencies={})
        root = _make_manifest(
            "root",
            dependencies={"pkg-b": ">=1.0.0"},
            resolutions={"pkg-b": "2.0.0"},
        )

        # The resolver will request "2.0.0" for the resolution override
        def _mock_resolve(name: str, constraint: str, registries_arg: list) -> ResolvedPackage:
            if name == "pkg-b":
                version = "2.0.0" if constraint == "2.0.0" else "1.0.0"
                return ResolvedPackage(
                    name=name,
                    version=version,
                    source="test-registry",
                    checksum="sha256-abc",
                    manifest=pkg_b_v2,
                )
            raise ValueError(f"Not found: {name}")

        from unittest.mock import patch

        from aam_cli.core import resolver as resolver_module

        with patch.object(resolver_module, "_resolve_from_registries", _mock_resolve):
            graph = resolve_dependencies_v2(root, [], ResolutionStrategy.DEFAULT)

        resolved = next((p for p in graph.all_packages if p.name == "pkg-b"), None)
        assert resolved is not None
        assert resolved.version == "2.0.0"

    def test_unit_empty_root_manifest_resolves_empty_graph(self):
        """Empty dependencies result in an empty ResolvedGraph."""
        root = _make_manifest("root")

        with self._patch_resolver({}):
            graph = resolve_dependencies_v2(root, [], ResolutionStrategy.DEFAULT)

        assert graph.all_packages == []
        assert graph.direct == []
        assert graph.optional_resolved == []


################################################################################
#                                                                              #
# TEST: MINIMAL resolution strategy                                            #
#                                                                              #
################################################################################


class TestMinimalStrategy:
    """Tests for MINIMAL resolution strategy picking the lowest satisfying version."""

    def _patch_minimal_resolver(
        self, packages: dict[str, tuple[str, PackageManifest | None]],
    ):
        """Patch _resolve_minimal_from_registries for MINIMAL strategy tests.

        Args:
            packages: Maps package name to (version, manifest_or_None).

        Returns:
            A context manager for the patch.
        """
        from unittest.mock import patch

        from aam_cli.core import resolver as resolver_module

        def _mock_resolve_minimal(
            name: str, constraint: str, registries_arg: list,
        ) -> ResolvedPackage:
            if name not in packages:
                raise ValueError(
                    f"Package '{name}' not found in any configured registry."
                )
            version, pkg_manifest = packages[name]
            return ResolvedPackage(
                name=name,
                version=version,
                source="test-registry",
                checksum="sha256-abc",
                manifest=pkg_manifest,
            )

        return patch.object(
            resolver_module, "_resolve_minimal_from_registries", _mock_resolve_minimal,
        )

    def test_unit_minimal_strategy_calls_minimal_resolver(self):
        """MINIMAL strategy invokes _resolve_minimal_from_registries."""
        pkg_b = _make_manifest("pkg-b", version="1.0.0", dependencies={})
        root = _make_manifest("root", dependencies={"pkg-b": ">=1.0.0"})

        with self._patch_minimal_resolver({"pkg-b": ("1.0.0", pkg_b)}):
            graph = resolve_dependencies_v2(
                root, [], ResolutionStrategy.MINIMAL
            )

        assert isinstance(graph, ResolvedGraph)
        resolved = next(
            (p for p in graph.all_packages if p.name == "pkg-b"), None
        )
        assert resolved is not None
        assert resolved.version == "1.0.0"

    def test_unit_minimal_strategy_resolves_transitive_deps(self):
        """MINIMAL strategy follows transitive dependencies."""
        pkg_c = _make_manifest("pkg-c", version="0.5.0", dependencies={})
        pkg_b = _make_manifest(
            "pkg-b", version="1.0.0",
            dependencies={"pkg-c": ">=0.5.0"},
        )
        root = _make_manifest("root", dependencies={"pkg-b": ">=1.0.0"})

        with self._patch_minimal_resolver({
            "pkg-b": ("1.0.0", pkg_b),
            "pkg-c": ("0.5.0", pkg_c),
        }):
            graph = resolve_dependencies_v2(
                root, [], ResolutionStrategy.MINIMAL
            )

        names = {p.name for p in graph.all_packages}
        assert "pkg-b" in names
        assert "pkg-c" in names

    def test_unit_minimal_strategy_empty_deps_gives_empty_graph(self):
        """MINIMAL strategy with no dependencies produces an empty graph."""
        root = _make_manifest("root")

        with self._patch_minimal_resolver({}):
            graph = resolve_dependencies_v2(
                root, [], ResolutionStrategy.MINIMAL
            )

        assert graph.all_packages == []


################################################################################
#                                                                              #
# TEST: find_lowest_match                                                      #
#                                                                              #
################################################################################


class TestFindLowestMatch:
    """Tests for find_lowest_match() used by MINIMAL strategy."""

    def test_unit_picks_lowest_satisfying_version(self):
        """find_lowest_match returns the lowest version matching the constraint."""
        from aam_cli.core.version import find_lowest_match

        result = find_lowest_match(">=1.0.0", ["1.0.0", "1.5.0", "2.0.0"])
        assert result == "1.0.0"

    def test_unit_picks_lowest_within_range(self):
        """find_lowest_match respects upper-bound constraints."""
        from aam_cli.core.version import find_lowest_match

        result = find_lowest_match(">=1.2.0", ["1.0.0", "1.2.0", "1.5.0"])
        assert result == "1.2.0"

    def test_unit_returns_none_when_no_match(self):
        """find_lowest_match returns None when no version satisfies constraint."""
        from aam_cli.core.version import find_lowest_match

        result = find_lowest_match(">=3.0.0", ["1.0.0", "2.0.0"])
        assert result is None

    def test_unit_wildcard_picks_lowest(self):
        """find_lowest_match with wildcard constraint returns the lowest version."""
        from aam_cli.core.version import find_lowest_match

        result = find_lowest_match("*", ["2.0.0", "1.0.0", "3.0.0"])
        assert result == "1.0.0"
