"""Test service for AAM deterministic assert tests.

Discovers and runs test cases defined in ``tests/`` directories for skills
and hooks. Test cases use YAML format with input/expected assertions.

Reference: UAAPS v0.5.0 spec §15 validation.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from aam_cli.utils.yaml_utils import load_yaml

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

DEFAULT_TIMEOUT_MS: int = 30000

################################################################################
#                                                                              #
# RESULT MODELS                                                                #
#                                                                              #
################################################################################


class TestCaseResult:
    """Result of a single test case execution."""

    def __init__(
        self,
        name: str,
        passed: bool,
        duration_ms: float,
        error: str | None = None,
    ) -> None:
        self.name = name
        self.passed = passed
        self.duration_ms = duration_ms
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        result: dict[str, Any] = {
            "name": self.name,
            "passed": self.passed,
            "duration_ms": round(self.duration_ms, 2),
        }
        if self.error:
            result["error"] = self.error
        return result


class TestSuiteResult:
    """Result of an entire test suite run."""

    def __init__(self, suite_name: str) -> None:
        self.suite_name = suite_name
        self.cases: list[TestCaseResult] = []

    @property
    def passed(self) -> int:
        """Count of passing cases."""
        return sum(1 for c in self.cases if c.passed)

    @property
    def failed(self) -> int:
        """Count of failing cases."""
        return sum(1 for c in self.cases if not c.passed)

    @property
    def total(self) -> int:
        """Total test cases."""
        return len(self.cases)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "suite": self.suite_name,
            "passed": self.passed,
            "failed": self.failed,
            "total": self.total,
            "cases": [c.to_dict() for c in self.cases],
        }


################################################################################
#                                                                              #
# TEST RUNNER                                                                  #
#                                                                              #
################################################################################


def _load_test_config(tests_dir: Path) -> dict[str, Any]:
    """Load test-config.json from a tests directory.

    Args:
        tests_dir: Path to the ``tests/`` directory.

    Returns:
        Parsed config dict with defaults applied.
    """
    config_path = tests_dir / "test-config.json"
    if config_path.is_file():
        config: dict[str, Any] = json.loads(
            config_path.read_text(encoding="utf-8")
        )
    else:
        config = {}

    config.setdefault("timeout_ms", DEFAULT_TIMEOUT_MS)
    config.setdefault("env", {})
    return config


def _discover_test_cases(tests_dir: Path) -> list[Path]:
    """Discover YAML test case files in a tests/cases/ directory.

    Args:
        tests_dir: Path to the ``tests/`` directory.

    Returns:
        Sorted list of case file paths.
    """
    cases_dir = tests_dir / "cases"
    if not cases_dir.is_dir():
        return []

    cases = sorted(
        p for p in cases_dir.iterdir()
        if p.suffix in (".yaml", ".yml")
    )
    logger.debug(f"Discovered {len(cases)} test cases in {cases_dir}")
    return cases


def _run_test_case(
    case_path: Path,
    config: dict[str, Any],
    working_dir: Path,
) -> TestCaseResult:
    """Execute a single test case.

    Parses the YAML case file, runs the input command as a subprocess,
    and asserts against expected exit code, stdout, and stderr patterns.

    Args:
        case_path: Path to the YAML test case file.
        config: Test suite configuration.
        working_dir: Working directory for subprocess execution.

    Returns:
        Test case result with pass/fail status.
    """
    case_name = case_path.stem

    logger.info(f"Running test case: {case_name}")
    start = time.monotonic()

    case_data: dict[str, Any] = load_yaml(case_path)
    input_section = case_data.get("input", {})
    expected = case_data.get("expected", {})

    command = input_section.get("command")
    if not command:
        elapsed = (time.monotonic() - start) * 1000
        return TestCaseResult(
            name=case_name,
            passed=False,
            duration_ms=elapsed,
            error="No 'input.command' defined in test case",
        )

    timeout_s = config.get("timeout_ms", DEFAULT_TIMEOUT_MS) / 1000
    env_vars = {**config.get("env", {}), **input_section.get("env", {})}

    run_env = {**os.environ, **env_vars}

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=str(working_dir),
            env=run_env,
        )
    except subprocess.TimeoutExpired:
        elapsed = (time.monotonic() - start) * 1000
        return TestCaseResult(
            name=case_name,
            passed=False,
            duration_ms=elapsed,
            error=f"Timed out after {timeout_s}s",
        )

    elapsed = (time.monotonic() - start) * 1000

    # -----
    # Assert expected conditions
    # -----
    errors: list[str] = []

    expected_exit = expected.get("exit-code", expected.get("exit_code"))
    if expected_exit is not None and result.returncode != expected_exit:
        errors.append(
            f"exit-code: expected {expected_exit}, got {result.returncode}"
        )

    for pattern in expected.get("stdout-contains", []):
        if pattern not in result.stdout:
            errors.append(f"stdout-contains: '{pattern}' not found")

    for pattern in expected.get("stderr-contains", []):
        if pattern not in result.stderr:
            errors.append(f"stderr-contains: '{pattern}' not found")

    for pattern in expected.get("not-contains", []):
        if pattern in result.stdout or pattern in result.stderr:
            errors.append(f"not-contains: '{pattern}' was found in output")

    if "stdout-json" in expected:
        try:
            actual_json = json.loads(result.stdout)
            expected_json = expected["stdout-json"]
            if actual_json != expected_json:
                errors.append("stdout-json: output JSON does not match expected")
        except json.JSONDecodeError:
            errors.append("stdout-json: stdout is not valid JSON")

    if errors:
        return TestCaseResult(
            name=case_name,
            passed=False,
            duration_ms=elapsed,
            error="; ".join(errors),
        )

    return TestCaseResult(name=case_name, passed=True, duration_ms=elapsed)


def run_skill_tests(
    package_dir: Path,
    skill_name: str | None = None,
) -> list[TestSuiteResult]:
    """Run tests for skills in a package.

    Args:
        package_dir: Root directory of the AAM package.
        skill_name: Optional specific skill to test.

    Returns:
        List of test suite results.
    """
    logger.info(f"Running skill tests: package={package_dir}, skill={skill_name}")
    results: list[TestSuiteResult] = []

    skills_dir = package_dir / "skills"
    if not skills_dir.is_dir():
        logger.warning(f"No skills directory found at {skills_dir}")
        return results

    skill_dirs = (
        [skills_dir / skill_name]
        if skill_name
        else [d for d in skills_dir.iterdir() if d.is_dir()]
    )

    for skill_dir in skill_dirs:
        tests_dir = skill_dir / "tests"
        if not tests_dir.is_dir():
            logger.debug(f"No tests/ directory in {skill_dir.name}, skipping")
            continue

        suite = TestSuiteResult(suite_name=f"skill:{skill_dir.name}")
        config = _load_test_config(tests_dir)
        cases = _discover_test_cases(tests_dir)

        for case_path in cases:
            case_result = _run_test_case(case_path, config, package_dir)
            suite.cases.append(case_result)

        results.append(suite)

    return results


def run_hook_tests(
    package_dir: Path,
    event_name: str | None = None,
    case_name: str | None = None,
) -> list[TestSuiteResult]:
    """Run tests for hooks in a package.

    Args:
        package_dir: Root directory of the AAM package.
        event_name: Optional event name filter.
        case_name: Optional case name filter.

    Returns:
        List of test suite results.
    """
    logger.info(
        f"Running hook tests: package={package_dir}, "
        f"event={event_name}, case={case_name}"
    )
    results: list[TestSuiteResult] = []

    hooks_tests_dir = package_dir / "hooks" / "tests"
    if not hooks_tests_dir.is_dir():
        logger.warning(f"No hooks/tests directory found at {hooks_tests_dir}")
        return results

    suite = TestSuiteResult(suite_name="hooks")
    config = _load_test_config(hooks_tests_dir)
    cases = _discover_test_cases(hooks_tests_dir)

    for case_path in cases:
        if case_name and case_path.stem != case_name:
            continue
        case_result = _run_test_case(case_path, config, package_dir)
        suite.cases.append(case_result)

    results.append(suite)
    return results
