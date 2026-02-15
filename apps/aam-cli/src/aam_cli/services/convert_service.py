"""Core conversion logic for cross-platform artifact conversion.

Reads artifacts from one platform's format and writes them in another's,
tracking warnings for lossy conversions and errors for incompatible ones.

Reference: docs/specs/SPEC-convert-command.md
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from aam_cli.converters.frontmatter import generate_frontmatter, parse_frontmatter
from aam_cli.converters.mappings import (
    AGENT_SUPPORTED_FIELDS,
    AGENT_TARGET_DIRS,
    AGENT_TARGET_EXTENSIONS,
    INSTRUCTION_SUPPORTED_FIELDS,
    PROMPT_SUPPORTED_FIELDS,
    PROMPT_TARGET_DIRS,
    PROMPT_TARGET_EXTENSIONS,
    SINGLE_FILE_INSTRUCTION_TARGETS,
    SKILL_TARGET_DIRS,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# DATA MODELS                                                                  #
#                                                                              #
################################################################################


@dataclass
class ConversionResult:
    """Result of a single artifact conversion."""

    source_path: str
    target_path: str
    artifact_type: str
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
    skipped: bool = False


@dataclass
class ConversionReport:
    """Summary report of a full conversion run."""

    source_platform: str
    target_platform: str
    results: list[ConversionResult] = field(default_factory=list)

    @property
    def converted_count(self) -> int:
        return sum(
            1 for r in self.results if not r.skipped and r.error is None
        )

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.error is not None)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.skipped)

    @property
    def warning_count(self) -> int:
        return sum(len(r.warnings) for r in self.results)


################################################################################
#                                                                              #
# MARKER SECTION HELPERS                                                       #
#                                                                              #
################################################################################

BEGIN_MARKER_TEMPLATE = "<!-- BEGIN AAM CONVERTED: {name} -->"
END_MARKER_TEMPLATE = "<!-- END AAM CONVERTED: {name} -->"


def _upsert_marker_section(file_path: Path, name: str, content: str) -> None:
    """Insert or replace a marker-delimited section in a file.

    Args:
        file_path: Path to the target file.
        name: Section identifier used in markers.
        content: Markdown body to place between the markers.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    begin_marker = BEGIN_MARKER_TEMPLATE.format(name=name)
    end_marker = END_MARKER_TEMPLATE.format(name=name)

    section_block = f"{begin_marker}\n{content.rstrip()}\n{end_marker}\n"

    if file_path.is_file():
        existing = file_path.read_text(encoding="utf-8")

        if begin_marker in existing and end_marker in existing:
            before = existing[: existing.index(begin_marker)]
            after = existing[existing.index(end_marker) + len(end_marker) :]
            after = after.lstrip("\n")
            new_content = before.rstrip("\n") + "\n\n" + section_block
            if after.strip():
                new_content += "\n" + after
        else:
            new_content = existing.rstrip("\n") + "\n\n" + section_block
    else:
        new_content = section_block

    file_path.write_text(new_content, encoding="utf-8")


################################################################################
#                                                                              #
# SOURCE SCANNING                                                              #
#                                                                              #
################################################################################


def _find_cursor_instructions(root: Path) -> list[Path]:
    """Find Cursor instruction files (.mdc rules and .cursorrules)."""
    files: list[Path] = []

    # .cursor/rules/*.mdc (non-agent)
    rules_dir = root / ".cursor" / "rules"
    if rules_dir.is_dir():
        for mdc in rules_dir.glob("*.mdc"):
            if not mdc.name.startswith("agent-"):
                files.append(mdc)

    # Legacy .cursorrules
    cursorrules = root / ".cursorrules"
    if cursorrules.is_file():
        files.append(cursorrules)

    return files


def _find_copilot_instructions(root: Path) -> list[Path]:
    """Find Copilot instruction files."""
    files: list[Path] = []

    main = root / ".github" / "copilot-instructions.md"
    if main.is_file():
        files.append(main)

    instr_dir = root / ".github" / "instructions"
    if instr_dir.is_dir():
        for f in instr_dir.glob("*.instructions.md"):
            files.append(f)

    return files


