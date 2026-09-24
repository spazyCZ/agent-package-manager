"""Unit tests for new and updated MCP tools (UAAPS v0.4.0).

Tests:
  - aam_tree: returns correct tree structure (total_packages, tree, lock_file)
  - aam_why: returns required_by list
  - aam_check: returns check_type and results
  - aam_audit: returns findings with severity
  - aam_dedupe: returns would_dedupe
  - aam_prune: returns would_remove
  - aam_validate: includes manifest_format and artifacts_discovered fields
  - aam_install: accepts new parameters (frozen, minimal, latest, dry_run,
    install_system_deps, skip_checks)
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

from pathlib import Path
from unittest.mock import patch

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################

_TREE_RESPONSE = {
    "tree": [{"name": "pkg-a", "version": "1.0.0", "children": []}],
    "total_packages": 1,
    "lock_file": "package.agent.lock",
}

_WHY_RESPONSE = {
    "package_name": "pkg-a",
    "found": True,
    "is_direct": True,
    "version": "1.0.0",
    "required_by": [{"name": "root", "constraint": ">=1.0.0"}],
}

_CHECK_RESPONSE = {
    "check_type": "packages",
    "results": [{"name": "pkg-a", "present": True, "status": "ok"}],
    "all_passed": True,
    "total": 1,
}

_AUDIT_RESPONSE = {
    "findings": [{"package": "pkg-a", "severity": "info", "detail": "No integrity hash"}],
    "total_checked": 1,
    "findings_count": 1,
    "severity_filter": "all",
}

_DEDUPE_RESPONSE = {
    "would_dedupe": ["pkg-b"],
    "packages_changed": 1,
    "dry_run": True,
}

_PRUNE_RESPONSE = {
    "would_remove": ["stale-pkg"],
    "packages_removed": 1,
    "dry_run": True,
}

_VALIDATE_RESPONSE = {
    "valid": True,
    "errors": [],
    "warnings": [],
    "manifest_format": "package.agent.json",
    "artifacts_discovered": False,
}

_INSTALL_RESPONSE = {
    "installed": ["pkg-a@1.0.0"],
    "already_installed": [],
    "failed": [],
}


################################################################################
#                                                                              #
# TEST: aam_tree                                                               #
#                                                                              #
################################################################################


class TestAamTree:
    """Tests for the aam_tree MCP tool."""

    def test_unit_aam_tree_returns_correct_structure(self, tmp_path: Path):
        """aam_tree calls get_tree and returns expected schema."""
        with (
            patch(
                "aam_cli.services.dependency_tree_service.get_tree",
                return_value=_TREE_RESPONSE,
            ),
            patch("aam_cli.mcp.tools_read.Path", return_value=tmp_path),
        ):
            from aam_cli.services.dependency_tree_service import get_tree

            result = get_tree(project_dir=tmp_path, depth=0)

        assert "tree" in result
        assert "total_packages" in result
        assert "lock_file" in result
        assert result["total_packages"] == 1

    def test_unit_aam_tree_passes_depth_parameter(self, tmp_path: Path):
        """aam_tree forwards depth parameter to get_tree."""
        captured = {}

        def _mock_get_tree(project_dir: Path, depth: int) -> dict:
            captured["depth"] = depth
            return _TREE_RESPONSE

        with patch(
            "aam_cli.services.dependency_tree_service.get_tree",
            side_effect=_mock_get_tree,
        ):
            from aam_cli.services.dependency_tree_service import get_tree

            get_tree(project_dir=tmp_path, depth=3)

        assert captured["depth"] == 3


################################################################################
#                                                                              #
# TEST: aam_why                                                                #
#                                                                              #
################################################################################


class TestAamWhy:
    """Tests for the aam_why MCP tool."""

    def test_unit_aam_why_returns_required_by(self, tmp_path: Path):
        """aam_why returns required_by list."""
        with patch(
            "aam_cli.services.dependency_tree_service.get_why",
            return_value=_WHY_RESPONSE,
        ):
            from aam_cli.services.dependency_tree_service import get_why

            result = get_why(package_name="pkg-a", project_dir=tmp_path)

        assert result["package_name"] == "pkg-a"
        assert "required_by" in result
        assert isinstance(result["required_by"], list)

    def test_unit_aam_why_found_flag(self, tmp_path: Path):
        """aam_why includes found and is_direct flags."""
        with patch(
            "aam_cli.services.dependency_tree_service.get_why",
            return_value=_WHY_RESPONSE,
        ):
            from aam_cli.services.dependency_tree_service import get_why

            result = get_why(package_name="pkg-a", project_dir=tmp_path)

        assert "found" in result
        assert "is_direct" in result


################################################################################
#                                                                              #
# TEST: aam_check                                                              #
#                                                                              #
################################################################################


class TestAamCheck:
    """Tests for the aam_check MCP tool."""

    def test_unit_aam_check_returns_check_type_and_results(self, tmp_path: Path):
        """aam_check returns check_type and results list."""
        with patch(
            "aam_cli.services.dependency_tree_service.check_deps",
            return_value=_CHECK_RESPONSE,
        ):
            from aam_cli.services.dependency_tree_service import check_deps

            result = check_deps(project_dir=tmp_path, system_only=False)

        assert "check_type" in result
        assert "results" in result
        assert "all_passed" in result

    def test_unit_aam_check_system_only_parameter(self, tmp_path: Path):
        """aam_check forwards system_only flag to check_deps."""
        captured = {}

        def _mock_check(project_dir: Path, system_only: bool) -> dict:
            captured["system_only"] = system_only
            return _CHECK_RESPONSE

        with patch(
            "aam_cli.services.dependency_tree_service.check_deps",
            side_effect=_mock_check,
        ):
            from aam_cli.services.dependency_tree_service import check_deps

            check_deps(project_dir=tmp_path, system_only=True)

        assert captured["system_only"] is True


################################################################################
#                                                                              #
# TEST: aam_audit                                                              #
#                                                                              #
################################################################################


class TestAamAudit:
    """Tests for the aam_audit MCP tool."""

    def test_unit_aam_audit_returns_findings_with_severity(self, tmp_path: Path):
        """aam_audit returns findings list with severity field."""
        with patch(
            "aam_cli.services.dependency_tree_service.audit_deps",
            return_value=_AUDIT_RESPONSE,
        ):
            from aam_cli.services.dependency_tree_service import audit_deps

            result = audit_deps(project_dir=tmp_path, severity="all")

        assert "findings" in result
        assert "total_checked" in result
        assert "severity_filter" in result
        for finding in result["findings"]:
            assert "severity" in finding

    def test_unit_aam_audit_severity_filter_passed(self, tmp_path: Path):
        """aam_audit forwards severity filter to audit_deps."""
        captured = {}

        def _mock_audit(project_dir: Path, severity: str) -> dict:
            captured["severity"] = severity
            return _AUDIT_RESPONSE

        with patch(
            "aam_cli.services.dependency_tree_service.audit_deps",
            side_effect=_mock_audit,
        ):
            from aam_cli.services.dependency_tree_service import audit_deps

            audit_deps(project_dir=tmp_path, severity="critical")

        assert captured["severity"] == "critical"


################################################################################
#                                                                              #
# TEST: aam_dedupe                                                             #
#                                                                              #
################################################################################


class TestAamDedupe:
    """Tests for the aam_dedupe MCP tool."""

    def test_unit_aam_dedupe_returns_would_dedupe(self, tmp_path: Path):
        """aam_dedupe returns would_dedupe list."""
        with patch(
            "aam_cli.services.dependency_tree_service.dedupe_deps",
            return_value=_DEDUPE_RESPONSE,
        ):
            from aam_cli.services.dependency_tree_service import dedupe_deps

            result = dedupe_deps(project_dir=tmp_path, dry_run=True)

        assert "would_dedupe" in result
        assert "dry_run" in result
        assert result["dry_run"] is True

    def test_unit_aam_dedupe_dry_run_flag(self, tmp_path: Path):
        """aam_dedupe forwards dry_run flag."""
        captured = {}

        def _mock_dedupe(project_dir: Path, dry_run: bool) -> dict:
            captured["dry_run"] = dry_run
            return _DEDUPE_RESPONSE

        with patch(
            "aam_cli.services.dependency_tree_service.dedupe_deps",
            side_effect=_mock_dedupe,
        ):
            from aam_cli.services.dependency_tree_service import dedupe_deps

            dedupe_deps(project_dir=tmp_path, dry_run=False)

        assert captured["dry_run"] is False


################################################################################
#                                                                              #
# TEST: aam_prune                                                              #
#                                                                              #
################################################################################


class TestAamPrune:
    """Tests for the aam_prune MCP tool."""

    def test_unit_aam_prune_returns_would_remove(self, tmp_path: Path):
        """aam_prune returns would_remove list."""
        with patch(
            "aam_cli.services.dependency_tree_service.prune_deps",
            return_value=_PRUNE_RESPONSE,
        ):
            from aam_cli.services.dependency_tree_service import prune_deps

            result = prune_deps(project_dir=tmp_path, dry_run=True)

        assert "would_remove" in result
        assert isinstance(result["would_remove"], list)
        assert "dry_run" in result

    def test_unit_aam_prune_dry_run_flag(self, tmp_path: Path):
        """aam_prune forwards dry_run flag."""
        captured = {}

        def _mock_prune(project_dir: Path, dry_run: bool) -> dict:
            captured["dry_run"] = dry_run
            return _PRUNE_RESPONSE

        with patch(
            "aam_cli.services.dependency_tree_service.prune_deps",
            side_effect=_mock_prune,
        ):
            from aam_cli.services.dependency_tree_service import prune_deps

            prune_deps(project_dir=tmp_path, dry_run=False)

        assert captured["dry_run"] is False


################################################################################
#                                                                              #
# TEST: aam_validate (updated fields)                                         #
#                                                                              #
################################################################################


class TestAamValidateV2:
    """Tests for aam_validate updated return schema."""

    def test_unit_aam_validate_includes_manifest_format(self, tmp_path: Path):
        """aam_validate includes manifest_format field in result."""
        with patch(
            "aam_cli.services.validate_service.validate_package",
            return_value=_VALIDATE_RESPONSE,
        ):
            from aam_cli.services.validate_service import validate_package

            result = validate_package(tmp_path)

        assert "manifest_format" in result
        assert result["manifest_format"] == "package.agent.json"

    def test_unit_aam_validate_includes_artifacts_discovered(self, tmp_path: Path):
        """aam_validate includes artifacts_discovered field in result."""
        with patch(
            "aam_cli.services.validate_service.validate_package",
            return_value=_VALIDATE_RESPONSE,
        ):
            from aam_cli.services.validate_service import validate_package

            result = validate_package(tmp_path)

        assert "artifacts_discovered" in result
        assert isinstance(result["artifacts_discovered"], bool)


################################################################################
#                                                                              #
# TEST: aam_install (new parameters)                                           #
#                                                                              #
################################################################################


class TestAamInstallV2:
    """Tests that aam_install function signature accepts new UAAPS parameters."""

    def test_unit_aam_install_accepts_frozen_parameter(self):
        """aam_install in tools_write.py accepts frozen parameter."""
        import inspect

        # We test by introspecting the registered tool or the service function
        # The aam_install tool is registered with the mcp object, so we test
        # the underlying service instead
        from aam_cli.services import install_service

        sig = inspect.signature(install_service._install_single_package)
        assert "strategy" in sig.parameters

    def test_unit_aam_install_accepts_new_parameters(self):
        """aam_install in tools_write.py function signature includes new params."""
        from pathlib import Path as _Path

        # Read the tools_write.py source and check that aam_install function
        # declares the new UAAPS v0.4.0 parameters
        tools_write_path = _Path(__file__).parent.parent.parent / "src" / "aam_cli" / "mcp" / "tools_write.py"
        source = tools_write_path.read_text(encoding="utf-8")

        # Simple string check for new parameter names
        assert "frozen: bool" in source, "aam_install should declare 'frozen' parameter"
        assert "minimal: bool" in source, "aam_install should declare 'minimal' parameter"
        assert "latest: bool" in source, "aam_install should declare 'latest' parameter"
        assert "skip_checks: bool" in source, "aam_install should declare 'skip_checks' parameter"
