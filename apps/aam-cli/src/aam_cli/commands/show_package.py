"""Show package command for AAM CLI.

Displays detailed metadata about a package.  Works for both **installed**
packages (read from the lock file / local manifest) and **uninstalled**
packages discovered via the source artifact index.  When a package is not
installed, a GitHub link to the original artifact directory is shown so the
user can inspect it in the browser.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from aam_cli.core.config import SourceEntry, load_config
from aam_cli.core.manifest import load_manifest
from aam_cli.core.workspace import get_packages_dir, read_lock_file
from aam_cli.services.source_service import (
    ArtifactIndex,
    VirtualPackage,
    build_source_index,
)
from aam_cli.utils.git_url import GitSourceURL, parse
from aam_cli.utils.naming import parse_package_name, to_filesystem_name

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _find_source_entry(
    source_name: str,
    sources: list[SourceEntry],
) -> SourceEntry | None:
    """Find the SourceEntry whose ``name`` matches *source_name*.

    Args:
        source_name: Display name stored on the VirtualPackage.
        sources: All configured source entries from AAM config.

    Returns:
        Matching :class:`SourceEntry`, or ``None`` if not found.
    """
    for entry in sources:
        if entry.name == source_name:
            return entry
    return None


def _build_github_tree_url(
    parsed_url: GitSourceURL,
    commit_sha: str,
    source_path: str,
    artifact_path: str,
) -> str:
    """Build a GitHub ``tree`` URL pointing at the artifact directory.

    Args:
        parsed_url: Parsed git source URL with host/owner/repo.
        commit_sha: Commit SHA to pin the link to.
        source_path: Subdirectory scope configured on the source.
        artifact_path: Relative artifact path within the scoped dir.

    Returns:
        Full HTTPS URL to the artifact directory on the hosting
        platform (GitHub, GitLab, etc.).
    """
    # -----
    # Combine source scope path with artifact relative path
    # -----
    parts = [p for p in (source_path, artifact_path) if p]
    full_path = "/".join(parts)

    url = (
        f"https://{parsed_url.host}/{parsed_url.owner}/"
        f"{parsed_url.repo}/tree/{commit_sha}/{full_path}"
    )

    logger.debug(f"Built GitHub tree URL: {url}")
    return url


def _resolve_artifact_file(
    vp: VirtualPackage,
    source_entry: SourceEntry,
) -> Path | None:
    """Locate the primary artifact file in the local git cache.

    For skills the primary file is ``SKILL.md``; for other artifact
    types (prompts, instructions) it is the first ``.md`` file found
    in the artifact directory.

    Args:
        vp: The virtual package to locate.
        source_entry: Matching source entry (provides scope path).

    Returns:
        Absolute :class:`Path` to the artifact file, or ``None``
        if it cannot be found.
    """
    cache_dir = Path(vp.cache_dir)
    scan_root = (
        cache_dir / source_entry.path if source_entry.path else cache_dir
    )
    artifact_dir = scan_root / vp.path

    # -----
    # Skills always use SKILL.md
    # -----
    if vp.type == "skill":
        skill_md = artifact_dir / "SKILL.md"
        if skill_md.is_file():
            return skill_md

    # -----
    # Fallback: first .md file in the directory
    # -----
    if artifact_dir.is_dir():
        for md_file in sorted(artifact_dir.glob("*.md")):
            if md_file.is_file():
                return md_file

    logger.debug(f"No artifact file found in {artifact_dir}")
    return None


def _extract_frontmatter(file_path: Path) -> dict | None:
    """Parse YAML frontmatter delimited by ``---`` from a file.

    Reads only the frontmatter block at the top of the file (between
    two ``---`` lines).  Returns the parsed YAML as a dict, or
    ``None`` if no valid frontmatter is found.

    Args:
        file_path: Path to the markdown file.

    Returns:
        Parsed frontmatter dict, or ``None``.
    """
    try:
        with file_path.open("r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line != "---":
                return None

            # -----
            # Collect lines until the closing ---
            # -----
            fm_lines: list[str] = []
            for line in f:
                if line.strip() == "---":
                    break
                fm_lines.append(line)
            else:
                # Reached EOF without a closing ---
                return None

            raw = "\n".join(fm_lines)
            parsed = yaml.safe_load(raw)
            if isinstance(parsed, dict):
                return parsed
    except (OSError, yaml.YAMLError) as e:
        logger.debug(f"Failed to extract frontmatter from {file_path}: {e}")

    return None


def _render_frontmatter(
    console: Console,
    frontmatter: dict,
) -> None:
    """Render YAML frontmatter as a Rich panel.

    Displays the original key/value pairs in a bordered panel
    so the user can see the full artifact header metadata.

    Args:
        console: Rich console for output.
        frontmatter: Parsed frontmatter dict.
    """
    lines: list[str] = []
    for key, value in frontmatter.items():
        # -----
        # Wrap long values at ~72 chars for readability
        # -----
        value_str = str(value)
        lines.append(f"[bold]{key}:[/bold] {value_str}")

    body = Text.from_markup("\n".join(lines))
    panel = Panel(
        body,
        title="[bold]Artifact header[/bold]",
        border_style="dim",
        expand=False,
        padding=(0, 1),
    )
    console.print()
    console.print(panel)


def _resolve_from_index(
    name: str,
    index: ArtifactIndex,
) -> VirtualPackage | None:
    """Try to find a package in the source index by name.

    Attempts qualified name lookup first, then unqualified.

    Args:
        name: Package name (qualified ``source/name`` or plain).
        index: Pre-built artifact index.

    Returns:
        Matching :class:`VirtualPackage`, or ``None``.
    """
    # -----
    # Qualified name (contains "/")
    # -----
    if "/" in name:
        vp = index.by_qualified_name.get(name)
        if vp:
            return vp

    # -----
    # Unqualified name
    # -----
    matches = index.by_name.get(name)
    if matches:
        return matches[0]

    return None


def _show_installed_package(
    console: Console,
    ctx: click.Context,
    package: str,
    project_dir: Path,
) -> None:
    """Display full metadata for an installed package.

    Args:
        console: Rich console for output.
        ctx: Click context (used for exit codes).
        package: Package name.
        project_dir: Current working directory.
    """
    lock = read_lock_file(project_dir)
    locked = lock.packages.get(package)

    if not locked:
        # Should not happen — caller checks first. Guard for safety.
        console.print(f"[red]Error:[/red] '{package}' lock entry missing.")
        ctx.exit(1)
        return

    # -----
    # Load manifest from installed directory
    # -----
    scope, base_name = parse_package_name(package)
    fs_name = to_filesystem_name(scope, base_name)
    pkg_dir = get_packages_dir(project_dir) / fs_name

    try:
        manifest = load_manifest(pkg_dir)
    except FileNotFoundError:
        console.print(
            f"[red]Error:[/red] Package directory not found: {pkg_dir}"
        )
        ctx.exit(1)
        return

    # -----
    # Header with install status
    # -----
    console.print(f"[bold]{manifest.name}@{manifest.version}[/bold]")
    console.print("  Status:      [green]Installed[/green]")
    console.print(f"  Description: {manifest.description}")

    if manifest.author:
        console.print(f"  Author:      {manifest.author}")
    if manifest.license:
        console.print(f"  License:     {manifest.license}")
    if manifest.repository:
        console.print(f"  Repository:  {manifest.repository}")

    # -----
    # Artifacts
    # -----
    console.print("\n  [bold]Artifacts:[/bold]")
    for artifact_type, ref in manifest.all_artifacts:
        console.print(
            f"    {artifact_type}: [cyan]{ref.name}[/cyan]"
            f"           — {ref.description}"
        )

    # -----
    # Dependencies
    # -----
    console.print("\n  [bold]Dependencies:[/bold]")
    if manifest.dependencies:
        for dep_name, constraint in manifest.dependencies.items():
            dep_locked = lock.packages.get(dep_name)
            installed_str = (
                f" (installed: {dep_locked.version})" if dep_locked else ""
            )
            console.print(f"    {dep_name}  {constraint}{installed_str}")
    else:
        console.print("    None")

    # -----
    # Source info
    # -----
    console.print(f"\n  [bold]Source:[/bold] {locked.source}")
    if locked.checksum:
        console.print(f"  [bold]Checksum:[/bold] {locked.checksum}")


def _show_source_package(
    console: Console,
    vp: VirtualPackage,
    sources: list[SourceEntry],
) -> None:
    """Display metadata for an uninstalled package found in sources.

    Includes a GitHub link so the user can inspect the original
    artifact files directly in the browser.  When the artifact file
    contains YAML frontmatter (``---`` delimited), the header is
    displayed in a bordered panel.

    Args:
        console: Rich console for output.
        vp: Virtual package from the source index.
        sources: Configured source entries (used to resolve the URL).
    """
    # -----
    # Header with install status
    # -----
    console.print(
        f"[bold]{vp.name}[/bold]  source@{vp.commit_sha[:7]}"
    )
    console.print("  Status:      [yellow]Not installed[/yellow]")
    console.print(f"  Type:        {vp.type}")

    if vp.description:
        console.print(f"  Description: {vp.description}")

    console.print(f"  Source:      {vp.source_name}")
    console.print(f"  Commit:      {vp.commit_sha[:12]}")

    if vp.has_vendor_agent and vp.vendor_agent_file:
        console.print(f"  Vendor agent: {vp.vendor_agent_file}")

    # -----
    # Extract and display frontmatter from the artifact file
    # -----
    source_entry = _find_source_entry(vp.source_name, sources)

    if source_entry:
        artifact_file = _resolve_artifact_file(vp, source_entry)
        if artifact_file:
            frontmatter = _extract_frontmatter(artifact_file)
            if frontmatter:
                _render_frontmatter(console, frontmatter)

    # -----
    # Build GitHub link to the original artifact directory
    # -----
    if source_entry:
        try:
            parsed_url = parse(source_entry.url)
            github_url = _build_github_tree_url(
                parsed_url,
                vp.commit_sha,
                source_entry.path,
                vp.path,
            )
            console.print(
                f"\n  [bold]View on GitHub:[/bold]\n"
                f"  [link={github_url}]{github_url}[/link]"
            )
        except ValueError as e:
            logger.debug(f"Could not build GitHub URL: {e}")
    else:
        logger.debug(
            f"Source entry not found for '{vp.source_name}', "
            "skipping GitHub link."
        )

    # -----
    # Install hint
    # -----
    console.print(
        f"\n  [dim]To install, run:[/dim]  "
        f"[bold]aam install {vp.qualified_name}[/bold]"
    )


################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command("info")
@click.argument("package")
@click.pass_context
def show_package(ctx: click.Context, package: str) -> None:
    """Show detailed information about a package.

    Works for both installed packages (from the lock file) and
    uninstalled packages discovered in configured git sources.
    When a source package is not installed, a link to the original
    artifact on GitHub is provided.

    Examples::

        aam info my-package
        aam info @author/my-package
        aam info docs-changelog
    """
    console: Console = ctx.obj["console"]
    project_dir = Path.cwd()

    logger.info(f"Showing package info: package='{package}'")

    # -----
    # Step 1: Check if the package is installed
    # -----
    lock = read_lock_file(project_dir)
    is_installed = package in lock.packages

    if is_installed:
        logger.info(f"Package '{package}' is installed, showing local info")
        _show_installed_package(console, ctx, package, project_dir)
        return

    # -----
    # Step 2: Not installed — search the source artifact index
    # -----
    logger.info(
        f"Package '{package}' not installed, searching source index"
    )

    config = load_config()
    index = build_source_index(config)
    vp = _resolve_from_index(package, index)

    if vp:
        _show_source_package(console, vp, config.sources)
        return

    # -----
    # Step 3: Not found anywhere
    # -----
    console.print(
        f"[red]Error:[/red] '{package}' is not installed and was not "
        f"found in any configured source."
    )
    console.print(
        f"\n  [dim]Try:[/dim]  aam search {package}"
    )
    ctx.exit(1)