def _find_claude_instructions(root: Path) -> list[Path]:
    """Find Claude instruction files."""
    files: list[Path] = []

    for name in ("CLAUDE.md", ".claude/CLAUDE.md"):
        p = root / name
        if p.is_file():
            files.append(p)

    return files


def _find_codex_instructions(root: Path) -> list[Path]:
    """Find Codex instruction files."""
    files: list[Path] = []

    for name in ("AGENTS.md", "AGENTS.override.md"):
        p = root / name
        if p.is_file():
            files.append(p)

    return files


def _find_instructions(root: Path, platform: str) -> list[Path]:
    """Find instruction files for a given source platform."""
    finders = {
        "cursor": _find_cursor_instructions,
        "copilot": _find_copilot_instructions,
        "claude": _find_claude_instructions,
        "codex": _find_codex_instructions,
    }
    return finders[platform](root)


def _find_agents(root: Path, platform: str) -> list[Path]:
    """Find agent files for a given source platform."""
    files: list[Path] = []

    if platform == "cursor":
        # .cursor/rules/agent-*.mdc
        rules_dir = root / ".cursor" / "rules"
        if rules_dir.is_dir():
            files.extend(rules_dir.glob("agent-*.mdc"))
        # .cursor/agents/*.md
        agents_dir = root / ".cursor" / "agents"
        if agents_dir.is_dir():
            files.extend(agents_dir.glob("*.md"))

    elif platform == "copilot":
        agents_dir = root / ".github" / "agents"
        if agents_dir.is_dir():
            files.extend(agents_dir.glob("*.agent.md"))

    elif platform == "claude":
        agents_dir = root / ".claude" / "agents"
        if agents_dir.is_dir():
            files.extend(agents_dir.glob("*.md"))

    # codex: no discrete agent files

    return files


def _find_prompts(root: Path, platform: str) -> list[Path]:
    """Find prompt files for a given source platform."""
    files: list[Path] = []

    if platform == "cursor":
        for subdir in ("prompts", "commands"):
            d = root / ".cursor" / subdir
            if d.is_dir():
                files.extend(d.glob("*.md"))

    elif platform == "copilot":
        d = root / ".github" / "prompts"
        if d.is_dir():
            files.extend(d.glob("*.prompt.md"))

    elif platform == "claude":
        d = root / ".claude" / "prompts"
        if d.is_dir():
            files.extend(d.glob("*.md"))

    # codex: no prompt files

    return files


def _find_skills(root: Path, platform: str) -> list[Path]:
    """Find skill directories for a given source platform.

    Returns paths to skill directories (parent of SKILL.md).
    """
    dirs: list[Path] = []
    base_map = {
        "cursor": ".cursor/skills",
        "copilot": ".github/skills",
        "claude": ".claude/skills",
        "codex": ".agents/skills",
    }

    base = root / base_map.get(platform, "")
    if base.is_dir():
        for skill_dir in base.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
                dirs.append(skill_dir)

    return dirs


################################################################################
#                                                                              #
# CONVERSION FUNCTIONS                                                         #
#                                                                              #
################################################################################


def _derive_name(file_path: Path, platform: str) -> str:
    """Derive an artifact name from a file path."""
    stem = file_path.stem

    # Strip platform-specific extensions
    if stem.endswith(".instructions"):
        stem = stem.removesuffix(".instructions")
    elif stem.endswith(".agent"):
        stem = stem.removesuffix(".agent")
    elif stem.endswith(".prompt"):
        stem = stem.removesuffix(".prompt")

    # Strip agent- prefix from Cursor agent rules
    if platform == "cursor" and stem.startswith("agent-"):
        stem = stem.removeprefix("agent-")

    return stem


