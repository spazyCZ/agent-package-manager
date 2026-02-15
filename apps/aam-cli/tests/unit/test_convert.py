"""Unit tests for the convert command and conversion service."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import pytest
from click.testing import CliRunner

from aam_cli.converters.frontmatter import generate_frontmatter, parse_frontmatter
from aam_cli.main import cli
from aam_cli.services.convert_service import (
    ConversionReport,
    ConversionResult,
    run_conversion,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _write_file(path: Path, content: str) -> None:
    """Write a file, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


################################################################################
#                                                                              #
# FRONTMATTER TESTS                                                            #
#                                                                              #
################################################################################


class TestParseFrontmatter:
    """Tests for YAML frontmatter parsing."""

    def test_parse_with_frontmatter(self) -> None:
        text = '---\ndescription: "test"\nalwaysApply: true\n---\n# Body\nContent here'
        meta, body = parse_frontmatter(text)
        assert meta["description"] == "test"
        assert meta["alwaysApply"] is True
        assert "# Body" in body
        assert "Content here" in body

    def test_parse_without_frontmatter(self) -> None:
        text = "# Just markdown\nNo frontmatter here."
        meta, body = parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_parse_with_list_field(self) -> None:
        text = '---\nglobs:\n  - "**/*.py"\n  - "**/*.pyi"\n---\nBody'
        meta, body = parse_frontmatter(text)
        assert meta["globs"] == ["**/*.py", "**/*.pyi"]
        assert body == "Body"

    def test_parse_empty_frontmatter(self) -> None:
        text = "---\n---\nBody content"
        meta, body = parse_frontmatter(text)
        assert meta == {}
        assert "Body content" in body

    def test_parse_invalid_yaml(self) -> None:
        text = "---\n: invalid: yaml: [[\n---\nBody"
        meta, body = parse_frontmatter(text)
        # Should return empty dict and original text on parse error
        assert meta == {}


class TestGenerateFrontmatter:
    """Tests for YAML frontmatter generation."""

    def test_generate_with_metadata(self) -> None:
        result = generate_frontmatter(
            {"name": "test", "description": "A test"},
            "# Body\nContent",
        )
        assert result.startswith("---\n")
        assert "name: test" in result
        assert "description: A test" in result
        assert result.endswith("# Body\nContent")

    def test_generate_without_metadata(self) -> None:
        result = generate_frontmatter({}, "# Body\nContent")
        assert result == "# Body\nContent"

    def test_roundtrip(self) -> None:
        original_meta = {"description": "test", "alwaysApply": False}
        original_body = "# Instructions\nDo things."
        text = generate_frontmatter(original_meta, original_body)
        parsed_meta, parsed_body = parse_frontmatter(text)
        assert parsed_meta["description"] == "test"
        assert parsed_meta["alwaysApply"] is False
        assert "# Instructions" in parsed_body


################################################################################
#                                                                              #
# CONVERSION SERVICE TESTS                                                     #
#                                                                              #
################################################################################


class TestConversionReport:
    """Tests for ConversionReport data model."""

    def test_counts(self) -> None:
        report = ConversionReport(
            source_platform="cursor",
            target_platform="copilot",
            results=[
                ConversionResult("a", "b", "instruction"),
                ConversionResult("c", "d", "instruction", warnings=["w1"]),
                ConversionResult("e", "f", "agent", error="failed"),
                ConversionResult("g", "h", "skill", skipped=True),
            ],
        )
        assert report.converted_count == 2
        assert report.failed_count == 1
        assert report.skipped_count == 1
        assert report.warning_count == 1


