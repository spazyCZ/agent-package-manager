"""Unit tests for remote scanning (scan_directory) and vendor agent detection.

Tests the extended scanner's ability to handle dot-prefixed directories,
vendor agent YAML files, and the openai/skills repository layout.

Reference: tasks.md T022.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import pytest

from aam_cli.detection.scanner import scan_directory

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


@pytest.fixture
def openai_skills_layout(tmp_path: Path) -> Path:
    """Create a directory structure mimicking the openai/skills repo.

    Structure:
      skills/
        .curated/
          gh-fix-ci/
            SKILL.md
            agents/
              openai.yaml
          playwright/
            SKILL.md
        .experimental/
          beta-tool/
            SKILL.md
        .system/
          core-skill/
            SKILL.md
      agents/
        standalone.yaml
      prompts/
        my-prompt.md
      AGENTS.md
    """
    root = tmp_path / "repo"
    root.mkdir()

    # -----
    # .curated skills with vendor agents
    # -----
    curated = root / "skills" / ".curated"

    gh_fix = curated / "gh-fix-ci"
    gh_fix.mkdir(parents=True)
    (gh_fix / "SKILL.md").write_text("# Fix CI\nA skill to fix CI pipelines.")
    agents_dir = gh_fix / "agents"
    agents_dir.mkdir()
    (agents_dir / "openai.yaml").write_text("name: openai-agent\n")

    playwright = curated / "playwright"
    playwright.mkdir(parents=True)
    (playwright / "SKILL.md").write_text("# Playwright\nBrowser testing skill.")

    # -----
    # .experimental skills
    # -----
    beta = root / "skills" / ".experimental" / "beta-tool"
    beta.mkdir(parents=True)
    (beta / "SKILL.md").write_text("# Beta Tool\nExperimental tool.")

    # -----
    # .system skills
    # -----
    core = root / "skills" / ".system" / "core-skill"
    core.mkdir(parents=True)
    (core / "SKILL.md").write_text("# Core Skill\nSystem-level skill.")

    # -----
    # Standalone agent (no SKILL.md in parent)
    # -----
    standalone_agents = root / "agents"
    standalone_agents.mkdir()
    (standalone_agents / "standalone.yaml").write_text("name: standalone\n")

    # -----
    # Prompts
    # -----
    prompts = root / "prompts"
    prompts.mkdir()
    (prompts / "my-prompt.md").write_text("# My Prompt\nContent here.")

    # -----
    # Root-level instruction
    # -----
    (root / "AGENTS.md").write_text("# Agents\nAgent instructions.")

    return root


@pytest.fixture
def simple_layout(tmp_path: Path) -> Path:
    """Create a simple directory with mixed artifact types."""
    root = tmp_path / "simple"
    root.mkdir()

    # Simple skill
    skill_dir = root / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# My Skill\nA simple test skill.")

    # Simple agent
    agent_dir = root / "my-agent"
    agent_dir.mkdir()
    (agent_dir / "agent.yaml").write_text("name: my-agent\n")

    return root


################################################################################
#                                                                              #
# DOT-PREFIXED DIRECTORY TESTS                                                 #
#                                                                              #
################################################################################


class TestDotPrefixedDirectories:
    """Tests for scanning directories with dot-prefixed names."""

    def test_unit_scans_dot_curated(self, openai_skills_layout: Path) -> None:
        """Scanner finds skills in .curated/ directories."""
        result = scan_directory(openai_skills_layout, scan_scope="skills/.curated")

        skill_names = {a.name for a in result if a.type == "skill"}
        assert "gh-fix-ci" in skill_names
        assert "playwright" in skill_names

    def test_unit_scans_dot_experimental(self, openai_skills_layout: Path) -> None:
        """Scanner finds skills in .experimental/ directories."""
        result = scan_directory(openai_skills_layout, scan_scope="skills/.experimental")

        skill_names = {a.name for a in result if a.type == "skill"}
        assert "beta-tool" in skill_names

    def test_unit_scans_dot_system(self, openai_skills_layout: Path) -> None:
        """Scanner finds skills in .system/ directories."""
        result = scan_directory(openai_skills_layout, scan_scope="skills/.system")

        skill_names = {a.name for a in result if a.type == "skill"}
        assert "core-skill" in skill_names

    def test_unit_full_scan_finds_all_skills(self, openai_skills_layout: Path) -> None:
        """Full repo scan finds skills across all dot-prefixed directories."""
        result = scan_directory(openai_skills_layout)

        skill_names = {a.name for a in result if a.type == "skill"}
        assert "gh-fix-ci" in skill_names
        assert "playwright" in skill_names
        assert "beta-tool" in skill_names
        assert "core-skill" in skill_names


################################################################################
#                                                                              #
# VENDOR AGENT DETECTION TESTS                                                 #
#                                                                              #
################################################################################


class TestVendorAgentDetection:
    """Tests for vendor agent YAML file detection heuristic."""

    def test_unit_companion_agent_not_standalone(
        self, openai_skills_layout: Path
    ) -> None:
        """Agents in a skill dir (with SKILL.md) are NOT detected as standalone."""
        result = scan_directory(openai_skills_layout, scan_scope="skills/.curated")

        # -----
        # The openai.yaml inside gh-fix-ci/agents/ should NOT appear as
        # a standalone agent because gh-fix-ci has SKILL.md
        # -----
        standalone_agents = [
            a for a in result
            if a.type == "agent" and a.source_dir == "vendor"
        ]
        assert len(standalone_agents) == 0

    def test_unit_standalone_agent_detected(
        self, openai_skills_layout: Path
    ) -> None:
        """Agents in a directory WITHOUT SKILL.md are standalone agents."""
        result = scan_directory(openai_skills_layout)

        standalone_agents = [
            a for a in result
            if a.type == "agent" and a.name == "standalone"
        ]
        assert len(standalone_agents) == 1
        assert standalone_agents[0].source_dir == "vendor"


################################################################################
#                                                                              #
# SCAN SCOPE TESTS                                                             #
#                                                                              #
################################################################################


class TestScanScope:
    """Tests for scan_scope filtering."""

    def test_unit_scope_limits_results(self, openai_skills_layout: Path) -> None:
        """Scan with scope only returns artifacts from that subtree."""
        result = scan_directory(openai_skills_layout, scan_scope="skills/.curated")

        # Only curated skills should be found
        assert len([a for a in result if a.type == "skill"]) == 2

    def test_unit_nonexistent_scope_returns_empty(
        self, openai_skills_layout: Path
    ) -> None:
        """Non-existent scope returns empty list."""
        result = scan_directory(openai_skills_layout, scan_scope="nonexistent/path")
        assert len(result) == 0


################################################################################
#                                                                              #
# EXCLUSION TESTS                                                              #
#                                                                              #
################################################################################


class TestExclusion:
    """Tests for directory exclusion."""

    def test_unit_custom_exclusions(self, simple_layout: Path) -> None:
        """Custom exclude_dirs are honored."""
        # Exclude the skill directory name
        result = scan_directory(simple_layout, exclude_dirs={"my-skill"})

        skill_names = {a.name for a in result if a.type == "skill"}
        assert "my-skill" not in skill_names

    def test_unit_default_exclusions(self, tmp_path: Path) -> None:
        """Default exclusions (.git, node_modules, etc.) are applied."""
        root = tmp_path / "test"
        root.mkdir()

        # Create a skill inside node_modules (should be excluded)
        nm_skill = root / "node_modules" / "pkg" / "skill"
        nm_skill.mkdir(parents=True)
        (nm_skill / "SKILL.md").write_text("# Hidden\nShould be excluded.")

        result = scan_directory(root)

        assert len([a for a in result if a.name == "skill"]) == 0


################################################################################
#                                                                              #
# DESCRIPTION EXTRACTION TESTS                                                 #
#                                                                              #
################################################################################


class TestDescriptionExtraction:
    """Tests for SKILL.md first-line description extraction."""

    def test_unit_extracts_first_line_after_heading(
        self, openai_skills_layout: Path
    ) -> None:
        """Description is extracted from first non-empty, non-heading line."""
        result = scan_directory(openai_skills_layout, scan_scope="skills/.curated")

        gh_fix = next(a for a in result if a.name == "gh-fix-ci")
        # First line is "# Fix CI", so description should be "Fix CI"
        assert gh_fix.description is not None
        assert "Fix CI" in gh_fix.description


################################################################################
#                                                                              #
# MIXED ARTIFACT TYPE TESTS                                                    #
#                                                                              #
################################################################################


class TestMixedArtifacts:
    """Tests for detecting multiple artifact types in one scan."""

    def test_unit_finds_prompts(self, openai_skills_layout: Path) -> None:
        """Scanner detects prompt files in prompts/ directories."""
        result = scan_directory(openai_skills_layout)

        prompts = [a for a in result if a.type == "prompt"]
        assert len(prompts) >= 1
        assert any(a.name == "my-prompt" for a in prompts)

    def test_unit_finds_instructions(self, openai_skills_layout: Path) -> None:
        """Scanner detects root-level instruction files."""
        result = scan_directory(openai_skills_layout)

        instructions = [a for a in result if a.type == "instruction"]
        assert any(a.name == "codex-instructions" for a in instructions)

    def test_unit_simple_skill_and_agent(self, simple_layout: Path) -> None:
        """Scanner finds both skills and agents in simple layout."""
        result = scan_directory(simple_layout)

        types = {a.type for a in result}
        assert "skill" in types
        assert "agent" in types
