"""Create-package command for AAM CLI.

Scans an existing project for skills, agents, prompts, and instructions
that are not yet managed by AAM, and packages them into an AAM package
with interactive artifact selection.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from aam_cli.detection.scanner import DetectedArtifact, scan_project
from aam_cli.utils.naming import validate_package_name
from aam_cli.utils.yaml_utils import dump_yaml

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

# Artifact type ordering for display
TYPE_ORDER: list[str] = ["skill", "agent", "prompt", "instruction"]

################################################################################
#                                                                              #
# INTERACTIVE SELECTION                                                        #
#                                                                              #
################################################################################


def _display_detected(
    console: Console,
    artifacts: list[DetectedArtifact],
    selected: set[int],
) -> None:
    """Display detected artifacts grouped by type with selection checkboxes."""
    grouped: dict[str, list[tuple[int, DetectedArtifact]]] = {}
    for idx, art in enumerate(artifacts):
        grouped.setdefault(art.type, []).append((idx, art))

    display_idx = 1
    for atype in TYPE_ORDER:
        group = grouped.get(atype, [])
        if not group:
            continue

        label = atype.capitalize() + "s"
        console.print(f"\n  [bold]{label} ({len(group)}):[/bold]")

        for real_idx, art in group:
            check = "[green]x[/green]" if real_idx in selected else " "
            console.print(
                f"    [{check}] {display_idx:>2}. [cyan]{art.name:<20}[/cyan] {art.source_path}"
            )
            display_idx += 1


def _interactive_select(
    console: Console,
    artifacts: list[DetectedArtifact],
) -> list[DetectedArtifact]:
    """Let the user interactively toggle artifact selection."""
    if not artifacts:
        return []

    # All selected by default
    selected: set[int] = set(range(len(artifacts)))

    console.print("\n[bold]Found artifacts:[/bold]")
    _display_detected(console, artifacts, selected)

    console.print("\n[dim]Toggle items by entering their number (space-separated).[/dim]")
    console.print(
        "[dim]Press [bold]enter[/bold] to confirm, "
        "[bold]a[/bold] to select all, "
        "[bold]n[/bold] to select none.[/dim]"
    )

    # -----
    # Build display-index → real-index mapping
    # -----
    display_to_real: dict[int, int] = {}
    display_idx = 1
    for atype in TYPE_ORDER:
        for real_idx, art in enumerate(artifacts):
            if art.type == atype:
                display_to_real[display_idx] = real_idx
                display_idx += 1

    while True:
        response = Prompt.ask("\nToggle / confirm", default="").strip().lower()

        if response == "":
            break
        elif response == "a":
            selected = set(range(len(artifacts)))
            _display_detected(console, artifacts, selected)
        elif response == "n":
            selected = set()
            _display_detected(console, artifacts, selected)
        else:
            for token in response.split():
                if token.isdigit():
                    disp = int(token)
                    real = display_to_real.get(disp)
                    if real is not None:
                        if real in selected:
                            selected.discard(real)
                        else:
                            selected.add(real)
            _display_detected(console, artifacts, selected)

    return [artifacts[i] for i in sorted(selected)]


################################################################################
#                                                                              #
# MANIFEST GENERATION                                                          #
#                                                                              #
################################################################################


def _artifact_target_path(art: DetectedArtifact, organize: str) -> str:
    """Compute the target path for an artifact in the generated aam.yaml."""
    if organize == "reference":
        return str(art.source_path)

    # For copy / move: map into canonical AAM structure
    type_dirs = {
        "skill": "skills",
        "agent": "agents",
        "prompt": "prompts",
        "instruction": "instructions",
    }
    base = type_dirs[art.type]

    if art.type in ("skill", "agent"):
        return f"{base}/{art.name}/"
    return f"{base}/{art.name}.md"


def _generate_manifest_dict(
    name: str,
    version: str,
    description: str,
    author: str,
    license_str: str,
    artifacts: list[DetectedArtifact],
    organize: str,
) -> dict:
    """Generate the aam.yaml manifest data as a dict."""
    grouped: dict[str, list[dict]] = {
        "agents": [],
        "skills": [],
        "prompts": [],
        "instructions": [],
    }

    for art in artifacts:
        target = _artifact_target_path(art, organize)
        ref = {
            "name": art.name,
            "path": target,
            "description": art.description or f"{art.type.capitalize()} {art.name}",
        }
        grouped[art.type + "s"].append(ref)

    data: dict = {
        "name": name,
        "version": version,
        "description": description,
    }
    if author:
        data["author"] = author
    if license_str:
        data["license"] = license_str

    data["artifacts"] = grouped
    data["dependencies"] = {}
    data["platforms"] = {
        "cursor": {
            "skill_scope": "project",
            "deploy_instructions_as": "rules",
        },
    }

    return data


################################################################################
#                                                                              #
# FILE OPERATIONS                                                              #
#                                                                              #
################################################################################


def _copy_artifact(
    project_path: Path,
    art: DetectedArtifact,
    output_dir: Path,
    organize: str,
    console: Console,
    dry_run: bool,
) -> None:
    """Copy or move a single artifact into the AAM package structure."""
    target_rel = _artifact_target_path(art, organize)
    source = project_path / art.source_path
    dest = output_dir / target_rel

    if dry_run:
        console.print(f"  [dim]Would copy: {art.source_path} → {target_rel}[/dim]")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)

    if source.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        if organize == "move":
            shutil.rmtree(source)
    elif source.is_file():
        shutil.copy2(source, dest)
        if organize == "move":
            source.unlink()

    console.print(f"  [green]✓[/green] Copied {art.source_path} → {target_rel}")


################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command("create-package")
@click.argument(
    "path",
    default=".",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
)
@click.option("--all", "include_all", is_flag=True, help="Include all detected artifacts")
@click.option(
    "--type",
    "-t",
    "artifact_types",
    multiple=True,
    type=click.Choice(["skill", "agent", "prompt", "instruction"], case_sensitive=False),
    help="Filter detection to specific artifact types",
)
@click.option(
    "--organize",
    type=click.Choice(["copy", "reference", "move"], case_sensitive=False),
    default="copy",
    help="File organization mode",
)
@click.option(
    "--include", "includes", multiple=True, type=click.Path(), help="Manually include file/dir"
)
@click.option(
    "--include-as",
    type=click.Choice(["skill", "agent", "prompt", "instruction"], case_sensitive=False),
    default=None,
    help="Artifact type for --include",
)
@click.option("--name", "pkg_name", default=None, help="Package name")
@click.option("--scope", "pkg_scope", default=None, help="Scope prefix")
@click.option("--version", "pkg_version", default=None, help="Package version")
@click.option("--description", "pkg_description", default=None, help="Package description")
@click.option("--author", "pkg_author", default=None, help="Package author")
@click.option("--dry-run", is_flag=True, help="Preview without writing")
@click.option("--output-dir", type=click.Path(file_okay=False, resolve_path=True), default=None)
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompts")
@click.pass_context
def create_package(
    ctx: click.Context,
    path: str,
    include_all: bool,
    artifact_types: tuple[str, ...],
    organize: str,
    includes: tuple[str, ...],
    include_as: str | None,
    pkg_name: str | None,
    pkg_scope: str | None,
    pkg_version: str | None,
    pkg_description: str | None,
    pkg_author: str | None,
    dry_run: bool,
    output_dir: str | None,
    yes: bool,
) -> None:
    """Create an AAM package from an existing project.

    Scans the project for artifacts, lets you select which to include,
    then generates ``aam.yaml`` and copies files.

    Examples::

        aam create-package
        aam create-package ./my-project/
        aam create-package --all --name my-pkg --yes
        aam create-package --type skill --type agent
    """
    console: Console = ctx.obj["console"]
    project_path = Path(path)
    out_dir = Path(output_dir) if output_dir else project_path

    # -----
    # Step 1: Detect artifacts
    # -----
    console.print("\n[bold]Scanning for artifacts not managed by AAM...[/bold]")
    artifacts = scan_project(project_path)

    # Filter by type if requested
    if artifact_types:
        type_set = set(artifact_types)
        artifacts = [a for a in artifacts if a.type in type_set]

    # Add manual includes
    if includes:
        inc_type = include_as or "skill"
        for inc_path in includes:
            inc = Path(inc_path)
            artifacts.append(
                DetectedArtifact(
                    name=inc.stem if inc.is_file() else inc.name,
                    type=inc_type,
                    source_path=inc,
                    description=f"Manually included from {inc}",
                )
            )

    if not artifacts:
        console.print("\n[yellow]No unmanaged artifacts found in this project.[/yellow]")
        console.print("[dim]Use 'aam init' to create a new package from scratch.[/dim]")
        return

    # -----
    # Step 2: Interactive selection (or --all)
    # -----
    selected = artifacts if include_all else _interactive_select(console, artifacts)

    if not selected:
        console.print("\n[yellow]No artifacts selected. Aborting.[/yellow]")
        return

    if (
        not yes
        and not include_all
        and not Confirm.ask(
            f"\nSelected {len(selected)} artifacts. Continue?",
            default=True,
        )
    ):
        console.print("[yellow]Aborted.[/yellow]")
        return

    # -----
    # Step 3: Collect metadata
    # -----
    if pkg_scope and pkg_name and not pkg_name.startswith("@"):
        pkg_name = f"@{pkg_scope}/{pkg_name}"

    if pkg_name and pkg_version and pkg_description is not None:
        # Non-interactive mode
        name = pkg_name
        version = pkg_version or "1.0.0"
        description = pkg_description or ""
        author = pkg_author or ""
        license_str = "MIT"
    else:
        # Interactive prompts
        default_name = project_path.resolve().name
        if pkg_scope:
            default_name = f"@{pkg_scope}/{default_name}"

        while True:
            name = Prompt.ask(
                "Package name",
                default=pkg_name or default_name,
            )
            if validate_package_name(name):
                break
            console.print(
                "[red]Invalid package name.[/red] Use lowercase, hyphens, optional @scope/ prefix."
            )

        version = Prompt.ask("Version", default=pkg_version or "1.0.0")
        description = Prompt.ask("Description", default=pkg_description or "")
        author = Prompt.ask("Author", default=pkg_author or "")
        license_str = Prompt.ask("License", default="MIT")

    # -----
    # Step 4: Generate manifest
    # -----
    manifest_data = _generate_manifest_dict(
        name,
        version,
        description,
        author,
        license_str,
        selected,
        organize,
    )

    manifest_path = out_dir / "aam.yaml"

    if dry_run:
        console.print("\n[bold]Would create:[/bold]")
        console.print("  aam.yaml")
        if organize != "reference":
            for art in selected:
                _copy_artifact(
                    project_path,
                    art,
                    out_dir,
                    organize,
                    console,
                    dry_run=True,
                )
        import yaml

        content = yaml.safe_dump(manifest_data, default_flow_style=False, sort_keys=False)
        console.print("\n[yellow]\\[Dry run — no files written][/yellow]")
        console.print(Panel(content, title="aam.yaml", border_style="blue"))
        return

    # -----
    # Step 5: Write files
    # -----
    console.print("\n[bold]Creating package...[/bold]")

    dump_yaml(manifest_data, manifest_path)
    console.print("  [green]✓[/green] Created aam.yaml")

    if organize != "reference":
        for art in selected:
            _copy_artifact(
                project_path,
                art,
                out_dir,
                organize,
                console,
                dry_run=False,
            )

    # -----
    # Summary
    # -----
    type_counts: dict[str, int] = {}
    for art in selected:
        label = art.type + "s"
        type_counts[label] = type_counts.get(label, 0) + 1

    parts = [f"{count} {label}" for label, count in type_counts.items()]
    summary = ", ".join(parts)

    console.print(f"\n[green]✓[/green] Package created: [bold]{name}@{version}[/bold]")
    console.print(f"  {len(selected)} artifacts ({summary})")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  [cyan]aam validate[/cyan]    — verify the package is well-formed")
    console.print("  [cyan]aam pack[/cyan]        — build distributable .aam archive")
    console.print("  [cyan]aam publish[/cyan]     — publish to registry")