class TestInstructionConversion:
    """Tests for instruction file conversion."""

    def test_cursor_mdc_to_copilot_instructions(self, tmp_path: Path) -> None:
        """Cursor .mdc with globs → Copilot .instructions.md."""
        _write_file(
            tmp_path / ".cursor" / "rules" / "python-style.mdc",
            '---\ndescription: "Python coding standards"\nalwaysApply: false\n'
            'globs:\n  - "**/*.py"\n---\n# Python Standards\nUse type hints.',
        )

        report = run_conversion(tmp_path, "cursor", "copilot")

        assert report.converted_count == 1
        result = report.results[0]
        assert result.artifact_type == "instruction"
        assert ".github/instructions/python-style.instructions.md" in result.target_path

        # Check output file
        target = tmp_path / ".github" / "instructions" / "python-style.instructions.md"
        assert target.is_file()
        content = target.read_text()
        assert "applyTo" in content
        assert "**/*.py" in content
        assert "# Python Standards" in content

        # Should warn about alwaysApply dropped
        assert any("alwaysApply" in w for w in result.warnings)

    def test_cursor_mdc_always_apply_to_copilot(self, tmp_path: Path) -> None:
        """Cursor .mdc with alwaysApply=true → Copilot copilot-instructions.md."""
        _write_file(
            tmp_path / ".cursor" / "rules" / "general.mdc",
            '---\ndescription: "General rules"\nalwaysApply: true\n---\n'
            "Always follow these rules.",
        )

        report = run_conversion(tmp_path, "cursor", "copilot")

        assert report.converted_count == 1
        result = report.results[0]
        assert "copilot-instructions.md" in result.target_path

    def test_cursor_mdc_to_claude(self, tmp_path: Path) -> None:
        """Cursor .mdc → Claude CLAUDE.md (appended with markers)."""
        _write_file(
            tmp_path / ".cursor" / "rules" / "style.mdc",
            '---\nglobs:\n  - "**/*.py"\n---\nUse Black formatter.',
        )

        report = run_conversion(tmp_path, "cursor", "claude")

        assert report.converted_count == 1
        target = tmp_path / "CLAUDE.md"
        assert target.is_file()
        content = target.read_text()
        assert "<!-- BEGIN AAM CONVERTED: style -->" in content
        assert "<!-- END AAM CONVERTED: style -->" in content
        assert "Use Black formatter." in content

        # Should warn about globs lost
        result = report.results[0]
        assert any("globs" in w.lower() or "always-on" in w.lower() for w in result.warnings)

    def test_cursorrules_to_claude(self, tmp_path: Path) -> None:
        """Legacy .cursorrules → Claude CLAUDE.md."""
        _write_file(tmp_path / ".cursorrules", "Be helpful and concise.")

        report = run_conversion(tmp_path, "cursor", "claude")

        assert report.converted_count == 1
        target = tmp_path / "CLAUDE.md"
        assert target.is_file()
        assert "Be helpful and concise." in target.read_text()

    def test_copilot_instructions_to_cursor(self, tmp_path: Path) -> None:
        """Copilot .instructions.md with applyTo → Cursor .mdc."""
        _write_file(
            tmp_path / ".github" / "instructions" / "react.instructions.md",
            '---\napplyTo: "**/*.tsx"\n---\nUse functional components.',
        )

        report = run_conversion(tmp_path, "copilot", "cursor")

        assert report.converted_count == 1
        target = tmp_path / ".cursor" / "rules" / "react.mdc"
        assert target.is_file()
        content = target.read_text()
        meta, body = parse_frontmatter(content)
        assert meta["globs"] == ["**/*.tsx"]
        assert meta["alwaysApply"] is False
        assert "Use functional components." in body

    def test_copilot_main_to_codex(self, tmp_path: Path) -> None:
        """Copilot copilot-instructions.md → Codex AGENTS.md."""
        _write_file(
            tmp_path / ".github" / "copilot-instructions.md",
            "Follow coding standards.",
        )

        report = run_conversion(tmp_path, "copilot", "codex")

        assert report.converted_count == 1
        target = tmp_path / "AGENTS.md"
        assert target.is_file()
        assert "Follow coding standards." in target.read_text()

    def test_claude_to_codex(self, tmp_path: Path) -> None:
        """Claude CLAUDE.md → Codex AGENTS.md."""
        _write_file(tmp_path / "CLAUDE.md", "Always write tests.")

        report = run_conversion(tmp_path, "claude", "codex")

        assert report.converted_count == 1
        target = tmp_path / "AGENTS.md"
        assert target.is_file()
        assert "Always write tests." in target.read_text()

    def test_no_source_files(self, tmp_path: Path) -> None:
        """No source files → empty report."""
        report = run_conversion(tmp_path, "cursor", "copilot")
        assert report.converted_count == 0
        assert len(report.results) == 0


