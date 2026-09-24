"""Eval service for AAM LLM-judged evaluations.

Discovers and runs eval cases defined in ``evals/`` directories for skills.
Supports dry-run mode and Claude Code engine. Full sandbox and multi-engine
support is planned for future iterations.

Reference: UAAPS v0.5.0 spec §15 validation.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
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

SUPPORTED_ENGINES: list[str] = ["claude-code"]
DEFAULT_ENGINE: str = "claude-code"

################################################################################
#                                                                              #
# RESULT MODELS                                                                #
#                                                                              #
################################################################################


class EvalCaseResult:
    """Result of a single eval case."""

    def __init__(
        self,
        name: str,
        status: str,
        duration_ms: float = 0.0,
        score: float | None = None,
        error: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.status = status
        self.duration_ms = duration_ms
        self.score = score
        self.error = error
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        result: dict[str, Any] = {
            "name": self.name,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 2),
        }
        if self.score is not None:
            result["score"] = self.score
        if self.error:
            result["error"] = self.error
        if self.details:
            result["details"] = self.details
        return result


class EvalSuiteResult:
    """Result of an eval suite run."""

    def __init__(self, suite_name: str, engine: str) -> None:
        self.suite_name = suite_name
        self.engine = engine
        self.cases: list[EvalCaseResult] = []

    @property
    def passed(self) -> int:
        """Count of passing cases."""
        return sum(1 for c in self.cases if c.status == "pass")

    @property
    def failed(self) -> int:
        """Count of failing cases."""
        return sum(1 for c in self.cases if c.status == "fail")

    @property
    def skipped(self) -> int:
        """Count of skipped cases (dry-run)."""
        return sum(1 for c in self.cases if c.status == "dry-run")

    @property
    def total(self) -> int:
        """Total eval cases."""
        return len(self.cases)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "suite": self.suite_name,
            "engine": self.engine,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "total": self.total,
            "cases": [c.to_dict() for c in self.cases],
        }


################################################################################
#                                                                              #
# EVAL RUNNER                                                                  #
#                                                                              #
################################################################################


def _load_eval_config(evals_dir: Path) -> dict[str, Any]:
    """Load eval-config.json from an evals directory.

    Args:
        evals_dir: Path to the ``evals/`` directory.

    Returns:
        Parsed config dict with defaults applied.
    """
    config_path = evals_dir / "eval-config.json"
    if config_path.is_file():
        config: dict[str, Any] = json.loads(
            config_path.read_text(encoding="utf-8")
        )
    else:
        config = {}

    config.setdefault("engine", DEFAULT_ENGINE)
    config.setdefault("timeout_ms", 120000)
    config.setdefault("judge", {})
    return config


def _discover_eval_cases(evals_dir: Path) -> list[Path]:
    """Discover YAML eval case files.

    Args:
        evals_dir: Path to the ``evals/`` directory.

    Returns:
        Sorted list of case file paths.
    """
    cases_dir = evals_dir / "cases"
    if not cases_dir.is_dir():
        return []

    cases = sorted(
        p for p in cases_dir.iterdir()
        if p.suffix in (".yaml", ".yml")
    )
    logger.debug(f"Discovered {len(cases)} eval cases in {cases_dir}")
    return cases


def run_evals(
    package_dir: Path,
    target: str | None = None,
    engine: str = DEFAULT_ENGINE,
    dry_run: bool = False,
) -> list[EvalSuiteResult]:
    """Run LLM-judged evaluations for a package.

    In dry-run mode, cases are discovered and parsed but not executed.

    Args:
        package_dir: Root directory of the AAM package.
        target: Optional specific skill/artifact to evaluate.
        engine: Eval engine to use (currently only ``claude-code``).
        dry_run: If True, only parse and report what would run.

    Returns:
        List of eval suite results.
    """
    logger.info(
        f"Running evals: package={package_dir}, target={target}, "
        f"engine={engine}, dry_run={dry_run}"
    )

    results: list[EvalSuiteResult] = []

    skills_dir = package_dir / "skills"
    if not skills_dir.is_dir():
        logger.warning(f"No skills directory at {skills_dir}")
        return results

    skill_dirs = (
        [skills_dir / target]
        if target
        else [d for d in skills_dir.iterdir() if d.is_dir()]
    )

    for skill_dir in skill_dirs:
        evals_dir = skill_dir / "evals"
        if not evals_dir.is_dir():
            logger.debug(f"No evals/ directory in {skill_dir.name}, skipping")
            continue

        suite = EvalSuiteResult(
            suite_name=f"eval:{skill_dir.name}",
            engine=engine,
        )
        config = _load_eval_config(evals_dir)
        cases = _discover_eval_cases(evals_dir)

        for case_path in cases:
            case_data: dict[str, Any] = load_yaml(case_path)
            case_name = case_data.get("name", case_path.stem)

            if dry_run:
                suite.cases.append(
                    EvalCaseResult(
                        name=case_name,
                        status="dry-run",
                        details={
                            "input": case_data.get("input", {}),
                            "engine": config.get("engine", engine),
                        },
                    )
                )
            else:
                start = time.monotonic()
                case_result = _execute_eval_case(
                    case_data, config, package_dir, engine
                )
                case_result.duration_ms = (time.monotonic() - start) * 1000
                suite.cases.append(case_result)

        results.append(suite)

    return results


def _execute_eval_case(
    case_data: dict[str, Any],
    config: dict[str, Any],
    working_dir: Path,
    engine: str,
) -> EvalCaseResult:
    """Execute a single eval case.

    Currently returns a placeholder result — full LLM sandbox execution
    is planned for future iterations.

    Args:
        case_data: Parsed YAML case data.
        config: Eval suite configuration.
        working_dir: Working directory for execution.
        engine: Engine to use.

    Returns:
        Eval case result.
    """
    case_name = case_data.get("name", "unnamed")

    logger.info(f"Executing eval case: {case_name} (engine={engine})")

    return EvalCaseResult(
        name=case_name,
        status="fail",
        error=f"Engine '{engine}' execution not yet implemented — "
              "use --dry-run to preview cases",
    )
