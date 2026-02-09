"""Artifact auto-detection scanner.

Scans a project directory for skills, agents, prompts, and instructions
across multiple platform conventions (Cursor, Codex, Copilot, Claude).

Detection patterns from R-009 in research.md and DESIGN.md Section 5.2.

Supported source directories and their mappings:

    .cursor/
        skills/*/SKILL.md        -> skill  (platform=cursor)
        rules/agent-*.mdc        -> agent  (platform=cursor)
        rules/*.mdc              -> instruction (platform=cursor)
        prompts/*.md             -> prompt (platform=cursor)
        commands/*.md            -> prompt (platform=cursor)

    .github/
        prompts/*.md             -> prompt (platform=copilot)
        copilot-instructions.md  -> instruction (platform=copilot)

    .codex/
        skills/*/SKILL.md        -> skill  (platform=codex)

    Root-level:
        CLAUDE.md                -> instruction (platform=claude)
        AGENTS.md                -> instruction (platform=codex)
        **/SKILL.md              -> skill  (platform=None)
        **/agent.yaml            -> agent  (platform=None)
        prompts/*.md             -> prompt (platform=None)
        instructions/*.md        -> instruction (platform=None)
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict

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

# All recognised platform identifiers (used for validation & filtering)
KNOWN_PLATFORMS: set[str] = {"cursor", "codex", "copilot", "claude"}

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
    # The source directory where the artifact was found (e.g. ".cursor", ".github")
    source_dir: str = ""

    model_config = ConfigDict(arbitrary_types_allowed=True)


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
        # Determine platform and source directory from path
        # -----
        platform: str | None = None
        source_dir = ""
        str_path = str(rel)
        if str_path.startswith(".cursor/skills/") or str_path.startswith(".cursor/"):
            platform = "cursor"
            source_dir = ".cursor"
        elif str_path.startswith(".codex/skills/") or str_path.startswith(".codex/"):
            platform = "codex"
            source_dir = ".codex"

        artifacts.append(
            DetectedArtifact(
                name=name,
                type="skill",
                source_path=rel_dir,
                platform=platform,
                source_dir=source_dir,
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

        # Determine source directory
        source_dir = ""
        str_path = str(rel)
        if str_path.startswith(".cursor/"):
            source_dir = ".cursor"
        elif str_path.startswith(".github/"):
            source_dir = ".github"

        artifacts.append(
            DetectedArtifact(
                name=name,
                type="agent",
                source_path=rel_dir,
                platform=None,
                source_dir=source_dir,
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
                    source_dir=".cursor",
                    description=f"Cursor agent rule at {rel}",
                )
            )

    return artifacts


def _detect_prompts(root: Path) -> list[DetectedArtifact]:
    """Detect prompt artifacts.

    Patterns:
      - ``prompts/*.md`` (AAM convention)
      - ``.cursor/prompts/*.md`` (Cursor convention)
      - ``.cursor/commands/*.md`` (Cursor command prompts)
      - ``.github/prompts/*.md`` (Copilot convention)
    """
    artifacts: list[DetectedArtifact] = []

    # -----
    # Standard prompt directories with platform mapping
    # (directory_path, platform, source_dir)
    # -----
    prompt_dirs: list[tuple[Path, str | None, str]] = [
        (root / "prompts", None, ""),
        (root / ".cursor" / "prompts", "cursor", ".cursor"),
        (root / ".cursor" / "commands", "cursor", ".cursor"),
        (root / ".github" / "prompts", "copilot", ".github"),
    ]

    for prompt_dir, platform, source_dir in prompt_dirs:
        if not prompt_dir.is_dir():
            continue
        for md_file in prompt_dir.glob("*.md"):
            rel = md_file.relative_to(root)
            if _in_aam_packages(rel):
                continue

            # -----
            # Derive a clean name from the filename
            # Strip common prompt file suffixes like ".prompt.md" -> stem
            # -----
            name = md_file.stem
            if name.endswith(".prompt"):
                name = name.removesuffix(".prompt")

            # Determine description based on source
            if source_dir == ".cursor" and "commands" in str(rel):
                desc = f"Cursor command prompt at {rel}"
            else:
                desc = f"Prompt at {rel}"

            artifacts.append(
                DetectedArtifact(
                    name=name,
                    type="prompt",
                    source_path=rel,
                    platform=platform,
                    source_dir=source_dir,
                    description=desc,
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
                    source_dir="",
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
                    source_dir=".cursor",
                    description=f"Cursor rule at {rel}",
                )
            )

    # -----
    # Pattern 3: Standalone instruction files
    # (file_rel, artifact_name, platform, source_dir)
    # -----
    standalone: list[tuple[str, str, str, str]] = [
        ("CLAUDE.md", "claude-instructions", "claude", ""),
        ("AGENTS.md", "codex-instructions", "codex", ""),
        (".github/copilot-instructions.md", "copilot-instructions", "copilot", ".github"),
    ]

    for file_rel, name, platform, source_dir in standalone:
        filepath = root / file_rel
        if filepath.is_file():
            artifacts.append(
                DetectedArtifact(
                    name=name,
                    type="instruction",
                    source_path=Path(file_rel),
                    platform=platform,
                    source_dir=source_dir,
                    description=f"Platform instruction at {file_rel}",
                )
            )

    return artifacts


################################################################################
#                                                                              #
# VENDOR AGENT DETECTION                                                       #
#                                                                              #
################################################################################


def _detect_vendor_agents(root: Path) -> list[DetectedArtifact]:
    """Detect vendor agent YAML files in scanned directories.

    Heuristic:
      - If a directory has ``SKILL.md`` AND ``agents/*.yaml``, the YAML
        files are treated as companion metadata (not standalone agents).
      - If ``agents/*.yaml`` exists WITHOUT ``SKILL.md`` in the parent,
        they are treated as standalone agents.

    Args:
        root: Root directory to scan.

    Returns:
        List of standalone vendor agent artifacts.
    """
    artifacts: list[DetectedArtifact] = []

    for agents_dir in root.rglob("agents"):
        if not agents_dir.is_dir():
            continue

        rel = agents_dir.relative_to(root)
        if _should_skip(rel) or _in_aam_packages(rel):
            continue

        parent = agents_dir.parent
        has_skill_md = (parent / "SKILL.md").is_file()

        for yaml_file in agents_dir.glob("*.yaml"):
            yaml_rel = yaml_file.relative_to(root)

            if has_skill_md:
                # -----
                # Companion agent — attached to a skill, skip as standalone
                # -----
                logger.debug(
                    f"Vendor agent is skill companion, skipping: {yaml_rel}"
                )
                continue

            # -----
            # Standalone vendor agent
            # -----
            name = yaml_file.stem
            artifacts.append(
                DetectedArtifact(
                    name=name,
                    type="agent",
                    source_path=yaml_rel,
                    platform=None,
                    source_dir="vendor",
                    description=f"Vendor agent at {yaml_rel}",
                )
            )

    return artifacts


################################################################################
#                                                                              #
# PUBLIC API                                                                   #
#                                                                              #
################################################################################


def scan_directory(
    root: Path,
    scan_scope: str = "",
    exclude_dirs: set[str] | None = None,
) -> list[DetectedArtifact]:
    """Scan a directory for artifacts (generalized for remote sources).

    Unlike :func:`scan_project`, this function:
      - Handles dot-prefixed directories (e.g., ``.curated/``,
        ``.experimental/``, ``.system/``) commonly found in curated
        skill repositories.
      - Supports a ``scan_scope`` subdirectory filter.
      - Detects vendor agent YAML files.

    Args:
        root: Root directory to scan.
        scan_scope: Subdirectory within root to constrain the scan.
            Pass empty string to scan the entire directory.
        exclude_dirs: Additional directory names to exclude from scan.
            Merged with :data:`EXCLUDED_DIRS`.

    Returns:
        List of :class:`DetectedArtifact` instances.
    """
    logger.info(
        f"Scanning directory for artifacts: root='{root}', "
        f"scope='{scan_scope}'"
    )

    # -----
    # Resolve scan root (apply scope if given)
    # -----
    scan_root = root / scan_scope if scan_scope else root

    if not scan_root.is_dir():
        logger.warning(f"Scan root is not a directory: {scan_root}")
        return []

    # -----
    # Build exclusion set
    # -----
    exclusions = set(EXCLUDED_DIRS)
    if exclude_dirs:
        exclusions.update(exclude_dirs)

    artifacts: list[DetectedArtifact] = []

    # -----
    # Walk directory tree manually to handle dot-prefixed directories
    # (os.walk and Path.rglob handle dots, but we need custom exclusion)
    # -----
    import os

    for dirpath_str, dirnames, filenames in os.walk(scan_root):
        dirpath = Path(dirpath_str)

        # -----
        # Prune excluded directories (modifying dirnames in-place)
        # -----
        dirnames[:] = [
            d for d in dirnames
            if d not in exclusions
        ]

        # -----
        # Check for SKILL.md -> skill artifact
        # -----
        if "SKILL.md" in filenames:
            skill_name = dirpath.name
            skill_rel = dirpath.relative_to(scan_root)

            # Determine platform from path
            platform: str | None = None
            source_dir = ""
            path_str = str(skill_rel)
            if path_str.startswith(".cursor"):
                platform = "cursor"
                source_dir = ".cursor"
            elif path_str.startswith(".codex"):
                platform = "codex"
                source_dir = ".codex"

            # -----
            # Extract description from first line of SKILL.md
            # -----
            description = f"Skill at {skill_rel}"
            skill_md = dirpath / "SKILL.md"
            if skill_md.is_file():
                desc = _extract_first_line(skill_md)
                if desc:
                    description = desc

            artifacts.append(
                DetectedArtifact(
                    name=skill_name,
                    type="skill",
                    source_path=skill_rel,
                    platform=platform,
                    source_dir=source_dir,
                    description=description,
                )
            )

        # -----
        # Check for agent.yaml -> agent artifact
        # -----
        if "agent.yaml" in filenames:
            agent_name = dirpath.name
            agent_rel = dirpath.relative_to(scan_root)

            # Determine source directory
            source_dir = ""
            path_str = str(agent_rel)
            if path_str.startswith(".cursor"):
                source_dir = ".cursor"
            elif path_str.startswith(".github"):
                source_dir = ".github"

            artifacts.append(
                DetectedArtifact(
                    name=agent_name,
                    type="agent",
                    source_path=agent_rel,
                    platform=None,
                    source_dir=source_dir,
                    description=f"Agent at {agent_rel}",
                )
            )

        # -----
        # Check for standalone vendor agent YAMLs in agents/ dirs
        # -----
        if dirpath.name == "agents":
            parent = dirpath.parent
            has_skill_md = (parent / "SKILL.md").is_file()
            if not has_skill_md:
                for fname in filenames:
                    if fname.endswith(".yaml"):
                        yaml_rel = dirpath.relative_to(scan_root) / fname
                        agent_name = Path(fname).stem
                        artifacts.append(
                            DetectedArtifact(
                                name=agent_name,
                                type="agent",
                                source_path=yaml_rel,
                                platform=None,
                                source_dir="vendor",
                                description=f"Vendor agent at {yaml_rel}",
                            )
                        )

        # -----
        # Check for prompt files in prompts/ directories
        # -----
        if dirpath.name in ("prompts", "commands"):
            for fname in filenames:
                if fname.endswith(".md"):
                    prompt_rel = dirpath.relative_to(scan_root) / fname
                    prompt_name = Path(fname).stem
                    if prompt_name.endswith(".prompt"):
                        prompt_name = prompt_name.removesuffix(".prompt")

                    platform = None
                    source_dir = ""
                    path_str = str(prompt_rel)
                    if ".cursor" in path_str:
                        platform = "cursor"
                        source_dir = ".cursor"
                    elif ".github" in path_str:
                        platform = "copilot"
                        source_dir = ".github"

                    artifacts.append(
                        DetectedArtifact(
                            name=prompt_name,
                            type="prompt",
                            source_path=prompt_rel,
                            platform=platform,
                            source_dir=source_dir,
                            description=f"Prompt at {prompt_rel}",
                        )
                    )

        # -----
        # Check for instruction files
        # -----
        if dirpath.name == "instructions":
            for fname in filenames:
                if fname.endswith(".md"):
                    instr_rel = dirpath.relative_to(scan_root) / fname
                    instr_name = Path(fname).stem
                    artifacts.append(
                        DetectedArtifact(
                            name=instr_name,
                            type="instruction",
                            source_path=instr_rel,
                            platform=None,
                            source_dir="",
                            description=f"Instruction at {instr_rel}",
                        )
                    )

    # -----
    # Check for root-level instruction files
    # -----
    standalone_instructions: list[tuple[str, str, str, str]] = [
        ("CLAUDE.md", "claude-instructions", "claude", ""),
        ("AGENTS.md", "codex-instructions", "codex", ""),
    ]
    for filename, name, platform, source_dir in standalone_instructions:
        filepath = scan_root / filename
        if filepath.is_file():
            artifacts.append(
                DetectedArtifact(
                    name=name,
                    type="instruction",
                    source_path=Path(filename),
                    platform=platform,
                    source_dir=source_dir,
                    description=f"Platform instruction at {filename}",
                )
            )

    logger.info(
        f"Directory scan complete: found {len(artifacts)} artifacts "
        f"(skills={sum(1 for a in artifacts if a.type == 'skill')}, "
        f"agents={sum(1 for a in artifacts if a.type == 'agent')}, "
        f"prompts={sum(1 for a in artifacts if a.type == 'prompt')}, "
        f"instructions={sum(1 for a in artifacts if a.type == 'instruction')})"
    )

    return artifacts


def _extract_first_line(filepath: Path) -> str | None:
    """Extract the first meaningful line from a markdown file.

    Skips empty lines and heading markers.

    Args:
        filepath: Path to the file.

    Returns:
        First content line, or ``None`` if file is empty.
    """
    try:
        with filepath.open("r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    stripped = stripped.lstrip("#").strip()
                if stripped:
                    return stripped[:256]
    except OSError:
        pass
    return None


def scan_project(
    root: Path,
    platforms: list[str] | None = None,
) -> list[DetectedArtifact]:
    """Scan a project directory for all detectable artifacts.

    Args:
        root: Project root directory to scan.
        platforms: Optional list of platform names to filter results.
            Only artifacts belonging to these platforms are returned.
            Pass ``None`` or an empty list to return all artifacts.
            Valid values: ``cursor``, ``copilot``, ``claude``, ``codex``.

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

    # -----
    # Apply platform filter if specified
    # -----
    if platforms:
        platform_set = {p.lower() for p in platforms}
        before_count = len(artifacts)
        artifacts = [
            a for a in artifacts
            if a.platform is not None and a.platform in platform_set
        ]
        logger.info(
            f"Platform filter applied ({', '.join(platform_set)}): "
            f"{before_count} -> {len(artifacts)} artifacts"
        )

    logger.info(
        f"Scan complete: found {len(artifacts)} artifacts "
        f"(skills={sum(1 for a in artifacts if a.type == 'skill')}, "
        f"agents={sum(1 for a in artifacts if a.type == 'agent')}, "
        f"prompts={sum(1 for a in artifacts if a.type == 'prompt')}, "
        f"instructions={sum(1 for a in artifacts if a.type == 'instruction')})"
    )

    return artifacts
