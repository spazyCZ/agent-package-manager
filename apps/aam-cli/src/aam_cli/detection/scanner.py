"""Artifact auto-detection scanner.

Scans a project directory for skills, agents, prompts, and instructions
across multiple platform conventions (Cursor, Codex, Copilot, Claude).

Detection patterns from R-009 in research.md and DESIGN.md Section 5.2.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

from pydantic import BaseModel

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

# Directories excluded from scanning
EXCLUDED_DIRS: set[str] = {
    ".aam",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".tox",
    ".nox",
    ".eggs",
}

################################################################################
#                                                                              #
# DATA MODEL                                                                   #
#                                                                              #
################################################################################


class DetectedArtifact(BaseModel):
    """An artifact found during project scanning."""

    name: str  # Derived artifact name
    type: str  # skill, agent, prompt, instruction
    source_path: Path  # Relative path from project root
    platform: str | None = None  # cursor, codex, copilot, claude, or None
    description: str = ""

    class Config:
        """Pydantic config to allow arbitrary Path types."""

        arbitrary_types_allowed = True


################################################################################
#                                                                              #
# HELPER FUNCTIONS                                                             #
#                                                                              #
################################################################################


def _should_skip(rel_path: Path) -> bool:
    """Return True if the path contains an excluded directory component."""
    return any(part in EXCLUDED_DIRS for part in rel_path.parts)


def _in_aam_packages(rel_path: Path) -> bool:
    """Return True if the path is inside .aam/packages/ (installed pkgs)."""
    parts = rel_path.parts
    return len(parts) >= 2 and parts[0] == ".aam" and parts[1] == "packages"


################################################################################
#                                                                              #
# DETECTION FUNCTIONS                                                          #
#                                                                              #
################################################################################


def _detect_skills(root: Path) -> list[DetectedArtifact]:
    """Detect skill artifacts by looking for SKILL.md files.

    Patterns:
      - ``**/SKILL.md`` (any location — parent dir is the skill)
      - ``.cursor/skills/*/SKILL.md`` (Cursor convention)
      - ``.codex/skills/*/SKILL.md`` (Codex convention)
    """
    artifacts: list[DetectedArtifact] = []

    for skill_md in root.rglob("SKILL.md"):
        rel = skill_md.relative_to(root)
        if _should_skip(rel) or _in_aam_packages(rel):
            continue

        skill_dir = skill_md.parent
        name = skill_dir.name
        rel_dir = skill_dir.relative_to(root)

        # -----
        # Determine platform from path
        # -----
        platform: str | None = None
        str_path = str(rel)
        if str_path.startswith(".cursor/skills/"):
            platform = "cursor"
        elif str_path.startswith(".codex/skills/"):
            platform = "codex"

        artifacts.append(
            DetectedArtifact(
                name=name,
                type="skill",
                source_path=rel_dir,
                platform=platform,
                description=f"Skill at {rel_dir}",
            )
        )

    return artifacts


def _detect_agents(root: Path) -> list[DetectedArtifact]:
    """Detect agent artifacts.

    Patterns:
      - ``**/agent.yaml`` (AAM convention)
      - ``.cursor/rules/agent-*.mdc`` (Cursor convention)
    """
    artifacts: list[DetectedArtifact] = []

    # -----
    # Pattern 1: agent.yaml files
    # -----
    for agent_yaml in root.rglob("agent.yaml"):
        rel = agent_yaml.relative_to(root)
        if _should_skip(rel) or _in_aam_packages(rel):
            continue

        agent_dir = agent_yaml.parent
        name = agent_dir.name
        rel_dir = agent_dir.relative_to(root)

        artifacts.append(
            DetectedArtifact(
                name=name,
                type="agent",
                source_path=rel_dir,
                platform=None,
                description=f"Agent at {rel_dir}",
            )
        )

    # -----
    # Pattern 2: .cursor/rules/agent-*.mdc
    # -----
    cursor_rules_dir = root / ".cursor" / "rules"
    if cursor_rules_dir.is_dir():
        for mdc_file in cursor_rules_dir.glob("agent-*.mdc"):
            rel = mdc_file.relative_to(root)
            if _in_aam_packages(rel):
                continue

            name = mdc_file.stem.removeprefix("agent-")
            artifacts.append(
                DetectedArtifact(
                    name=name,
                    type="agent",
                    source_path=rel,
                    platform="cursor",
                    description=f"Cursor agent rule at {rel}",
                )
            )

    return artifacts


def _detect_prompts(root: Path) -> list[DetectedArtifact]:
    """Detect prompt artifacts.

    Patterns:
      - ``prompts/*.md`` (AAM convention)
      - ``.cursor/prompts/*.md`` (Cursor convention)
      - ``.github/prompts/*.md`` (Copilot convention)
    """
    artifacts: list[DetectedArtifact] = []

    prompt_dirs: list[tuple[Path, str | None]] = [
        (root / "prompts", None),
        (root / ".cursor" / "prompts", "cursor"),
        (root / ".github" / "prompts", "copilot"),
    ]

    for prompt_dir, platform in prompt_dirs:
        if not prompt_dir.is_dir():
            continue
        for md_file in prompt_dir.glob("*.md"):
            rel = md_file.relative_to(root)
            if _in_aam_packages(rel):
                continue
            artifacts.append(
                DetectedArtifact(
                    name=md_file.stem,
                    type="prompt",
                    source_path=rel,
                    platform=platform,
                    description=f"Prompt at {rel}",
                )
            )

    return artifacts


def _detect_instructions(root: Path) -> list[DetectedArtifact]:
    """Detect instruction artifacts.

    Patterns:
      - ``instructions/*.md`` (AAM convention)
      - ``.cursor/rules/*.mdc`` non-agent (Cursor convention)
      - ``CLAUDE.md`` (Claude convention)
      - ``AGENTS.md`` (Codex convention)
      - ``.github/copilot-instructions.md`` (Copilot convention)
    """
    artifacts: list[DetectedArtifact] = []

    # -----
    # Pattern 1: instructions/*.md
    # -----
    instructions_dir = root / "instructions"
    if instructions_dir.is_dir():
        for md_file in instructions_dir.glob("*.md"):
            rel = md_file.relative_to(root)
            artifacts.append(
                DetectedArtifact(
                    name=md_file.stem,
                    type="instruction",
                    source_path=rel,
                    platform=None,
                    description=f"Instruction at {rel}",
                )
            )

    # -----
    # Pattern 2: .cursor/rules/*.mdc (non-agent)
    # -----
    cursor_rules_dir = root / ".cursor" / "rules"
    if cursor_rules_dir.is_dir():
        for mdc_file in cursor_rules_dir.glob("*.mdc"):
            if mdc_file.name.startswith("agent-"):
                continue  # Handled by _detect_agents
            rel = mdc_file.relative_to(root)
            if _in_aam_packages(rel):
                continue
            artifacts.append(
                DetectedArtifact(
                    name=mdc_file.stem,
                    type="instruction",
                    source_path=rel,
                    platform="cursor",
                    description=f"Cursor rule at {rel}",
                )
            )

    # -----
    # Pattern 3: Standalone instruction files
    # -----
    standalone: list[tuple[str, str, str]] = [
        ("CLAUDE.md", "claude-instructions", "claude"),
        ("AGENTS.md", "codex-instructions", "codex"),
        (".github/copilot-instructions.md", "copilot-instructions", "copilot"),
    ]

    for file_rel, name, platform in standalone:
        filepath = root / file_rel
        if filepath.is_file():
            artifacts.append(
                DetectedArtifact(
                    name=name,
                    type="instruction",
                    source_path=Path(file_rel),
                    platform=platform,
                    description=f"Platform instruction at {file_rel}",
                )
            )

    return artifacts


################################################################################
#                                                                              #
# PUBLIC API                                                                   #
#                                                                              #
################################################################################


def scan_project(root: Path) -> list[DetectedArtifact]:
    """Scan a project directory for all detectable artifacts.

    Args:
        root: Project root directory to scan.

    Returns:
        List of :class:`DetectedArtifact` instances found in the project.
    """
    logger.info(f"Scanning project for artifacts: root='{root}'")

    if not root.is_dir():
        logger.warning(f"Project root is not a directory: {root}")
        return []

    artifacts: list[DetectedArtifact] = []
    artifacts.extend(_detect_skills(root))
    artifacts.extend(_detect_agents(root))
    artifacts.extend(_detect_prompts(root))
    artifacts.extend(_detect_instructions(root))

    logger.info(
        f"Scan complete: found {len(artifacts)} artifacts "
        f"(skills={sum(1 for a in artifacts if a.type == 'skill')}, "
        f"agents={sum(1 for a in artifacts if a.type == 'agent')}, "
        f"prompts={sum(1 for a in artifacts if a.type == 'prompt')}, "
        f"instructions={sum(1 for a in artifacts if a.type == 'instruction')})"
    )

    return artifacts