def _convert_instruction(
    source_file: Path,
    root: Path,
    source_platform: str,
    target_platform: str,
    force: bool,
    dry_run: bool,
) -> ConversionResult:
    """Convert a single instruction file."""
    name = _derive_name(source_file, source_platform)
    rel_source = str(source_file.relative_to(root))

    # Parse source content
    raw_content = source_file.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(raw_content)

    warnings: list[str] = []
    target_path_str = ""

    # -----
    # Determine target path and content
    # -----
    if target_platform in SINGLE_FILE_INSTRUCTION_TARGETS:
        # Claude / Codex: append to single file with markers
        target_file = root / SINGLE_FILE_INSTRUCTION_TARGETS[target_platform]
        target_path_str = str(target_file.relative_to(root))

        # Warn about lost fields
        if frontmatter.get("globs"):
            globs = frontmatter["globs"]
            warnings.append(
                f"Glob-scoped instruction converted to always-on. "
                f"Original globs: {globs}"
            )
        if frontmatter.get("applyTo"):
            apply_to = frontmatter["applyTo"]
            warnings.append(
                f"Conditional instruction converted to always-on. "
                f"Original applyTo: {apply_to}"
            )
        if "alwaysApply" in frontmatter:
            warnings.append("alwaysApply metadata not supported on target platform.")

        # Build section content with scope hint
        scope_hint = ""
        if frontmatter.get("globs"):
            scope_hint = f" (applies to: {frontmatter['globs']})"
        elif frontmatter.get("applyTo"):
            scope_hint = f" (applies to: {frontmatter['applyTo']})"

        section_content = body
        if scope_hint:
            # Prepend scope hint to first heading or as a comment
            section_content = f"## {name}{scope_hint}\n\n{body}"

        if not dry_run:
            if not force and target_file.is_file():
                # Check if section already exists
                existing = target_file.read_text(encoding="utf-8")
                begin_marker = BEGIN_MARKER_TEMPLATE.format(name=name)
                if begin_marker not in existing:
                    # Safe to append
                    pass
            _upsert_marker_section(target_file, name, section_content)

        return ConversionResult(
            source_path=rel_source,
            target_path=f"{target_path_str} (appended)",
            artifact_type="instruction",
            warnings=warnings,
        )

    elif target_platform == "copilot":
        # Copilot: scoped instructions or main file
        if frontmatter.get("globs") or frontmatter.get("alwaysApply") is False:
            # Convert to scoped .instructions.md
            target_dir = root / ".github" / "instructions"
            target_file = target_dir / f"{name}.instructions.md"
            target_path_str = str(target_file.relative_to(root))

            new_meta: dict[str, object] = {"name": name}
            if frontmatter.get("description"):
                new_meta["description"] = frontmatter["description"]
            if frontmatter.get("globs"):
                globs = frontmatter["globs"]
                # Convert list to single glob (take first if list)
                if isinstance(globs, list):
                    new_meta["applyTo"] = globs[0] if len(globs) == 1 else ", ".join(globs)
                else:
                    new_meta["applyTo"] = globs

            if "alwaysApply" in frontmatter:
                warnings.append("alwaysApply field dropped (not supported in Copilot instructions.md)")

            content = generate_frontmatter(new_meta, body)

            if not dry_run:
                if target_file.exists() and not force:
                    return ConversionResult(
                        source_path=rel_source,
                        target_path=target_path_str,
                        artifact_type="instruction",
                        skipped=True,
                        warnings=["Target exists, use --force to overwrite"],
                    )
                if target_file.exists() and force:
                    _backup_file(target_file)
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(content, encoding="utf-8")

        else:
            # Always-on instruction -> copilot-instructions.md
            target_file = root / ".github" / "copilot-instructions.md"
            target_path_str = f"{target_file.relative_to(root)} (appended)"

            if "alwaysApply" in frontmatter:
                warnings.append("alwaysApply field dropped (not supported in Copilot)")

            if not dry_run:
                _upsert_marker_section(target_file, name, body)

        return ConversionResult(
            source_path=rel_source,
            target_path=target_path_str,
            artifact_type="instruction",
            warnings=warnings,
        )

    elif target_platform == "cursor":
        # Convert to .cursor/rules/*.mdc
        target_dir = root / ".cursor" / "rules"
        target_file = target_dir / f"{name}.mdc"
        target_path_str = str(target_file.relative_to(root))

        new_meta: dict[str, object] = {}
        new_meta["description"] = frontmatter.get("description", "Converted instruction")

        if frontmatter.get("applyTo"):
            new_meta["alwaysApply"] = False
            apply_to = frontmatter["applyTo"]
            new_meta["globs"] = [apply_to] if isinstance(apply_to, str) else apply_to
        else:
            new_meta["alwaysApply"] = True

        content = generate_frontmatter(new_meta, body)

        if not dry_run:
            if target_file.exists() and not force:
                return ConversionResult(
                    source_path=rel_source,
                    target_path=target_path_str,
                    artifact_type="instruction",
                    skipped=True,
                    warnings=["Target exists, use --force to overwrite"],
                )
            if target_file.exists() and force:
                _backup_file(target_file)
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(content, encoding="utf-8")

        return ConversionResult(
            source_path=rel_source,
            target_path=target_path_str,
            artifact_type="instruction",
            warnings=warnings,
        )

    return ConversionResult(
        source_path=rel_source,
        target_path="",
        artifact_type="instruction",
        error=f"Unsupported target platform: {target_platform}",
    )


