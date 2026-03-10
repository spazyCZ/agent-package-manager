"""Unit tests for the dependency tree service.

Tests all 6 service functions with mocked lock files.

Reference: tasks.md T081.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
from pathlib import Path

from aam_cli.services.dependency_tree_service import (
    audit_deps,
    check_deps,
    dedupe_deps,
    get_tree,
    get_why,
    prune_deps,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)


################################################################################
#                                                                              #
# FIXTURES                                                                     #
#                                                                              #
################################################################################


def _write_lock_file(project_dir: Path, packages: dict) -> None:
    """Write a minimal package.agent.lock to project_dir."""
    lock_data = {
        "lockVersion": 1,
        "resolved": {
            name: {
                "version": info.get("version", "1.0.0"),
                "source": info.get("source", "local"),
                "integrity": info.get("integrity", ""),
                "dependencies": info.get("dependencies", {}),
            }
            for name, info in packages.items()
        },
        "systemChecks": {},
    }
    (project_dir / "package.agent.lock").write_text(
        json.dumps(lock_data), encoding="utf-8"
    )


def _create_pkg_dir(packages_dir: Path, pkg_name: str) -> Path:
    """Create a package directory under .agent-packages/."""
    import re
    fs_name = re.sub(r"[@/]", "_", pkg_name).strip("_")
    pkg_dir = packages_dir / fs_name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    # Write a stub file so the directory is non-empty
    (pkg_dir / "README.md").write_text("# pkg")
    return pkg_dir


################################################################################
#                                                                              #
# TESTS: get_tree                                                              #
#                                                                              #
################################################################################


class TestGetTree:
    """Tests for ``get_tree()``."""

    def test_unit_get_tree_returns_tree_key(self, tmp_path: Path) -> None:
        """get_tree returns a dict with a 'tree' key."""
        _write_lock_file(tmp_path, {"@test/pkg": {"version": "1.0.0"}})
        result = get_tree(project_dir=tmp_path, depth=0)
        assert "tree" in result

    def test_unit_get_tree_empty_lock_returns_empty(self, tmp_path: Path) -> None:
        """get_tree on empty lock file returns empty tree."""
        _write_lock_file(tmp_path, {})
        result = get_tree(project_dir=tmp_path, depth=0)
        assert result["total_packages"] == 0

    def test_unit_get_tree_single_package(self, tmp_path: Path) -> None:
        """get_tree with one package shows that package in tree."""
        _write_lock_file(
            tmp_path,
            {
                "@test/pkg": {
                    "version": "1.0.0",
                    "source": "local",
                    "dependencies": {},
                }
            },
        )
        result = get_tree(project_dir=tmp_path, depth=0)
        assert result["total_packages"] == 1


################################################################################
#                                                                              #
# TESTS: get_why                                                               #
#                                                                              #
################################################################################


class TestGetWhy:
    """Tests for ``get_why()``."""

    def test_unit_get_why_direct_package(self, tmp_path: Path) -> None:
        """Direct (root) packages show is_direct=True."""
        _write_lock_file(
            tmp_path,
            {
                "@test/pkg": {
                    "version": "1.0.0",
                    "dependencies": {},
                }
            },
        )
        result = get_why(package_name="@test/pkg", project_dir=tmp_path)
        assert result["package_name"] == "@test/pkg"
        assert result["is_direct"] is True

    def test_unit_get_why_transitive_shows_parent(self, tmp_path: Path) -> None:
        """Transitive packages list the parent that requires them."""
        _write_lock_file(
            tmp_path,
            {
                "@test/parent": {
                    "version": "1.0.0",
                    "dependencies": {"@test/child": "1.0.0"},
                },
                "@test/child": {
                    "version": "1.0.0",
                    "dependencies": {},
                },
            },
        )
        result = get_why(package_name="@test/child", project_dir=tmp_path)
        assert result["package_name"] == "@test/child"
        required_by_names = [r["name"] for r in result["required_by"]]
        assert "@test/parent" in required_by_names
        assert result["is_direct"] is False

    def test_unit_get_why_missing_package(self, tmp_path: Path) -> None:
        """get_why for a package not in lock file returns found=False."""
        _write_lock_file(tmp_path, {})
        result = get_why(package_name="nonexistent", project_dir=tmp_path)
        assert result.get("found") is False


################################################################################
#                                                                              #
# TESTS: check_deps                                                            #
#                                                                              #
################################################################################


class TestCheckDeps:
    """Tests for ``check_deps()``."""

    def test_unit_check_deps_all_present(self, tmp_path: Path) -> None:
        """check_deps reports present=True for each installed package dir."""
        packages_dir = tmp_path / ".agent-packages"
        packages_dir.mkdir()
        # Create the actual directory that check_deps expects
        # The fs_name is derived from the pkg_name via to_filesystem_name
        from aam_cli.utils.naming import parse_package_name, to_filesystem_name
        scope, base = parse_package_name("@test/pkg")
        (packages_dir / to_filesystem_name(scope, base)).mkdir()

        _write_lock_file(tmp_path, {"@test/pkg": {"version": "1.0.0"}})
        result = check_deps(project_dir=tmp_path, system_only=False)

        assert result["all_passed"] is True
        results = result["results"]
        assert any(c["name"] == "@test/pkg" and c["present"] for c in results)

    def test_unit_check_deps_missing_dir_detected(self, tmp_path: Path) -> None:
        """check_deps detects missing package directory."""
        # Lock file has package, but .agent-packages/ dir does not
        (tmp_path / ".agent-packages").mkdir()
        _write_lock_file(tmp_path, {"@test/missing": {"version": "1.0.0"}})

        result = check_deps(project_dir=tmp_path, system_only=False)
        assert result["all_passed"] is False
        results = result["results"]
        assert any(c["name"] == "@test/missing" and not c["present"] for c in results)

    def test_unit_check_deps_empty_lock_all_present(self, tmp_path: Path) -> None:
        """Empty lock file returns all_passed=True (nothing to check)."""
        _write_lock_file(tmp_path, {})
        result = check_deps(project_dir=tmp_path, system_only=False)
        assert result["all_passed"] is True


################################################################################
#                                                                              #
# TESTS: audit_deps                                                            #
#                                                                              #
################################################################################


class TestAuditDeps:
    """Tests for ``audit_deps()``."""

    def test_unit_audit_no_integrity_stored_no_findings(
        self, tmp_path: Path
    ) -> None:
        """No findings when integrity field in lock is empty string."""
        packages_dir = tmp_path / ".agent-packages"
        packages_dir.mkdir()
        # Use simple unscoped package for easier fs_name matching
        (packages_dir / "test-pkg").mkdir()
        (packages_dir / "test-pkg" / "README.md").write_text("# test")

        _write_lock_file(
            tmp_path,
            {"test-pkg": {"version": "1.0.0", "integrity": ""}},
        )
        result = audit_deps(project_dir=tmp_path, severity="all")
        # With empty integrity, at most an info-level "no hash recorded" finding
        # but no critical/high mismatch finding
        findings = result.get("findings", [])
        assert not any(
            f["finding_type"] == "integrity" and f["severity"] == "critical"
            for f in findings
        )

    def test_unit_audit_hash_mismatch_is_critical(self, tmp_path: Path) -> None:
        """Mismatched directory hash is reported as CRITICAL finding."""
        packages_dir = tmp_path / ".agent-packages"
        packages_dir.mkdir()
        # Create a simple unscoped package
        (packages_dir / "test-pkg").mkdir()
        (packages_dir / "test-pkg" / "README.md").write_text("# test")

        # Write a lock file with a deliberately wrong hash
        _write_lock_file(
            tmp_path,
            {
                "test-pkg": {
                    "version": "1.0.0",
                    "integrity": "sha256-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                }
            },
        )
        result = audit_deps(project_dir=tmp_path, severity="all")
        findings = result.get("findings", [])
        # Should have a CRITICAL finding for the mismatch
        assert any(
            f["severity"] == "critical" and f["finding_type"] == "integrity"
            for f in findings
        )

    def test_unit_audit_returns_findings_key(self, tmp_path: Path) -> None:
        """audit_deps always returns a 'findings' key."""
        _write_lock_file(tmp_path, {})
        result = audit_deps(project_dir=tmp_path, severity="all")
        assert "findings" in result


################################################################################
#                                                                              #
# TESTS: dedupe_deps                                                           #
#                                                                              #
################################################################################


class TestDedupeDeps:
    """Tests for ``dedupe_deps()``."""

    def test_unit_dedupe_dry_run_no_changes_when_flat(
        self, tmp_path: Path
    ) -> None:
        """Flat install with no nested packages returns packages_changed=0."""
        packages_dir = tmp_path / ".agent-packages"
        packages_dir.mkdir()
        _create_pkg_dir(packages_dir, "@test/pkg")
        _write_lock_file(tmp_path, {"@test/pkg": {"version": "1.0.0"}})

        result = dedupe_deps(project_dir=tmp_path, dry_run=True)
        assert result["packages_changed"] == 0
        assert result["dry_run"] is True

    def test_unit_dedupe_dry_run_does_not_modify_files(
        self, tmp_path: Path
    ) -> None:
        """dry_run=True never deletes directories."""
        packages_dir = tmp_path / ".agent-packages"
        packages_dir.mkdir()
        _create_pkg_dir(packages_dir, "@test/pkg")
        _write_lock_file(tmp_path, {"@test/pkg": {"version": "1.0.0"}})

        before_dirs = set(packages_dir.iterdir())
        dedupe_deps(project_dir=tmp_path, dry_run=True)
        after_dirs = set(packages_dir.iterdir())
        assert before_dirs == after_dirs


################################################################################
#                                                                              #
# TESTS: prune_deps                                                            #
#                                                                              #
################################################################################


class TestPruneDeps:
    """Tests for ``prune_deps()``."""

    def test_unit_prune_dry_run_returns_removal_list(
        self, tmp_path: Path
    ) -> None:
        """dry_run=True returns list of dirs that would be removed."""
        packages_dir = tmp_path / ".agent-packages"
        packages_dir.mkdir()

        # Create an unlisted package directory
        unlisted = packages_dir / "unlisted-pkg"
        unlisted.mkdir()

        # Lock file does not list unlisted-pkg
        _write_lock_file(tmp_path, {})

        result = prune_deps(project_dir=tmp_path, dry_run=True)
        assert result["dry_run"] is True
        assert len(result["would_remove"]) > 0

    def test_unit_prune_dry_run_does_not_delete_dirs(
        self, tmp_path: Path
    ) -> None:
        """dry_run=True does not actually remove directories."""
        packages_dir = tmp_path / ".agent-packages"
        packages_dir.mkdir()
        unlisted = packages_dir / "ghost"
        unlisted.mkdir()

        _write_lock_file(tmp_path, {})

        prune_deps(project_dir=tmp_path, dry_run=True)
        assert unlisted.exists()

    def test_unit_prune_listed_packages_not_removed(
        self, tmp_path: Path
    ) -> None:
        """Packages listed in lock file are NOT in would_remove."""
        packages_dir = tmp_path / ".agent-packages"
        packages_dir.mkdir()
        # Create the exact fs_name for @test/pkg
        from aam_cli.utils.naming import parse_package_name, to_filesystem_name
        scope, base = parse_package_name("@test/pkg")
        listed_dir = packages_dir / to_filesystem_name(scope, base)
        listed_dir.mkdir()

        _write_lock_file(tmp_path, {"@test/pkg": {"version": "1.0.0"}})

        result = prune_deps(project_dir=tmp_path, dry_run=True)
        # Ensure the listed package is not flagged for removal
        remove_names = result.get("would_remove", [])
        fs_name = to_filesystem_name(scope, base)
        assert fs_name not in remove_names
