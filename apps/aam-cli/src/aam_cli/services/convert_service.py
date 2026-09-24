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
    COMMAND_SUPPORTED_FIELDS,
    COMMAND_TARGET_DIRS,
    COMMAND_TARGET_EXTENSIONS,
    PROMPT_TARGET_DIRS,
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
        "claude-code": _find_claude_instructions,
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

    elif platform == "claude-code":
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

    elif platform == "claude-code":
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
        "claude-code": ".claude/skills",
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

        cursor_meta: dict[str, object] = {}
        cursor_meta["description"] = frontmatter.get(
            "description", "Converted instruction"
        )

        if frontmatter.get("applyTo"):
            cursor_meta["alwaysApply"] = False
            apply_to = frontmatter["applyTo"]
            cursor_meta["globs"] = (
                [apply_to] if isinstance(apply_to, str) else apply_to
            )
        else:
            cursor_meta["alwaysApply"] = True

        content = generate_frontmatter(cursor_meta, body)

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
                if target_platform in ("cursor", "claude-code"):
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
    target_ext = COMMAND_TARGET_EXTENSIONS.get(target_platform)

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
    supported = COMMAND_SUPPORTED_FIELDS.get(target_platform, set())
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


def _convert_rule(
    src_file: Path,
    root: Path,
    source_platform: str,
    target_platform: str,
    force: bool,
    dry_run: bool,
) -> ConversionResult:
    """Convert a rule/instruction file between platforms.

    Maps ``applyTo`` → ``globs`` (Copilot → Cursor) or vice versa.
    For platforms that have no per-file scoping (Claude, Codex), the rule
    is written as a plain markdown block.

    Args:
        src_file: Path to the source rule file.
        root: Project root directory.
        source_platform: Source platform identifier.
        target_platform: Target platform identifier.
        force: If True, overwrite existing files.
        dry_run: If True, do not write files.

    Returns:
        ConversionResult for the rule.
    """
    from aam_cli.converters.frontmatter import generate_frontmatter, parse_frontmatter
    from aam_cli.converters.mappings import VERBOSE_WORKAROUNDS

    name = _derive_name(src_file, source_platform)
    rel_source = str(src_file.relative_to(root))

    try:
        raw = src_file.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(raw)

        new_fm: dict[str, object] = {}
        warnings: list[str] = []

        # -----
        # Translate applyTo (Copilot) → globs (Cursor) and vice versa
        # -----
        if source_platform == "copilot" and target_platform == "cursor":
            apply_to = fm.get("applyTo", "")
            if apply_to:
                new_fm["globs"] = apply_to
            new_fm["description"] = fm.get("description", fm.get("name", name))
            new_fm["alwaysApply"] = not bool(apply_to)
        elif source_platform == "cursor" and target_platform == "copilot":
            globs = fm.get("globs", "")
            if globs:
                new_fm["applyTo"] = globs if isinstance(globs, str) else ", ".join(globs)
            new_fm["name"] = fm.get("description", name)
            new_fm["description"] = fm.get("description", "")
        else:
            # Plain markdown (Claude, Codex) — drop frontmatter
            if "globs" in fm or "applyTo" in fm:
                warnings.append(VERBOSE_WORKAROUNDS.get("globs_lost", ""))

        content = generate_frontmatter(new_fm, body) if new_fm else body

        # -----
        # Determine target path
        # -----
        if target_platform == "cursor":
            target_path = root / ".cursor" / "rules" / f"{name}.mdc"
        elif target_platform == "copilot":
            target_path = root / ".github" / "instructions" / f"{name}.instructions.md"
        elif target_platform == "claude-code":
            target_path = root / "CLAUDE.md"
            content = f"\n## Rule: {name}\n\n{body}"
        elif target_platform == "codex":
            target_path = root / "AGENTS.md"
            content = f"\n## Rule: {name}\n\n{body}"
        else:
            return ConversionResult(
                source_path=rel_source,
                artifact_type="rule",
                target_path="",
                error=f"Unknown target platform: {target_platform}",
            )

        rel_target = str(target_path.relative_to(root))

        if dry_run:
            return ConversionResult(
                source_path=rel_source,
                artifact_type="rule",
                target_path=rel_target,
                warnings=warnings,
            )

        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.is_file() and not force:
            return ConversionResult(
                source_path=rel_source,
                artifact_type="rule",
                target_path=rel_target,
                skipped=True,
                warnings=warnings,
            )

        if target_path.is_file() and force:
            _backup_file(target_path)

        target_path.write_text(content, encoding="utf-8")
        return ConversionResult(
            source_path=rel_source,
            artifact_type="rule",
            target_path=rel_target,
            warnings=warnings,
        )

    except Exception as exc:
        logger.error(f"Failed to convert rule '{src_file}': {exc}", exc_info=True)
        return ConversionResult(
            source_path=rel_source,
            artifact_type="rule",
            target_path="",
            error=str(exc),
        )


