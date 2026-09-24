"""Unit tests for system dependency pre-flight checks.

Tests each check type with mocked subprocess and importlib.metadata,
and verifies SystemCheckResults.all_required_passed property.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
from unittest.mock import MagicMock, patch

from aam_cli.core.manifest import SystemDependencies, SystemPackages
from aam_cli.services.system_deps_service import (
    SystemCheckResult,
    SystemCheckResults,
    auto_install_system_deps,
    check_system_deps,
)

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _make_system_deps(
    python: str | None = None,
    node: str | None = None,
    binaries: list[str] | None = None,
    pip: list[str] | None = None,
    npm: list[str] | None = None,
    brew: list[str] | None = None,
    apt: list[str] | None = None,
    mcp_servers: list[str] | None = None,
) -> SystemDependencies:
    """Create a SystemDependencies fixture."""
    return SystemDependencies(
        python=python,
        node=node,
        binaries=binaries or [],
        packages=SystemPackages(
            pip=pip or [],
            npm=npm or [],
            brew=brew or [],
            apt=apt or [],
        ),
        mcp_servers=mcp_servers or [],
    )


def _passed_result(name: str, dep_type: str) -> SystemCheckResult:
    """Create a passing SystemCheckResult."""
    return SystemCheckResult(
        name=name, dep_type=dep_type, required=True, found=True, found_version="1.0.0"
    )


def _failed_result(name: str, dep_type: str) -> SystemCheckResult:
    """Create a failing SystemCheckResult."""
    return SystemCheckResult(
        name=name, dep_type=dep_type, required=True, found=False
    )


################################################################################
#                                                                              #
# TEST: SystemCheckResults model                                               #
#                                                                              #
################################################################################


class TestSystemCheckResults:
    """Tests for SystemCheckResults model and all_required_passed property."""

    def test_unit_all_required_passed_when_no_failures(self):
        """all_required_passed is True when failed list is empty."""
        results = SystemCheckResults(
            passed=[_passed_result("python", "runtime")],
        )
        assert results.all_required_passed is True

    def test_unit_all_required_passed_false_when_failures(self):
        """all_required_passed is False when failed list has entries."""
        results = SystemCheckResults(
            failed=[_failed_result("git", "binary")],
        )
        assert results.all_required_passed is False

    def test_unit_empty_results_all_passed(self):
        """all_required_passed is True when all lists are empty."""
        results = SystemCheckResults()
        assert results.all_required_passed is True

    def test_unit_optional_failed_does_not_affect_required_passed(self):
        """optional_failed entries do not affect all_required_passed."""
        results = SystemCheckResults(
            optional_failed=[_failed_result("opt-pkg", "pip")],
        )
        assert results.all_required_passed is True


################################################################################
#                                                                              #
# TEST: Python check                                                           #
#                                                                              #
################################################################################


class TestCheckPython:
    """Tests for _check_python() via check_system_deps()."""

    def test_unit_python_found(self):
        """check_system_deps detects python when subprocess returns successfully."""
        system_deps = _make_system_deps(python=">=3.11")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Python 3.11.5\n"

        with (
            patch("subprocess.run", return_value=mock_result),
            patch("shutil.which", return_value="/usr/bin/python3"),
        ):
            results = check_system_deps(system_deps)

        assert any(r.name == "python" and r.found for r in results.passed)

    def test_unit_python_not_found_on_path(self):
        """check_system_deps marks python as not found when subprocess raises."""
        system_deps = _make_system_deps(python=">=3.11")

        with patch("subprocess.run", side_effect=FileNotFoundError("python3 not found")):
            results = check_system_deps(system_deps)

        assert any(r.name == "python" and not r.found for r in results.failed)


################################################################################
#                                                                              #
# TEST: Node check                                                             #
#                                                                              #
################################################################################


class TestCheckNode:
    """Tests for _check_node() via check_system_deps()."""

    def test_unit_node_found(self):
        """check_system_deps detects node when subprocess returns successfully."""
        system_deps = _make_system_deps(node=">=18")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "v18.17.0\n"

        with (
            patch("subprocess.run", return_value=mock_result),
            patch("shutil.which", return_value="/usr/local/bin/node"),
        ):
            results = check_system_deps(system_deps)

        assert any(r.name == "node" and r.found for r in results.passed)

    def test_unit_node_not_found(self):
        """check_system_deps marks node as not found when subprocess raises."""
        system_deps = _make_system_deps(node=">=18")

        with patch("subprocess.run", side_effect=FileNotFoundError("node not found")):
            results = check_system_deps(system_deps)

        assert any(r.name == "node" and not r.found for r in results.failed)


################################################################################
#                                                                              #
# TEST: Binary check                                                           #
#                                                                              #
################################################################################


class TestCheckBinary:
    """Tests for _check_binary() via check_system_deps()."""

    def test_unit_binary_found_via_shutil_which(self):
        """check_system_deps detects a binary via shutil.which."""
        system_deps = _make_system_deps(binaries=["git"])

        with patch("shutil.which", return_value="/usr/bin/git"):
            results = check_system_deps(system_deps)

        assert any(r.name == "git" and r.found for r in results.passed)

    def test_unit_binary_not_on_path(self):
        """check_system_deps marks binary as not found when which returns None."""
        system_deps = _make_system_deps(binaries=["nonexistent-tool"])

        with patch("shutil.which", return_value=None):
            results = check_system_deps(system_deps)

        assert any(r.name == "nonexistent-tool" and not r.found for r in results.failed)


################################################################################
#                                                                              #
# TEST: pip package check                                                      #
#                                                                              #
################################################################################


class TestCheckPip:
    """Tests for _check_pip_package() via check_system_deps()."""

    def test_unit_pip_package_found_via_importlib(self):
        """check_system_deps detects a pip package via importlib.metadata."""
        system_deps = _make_system_deps(pip=["requests"])

        with patch(
            "importlib.metadata.version",
            return_value="2.31.0",
        ):
            results = check_system_deps(system_deps)

        assert any(
            r.name == "requests" and r.found and r.dep_type == "pip"
            for r in results.passed
        )

    def test_unit_pip_package_not_installed(self):
        """check_system_deps marks pip package as missing when not installed."""
        import importlib.metadata

        system_deps = _make_system_deps(pip=["non-existent-pkg"])

        with patch(
            "importlib.metadata.version",
            side_effect=importlib.metadata.PackageNotFoundError("not found"),
        ):
            results = check_system_deps(system_deps)

        assert any(
            r.name == "non-existent-pkg" and not r.found
            for r in results.failed
        )


################################################################################
#                                                                              #
# TEST: npm package check                                                      #
#                                                                              #
################################################################################


class TestCheckNpm:
    """Tests for _check_npm_package() via check_system_deps()."""

    def test_unit_npm_package_found_via_subprocess(self):
        """check_system_deps detects an npm package via npm list --json."""
        system_deps = _make_system_deps(npm=["typescript"])
        npm_output = json.dumps(
            {"dependencies": {"typescript": {"version": "5.0.0"}}}
        )
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = npm_output

        with patch("subprocess.run", return_value=mock_result):
            results = check_system_deps(system_deps)

        assert any(
            r.name == "typescript" and r.found and r.dep_type == "npm"
            for r in results.passed
        )

    def test_unit_npm_package_not_found(self):
        """check_system_deps marks npm package as missing when not in npm list."""
        system_deps = _make_system_deps(npm=["missing-npm-pkg"])
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"dependencies": {}})

        with patch("subprocess.run", return_value=mock_result):
            results = check_system_deps(system_deps)

        assert any(
            r.name == "missing-npm-pkg" and not r.found
            for r in results.failed
        )

    def test_unit_npm_subprocess_failure_is_handled(self):
        """check_system_deps marks npm package as missing when npm CLI unavailable."""
        system_deps = _make_system_deps(npm=["some-pkg"])

        with patch("subprocess.run", side_effect=FileNotFoundError("npm not found")):
            results = check_system_deps(system_deps)

        assert any(r.name == "some-pkg" and not r.found for r in results.failed)


################################################################################
#                                                                              #
# TEST: auto_install_system_deps                                               #
#                                                                              #
################################################################################


class TestAutoInstallSystemDeps:
    """Tests for auto_install_system_deps()."""

    def test_unit_pip_package_auto_installed(self):
        """auto_install_system_deps runs pip install for pip dep type."""
        missing = [_failed_result("mypackage", "pip")]
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            results = auto_install_system_deps(missing, allow_sudo=False)

        assert results["mypackage"] is True
        # Verify pip install was called
        call_args = mock_run.call_args[0][0]
        assert "pip" in call_args
        assert "install" in call_args
        assert "mypackage" in call_args

    def test_unit_brew_blocked_without_allow_sudo(self):
        """auto_install_system_deps skips brew installs when allow_sudo=False."""
        missing = [_failed_result("jq", "brew")]

        with patch("subprocess.run") as mock_run:
            results = auto_install_system_deps(missing, allow_sudo=False)

        # brew install should not be attempted
        mock_run.assert_not_called()
        assert results["jq"] is False

    def test_unit_binary_always_rejected(self):
        """auto_install_system_deps cannot install binaries; marks as False."""
        missing = [_failed_result("some-binary", "binary")]

        with patch("subprocess.run") as mock_subprocess:
            results = auto_install_system_deps(missing, allow_sudo=True)

        # binaries cannot be auto-installed — subprocess should not be called
        mock_subprocess.assert_not_called()
        assert results.get("some-binary") is False or "some-binary" not in results
        # If the binary type falls through without being attempted, that's correct
        # The service skips binary types entirely


################################################################################
#                                                                              #
# TEST: brew package check                                                     #
#                                                                              #
################################################################################


class TestCheckBrew:
    """Tests for _check_brew_package() via check_system_deps()."""

    def test_unit_brew_package_found(self):
        """check_system_deps detects a brew package via brew list --versions."""
        system_deps = _make_system_deps(brew=["jq"])
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "jq 1.7.1\n"

        with patch(
            "aam_cli.services.system_deps_service.subprocess.run",
            return_value=mock_result,
        ):
            results = check_system_deps(system_deps)

        assert any(
            r.name == "jq" and r.found and r.dep_type == "brew"
            for r in results.passed
        )

    def test_unit_brew_package_not_found(self):
        """check_system_deps marks brew package as missing when not installed."""
        system_deps = _make_system_deps(brew=["missing-brew"])
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch(
            "aam_cli.services.system_deps_service.subprocess.run",
            return_value=mock_result,
        ):
            results = check_system_deps(system_deps)

        assert any(
            r.name == "missing-brew" and not r.found
            for r in results.failed
        )

    def test_unit_brew_not_installed_on_system(self):
        """check_system_deps handles missing brew binary gracefully."""
        system_deps = _make_system_deps(brew=["some-pkg"])

        with patch(
            "aam_cli.services.system_deps_service.subprocess.run",
            side_effect=FileNotFoundError("brew not found"),
        ):
            results = check_system_deps(system_deps)

        failed = [r for r in results.failed if r.name == "some-pkg"]
        assert len(failed) == 1
        assert "Homebrew" in (failed[0].install_hint or "")


################################################################################
#                                                                              #
# TEST: apt package check                                                      #
#                                                                              #
################################################################################


class TestCheckApt:
    """Tests for _check_apt_package() via check_system_deps()."""

    def test_unit_apt_package_found(self):
        """check_system_deps detects an apt package via dpkg -s."""
        system_deps = _make_system_deps(apt=["curl"])
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "Package: curl\nStatus: install ok installed\nVersion: 7.88.1-10\n"
        )

        with patch(
            "aam_cli.services.system_deps_service.subprocess.run",
            return_value=mock_result,
        ):
            results = check_system_deps(system_deps)

        assert any(
            r.name == "curl" and r.found and r.dep_type == "apt"
            for r in results.passed
        )

    def test_unit_apt_package_not_installed(self):
        """check_system_deps marks apt package as missing when dpkg fails."""
        system_deps = _make_system_deps(apt=["missing-apt"])
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch(
            "aam_cli.services.system_deps_service.subprocess.run",
            return_value=mock_result,
        ):
            results = check_system_deps(system_deps)

        assert any(
            r.name == "missing-apt" and not r.found
            for r in results.failed
        )

    def test_unit_apt_not_available_on_system(self):
        """check_system_deps handles missing dpkg binary (non-Debian system)."""
        system_deps = _make_system_deps(apt=["some-pkg"])

        with patch(
            "aam_cli.services.system_deps_service.subprocess.run",
            side_effect=FileNotFoundError("dpkg not found"),
        ):
            results = check_system_deps(system_deps)

        failed = [r for r in results.failed if r.name == "some-pkg"]
        assert len(failed) == 1
        assert "apt is not available" in (failed[0].install_hint or "")
