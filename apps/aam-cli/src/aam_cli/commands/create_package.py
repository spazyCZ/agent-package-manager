"""Create-package command for AAM CLI.

Scans an existing project for skills, agents, prompts, and instructions
that are not yet managed by AAM, and packages them into an AAM package
with interactive artifact selection.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class ArtifactType(str, Enum):
    SKILL = "skill"
    AGENT = "agent"
    PROMPT = "prompt"
    INSTRUCTION = "instruction"


class OrganizeMode(str, Enum):
    COPY = "copy"
    REFERENCE = "reference"
    MOVE = "move"


@dataclass
class DetectedArtifact:
    """An artifact discovered in the project that is not part of an AAM package."""

    name: str
    artifact_type: ArtifactType
    source_path: Path
    description: str = ""
    selected: bool = True
    needs_conversion: bool = False
    conversion_note: str = ""


@dataclass
class CreatePackageConfig:
    """Collected configuration for the create-package operation."""

    project_path: Path = field(default_factory=lambda: Path.cwd())
    package_name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = "MIT"
    organize: OrganizeMode = OrganizeMode.COPY
    output_dir: Path = field(default_factory=lambda: Path.cwd())
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Directories excluded from scanning
# ---------------------------------------------------------------------------

EXCLUDED_DIRS = {
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


# ---------------------------------------------------------------------------
# Artifact detection
# ---------------------------------------------------------------------------

def _should_skip_dir(dir_path: Path) -> bool:
    """Return True if *dir_path* should be excluded from scanning."""
    return dir_path.name in EXCLUDED_DIRS


def _read_existing_manifest(project_path: Path) -> set[str]:
    """Return a set of artifact paths already declared in an existing aam.yaml."""
    manifest_path = project_path / "aam.yaml"
    if not manifest_path.exists():
        return set()

    # TODO: Replace with proper YAML parsing via pydantic model
    declared: set[str] = set()
    return declared


def _detect_skills(project_path: Path, declared: set[str]) -> list[DetectedArtifact]:
    """Detect skill artifacts by looking for SKILL.md files."""
    artifacts: list[DetectedArtifact] = []
    skill_md_paths: list[Path] = []

    for skill_md in project_path.rglob("SKILL.md"):
        if any(_should_skip_dir(p) for p in skill_md.relative_to(project_path).parents):
            continue
        # Avoid .aam/packages/ installed packages
        rel = str(skill_md.relative_to(project_path))
        if rel.startswith(".aam/packages"):
            continue
        if rel in declared:
            continue
        skill_md_paths.append(skill_md)

    for skill_md in skill_md_paths:
        skill_dir = skill_md.parent
        name = skill_dir.name
        rel_path = skill_dir.relative_to(project_path)

        # TODO: Parse SKILL.md frontmatter for name/description
        artifacts.append(
            DetectedArtifact(
                name=name,
                artifact_type=ArtifactType.SKILL,
                source_path=rel_path,
                description=f"Skill detected at {rel_path}",
            )
        )

    return artifacts


def _detect_agents(project_path: Path, declared: set[str]) -> list[DetectedArtifact]:
    """Detect agent artifacts from agent.yaml files and Cursor agent rules."""
    artifacts: list[DetectedArtifact] = []

    # Pattern 1: agent.yaml files
    for agent_yaml in project_path.rglob("agent.yaml"):
        if any(_should_skip_dir(p) for p in agent_yaml.relative_to(project_path).parents):
            continue
        rel = str(agent_yaml.relative_to(project_path))
        if rel.startswith(".aam/packages"):
            continue
        if rel in declared:
            continue

        agent_dir = agent_yaml.parent
        name = agent_dir.name
        rel_path = agent_dir.relative_to(project_path)

        # TODO: Parse agent.yaml for name/description
        artifacts.append(
            DetectedArtifact(
                name=name,
                artifact_type=ArtifactType.AGENT,
                source_path=rel_path,
                description=f"Agent detected at {rel_path}",
            )
        )

    # Pattern 2: .cursor/rules/agent-*.mdc
    cursor_rules_dir = project_path / ".cursor" / "rules"
    if cursor_rules_dir.is_dir():
        for mdc_file in cursor_rules_dir.glob("agent-*.mdc"):
            rel = str(mdc_file.relative_to(project_path))
            if rel in declared:
                continue
            # Derive name: agent-foo-bar.mdc → foo-bar
            name = mdc_file.stem.removeprefix("agent-")
            artifacts.append(
                DetectedArtifact(
                    name=name,
                    artifact_type=ArtifactType.AGENT,
                    source_path=mdc_file.relative_to(project_path),
                    description=f"Cursor agent rule at {rel}",
                    needs_conversion=True,
                    conversion_note="Convert .mdc rule → agents/*/agent.yaml + system-prompt.md",
                )
            )

    return artifacts


def _detect_prompts(project_path: Path, declared: set[str]) -> list[DetectedArtifact]:
    """Detect prompt artifacts from known prompt directories."""
    artifacts: list[DetectedArtifact] = []

    prompt_dirs = [
        project_path / "prompts",
        project_path / ".cursor" / "prompts",
        project_path / ".github" / "prompts",
    ]

    for prompt_dir in prompt_dirs:
        if not prompt_dir.is_dir():
            continue
        for md_file in prompt_dir.glob("*.md"):
            rel = str(md_file.relative_to(project_path))
            if rel in declared:
                continue
            name = md_file.stem
            artifacts.append(
                DetectedArtifact(
                    name=name,
                    artifact_type=ArtifactType.PROMPT,
                    source_path=md_file.relative_to(project_path),
                    description=f"Prompt at {rel}",
                )
            )

    return artifacts


def _detect_instructions(project_path: Path, declared: set[str]) -> list[DetectedArtifact]:
    """Detect instruction artifacts from rules, CLAUDE.md, AGENTS.md, etc."""
    artifacts: list[DetectedArtifact] = []

    # Pattern 1: instructions/*.md (AAM convention)
    instructions_dir = project_path / "instructions"
    if instructions_dir.is_dir():
        for md_file in instructions_dir.glob("*.md"):
            rel = str(md_file.relative_to(project_path))
            if rel in declared:
                continue
            artifacts.append(
                DetectedArtifact(
                    name=md_file.stem,
                    artifact_type=ArtifactType.INSTRUCTION,
                    source_path=md_file.relative_to(project_path),
                    description=f"Instruction at {rel}",
                )
            )

    # Pattern 2: .cursor/rules/*.mdc (excluding agent-* which are detected as agents)
    cursor_rules_dir = project_path / ".cursor" / "rules"
    if cursor_rules_dir.is_dir():
        for mdc_file in cursor_rules_dir.glob("*.mdc"):
            if mdc_file.name.startswith("agent-"):
                continue  # handled by _detect_agents
            rel = str(mdc_file.relative_to(project_path))
            if rel in declared:
                continue
            artifacts.append(
                DetectedArtifact(
                    name=mdc_file.stem,
                    artifact_type=ArtifactType.INSTRUCTION,
                    source_path=mdc_file.relative_to(project_path),
                    description=f"Cursor rule at {rel}",
                    needs_conversion=True,
                    conversion_note="Convert .mdc frontmatter → instruction YAML frontmatter",
                )
            )

    # Pattern 3: Standalone instruction files (CLAUDE.md, AGENTS.md, copilot-instructions.md)
    standalone_instructions = [
        ("CLAUDE.md", "claude-instructions"),
        ("AGENTS.md", "codex-instructions"),
        (".github/copilot-instructions.md", "copilot-instructions"),
    ]

    for file_rel, name in standalone_instructions:
        filepath = project_path / file_rel
        if filepath.is_file():
            rel = str(Path(file_rel))
            if rel in declared:
                continue
            artifacts.append(
                DetectedArtifact(
                    name=name,
                    artifact_type=ArtifactType.INSTRUCTION,
                    source_path=Path(file_rel),
                    description=f"Platform instruction file at {file_rel}",
                    needs_conversion=True,
                    conversion_note="Convert platform-specific format → instructions/*.md",
                )
            )

    return artifacts


def detect_artifacts(project_path: Path) -> list[DetectedArtifact]:
    """Scan project for all unmanaged artifacts."""
    declared = _read_existing_manifest(project_path)

    artifacts: list[DetectedArtifact] = []
    artifacts.extend(_detect_skills(project_path, declared))
    artifacts.extend(_detect_agents(project_path, declared))
    artifacts.extend(_detect_prompts(project_path, declared))
    artifacts.extend(_detect_instructions(project_path, declared))

    return artifacts


# ---------------------------------------------------------------------------
# Interactive selection
# ---------------------------------------------------------------------------

def _display_detected_artifacts(console: Console, artifacts: list[DetectedArtifact]) -> None:
    """Display detected artifacts grouped by type with selection checkboxes."""
    grouped: dict[ArtifactType, list[DetectedArtifact]] = {}
    for art in artifacts:
        grouped.setdefault(art.artifact_type, []).append(art)

    idx = 1
    for artifact_type in [ArtifactType.SKILL, ArtifactType.AGENT, ArtifactType.PROMPT, ArtifactType.INSTRUCTION]:
        group = grouped.get(artifact_type, [])
        if not group:
            continue

        label = artifact_type.value.capitalize() + "s"
        console.print(f"\n  [bold]{label} ({len(group)}):[/bold]")

        for art in group:
            check = "[green]x[/green]" if art.selected else " "
            conversion = " [yellow](needs conversion)[/yellow]" if art.needs_conversion else ""
            console.print(
                f"    [{check}] {idx:>2}. [cyan]{art.name:<20}[/cyan] {art.source_path}{conversion}"
            )
            idx += 1


def interactive_select(console: Console, artifacts: list[DetectedArtifact]) -> list[DetectedArtifact]:
    """Let the user interactively toggle artifact selection.

    Returns only the artifacts that remain selected.
    """
    if not artifacts:
        return []

    console.print("\n[bold]Found artifacts:[/bold]")
    _display_detected_artifacts(console, artifacts)

    console.print(
        "\n[dim]Toggle items by entering their number (space-separated).[/dim]"
    )
    console.print("[dim]Press [bold]enter[/bold] to confirm, [bold]a[/bold] to select all, [bold]n[/bold] to select none.[/dim]")

    while True:
        response = Prompt.ask("\nToggle / confirm", default="").strip().lower()

        if response == "":
            break
        elif response == "a":
            for art in artifacts:
                art.selected = True
            _display_detected_artifacts(console, artifacts)
        elif response == "n":
            for art in artifacts:
                art.selected = False
            _display_detected_artifacts(console, artifacts)
        else:
            # Parse space-separated indices
            for token in response.split():
                if token.isdigit():
                    index = int(token) - 1
                    if 0 <= index < len(artifacts):
                        artifacts[index].selected = not artifacts[index].selected
            _display_detected_artifacts(console, artifacts)

    return [art for art in artifacts if art.selected]


# ---------------------------------------------------------------------------
# Package metadata prompts
# ---------------------------------------------------------------------------

def prompt_metadata(console: Console, project_path: Path) -> CreatePackageConfig:
    """Interactively collect package metadata from the user."""
    default_name = project_path.resolve().name

    config = CreatePackageConfig(project_path=project_path)
    config.package_name = Prompt.ask("Package name", default=default_name)
    config.version = Prompt.ask("Version", default="1.0.0")
    config.description = Prompt.ask("Description", default="")
    config.author = Prompt.ask("Author", default="")
    config.license = Prompt.ask("License", default="MIT")

    console.print("\nHow should files be organized?")
    console.print("  [bold](c)[/bold] Copy into AAM package structure [dim](default)[/dim]")
    console.print("  [bold](r)[/bold] Reference in-place (keep files where they are)")
    console.print("  [bold](m)[/bold] Move into AAM package structure")

    mode_choice = Prompt.ask("Organization mode", choices=["c", "r", "m"], default="c")
    mode_map = {"c": OrganizeMode.COPY, "r": OrganizeMode.REFERENCE, "m": OrganizeMode.MOVE}
    config.organize = mode_map[mode_choice]

    return config


# ---------------------------------------------------------------------------
# Manifest generation
# ---------------------------------------------------------------------------

def _artifact_target_path(art: DetectedArtifact, organize: OrganizeMode) -> str:
    """Compute the target path for an artifact in the generated aam.yaml."""
    if organize == OrganizeMode.REFERENCE:
        return str(art.source_path)

    # For copy / move: map into canonical AAM structure
    type_dirs = {
        ArtifactType.SKILL: "skills",
        ArtifactType.AGENT: "agents",
        ArtifactType.PROMPT: "prompts",
        ArtifactType.INSTRUCTION: "instructions",
    }
    base = type_dirs[art.artifact_type]

    if art.artifact_type == ArtifactType.SKILL:
        return f"{base}/{art.name}/"
    elif art.artifact_type == ArtifactType.AGENT:
        return f"{base}/{art.name}/"
    elif art.artifact_type == ArtifactType.PROMPT:
        return f"{base}/{art.name}.md"
    elif art.artifact_type == ArtifactType.INSTRUCTION:
        return f"{base}/{art.name}.md"

    return str(art.source_path)


def generate_manifest_yaml(config: CreatePackageConfig, artifacts: list[DetectedArtifact]) -> str:
    """Generate the aam.yaml manifest content as a string."""
    grouped: dict[ArtifactType, list[DetectedArtifact]] = {}
    for art in artifacts:
        grouped.setdefault(art.artifact_type, []).append(art)

    lines: list[str] = [
        f"# aam.yaml — Package Manifest",
        f"name: {config.package_name}",
        f"version: {config.version}",
        f'description: "{config.description}"',
    ]

    if config.author:
        lines.append(f"author: {config.author}")
    if config.license:
        lines.append(f"license: {config.license}")

    lines.append("")
    lines.append("artifacts:")

    type_order = [ArtifactType.AGENT, ArtifactType.SKILL, ArtifactType.PROMPT, ArtifactType.INSTRUCTION]
    for atype in type_order:
        group = grouped.get(atype, [])
        plural = atype.value + "s"
        if group:
            lines.append(f"  {plural}:")
            for art in group:
                target = _artifact_target_path(art, config.organize)
                lines.append(f"    - name: {art.name}")
                lines.append(f"      path: {target}")
                lines.append(f'      description: "{art.description}"')
        else:
            lines.append(f"  {plural}: []")

    lines.append("")
    lines.append("dependencies: {}")
    lines.append("")
    lines.append("platforms:")
    lines.append("  cursor:")
    lines.append("    skill_scope: project")
    lines.append("    deploy_instructions_as: rules")
    lines.append("  claude:")
    lines.append("    merge_instructions: true")
    lines.append("  copilot:")
    lines.append("    merge_instructions: true")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# File operations (copy / move / convert)
# ---------------------------------------------------------------------------

def _copy_artifact(
    project_path: Path,
    art: DetectedArtifact,
    output_dir: Path,
    console: Console,
    dry_run: bool,
) -> None:
    """Copy (or move) a single artifact into the AAM package structure."""
    target_rel = _artifact_target_path(art, OrganizeMode.COPY)
    source = project_path / art.source_path
    dest = output_dir / target_rel

    if art.needs_conversion:
        action = "Convert"
    else:
        action = "Copy"

    if dry_run:
        console.print(f"  [dim]Would {action.lower()}: {art.source_path} → {target_rel}[/dim]")
        return

    # TODO: Implement actual file copy / conversion logic
    # For now, print what would happen
    console.print(f"  [green]✓[/green] {action} {art.source_path} → {target_rel}")


def execute_create_package(
    config: CreatePackageConfig,
    artifacts: list[DetectedArtifact],
    console: Console,
) -> None:
    """Execute the package creation: generate manifest and organize files."""
    manifest_content = generate_manifest_yaml(config, artifacts)
    manifest_path = config.output_dir / "aam.yaml"

    if config.dry_run:
        console.print("\n[bold]Would create:[/bold]")
        console.print(f"  {manifest_path.relative_to(config.project_path)}")
        if config.organize != OrganizeMode.REFERENCE:
            for art in artifacts:
                _copy_artifact(config.project_path, art, config.output_dir, console, dry_run=True)
        console.print(f"\n[yellow]\\[Dry run — no files written][/yellow]")
        console.print("\n[dim]Generated manifest preview:[/dim]")
        console.print(Panel(manifest_content, title="aam.yaml", border_style="blue"))
        return

    # Write manifest
    # TODO: Implement actual file write
    console.print(f"\n[bold]Creating package...[/bold]")
    console.print(f"  [green]✓[/green] Created aam.yaml")

    # Copy / move / convert artifacts
    if config.organize != OrganizeMode.REFERENCE:
        for art in artifacts:
            _copy_artifact(config.project_path, art, config.output_dir, console, dry_run=False)

    # Summary
    type_counts: dict[str, int] = {}
    for art in artifacts:
        label = art.artifact_type.value + "s"
        type_counts[label] = type_counts.get(label, 0) + 1

    parts = [f"{count} {label}" for label, count in type_counts.items()]
    summary = ", ".join(parts)

    console.print(
        f"\n[green]✓[/green] Package created: "
        f"[bold]{config.package_name}@{config.version}[/bold]"
    )
    console.print(f"  {len(artifacts)} artifacts ({summary})")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  [cyan]aam validate[/cyan]    — verify the package is well-formed")
    console.print("  [cyan]aam pack[/cyan]        — build distributable .aam archive")
    console.print("  [cyan]aam publish[/cyan]     — publish to registry")


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------

@click.command("create-package")
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("--all", "include_all", is_flag=True, help="Include all detected artifacts without interactive selection")
@click.option(
    "--type", "-t", "artifact_types",
    multiple=True,
    type=click.Choice(["skills", "agents", "prompts", "instructions"], case_sensitive=False),
    help="Filter detection to specific artifact types (repeatable)",
)
@click.option(
    "--organize",
    type=click.Choice(["copy", "reference", "move"], case_sensitive=False),
    default=None,
    help="File organization mode: copy (default), reference, move",
)
@click.option("--include", "includes", multiple=True, type=click.Path(), help="Manually include a file/directory (repeatable)")
@click.option(
    "--include-as",
    type=click.Choice(["skill", "agent", "prompt", "instruction"], case_sensitive=False),
    default=None,
    help="Artifact type for --include",
)
@click.option("--name", "pkg_name", default=None, help="Package name (skip interactive prompt)")
@click.option("--version", "pkg_version", default=None, help="Package version (skip interactive prompt)")
@click.option("--description", "pkg_description", default=None, help="Package description (skip interactive prompt)")
@click.option("--author", "pkg_author", default=None, help="Package author (skip interactive prompt)")
@click.option("--dry-run", is_flag=True, help="Show what would be created without writing files")
@click.option("--output-dir", type=click.Path(file_okay=False, resolve_path=True), default=None, help="Output directory for the package")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompts")
@click.pass_context
def create_package(
    ctx: click.Context,
    path: str,
    include_all: bool,
    artifact_types: tuple[str, ...],
    organize: str | None,
    includes: tuple[str, ...],
    include_as: str | None,
    pkg_name: str | None,
    pkg_version: str | None,
    pkg_description: str | None,
    pkg_author: str | None,
    dry_run: bool,
    output_dir: str | None,
    yes: bool,
) -> None:
    """Create an AAM package from an existing project.

    Scans the project directory for skills, agents, prompts, and instructions
    that are not yet managed by AAM. Presents an interactive selection UI so you
    can choose which artifacts to include, then generates the aam.yaml manifest
    and optionally copies/moves files into the standard AAM package structure.

    \b
    Examples:
        aam create-package
        aam create-package ./my-project/
        aam create-package --all --name my-pkg --yes
        aam create-package --type skills --type agents
        aam create-package --dry-run
        aam create-package --include ./docs/guide.md --include-as instruction
    """
    console: Console = ctx.obj["console"]
    project_path = Path(path)

    # --- Step 1: Detect artifacts ---
    console.print(f"\n[bold]Scanning for artifacts not managed by AAM...[/bold]")

    artifacts = detect_artifacts(project_path)

    # Filter by type if requested
    if artifact_types:
        type_set = {ArtifactType(t.rstrip("s")) for t in artifact_types}
        artifacts = [a for a in artifacts if a.artifact_type in type_set]

    # Add manual includes
    if includes:
        include_type = ArtifactType(include_as) if include_as else ArtifactType.SKILL
        for inc_path in includes:
            inc = Path(inc_path)
            artifacts.append(
                DetectedArtifact(
                    name=inc.stem if inc.is_file() else inc.name,
                    artifact_type=include_type,
                    source_path=inc,
                    description=f"Manually included from {inc}",
                )
            )

    if not artifacts:
        console.print("\n[yellow]No unmanaged artifacts found in this project.[/yellow]")
        console.print("[dim]If you want to create a new package from scratch, use: aam init[/dim]")
        return

    # --- Step 2: Interactive selection (or --all) ---
    if include_all:
        selected = artifacts
    else:
        selected = interactive_select(console, artifacts)

    if not selected:
        console.print("\n[yellow]No artifacts selected. Aborting.[/yellow]")
        return

    selected_count = len(selected)
    if not yes and not include_all:
        if not Confirm.ask(f"\nSelected {selected_count} artifacts. Continue?", default=True):
            console.print("[yellow]Aborted.[/yellow]")
            return

    # --- Step 3: Collect metadata ---
    if pkg_name and pkg_version and pkg_description is not None:
        # Non-interactive mode
        config = CreatePackageConfig(
            project_path=project_path,
            package_name=pkg_name,
            version=pkg_version or "1.0.0",
            description=pkg_description or "",
            author=pkg_author or "",
            organize=OrganizeMode(organize) if organize else OrganizeMode.COPY,
            output_dir=Path(output_dir) if output_dir else project_path,
            dry_run=dry_run,
        )
    else:
        config = prompt_metadata(console, project_path)
        config.dry_run = dry_run
        config.output_dir = Path(output_dir) if output_dir else project_path
        if organize:
            config.organize = OrganizeMode(organize)

    # --- Step 4: Execute ---
    execute_create_package(config, selected, console)
