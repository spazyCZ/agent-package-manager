"""Create-package command for AAM CLI.

Scans an existing project for skills, agents, prompts, and instructions
that are not yet managed by AAM, and packages them into an AAM package
with interactive artifact selection.

Supports filtering by platform (cursor, copilot, claude, codex) so users
can pick artifacts from specific source directories like ``.cursor/`` or
``.github/``.

Also supports ``--from-source`` to create packages from remote git
sources that have been registered with ``aam source add``.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from aam_cli.detection.scanner import (
    KNOWN_PLATFORMS,
    DetectedArtifact,
    scan_project,
)
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

# Rich colour for each platform badge
PLATFORM_COLORS: dict[str, str] = {
    "cursor": "bright_blue",
    "copilot": "bright_green",
    "claude": "bright_yellow",
    "codex": "bright_magenta",
}

################################################################################
#                                                                              #
# INTERACTIVE SELECTION                                                        #
#                                                                              #
################################################################################


def _platform_badge(platform: str | None) -> str:
    """Return a Rich-formatted platform badge string."""
    if not platform:
        return ""
    colour = PLATFORM_COLORS.get(platform, "dim")
    return f" [{colour}][{platform}][/{colour}]"


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
            badge = _platform_badge(art.platform)
            console.print(
                f"    [{check}] {display_idx:>2}. [cyan]{art.name:<20}[/cyan]"
                f" {art.source_path}{badge}"
            )
            display_idx += 1


def _interactive_select(
    console: Console,
    artifacts: list[DetectedArtifact],
) -> list[DetectedArtifact]:
    """Let the user interactively toggle artifact selection.

    All artifacts are selected by default. Entering a number toggles that
    artifact on or off.  Pressing Enter with **no input** confirms the
    current selection and proceeds to the next step.

    Args:
        console: Rich console for output.
        artifacts: Detected artifacts to present.

    Returns:
        list[DetectedArtifact]: The artifacts the user chose to keep.
    """
    if not artifacts:
        return []

    # -----
    # All selected by default
    # -----
    selected: set[int] = set(range(len(artifacts)))

    console.print("\n[bold]Found artifacts:[/bold]")
    _display_detected(console, artifacts, selected)

    console.print(
        "\n[dim]Enter numbers (space-separated) to toggle selection on/off.[/dim]"
    )
    console.print(
        "[dim]  [bold]a[/bold] = select all  |  "
        "[bold]n[/bold] = select none  |  "
        "[bold]Enter[/bold] (empty) = confirm & continue[/dim]"
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
        # -----
        # Show current selection count in the prompt so the user always
        # knows how many items are selected and what to do next.
        # -----
        prompt_label = (
            f"\n({len(selected)}/{len(artifacts)} selected) "
            f"Toggle # / Enter=confirm"
        )
        response = Prompt.ask(prompt_label, default="").strip().lower()

        if response == "":
            # -----
            # Empty input → confirm selection and exit the loop
            # -----
            break
        elif response == "a":
            selected = set(range(len(artifacts)))
            _display_detected(console, artifacts, selected)
        elif response == "n":
            selected = set()
            _display_detected(console, artifacts, selected)
        else:
            # -----
            # Toggle individual items and provide feedback
            # -----
            toggled_labels: list[str] = []
            for token in response.split():
                if token.isdigit():
                    disp = int(token)
                    real = display_to_real.get(disp)
                    if real is not None:
                        if real in selected:
                            selected.discard(real)
                            toggled_labels.append(f"−{disp}")
                        else:
                            selected.add(real)
                            toggled_labels.append(f"+{disp}")
                    else:
                        console.print(
                            f"  [yellow]Unknown item: {disp}[/yellow]"
                        )
            _display_detected(console, artifacts, selected)
            if toggled_labels:
                console.print(
                    f"  [dim]Toggled: {', '.join(toggled_labels)} — "
                    f"{len(selected)}/{len(artifacts)} selected[/dim]"
                )

    logger.info(
        f"Interactive selection complete: "
        f"{len(selected)}/{len(artifacts)} artifacts selected"
    )
    return [artifacts[i] for i in sorted(selected)]


################################################################################
#                                                                              #
# SCAN SUMMARY                                                                 #
#                                                                              #
################################################################################


def _print_scan_summary(
    console: Console,
    artifacts: list[DetectedArtifact],
) -> None:
    """Print a compact summary table of the scan results."""
    # -----
    # Count by platform
    # -----
    by_platform: dict[str, int] = {}
    for art in artifacts:
        key = art.platform or "generic"
        by_platform[key] = by_platform.get(key, 0) + 1

    # -----
    # Count by type
    # -----
    by_type: dict[str, int] = {}
    for art in artifacts:
        by_type[art.type] = by_type.get(art.type, 0) + 1

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("label", style="dim")
    table.add_column("value")

    # Type summary
    type_parts = [f"{count} {t}s" for t, count in by_type.items()]
    table.add_row("Artifacts:", ", ".join(type_parts))

    # Platform summary
    platform_parts = []
    for plat, count in by_platform.items():
        colour = PLATFORM_COLORS.get(plat, "dim")
        platform_parts.append(f"[{colour}]{plat}[/{colour}] ({count})")
    table.add_row("Sources:", ", ".join(platform_parts))

    console.print()
    console.print(table)


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
# FROM-SOURCE PACKAGING                                                        #
#                                                                              #
################################################################################


def _create_from_source(
    ctx: click.Context,
    console: Console,
    source_name: str,
    artifact_names: list[str],
    artifact_types: list[str],
    include_all: bool,
    pkg_name: str | None,
    pkg_scope: str | None,
    pkg_version: str | None,
    pkg_description: str | None,
    pkg_author: str | None,
    dry_run: bool,
    output_dir: Path,
    yes: bool,
) -> None:
    """Create a package from a registered remote git source.

    Scans the source cache for artifacts, lets the user select which
    to include, copies them to the output directory, generates an
    ``aam.yaml`` with provenance metadata, and computes per-file
    checksums.

    Args:
        ctx: Click context.
        console: Rich console for output.
        source_name: Registered source name (e.g. ``openai/skills``).
        artifact_names: Specific artifact names to include.
        artifact_types: Filter by artifact types.
        include_all: Include all discovered artifacts.
        pkg_name: Override package name.
        pkg_scope: Override scope prefix.
        pkg_version: Override version.
        pkg_description: Override description.
        pkg_author: Override author.
        dry_run: Preview without writing.
        output_dir: Directory to write package into.
        yes: Skip confirmation prompts.
    """
    from aam_cli.services.source_service import scan_source

    logger.info(
        f"Creating package from source: source='{source_name}', "
        f"artifacts={artifact_names}"
    )

    # -----
    # Step 1: Scan the source for artifacts
    # -----
    console.print(
        f"\n[bold]Scanning source [cyan]{source_name}[/cyan] "
        f"for artifacts...[/bold]"
    )

    try:
        scan_result = scan_source(source_name)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return

    artifacts = scan_result.get("artifacts", [])

    if not artifacts:
        console.print(
            f"[yellow]No artifacts found in source '{source_name}'.[/yellow]"
        )
        return

    # -----
    # Step 2: Filter by type if requested
    # -----
    if artifact_types:
        type_set = set(artifact_types)
        artifacts = [a for a in artifacts if a["type"] in type_set]

    # -----
    # Step 3: Filter by specific artifact names if requested
    # -----
    if artifact_names:
        name_set = set(artifact_names)
        artifacts = [a for a in artifacts if a["name"] in name_set]

        # Warn about names that were not found
        found_names = {a["name"] for a in artifacts}
        missing_names = name_set - found_names
        if missing_names:
            for missing in sorted(missing_names):
                console.print(
                    f"[yellow]Warning:[/yellow] Artifact '{missing}' "
                    f"not found in source '{source_name}'"
                )

    if not artifacts:
        console.print(
            "[yellow]No matching artifacts after filtering. Aborting.[/yellow]"
        )
        return

    # -----
    # Step 4: Display and confirm selection
    # -----
    console.print(
        f"\n  Found [bold]{len(artifacts)}[/bold] artifact(s) "
        f"in source [cyan]{source_name}[/cyan]:"
    )

    table = Table(show_header=True, box=None, padding=(0, 2))
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Description", style="dim")

    for idx, art in enumerate(artifacts, 1):
        desc = (art.get("description") or "")[:60]
        table.add_row(str(idx), art["name"], art["type"], desc)

    console.print(table)

    if (
        not include_all
        and not artifact_names
        and not yes
        and not Confirm.ask(
            f"\nInclude all {len(artifacts)} artifacts?",
            default=True,
        )
    ):
        console.print("[yellow]Aborted.[/yellow]")
        return

    # -----
    # Step 5: Collect metadata (interactive or from options)
    # -----
    if pkg_scope and pkg_name and not pkg_name.startswith("@"):
        pkg_name = f"@{pkg_scope}/{pkg_name}"

    if pkg_name and pkg_version and pkg_description is not None:
        name = pkg_name
        version = pkg_version or "1.0.0"
        description = pkg_description or ""
        author = pkg_author or ""
        license_str = "Apache-2.0"
    else:
        default_name = source_name.replace("/", "-")
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
                "[red]Invalid package name.[/red] "
                "Use lowercase, hyphens, optional @scope/ prefix."
            )

        version = Prompt.ask("Version", default=pkg_version or "1.0.0")
        description = Prompt.ask("Description", default=pkg_description or "")
        author = Prompt.ask("Author", default=pkg_author or "")
        license_str = Prompt.ask("License", default="Apache-2.0")

    # -----
    # Step 6: Build provenance metadata from scan result
    # (source_entry details will be enriched below for non-dry-run)
    # -----
    provenance_data = {
        "source_type": "git",
        "source_url": source_name,
        "source_ref": "",
        "source_path": scan_result.get("scan_path", ""),
        "source_commit": scan_result.get("commit", ""),
        "fetched_at": datetime.now(UTC).isoformat(),
    }

    # -----
    # Step 7: Generate manifest with provenance
    # -----
    grouped: dict[str, list[dict]] = {
        "agents": [],
        "skills": [],
        "prompts": [],
        "instructions": [],
    }
    for art in artifacts:
        art_type = art["type"]
        type_key = art_type + "s"

        if art_type in ("skill", "agent"):
            target_path = f"{type_key}/{art['name']}/"
        else:
            target_path = f"{type_key}/{art['name']}.md"

        grouped[type_key].append({
            "name": art["name"],
            "path": target_path,
            "description": art.get("description") or f"{art_type.capitalize()} {art['name']}",
        })

    manifest_data: dict = {
        "name": name,
        "version": version,
        "description": description,
    }
    if author:
        manifest_data["author"] = author
    if license_str:
        manifest_data["license"] = license_str

    manifest_data["artifacts"] = grouped
    manifest_data["dependencies"] = {}
    manifest_data["provenance"] = provenance_data
    manifest_data["platforms"] = {
        "cursor": {
            "skill_scope": "project",
            "deploy_instructions_as": "rules",
        },
    }

    # -----
    # Step 10: Copy files and write manifest
    # -----
    if dry_run:
        console.print("\n[bold]Would create:[/bold]")
        console.print("  aam.yaml (with provenance)")
        for art in artifacts:
            art_type = art["type"]
            type_key = art_type + "s"
            if art_type in ("skill", "agent"):
                console.print(f"  {type_key}/{art['name']}/")
            else:
                console.print(f"  {type_key}/{art['name']}.md")

        import yaml
        content = yaml.safe_dump(
            manifest_data, default_flow_style=False, sort_keys=False
        )
        console.print("\n[yellow]\\[Dry run — no files written][/yellow]")
        console.print(Panel(content, title="aam.yaml", border_style="blue"))
        return

    console.print("\n[bold]Creating package from remote source...[/bold]")

    # -----
    # Step 9: Resolve source cache path for file copying
    # -----
    from aam_cli.core.config import load_config
    from aam_cli.services.git_service import get_cache_dir, validate_cache
    from aam_cli.utils.git_url import parse

    config = load_config()
    source_entry = None
    for s in config.sources:
        if s.name == source_name:
            source_entry = s
            break

    if source_entry is None:
        console.print(
            f"[red]Error:[/red] Source '{source_name}' not found in config"
        )
        ctx.exit(1)
        return

    parsed = parse(source_entry.url)
    cache_dir = get_cache_dir(parsed.host, parsed.owner, parsed.repo)

    if not validate_cache(cache_dir):
        console.print(
            f"[red]Error:[/red] Source cache is missing or corrupted. "
            f"Run 'aam source update {source_name}' to re-clone."
        )
        ctx.exit(1)
        return

    # Determine scan root (apply path scope)
    scan_root = cache_dir / source_entry.path if source_entry.path else cache_dir

    # Enrich provenance with actual source entry details
    provenance_data["source_url"] = source_entry.url
    provenance_data["source_ref"] = source_entry.ref
    provenance_data["source_path"] = source_entry.path or ""
    manifest_data["provenance"] = provenance_data

    # -----
    # Step 10: Copy artifact files from cache to output directory
    # -----
    for art in artifacts:
        art_type = art["type"]
        type_key = art_type + "s"
        art_path = art.get("path", "")

        # Source: the artifact in the cached clone
        src = scan_root / art_path if art_path else scan_root / art["name"]

        # Destination: canonical AAM structure
        if art_type in ("skill", "agent"):
            dest = output_dir / type_key / art["name"]
        else:
            dest = output_dir / type_key / f"{art['name']}.md"

        dest.parent.mkdir(parents=True, exist_ok=True)

        if src.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            console.print(
                f"  [green]✓[/green] Copied {art['name']} → {type_key}/{art['name']}/"
            )
        elif src.is_file():
            shutil.copy2(src, dest)
            console.print(
                f"  [green]✓[/green] Copied {art['name']} → {type_key}/{art['name']}.md"
            )
        else:
            console.print(
                f"  [yellow]⚠[/yellow] Skipped {art['name']} (source not found at {src})"
            )

    # -----
    # Step 11: Compute per-file checksums for the package
    # -----
    from aam_cli.services.checksum_service import compute_file_checksums

    file_checksums = compute_file_checksums(output_dir)

    # Store checksums in manifest metadata (separate section)
    if file_checksums:
        manifest_data["file_checksums"] = {
            "algorithm": "sha256",
            "files": file_checksums,
        }

    # -----
    # Step 12: Write aam.yaml manifest
    # -----
    manifest_path = output_dir / "aam.yaml"
    dump_yaml(manifest_data, manifest_path)
    console.print("  [green]✓[/green] Created aam.yaml (with provenance)")

    # -----
    # Summary
    # -----
    type_counts: dict[str, int] = {}
    for art in artifacts:
        label = art["type"] + "s"
        type_counts[label] = type_counts.get(label, 0) + 1

    parts = [f"{count} {label}" for label, count in type_counts.items()]
    summary = ", ".join(parts)

    console.print(
        f"\n[green]✓[/green] Package created: [bold]{name}@{version}[/bold]"
    )
    console.print(f"  {len(artifacts)} artifacts ({summary})")
    console.print(f"  Source: [cyan]{source_name}[/cyan] @ {scan_result.get('commit', '?')[:8]}")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  [cyan]aam validate[/cyan]    — verify the package is well-formed")
    console.print("  [cyan]aam pack[/cyan]        — build distributable .aam archive")
    console.print("  [cyan]aam publish[/cyan]     — publish to registry")

    logger.info(
        f"Package created from source: name='{name}', version='{version}', "
        f"source='{source_name}', artifacts={len(artifacts)}"
    )


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
    "--platform",
    "-p",
    "platforms",
    multiple=True,
    type=click.Choice(sorted(KNOWN_PLATFORMS), case_sensitive=False),
    help="Filter to artifacts from a specific platform (cursor, copilot, claude, codex)",
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
@click.option(
    "--from-source",
    "from_source",
    default=None,
    help="Create package from a registered remote source (e.g. 'openai/skills')",
)
@click.option(
    "--artifacts",
    "artifact_names",
    multiple=True,
    help="Select specific artifacts by name when using --from-source (repeatable)",
)
@click.pass_context
def create_package(
    ctx: click.Context,
    path: str,
    include_all: bool,
    artifact_types: tuple[str, ...],
    platforms: tuple[str, ...],
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
    from_source: str | None,
    artifact_names: tuple[str, ...],
) -> None:
    """Create an AAM package from an existing project or remote source.

    Scans the project for artifacts in .cursor/, .github/, and other
    platform directories, lets you pick which to include, then generates
    ``aam.yaml`` and copies files into an AAM package.

    Use ``--from-source`` to create a package from a registered remote
    git source instead of scanning a local project.

    Examples::

        aam create-package
        aam create-package ./my-project/
        aam create-package --platform cursor
        aam create-package --platform cursor --platform copilot
        aam create-package --platform cursor --type skill --type prompt
        aam create-package --all --name my-pkg --yes
        aam create-package --from-source openai/skills --all --name my-skills --yes
        aam create-package --from-source openai/skills --artifacts gh-fix-ci --artifacts coder
    """
    console: Console = ctx.obj["console"]
    project_path = Path(path)
    out_dir = Path(output_dir) if output_dir else project_path

    # -----
    # Route to from-source flow if --from-source is provided
    # -----
    if from_source:
        _create_from_source(
            ctx=ctx,
            console=console,
            source_name=from_source,
            artifact_names=list(artifact_names),
            artifact_types=list(artifact_types),
            include_all=include_all,
            pkg_name=pkg_name,
            pkg_scope=pkg_scope,
            pkg_version=pkg_version,
            pkg_description=pkg_description,
            pkg_author=pkg_author,
            dry_run=dry_run,
            output_dir=out_dir,
            yes=yes,
        )
        return

    # -----
    # Step 1: Detect artifacts (with optional platform filter)
    # -----
    platform_list = list(platforms) if platforms else None
    if platform_list:
        console.print(
            f"\n[bold]Scanning for artifacts from "
            f"[cyan]{', '.join(platform_list)}[/cyan]...[/bold]"
        )
    else:
        console.print("\n[bold]Scanning for artifacts not managed by AAM...[/bold]")

    artifacts = scan_project(project_path, platforms=platform_list)

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
        if platform_list:
            console.print(
                f"[dim]Tried platform(s): {', '.join(platform_list)}. "
                f"Try without --platform to scan everything.[/dim]"
            )
        else:
            console.print("[dim]Use 'aam init' to create a new package from scratch.[/dim]")
        return

    # -----
    # Show scan summary table
    # -----
    _print_scan_summary(console, artifacts)

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
        license_str = "Apache-2.0"
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
        license_str = Prompt.ask("License", default="Apache-2.0")

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