def _convert_agent(
    source_file: Path,
    root: Path,
    source_platform: str,
    target_platform: str,
    force: bool,
    dry_run: bool,
) -> ConversionResult:
    """Convert a single agent file."""
    name = _derive_name(source_file, source_platform)
    rel_source = str(source_file.relative_to(root))

    raw_content = source_file.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(raw_content)

    warnings: list[str] = []

    # -----
    # Codex target: append to AGENTS.md as a section
    # -----
    if target_platform == "codex":
        target_file = root / "AGENTS.md"
        target_path_str = f"{target_file.relative_to(root)} (appended)"

        warnings.append(
            "Codex does not support discrete agent files. "
            "Agent content appended as a section in AGENTS.md."
        )

        section = f"## Agent: {name}\n\n{body}"
        if not dry_run:
            _upsert_marker_section(target_file, f"agent-{name}", section)

        return ConversionResult(
            source_path=rel_source,
            target_path=target_path_str,
            artifact_type="agent",
            warnings=warnings,
        )

    # -----
    # Other platforms: create discrete agent file
    # -----
    target_dir_name = AGENT_TARGET_DIRS.get(target_platform)
    target_ext = AGENT_TARGET_EXTENSIONS.get(target_platform)

    if not target_dir_name or not target_ext:
        return ConversionResult(
            source_path=rel_source,
            target_path="",
            artifact_type="agent",
            error=f"Unsupported agent target platform: {target_platform}",
        )

    target_file = root / target_dir_name / f"{name}{target_ext}"
    target_path_str = str(target_file.relative_to(root))

    # Build target frontmatter with only supported fields
    supported = AGENT_SUPPORTED_FIELDS.get(target_platform, set())
    new_meta: dict[str, object] = {}

    if "name" in supported:
        new_meta["name"] = frontmatter.get("name", name)
    if "description" in supported and frontmatter.get("description"):
        new_meta["description"] = frontmatter["description"]

    # Warn about dropped fields
    for field_name in ("tools", "handoffs", "model", "readonly", "is_background",
                       "user-invokable", "target", "mcp-servers"):
        if field_name in frontmatter and field_name not in supported:
            value = frontmatter[field_name]
            if field_name == "tools":
                warnings.append(f"Tools {value} are {source_platform}-specific and were removed.")
            elif field_name == "handoffs":
                warnings.append(f"Handoffs are {source_platform}-specific and were removed: {value}.")
            elif field_name == "model":
                if target_platform in ("cursor", "claude"):
                    # Cursor/Claude subagents support model but map differently
                    if "model" in supported:
                        new_meta["model"] = "inherit"
                        warnings.append(f"Model '{value}' is {source_platform}-specific, set to 'inherit'.")
                    else:
                        warnings.append(f"Model '{value}' is {source_platform}-specific, removed.")
                else:
                    warnings.append(f"Model '{value}' is {source_platform}-specific. Set model manually.")
            elif field_name == "readonly" and value:
                warnings.append("readonly=true not supported on target. Enforce via instruction text.")
            elif field_name == "is_background" and value:
                warnings.append("is_background not supported on target.")
            elif field_name == "user-invokable":
                warnings.append("user-invokable flag removed.")
            elif field_name == "target":
                warnings.append("target field removed — not applicable on target platform.")
            elif field_name == "mcp-servers":
                warnings.append(
                    f"MCP server configuration {value} must be configured separately."
                )

    # Handle model field for Cursor target (supports model)
    if "model" in supported and "model" in frontmatter and "model" not in new_meta:
        # Copy model if source and target both support it
        new_meta["model"] = frontmatter["model"]

    content = generate_frontmatter(new_meta, body)

    if not dry_run:
        if target_file.exists() and not force:
            return ConversionResult(
                source_path=rel_source,
                target_path=target_path_str,
                artifact_type="agent",
                skipped=True,
                warnings=["Target exists, use --force to overwrite"],
            )
        if target_file.exists() and force:
            _backup_file(target_file)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content, encoding="utf-8")

    return ConversionResult(
        source_path=rel_source,
        target_path=target_path_str,
        artifact_type="agent",
        warnings=warnings,
    )