def _convert_hooks(
    hooks_json_path: Path,
    root: Path,
    source_platform: str,
    target_platform: str,
    force: bool,
    dry_run: bool,
) -> ConversionResult:
    """Convert a hooks.json file between platforms.

    Translates canonical UAAPS hook event names between platform-specific
    names using the mappings table.

    Args:
        hooks_json_path: Path to the source hooks.json file.
        root: Project root directory.
        source_platform: Source platform identifier.
        target_platform: Target platform identifier.
        force: If True, overwrite existing files.
        dry_run: If True, do not write files.

    Returns:
        ConversionResult for the hooks file.
    """
    import json as _json

    from aam_cli.converters.mappings import (
        translate_hook_event,
        translate_hook_event_from_platform,
    )

    rel_source = str(hooks_json_path.relative_to(root))

    try:
        source_hooks: dict[str, object] = _json.loads(
            hooks_json_path.read_text(encoding="utf-8")
        )
        translated: dict[str, object] = {}
        warnings: list[str] = []

        for event_name, entries in source_hooks.items():
            # -----
            # Canonicalize from source platform, then translate to target
            # -----
            canonical = translate_hook_event_from_platform(event_name, source_platform)
            if canonical is None:
                # Already canonical or unknown — try using as-is
                canonical = event_name

            target_event = translate_hook_event(canonical, target_platform)
            if target_event is None:
                warnings.append(
                    f"Hook event '{event_name}' has no equivalent on {target_platform} — dropped"
                )
                continue

            translated[target_event] = entries

        # -----
        # Determine target path
        # -----
        if target_platform == "claude-code":
            target_path = root / ".claude" / "hooks.json"
        elif target_platform == "cursor":
            target_path = root / ".cursor" / "hooks.json"
        elif target_platform == "copilot":
            target_path = root / ".github" / "copilot-hooks.json"
        else:
            return ConversionResult(
                source_path=rel_source,
                artifact_type="hooks",
                target_path="",
                skipped=True,
                warnings=[f"Hooks not supported on {target_platform}"],
            )

        rel_target = str(target_path.relative_to(root))

        if dry_run:
            return ConversionResult(
                source_path=rel_source,
                artifact_type="hooks",
                target_path=rel_target,
                warnings=warnings,
            )

        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.is_file() and not force:
            return ConversionResult(
                source_path=rel_source,
                artifact_type="hooks",
                target_path=rel_target,
                skipped=True,
                warnings=warnings,
            )

        if target_path.is_file() and force:
            _backup_file(target_path)

        target_path.write_text(_json.dumps(translated, indent=2), encoding="utf-8")
        return ConversionResult(
            source_path=rel_source,
            artifact_type="hooks",
            target_path=rel_target,
            warnings=warnings,
        )

    except Exception as exc:
        logger.error(f"Failed to convert hooks '{hooks_json_path}': {exc}", exc_info=True)
        return ConversionResult(
            source_path=rel_source,
            artifact_type="hooks",
            target_path="",
            error=str(exc),
        )


