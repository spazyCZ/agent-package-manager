"""Integration E2E: skill conversion conventions across real agent platforms.

Builds realistic Cursor / Copilot / Claude Code / Codex skill trees (SKILL.md
+ supporting files + platform frontmatter) and verifies ``aam convert``
follows BIDIRECTIONAL_CONVERSION_CONVENTIONS:

- Skills are copied as-is (frontmatter not rewritten)
- Cursor and Codex targets preserve nesting under the skills root
- Copilot and Claude targets flatten to the SKILL.md parent folder name
- Multi-root discovery (.agents/skills, legacy .codex/skills)
- Idempotent re-run without --force skips existing targets

Reference:
  docs/specs/BIDIRECTIONAL_CONVERSION_CONVENTIONS.md
  docs/specs/SPEC-convert-command.md
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import pytest
from click.testing import CliRunner

from aam_cli.converters.frontmatter import parse_frontmatter
from aam_cli.main import cli
from aam_cli.services.convert_service import run_conversion

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# FIXTURE HELPERS                                                              #
#                                                                              #
################################################################################

# Realistic Cursor skill frontmatter (agentskills.io + Cursor paths)
CURSOR_NESTED_SKILL_MD = """\
---
name: land-it
description: Land a change safely. Use when merging PRs or finishing a ship.
paths:
  - "**/*.ts"
  - "apps/**/*.py"
disable-model-invocation: false
metadata:
  author: aam-e2e
  version: "1.0"
---

# Land It

Ship carefully. Run tests before merge.

## Steps

1. Run the validation script: `scripts/validate.sh`
2. Read `references/CHECKLIST.md`
"""

CURSOR_FLAT_SKILL_MD = """\
---
name: code-review
description: Review code for defects. Use when the user asks for a review.
---

# Code Review

Review for correctness, security, and clarity.
"""

CLAUDE_SKILL_MD = """\
---
name: security-audit
description: Security-focused audit skill for Claude Code.
when_to_use: When reviewing auth, secrets, or injection risks.
allowed-tools: Read Grep Bash(git:*)
disable-model-invocation: false
---

# Security Audit