class TestAgentConversion:
    """Tests for agent file conversion."""

    def test_copilot_agent_to_cursor(self, tmp_path: Path) -> None:
        """Copilot .agent.md → Cursor subagent."""
        _write_file(
            tmp_path / ".github" / "agents" / "reviewer.agent.md",
            '---\ndescription: "Code review specialist"\n'
            'tools:\n  - "github/*"\n  - "terminal"\n'
            'model: "gpt-4o"\n---\nReview code for bugs.',
        )

        report = run_conversion(tmp_path, "copilot", "cursor")

        # Find agent result
        agent_results = [r for r in report.results if r.artifact_type == "agent"]
        assert len(agent_results) == 1
        result = agent_results[0]

        target = tmp_path / ".cursor" / "agents" / "reviewer.md"
        assert target.is_file()
        content = target.read_text()
        meta, body = parse_frontmatter(content)

        assert meta["name"] == "reviewer"
        assert meta["description"] == "Code review specialist"
        assert "Review code for bugs." in body

        # Should warn about tools and model
        assert any("tools" in w.lower() for w in result.warnings)

    def test_cursor_agent_to_claude(self, tmp_path: Path) -> None:
        """Cursor subagent → Claude subagent (drops unsupported fields)."""
        _write_file(
            tmp_path / ".cursor" / "agents" / "helper.md",
            '---\nname: helper\ndescription: "Helper subagent"\n'
            "model: fast\nreadonly: true\nis_background: true\n---\n"
            "Help with tasks.",
        )

        report = run_conversion(tmp_path, "cursor", "claude")

        agent_results = [r for r in report.results if r.artifact_type == "agent"]
        assert len(agent_results) == 1
        result = agent_results[0]

        target = tmp_path / ".claude" / "agents" / "helper.md"
        assert target.is_file()
        meta, body = parse_frontmatter(target.read_text())

        assert meta["name"] == "helper"
        assert meta["description"] == "Helper subagent"
        assert "model" not in meta
        assert "readonly" not in meta
        assert "is_background" not in meta

        # Check warnings
        assert any("model" in w.lower() for w in result.warnings)
        assert any("readonly" in w.lower() for w in result.warnings)
        assert any("is_background" in w.lower() for w in result.warnings)

    def test_agent_to_codex(self, tmp_path: Path) -> None:
        """Any agent → Codex appends to AGENTS.md."""
        _write_file(
            tmp_path / ".cursor" / "agents" / "tester.md",
            '---\nname: tester\ndescription: "Test agent"\n---\n'
            "Run all tests.",
        )

        report = run_conversion(tmp_path, "cursor", "codex")

        agent_results = [r for r in report.results if r.artifact_type == "agent"]
        assert len(agent_results) == 1

        target = tmp_path / "AGENTS.md"
        assert target.is_file()
        content = target.read_text()
        assert "## Agent: tester" in content
        assert "Run all tests." in content