def _convert_mcp_config(
    servers_path: Path,
    root: Path,
    source_platform: str,
    target_platform: str,
    force: bool,
    dry_run: bool,
) -> ConversionResult:
    """Convert an MCP server configuration file between platform formats.

    Maps between ``servers.json`` (UAAPS), ``.mcp.json`` (Claude/Cursor),
    and ``.vscode/mcp.json`` (Copilot/VS Code) formats.

    Args:
        servers_path: Path to the source MCP config file.
        root: Project root directory.
        source_platform: Source platform identifier.
        target_platform: Target platform identifier.
        force: If True, overwrite existing files.
        dry_run: If True, do not write files.

    Returns:
        ConversionResult for the MCP config file.
    """
    import json as _json

    rel_source = str(servers_path.relative_to(root))

    try:
        source_data: dict[str, object] = _json.loads(
            servers_path.read_text(encoding="utf-8")
        )

        # -----
        # Normalize to { "mcpServers": {...} } internal structure
        # -----
        if "mcpServers" in source_data:
            servers = source_data["mcpServers"]
        elif "servers" in source_data:
            servers = source_data["servers"]
        else:
            servers = source_data

        # -----
        # Format output per target platform
        # -----
        output: dict[str, object]
        if target_platform in ("claude-code", "cursor"):
            output = {"mcpServers": servers}
            if target_platform == "claude-code":
                target_path = root / ".mcp.json"
            else:
                target_path = root / ".cursor" / "mcp.json"
        elif target_platform == "copilot":
            output = {"servers": servers}
            target_path = root / ".vscode" / "mcp.json"
        else:
            return ConversionResult(
                source_path=rel_source,
                artifact_type="mcp",
                target_path="",
                skipped=True,
                warnings=[f"MCP config not supported on {target_platform}"],
            )

        rel_target = str(target_path.relative_to(root))

        if dry_run:
            return ConversionResult(
                source_path=rel_source,
                artifact_type="mcp",
                target_path=rel_target,
                warnings=[],
            )

        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.is_file() and not force:
            return ConversionResult(
                source_path=rel_source,
                artifact_type="mcp",
                target_path=rel_target,
                skipped=True,
                warnings=[],
            )

        if target_path.is_file() and force:
            _backup_file(target_path)

        target_path.write_text(_json.dumps(output, indent=2), encoding="utf-8")
        return ConversionResult(
            source_path=rel_source,
            artifact_type="mcp",
            target_path=rel_target,
            warnings=[],
        )

    except Exception as exc:
        logger.error(f"Failed to convert MCP config '{servers_path}': {exc}", exc_info=True)
        return ConversionResult(
            source_path=rel_source,
            artifact_type="mcp",
            target_path="",
            error=str(exc),
        )


def run_conversion(
    project_root: Path,
    source_platform: str,
    target_platform: str,
    artifact_type: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> ConversionReport:
    """Run a full cross-platform conversion.

    Supports instruction, agent, prompt, skill, rule, hooks, and mcp types.

    Args:
        project_root: Root directory of the project.
        source_platform: Source platform identifier.
        target_platform: Target platform identifier.
        artifact_type: Optional filter (instruction, agent, prompt, skill,
            rule, hooks, mcp).
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

    # Default types (instruction, agent, prompt, skill) match pre-UAAPS behavior.
    # The new types (rule, hooks, mcp) are only run when explicitly requested to
    # avoid double-processing files that overlap with instruction/prompt paths.
    DEFAULT_TYPES = ["instruction", "agent", "prompt", "skill"]
    types_to_convert = [artifact_type] if artifact_type else DEFAULT_TYPES

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

    # -----
    # Convert rules (UAAPS v0.4.0)
    # -----
    if "rule" in types_to_convert:
        rule_files: list[Path] = []
        if source_platform == "copilot":
            rule_files = list(root.glob(".github/instructions/*.instructions.md"))
        elif source_platform == "cursor":
            rule_files = [
                p for p in root.glob(".cursor/rules/*.mdc")
                if not p.name.startswith("agent-")
            ]
        for src_file in rule_files:
            result = _convert_rule(
                src_file, root, source_platform, target_platform, force, dry_run
            )
            report.results.append(result)

    # -----
    # Convert hooks config (UAAPS v0.4.0)
    # -----
    if "hooks" in types_to_convert:
        hooks_candidates: list[Path] = [
            root / ".claude" / "hooks.json",
            root / ".cursor" / "hooks.json",
            root / ".github" / "copilot-hooks.json",
        ]
        for hooks_file in hooks_candidates:
            if hooks_file.is_file():
                result = _convert_hooks(
                    hooks_file, root, source_platform, target_platform, force, dry_run
                )
                report.results.append(result)
                break  # Process first match only

    # -----
    # Convert MCP server config (UAAPS v0.4.0)
    # -----
    if "mcp" in types_to_convert:
        mcp_candidates: list[Path] = [
            root / ".mcp.json",
            root / ".cursor" / "mcp.json",
            root / ".vscode" / "mcp.json",
        ]
        for mcp_file in mcp_candidates:
            if mcp_file.is_file():
                result = _convert_mcp_config(
                    mcp_file, root, source_platform, target_platform, force, dry_run
                )
                report.results.append(result)
                break  # Process first match only

    return report
