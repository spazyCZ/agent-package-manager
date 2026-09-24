"""Unit tests for the eval service.

Tests for ``EvalCaseResult``, ``EvalSuiteResult``, config loading,
and eval runner discovery logic.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

from aam_cli.services.eval_service import (
    EvalCaseResult,
    EvalSuiteResult,
    _load_eval_config,
    run_evals,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# TESTS: EvalCaseResult                                                        #
#                                                                              #
################################################################################


class TestEvalCaseResult:
    """Tests for EvalCaseResult model."""

    def test_unit_dry_run_result(self) -> None:
        """Dry-run result serializes without score key."""
        result = EvalCaseResult(name="eval-1", status="dry-run")
        d = result.to_dict()
        assert d["status"] == "dry-run"
        assert "score" not in d

    def test_unit_pass_result_with_score(self) -> None:
        """Passing result includes score in serialized dict."""
        result = EvalCaseResult(name="eval-2", status="pass", score=0.95)
        d = result.to_dict()
        assert d["score"] == 0.95


################################################################################
#                                                                              #
# TESTS: EvalSuiteResult                                                       #
#                                                                              #
################################################################################


class TestEvalSuiteResult:
    """Tests for EvalSuiteResult model."""

    def test_unit_counts(self) -> None:
        """Suite correctly counts passed, failed, skipped, and total."""
        suite = EvalSuiteResult(suite_name="eval:my-skill", engine="claude-code")
        suite.cases.append(EvalCaseResult(name="a", status="pass"))
        suite.cases.append(EvalCaseResult(name="b", status="fail"))
        suite.cases.append(EvalCaseResult(name="c", status="dry-run"))
        assert suite.passed == 1
        assert suite.failed == 1
        assert suite.skipped == 1
        assert suite.total == 3


################################################################################
#                                                                              #
# TESTS: Config Loading                                                        #
#                                                                              #
################################################################################


class TestLoadEvalConfig:
    """Tests for eval config loading."""

    def test_unit_defaults_applied(self, tmp_path: Path) -> None:
        """Missing config file results in default values."""
        evals_dir = tmp_path / "evals"
        evals_dir.mkdir()
        config = _load_eval_config(evals_dir)
        assert config["engine"] == "claude-code"
        assert config["timeout_ms"] == 120000
        assert config["judge"] == {}


################################################################################
#                                                                              #
# TESTS: Eval Runner                                                           #
#                                                                              #
################################################################################


class TestRunEvals:
    """Tests for eval runner."""

    def test_unit_no_skills_dir(self, tmp_path: Path) -> None:
        """Returns empty results when no skills/ directory exists."""
        results = run_evals(tmp_path, dry_run=True)
        assert results == []

    def test_unit_no_evals_dir(self, tmp_path: Path) -> None:
        """Returns empty results when skill has no evals/ directory."""
        skills_dir = tmp_path / "skills" / "my-skill"
        skills_dir.mkdir(parents=True)
        results = run_evals(tmp_path, dry_run=True)
        assert results == []