class TestPromptConversion:
    """Tests for prompt file conversion."""

    def test_copilot_prompt_to_cursor(self, tmp_path: Path) -> None:
        """Copilot .prompt.md → Cursor command (drops frontmatter)."""
        _write_file(
            tmp_path / ".github" / "prompts" / "review.prompt.md",
            '---\ndescription: "Review changes"\nagent: "agent"\n'
            'model: "gpt-4o"\ntools:\n  - "terminal"\n---\n'
            "Review all staged changes.",
        )

        report = run_conversion(tmp_path, "copilot", "cursor")

        prompt_results = [r for r in report.results if r.artifact_type == "prompt"]
        assert len(prompt_results) == 1
        result = prompt_results[0]

        target = tmp_path / ".cursor" / "commands" / "review.md"
        assert target.is_file()
        content = target.read_text()

        # Should be plain markdown (no frontmatter)
        assert not content.startswith("---")
        assert "Review all staged changes." in content

        # Should warn about dropped fields
        assert any("agent" in w.lower() for w in result.warnings)
        assert any("model" in w.lower() for w in result.warnings)
        assert any("tools" in w.lower() for w in result.warnings)

    def test_cursor_prompt_to_copilot(self, tmp_path: Path) -> None:
        """Cursor prompt → Copilot .prompt.md (adds extension)."""
        _write_file(
            tmp_path / ".cursor" / "commands" / "deploy.md",
            "Deploy the application to production.",
        )

        report = run_conversion(tmp_path, "cursor", "copilot")

        prompt_results = [r for r in report.results if r.artifact_type == "prompt"]
        assert len(prompt_results) == 1

        target = tmp_path / ".github" / "prompts" / "deploy.prompt.md"
        assert target.is_file()

    def test_prompt_to_codex(self, tmp_path: Path) -> None:
        """Prompt → Codex appends to AGENTS.md."""
        _write_file(
            tmp_path / ".cursor" / "prompts" / "test.md",
            "Run all unit tests.",
        )

        report = run_conversion(tmp_path, "cursor", "codex")

        prompt_results = [r for r in report.results if r.artifact_type == "prompt"]
        assert len(prompt_results) == 1

        target = tmp_path / "AGENTS.md"
        assert target.is_file()
        assert "## Prompt: test" in target.read_text()

    def test_cursor_prompt_to_claude(self, tmp_path: Path) -> None:
        """Cursor prompt → Claude prompt (direct copy)."""
        _write_file(
            tmp_path / ".cursor" / "prompts" / "review.md",
            "Review the code changes.",
        )

        report = run_conversion(tmp_path, "cursor", "claude")

        prompt_results = [r for r in report.results if r.artifact_type == "prompt"]
        assert len(prompt_results) == 1

        target = tmp_path / ".claude" / "prompts" / "review.md"
        assert target.is_file()
        assert "Review the code changes." in target.read_text()


class TestSkillConversion:
    """Tests for skill directory conversion."""

    def test_cursor_skill_to_copilot(self, tmp_path: Path) -> None:
        """Cursor skill → Copilot skill (direct copy)."""
        skill_dir = tmp_path / ".cursor" / "skills" / "code-review"
        _write_file(skill_dir / "SKILL.md", "# Code Review Skill")
        _write_file(skill_dir / "config.yaml", "timeout: 30")

        report = run_conversion(tmp_path, "cursor", "copilot")

        skill_results = [r for r in report.results if r.artifact_type == "skill"]
        assert len(skill_results) == 1
        result = skill_results[0]
        assert "direct copy" in result.target_path

        target = tmp_path / ".github" / "skills" / "code-review"
        assert target.is_dir()
        assert (target / "SKILL.md").is_file()
        assert (target / "config.yaml").is_file()