Check for injection risks, secret leaks, and auth flaws.
"""


def _write_skill(
    skill_dir: Path,
    skill_md: str,
    *,
    with_support_files: bool = True,
) -> Path:
    """Write a realistic skill directory with optional scripts/references.

    Args:
        skill_dir: Destination skill directory (parent of SKILL.md).
        skill_md: Full SKILL.md contents including frontmatter.
        with_support_files: When True, add scripts/ and references/.

    Returns:
        Path to the skill directory.
    """
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    if with_support_files:
        scripts = skill_dir / "scripts"
        scripts.mkdir(exist_ok=True)
        (scripts / "validate.sh").write_text(
            "#!/usr/bin/env bash\necho ok\n", encoding="utf-8"
        )
        refs = skill_dir / "references"
        refs.mkdir(exist_ok=True)
        (refs / "CHECKLIST.md").write_text(
            "# Checklist\n- tests\n- review\n", encoding="utf-8"
        )
    return skill_dir


def _read(path: Path) -> str:
    """Read a UTF-8 text file."""
    return path.read_text(encoding="utf-8")


################################################################################
#                                                                              #
# FIXTURES                                                                     #
#                                                                              #
################################################################################


@pytest.fixture()
def multi_agent_project(tmp_path: Path) -> Path:
    """Create a project with real skill layouts for all supported agents.

    Layout:
      .cursor/skills/shipping/land-it/   (nested Cursor skill)
      .cursor/skills/code-review/        (flat Cursor skill)
      .agents/skills/shared-ops/         (shared root, Cursor/Codex/Copilot)
      .claude/skills/security-audit/     (Claude-only)
      .codex/skills/legacy-ops/          (Codex legacy root)

    Returns:
        Project root path.
    """
    root = tmp_path / "project"
    root.mkdir()

    _write_skill(
        root / ".cursor" / "skills" / "shipping" / "land-it",
        CURSOR_NESTED_SKILL_MD,
    )
    _write_skill(
        root / ".cursor" / "skills" / "code-review",
        CURSOR_FLAT_SKILL_MD,
        with_support_files=False,
    )
    _write_skill(
        root / ".agents" / "skills" / "shared-ops",
        "---\nname: shared-ops\ndescription: Shared ops skill.\n---\n"
        "# Shared Ops\nUse for shared workflows.\n",
    )
    _write_skill(
        root / ".claude" / "skills" / "security-audit",
        CLAUDE_SKILL_MD,
    )
    _write_skill(
        root / ".codex" / "skills" / "legacy-ops",
        "---\nname: legacy-ops\ndescription: Legacy Codex skill path.\n---\n"
        "# Legacy Ops\n",
        with_support_files=False,
    )

    logger.info(f"Created multi-agent E2E project at {root}")
    return root


################################################################################
#                                                                              #
# E2E: CURSOR → CODEX (preserve nesting)                                       #
#                                                                              #
################################################################################


class TestE2ECursorToCodexPreserveNesting:
    """Cursor nested skills convert to Codex with nesting preserved."""

    def test_integration_nested_skill_preserved_under_agents_skills(
        self, multi_agent_project: Path
    ) -> None:
        """``.cursor/skills/shipping/land-it`` → ``.agents/skills/shipping/land-it``."""
        root = multi_agent_project

        report = run_conversion(
            root, "cursor", "codex", artifact_type="skill", force=True
        )

        converted = [
            r for r in report.results
            if r.artifact_type == "skill" and not r.skipped and r.error is None
        ]
        assert len(converted) >= 2  # land-it + code-review (+ shared may skip)

        target = root / ".agents" / "skills" / "shipping" / "land-it"
        assert (target / "SKILL.md").is_file()
        assert (target / "scripts" / "validate.sh").is_file()
        assert (target / "references" / "CHECKLIST.md").is_file()

        # Frontmatter as-is (Cursor paths / metadata preserved)
        meta, body = parse_frontmatter(_read(target / "SKILL.md"))
        assert meta["name"] == "land-it"
        assert meta["paths"] == ["**/*.ts", "apps/**/*.py"]
        assert meta["metadata"]["author"] == "aam-e2e"
        assert "Ship carefully" in body

        flat = root / ".agents" / "skills" / "code-review"
        assert (flat / "SKILL.md").is_file()


################################################################################
#                                                                              #
# E2E: CURSOR → COPILOT / CLAUDE (flatten)                                     #
#                                                                              #
################################################################################


class TestE2ECursorFlattenToCopilotAndClaude:
    """Nested Cursor skills flatten when targeting Copilot or Claude."""

    def test_integration_nested_skill_flattens_for_copilot(
        self, multi_agent_project: Path
    ) -> None:
        """``.cursor/skills/shipping/land-it`` → ``.github/skills/land-it``."""
        root = multi_agent_project

        report = run_conversion(
            root, "cursor", "copilot", artifact_type="skill", force=True
        )
        assert report.failed_count == 0

        target = root / ".github" / "skills" / "land-it"
        assert (target / "SKILL.md").is_file()
        assert not (
            root / ".github" / "skills" / "shipping" / "land-it"
        ).exists()

        meta, body = parse_frontmatter(_read(target / "SKILL.md"))
        assert meta["name"] == "land-it"
        assert "paths" in meta  # as-is; Copilot ignores unknown keys
        assert "Ship carefully" in body
        assert (target / "scripts" / "validate.sh").is_file()

    def test_integration_nested_skill_flattens_for_claude(
        self, multi_agent_project: Path
    ) -> None:
        """``.cursor/skills/shipping/land-it`` → ``.claude/skills/land-it``."""
        root = multi_agent_project

        report = run_conversion(
            root, "cursor", "claude-code", artifact_type="skill", force=True
        )
        assert report.failed_count == 0

        target = root / ".claude" / "skills" / "land-it"
        assert (target / "SKILL.md").is_file()
        # Original Claude-only skill must still exist
        assert (
            root / ".claude" / "skills" / "security-audit" / "SKILL.md"
        ).is_file()


################################################################################
#                                                                              #
# E2E: CODEX LEGACY + SHARED ROOTS                                             #
#                                                                              #
################################################################################


class TestE2ECodexRoots:
    """Codex discovers `.agents/skills` and legacy `.codex/skills`."""

    def test_integration_codex_legacy_root_converts_to_cursor(
        self, multi_agent_project: Path
    ) -> None:
        """Legacy ``.codex/skills/legacy-ops`` → ``.cursor/skills/legacy-ops``."""
        root = multi_agent_project

        report = run_conversion(
            root, "codex", "cursor", artifact_type="skill", force=True
        )
        assert report.failed_count == 0

        legacy_target = root / ".cursor" / "skills" / "legacy-ops"
        assert (legacy_target / "SKILL.md").is_file()
        assert "Legacy Ops" in _read(legacy_target / "SKILL.md")

        shared_target = root / ".cursor" / "skills" / "shared-ops"
        assert (shared_target / "SKILL.md").is_file()


################################################################################
#                                                                              #
# E2E: CLAUDE → CURSOR (as-is frontmatter)                                     #
#                                                                              #
################################################################################


class TestE2EClaudeToCursorAsIs:
    """Claude-only frontmatter passes through to Cursor unchanged."""

    def test_integration_claude_extras_copied_as_is(
        self, multi_agent_project: Path
    ) -> None:
        """Claude ``when_to_use`` / ``allowed-tools`` survive convert to Cursor."""
        root = multi_agent_project

        report = run_conversion(
            root, "claude-code", "cursor", artifact_type="skill", force=True
        )
        assert report.failed_count == 0

        target = root / ".cursor" / "skills" / "security-audit"
        assert (target / "SKILL.md").is_file()
        meta, body = parse_frontmatter(_read(target / "SKILL.md"))
        assert meta["name"] == "security-audit"
        assert "when_to_use" in meta
        assert meta["allowed-tools"] == "Read Grep Bash(git:*)"
        assert "injection risks" in body


################################################################################
#                                                                              #
# E2E: CLI INVOCATION                                                          #
#                                                                              #
################################################################################


class TestE2EConvertCli:
    """Run ``aam convert`` via CliRunner against a real project tree."""

    def test_integration_cli_cursor_to_codex_skills(
        self, multi_agent_project: Path
    ) -> None:
        """CLI convert -s cursor -t codex --type skill writes nested Codex skills."""
        root = multi_agent_project
        runner = CliRunner()
        import os

        old = os.getcwd()
        try:
            os.chdir(root)
            result = runner.invoke(
                cli,
                [
                    "convert",
                    "-s", "cursor",
                    "-t", "codex",
                    "--type", "skill",
                    "--force",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old)

        assert result.exit_code == 0, result.output
        assert "Converting" in result.output
        assert (
            root / ".agents" / "skills" / "shipping" / "land-it" / "SKILL.md"
        ).is_file()
        assert (
            root / ".agents" / "skills" / "code-review" / "SKILL.md"
        ).is_file()

    def test_integration_cli_idempotent_skip_without_force(
        self, multi_agent_project: Path
    ) -> None:
        """Second convert without --force skips existing targets."""
        root = multi_agent_project
        import os

        old = os.getcwd()
        runner = CliRunner()
        try:
            os.chdir(root)
            first = runner.invoke(
                cli,
                [
                    "convert",
                    "-s", "cursor",
                    "-t", "copilot",
                    "--type", "skill",
                    "--force",
                ],
                catch_exceptions=False,
            )
            assert first.exit_code == 0, first.output

            second = runner.invoke(
                cli,
                [
                    "convert",
                    "-s", "cursor",
                    "-t", "copilot",
                    "--type", "skill",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old)

        assert second.exit_code == 0, second.output
        assert "force" in second.output.lower() or "skip" in second.output.lower()


################################################################################
#                                                                              #
# E2E: ROUND-TRIP AS-IS                                                        #
#                                                                              #
################################################################################


class TestE2ERoundTripAsIs:
    """Cursor → Codex → Cursor keeps skill body and nested path."""

    def test_integration_roundtrip_preserves_content(
        self, multi_agent_project: Path
    ) -> None:
        """Nested skill survives Cursor→Codex→Cursor without content drift."""
        root = multi_agent_project
        source = root / ".cursor" / "skills" / "shipping" / "land-it" / "SKILL.md"
        original = _read(source)

        run_conversion(
            root, "cursor", "codex", artifact_type="skill", force=True
        )
        # Remove Cursor nested skill so re-convert must rewrite it
        import shutil

        shutil.rmtree(root / ".cursor" / "skills" / "shipping")

        run_conversion(
            root, "codex", "cursor", artifact_type="skill", force=True
        )

        restored = root / ".cursor" / "skills" / "shipping" / "land-it" / "SKILL.md"
        assert restored.is_file()
        assert _read(restored) == original
        assert (
            root / ".cursor" / "skills" / "shipping" / "land-it" / "scripts"
            / "validate.sh"
        ).is_file()
