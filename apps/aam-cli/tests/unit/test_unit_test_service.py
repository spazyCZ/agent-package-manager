"""Unit tests for the test service.

Tests for ``TestCaseResult``, ``TestSuiteResult``, config loading,
and skill test runner discovery logic.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

from aam_cli.services.test_service import (
    TestCaseResult,
    TestSuiteResult,
    _load_test_config,
    run_skill_tests,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# TESTS: TestCaseResult                                                        #
#                                                                              #
################################################################################


class TestTestCaseResult:
    """Tests for TestCaseResult model."""

    def test_unit_passed_result(self) -> None:
        """Passing result serializes without error key."""
        result = TestCaseResult(name="test-1", passed=True, duration_ms=42.5)
        d = result.to_dict()
        assert d["passed"] is True
        assert d["name"] == "test-1"
        assert "error" not in d

    def test_unit_failed_result_with_error(self) -> None:
        """Failing result includes error message in dict."""
        result = TestCaseResult(
            name="test-2", passed=False, duration_ms=100, error="exit code mismatch"
        )
        d = result.to_dict()
        assert d["passed"] is False
        assert d["error"] == "exit code mismatch"


################################################################################
#                                                                              #
# TESTS: TestSuiteResult                                                       #
#                                                                              #
################################################################################


class TestTestSuiteResult:
    """Tests for TestSuiteResult model."""

    def test_unit_counts(self) -> None:
        """Suite correctly counts passed, failed, and total cases."""
        suite = TestSuiteResult(suite_name="skill:my-skill")
        suite.cases.append(TestCaseResult(name="a", passed=True, duration_ms=10))
        suite.cases.append(TestCaseResult(name="b", passed=False, duration_ms=20))
        suite.cases.append(TestCaseResult(name="c", passed=True, duration_ms=30))
        assert suite.passed == 2
        assert suite.failed == 1
        assert suite.total == 3


################################################################################
#                                                                              #
# TESTS: Config Loading                                                        #
#                                                                              #
################################################################################


class TestLoadTestConfig:
    """Tests for test config loading."""

    def test_unit_defaults_applied(self, tmp_path: Path) -> None:
        """Missing config file results in default values."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        config = _load_test_config(tests_dir)
        assert config["timeout_ms"] == 30000
        assert config["env"] == {}


################################################################################
#                                                                              #
# TESTS: Skill Test Runner                                                     #
#                                                                              #
################################################################################


class TestRunSkillTests:
    """Tests for skill test runner."""

    def test_unit_no_skills_dir(self, tmp_path: Path) -> None:
        """Returns empty results when no skills/ directory exists."""
        results = run_skill_tests(tmp_path)
        assert results == []

    def test_unit_no_tests_dir(self, tmp_path: Path) -> None:
        """Returns empty results when skill has no tests/ directory."""
        skills_dir = tmp_path / "skills" / "my-skill"
        skills_dir.mkdir(parents=True)
        results = run_skill_tests(tmp_path)
        assert results == []