class TestConflictHandling:
    """Tests for conflict resolution behavior."""

    def test_skip_existing_without_force(self, tmp_path: Path) -> None:
        """Target exists + no --force → skip with warning."""
        _write_file(
            tmp_path / ".cursor" / "agents" / "helper.md",
            '---\nname: helper\n---\nOriginal.',
        )
        # Pre-create target
        _write_file(
            tmp_path / ".claude" / "agents" / "helper.md",
            "Existing content.",
        )

        report = run_conversion(tmp_path, "cursor", "claude", force=False)

        agent_results = [r for r in report.results if r.artifact_type == "agent"]
        assert len(agent_results) == 1
        assert agent_results[0].skipped is True
        assert any("force" in w.lower() for w in agent_results[0].warnings)

        # Original content preserved
        assert "Existing content." in (
            tmp_path / ".claude" / "agents" / "helper.md"
        ).read_text()

    def test_overwrite_with_force(self, tmp_path: Path) -> None:
        """Target exists + --force → overwrite with .bak backup."""
        _write_file(
            tmp_path / ".cursor" / "agents" / "helper.md",
            '---\nname: helper\n---\nNew content.',
        )
        target = tmp_path / ".claude" / "agents" / "helper.md"
        _write_file(target, "Old content.")

        report = run_conversion(tmp_path, "cursor", "claude", force=True)

        agent_results = [r for r in report.results if r.artifact_type == "agent"]
        assert len(agent_results) == 1
        assert not agent_results[0].skipped

        # Backup created
        assert (tmp_path / ".claude" / "agents" / "helper.md.bak").is_file()
        assert "Old content." in (
            tmp_path / ".claude" / "agents" / "helper.md.bak"
        ).read_text()

        # New content written
        assert "New content." in target.read_text()

    def test_same_platform_error(self) -> None:
        """Same source and target → error."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["convert", "-s", "cursor", "-t", "cursor"],
            catch_exceptions=False,
        )
        assert "cannot be the same" in result.output


class TestDryRun:
    """Tests for dry-run mode."""

    def test_dry_run_no_files_written(self, tmp_path: Path) -> None:
        """Dry run should not create any files."""
        _write_file(
            tmp_path / ".cursor" / "rules" / "test.mdc",
            '---\ndescription: "Test"\nalwaysApply: true\n---\nTest content.',
        )

        report = run_conversion(
            tmp_path, "cursor", "copilot", dry_run=True
        )

        assert report.converted_count == 1

        # No target files created
        assert not (tmp_path / ".github").exists()


class TestTypeFilter:
    """Tests for --type filtering."""

    def test_filter_by_type(self, tmp_path: Path) -> None:
        """Only convert artifacts of the specified type."""
        _write_file(
            tmp_path / ".cursor" / "rules" / "style.mdc",
            '---\nalwaysApply: true\n---\nStyle rules.',
        )
        _write_file(
            tmp_path / ".cursor" / "agents" / "helper.md",
            '---\nname: helper\n---\nHelp.',
        )

        # Only convert instructions
        report = run_conversion(
            tmp_path, "cursor", "copilot", artifact_type="instruction"
        )

        assert report.converted_count == 1
        assert all(r.artifact_type == "instruction" for r in report.results)


class TestCLICommand:
    """Tests for the Click CLI command."""

    def test_convert_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["convert", "--help"])
        assert result.exit_code == 0
        assert "--source-platform" in result.output
        assert "--target-platform" in result.output
        assert "--dry-run" in result.output
        assert "--force" in result.output

    def test_convert_dry_run_output(self, tmp_path: Path) -> None:
        """CLI dry-run shows [DRY RUN] prefix."""
        _write_file(
            tmp_path / ".cursor" / "rules" / "test.mdc",
            '---\nalwaysApply: true\n---\nTest.',
        )

        runner = CliRunner()
        import os
        with runner.isolated_filesystem(temp_dir=tmp_path):
            os.chdir(tmp_path)
            result = runner.invoke(
                cli,
                ["convert", "-s", "cursor", "-t", "copilot", "--dry-run"],
                catch_exceptions=False,
            )
        assert "DRY RUN" in result.output

    def test_convert_no_artifacts_found(self, tmp_path: Path) -> None:
        """CLI shows message when no artifacts found."""
        runner = CliRunner()
        import os
        with runner.isolated_filesystem(temp_dir=tmp_path):
            os.chdir(tmp_path)
            result = runner.invoke(
                cli,
                ["convert", "-s", "cursor", "-t", "copilot"],
                catch_exceptions=False,
            )
        assert "No cursor artifacts found" in result.output