def _convert_prompt(
    source_file: Path,
    root: Path,
    source_platform: str,
    target_platform: str,
    force: bool,
    dry_run: bool,
) -> ConversionResult:
    """Convert a single prompt file."""
    name = _derive_name(source_file, source_platform)
    rel_source = str(source_file.relative_to(root))

    raw_content = source_file.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(raw_content)

    warnings: list[str] = []

    # -----
    # Codex target: append to AGENTS.md
    # -----
    if target_platform == "codex":
        target_file = root / "AGENTS.md"
        target_path_str = f"{target_file.relative_to(root)} (appended)"

        warnings.append(
            "Codex does not support prompt files. "
            "Prompt content appended to AGENTS.md as a reference section."
        )

        section = f"## Prompt: {name}\n\n{body}"
        if not dry_run:
            _upsert_marker_section(target_file, f"prompt-{name}", section)

        return ConversionResult(
            source_path=rel_source,
            target_path=target_path_str,
            artifact_type="prompt",
            warnings=warnings,
        )

    # -----
    # Other platforms
    # -----
    target_dir_name = PROMPT_TARGET_DIRS.get(target_platform)
    target_ext = PROMPT_TARGET_EXTENSIONS.get(target_platform)

    if not target_dir_name or not target_ext:
        return ConversionResult(
            source_path=rel_source,
            target_path="",
            artifact_type="prompt",
            error=f"Unsupported prompt target platform: {target_platform}",
        )

    target_file = root / target_dir_name / f"{name}{target_ext}"
    target_path_str = str(target_file.relative_to(root))

    # Build target frontmatter
    supported = PROMPT_SUPPORTED_FIELDS.get(target_platform, set())
    new_meta: dict[str, object] = {}

    if target_platform == "copilot":
        # Copilot prompts can have frontmatter
        if "name" in supported:
            new_meta["name"] = name
        if frontmatter.get("description") and "description" in supported:
            new_meta["description"] = frontmatter["description"]

    # Warn about dropped fields
    for field_name in ("agent", "model", "tools", "argument-hint"):
        if field_name in frontmatter and field_name not in supported:
            value = frontmatter[field_name]
            if field_name == "agent":
                warnings.append(
                    f"Prompt was bound to agent '{value}'. Bind manually on target platform."
                )
            elif field_name == "model":
                warnings.append(f"Model '{value}' removed — target platform doesn't specify models in prompts.")
            elif field_name == "tools":
                warnings.append(f"Prompt tools {value} removed.")
            elif field_name == "argument-hint":
                warnings.append(f"argument-hint '{value}' removed.")

    content = generate_frontmatter(new_meta, body) if new_meta else body

    if not dry_run:
        if target_file.exists() and not force:
            return ConversionResult(
                source_path=rel_source,
                target_path=target_path_str,
                artifact_type="prompt",
                skipped=True,
                warnings=["Target exists, use --force to overwrite"],
            )
        if target_file.exists() and force:
            _backup_file(target_file)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content, encoding="utf-8")

    return ConversionResult(
        source_path=rel_source,
        target_path=target_path_str,
        artifact_type="prompt",
        warnings=warnings,
    )


