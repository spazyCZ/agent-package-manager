"""``aam pkg init`` — Scaffold a new AAM package.

Self-contained implementation that handles both fresh scaffolding and
``--migrate`` conversion from ``aam.yaml`` to ``package.agent.json``.

Reference: spec 004 US7.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.prompt import Confirm, Prompt

from aam_cli.core.manifest import load_manifest_universal
from aam_cli.utils.naming import format_invalid_package_name_message, validate_package_name

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

# Artifact types aligned with UAAPS v0.4.0+: skills, agents, instructions,
# commands (replaces deprecated prompts), and rules.
ARTIFACT_TYPES: list[str] = ["skills", "agents", "instructions", "commands", "rules"]

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _pkg_name_to_dir(pkg_name: str) -> str:
    """Convert a package name to a filesystem-safe directory name.

    Strips the leading ``@`` and replaces ``/`` with ``_`` so that
    ``@org/my-pkg`` becomes ``org_my-pkg``.

    Args:
        pkg_name: The full package name (e.g. ``"@org/my-pkg"`` or
            ``"my-pkg"``).

    Returns:
        A filesystem-safe directory name.
    """
    return pkg_name.lstrip("@").replace("/", "_")


################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command("init")
@click.argument("name", required=False)
@click.option(
    "--migrate",
    is_flag=True,
    default=False,
    help="Migrate an existing aam.yaml to package.agent.json format.",
)
@click.pass_context
def pkg_init(ctx: click.Context, name: str | None, migrate: bool) -> None:
    """Scaffold a new AAM package (generates ``package.agent.json``).

    Creates a ``package.agent.json`` manifest and artifact directories.
    Use ``--migrate`` to convert an existing ``aam.yaml`` to the new
    ``package.agent.json`` format.

    Examples::

        aam pkg init
        aam pkg init my-package
        aam pkg init @author/my-package
        aam pkg init --migrate
    """
    logger.info(f"pkg init invoked: name='{name}', migrate={migrate}")

    console: Console = ctx.obj["console"]

    # -----
    # Handle --migrate: read existing manifest and rewrite as JSON
    # -----
    if migrate:
        cwd = Path.cwd()
        try:
            manifest = load_manifest_universal(cwd)
        except FileNotFoundError:
            console.print(
                "[red]Error:[/red] No manifest found to migrate. "
                "Run 'aam pkg init' to create a new package."
            )
            ctx.exit(1)
            return

        json_path = cwd / "package.agent.json"
        json_path.write_text(
            json.dumps(manifest.model_dump(by_alias=True), indent=2) + "\n",
            encoding="utf-8",
        )
        console.print(
            f"[green]Migrated[/green] manifest to "
            f"[bold]package.agent.json[/bold] "
            f"(format: {manifest.manifest_format} -> json)"
        )
        return

    # -----
    # Step 1: Collect package metadata
    # -----
    default_name = name or Path.cwd().name

    while True:
        pkg_name = Prompt.ask("Package name (e.g. my-pkg, @scope/my-pkg)", default=default_name)
        if validate_package_name(pkg_name):
            break
        console.print(f"[red]{format_invalid_package_name_message(pkg_name)}[/red]")

    version = Prompt.ask("Version", default="1.0.0")
    description = Prompt.ask("Description", default="")
    author = Prompt.ask("Author", default="")
    license_str = Prompt.ask("License", default="Apache-2.0")

    # -----
    # Step 2: Select artifact types
    # -----
    console.print("\n[bold]What artifacts will this package contain?[/bold]")
    selected_types: list[str] = []

    for atype in ARTIFACT_TYPES:
        if Confirm.ask(f"  {atype.capitalize()}", default=True):
            selected_types.append(atype)

    # -----
    # Step 3: Create directory structure
    # -----
    if name:
        dir_name = _pkg_name_to_dir(pkg_name)
        pkg_dir = Path.cwd() / dir_name
        pkg_dir.mkdir(parents=True, exist_ok=True)
    else:
        pkg_dir = Path.cwd()

    for atype in selected_types:
        (pkg_dir / atype).mkdir(parents=True, exist_ok=True)

    # -----
    # Step 4: Generate package.agent.json
    # -----
    manifest_data: dict[str, Any] = {
        "name": pkg_name,
        "version": version,
        "description": description,
    }

    if author:
        manifest_data["author"] = author
    if license_str:
        manifest_data["license"] = license_str

    manifest_data["artifacts"] = {atype: [] for atype in ARTIFACT_TYPES}
    manifest_data["dependencies"] = {}

    manifest_path = pkg_dir / "package.agent.json"
    manifest_path.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

    # -----
    # Step 5: Register default community sources
    # -----
    try:
        from aam_cli.services.source_service import register_default_sources

        defaults_result = register_default_sources()
        if defaults_result["registered"]:
            console.print(
                f"\n[dim]Registered {len(defaults_result['registered'])} "
                f"default source(s):[/dim]"
            )
            for src_name in defaults_result["registered"]:
                console.print(f"  [dim]• {src_name}[/dim]")
            console.print(
                "[dim]Run 'aam source scan <name>' to browse available artifacts[/dim]"
            )
    except Exception as e:
        # -----
        # Default sources are nice-to-have — don't fail init
        # -----
        logger.warning(f"Failed to register default sources: {e}")

    # -----
    # Step 6: Summary
    # -----
    dir_label = _pkg_name_to_dir(pkg_name) if name else "."

    console.print(f"\nCreated {dir_label}/")
    console.print("  ├── package.agent.json")
    for idx, atype in enumerate(selected_types):
        prefix = "└──" if idx == len(selected_types) - 1 else "├──"
        console.print(f"  {prefix} {atype}/")

    console.print(f"\n[green]✓[/green] Package initialized: [bold]{pkg_name}[/bold]")

    logger.info(f"Initialized new package: name='{pkg_name}', dir='{pkg_dir}'")