def _convert_skill(
    source_dir: Path,
    root: Path,
    source_platform: str,
    target_platform: str,
    force: bool,
    dry_run: bool,
) -> ConversionResult:
    """Convert a skill directory (direct copy)."""
    name = source_dir.name
    rel_source = str(source_dir.relative_to(root))

    target_base = SKILL_TARGET_DIRS.get(target_platform)
    if not target_base:
        return ConversionResult(
            source_path=rel_source,
            target_path="",
            artifact_type="skill",
            error=f"Unsupported skill target platform: {target_platform}",
        )

    target_dir = root / target_base / name
    target_path_str = str(target_dir.relative_to(root))

    if not dry_run:
        if target_dir.exists() and not force:
            return ConversionResult(
                source_path=rel_source,
                target_path=target_path_str,
                artifact_type="skill",
                skipped=True,
                warnings=["Target exists, use --force to overwrite"],
            )
        if target_dir.exists() and force:
            # Backup by renaming
            backup_dir = target_dir.with_suffix(".bak")
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            target_dir.rename(backup_dir)

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_dir, target_dir)

    return ConversionResult(
        source_path=rel_source,
        target_path=f"{target_path_str} (direct copy)",
        artifact_type="skill",
    )


################################################################################
#                                                                              #
# BACKUP HELPER                                                                #
#                                                                              #
################################################################################


def _backup_file(file_path: Path) -> Path:
    """Create a .bak backup of a file.

    Args:
        file_path: File to back up.

    Returns:
        Path to the backup file.
    """
    backup = file_path.with_suffix(file_path.suffix + ".bak")
    shutil.copy2(file_path, backup)
    logger.info(f"Backed up {file_path} -> {backup}")
    return backup


################################################################################
#                                                                              #
# PUBLIC API                                                                   #
#                                                                              #
################################################################################


def run_conversion(
    project_root: Path,
    source_platform: str,
    target_platform: str,
    artifact_type: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> ConversionReport:
    """Run a full cross-platform conversion.

    Args:
        project_root: Root directory of the project.
        source_platform: Source platform identifier.
        target_platform: Target platform identifier.
        artifact_type: Optional filter (instruction, agent, prompt, skill).
        dry_run: If True, do not write any files.
        force: If True, overwrite existing target files (with backup).

    Returns:
        ConversionReport with results for each artifact.
    """
    report = ConversionReport(
        source_platform=source_platform,
        target_platform=target_platform,
    )

    root = project_root.resolve()

    types_to_convert = (
        [artifact_type] if artifact_type
        else ["instruction", "agent", "prompt", "skill"]
    )

    # -----
    # Convert instructions
    # -----
    if "instruction" in types_to_convert:
        for src_file in _find_instructions(root, source_platform):
            result = _convert_instruction(
                src_file, root, source_platform, target_platform, force, dry_run
            )
            report.results.append(result)

    # -----
    # Convert agents
    # -----
    if "agent" in types_to_convert:
        for src_file in _find_agents(root, source_platform):
            result = _convert_agent(
                src_file, root, source_platform, target_platform, force, dry_run
            )
            report.results.append(result)

    # -----
    # Convert prompts
    # -----
    if "prompt" in types_to_convert:
        for src_file in _find_prompts(root, source_platform):
            result = _convert_prompt(
                src_file, root, source_platform, target_platform, force, dry_run
            )
            report.results.append(result)

    # -----
    # Convert skills
    # -----
    if "skill" in types_to_convert:
        for src_dir in _find_skills(root, source_platform):
            result = _convert_skill(
                src_dir, root, source_platform, target_platform, force, dry_run
            )
            report.results.append(result)

    return report
