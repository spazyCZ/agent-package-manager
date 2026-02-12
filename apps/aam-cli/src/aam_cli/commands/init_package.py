"""Init package command for AAM CLI.

Scaffolds a brand-new AAM package interactively using Rich prompts.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.prompt import Confirm, Prompt

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

ARTIFACT_TYPES: list[str] = ["skills", "agents", "prompts", "instructions"]
PLATFORM_NAMES: list[str] = ["cursor", "claude", "copilot", "codex"]

################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command("init")
@click.argument("name", required=False)
@click.pass_context
def init_package(ctx: click.Context, name: str | None) -> None:
    """Scaffold a new AAM package interactively.

    Creates an ``aam.yaml`` manifest and artifact directories.

    Examples::

        aam init
        aam init my-package
        aam init @author/my-package
    """
    console: Console = ctx.obj["console"]

    # -----
    # Step 1: Collect package metadata
    # -----
    default_name = name or Path.cwd().name

    while True:
        pkg_name = Prompt.ask("Package name", default=default_name)
        if validate_package_name(pkg_name):
            break
        console.print(
            "[red]Invalid package name.[/red] Use lowercase, hyphens, optional @scope/ prefix."
        )

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
    # Step 3: Select platforms
    # -----
    console.print("\n[bold]Which platforms should this package support?[/bold]")
    selected_platforms: list[str] = []

    for pname in PLATFORM_NAMES:
        default = pname == "cursor"
        if Confirm.ask(f"  {pname.capitalize()}", default=default):
            selected_platforms.append(pname)

    # -----
    # Step 4: Create directory structure
    # -----
    pkg_dir = Path.cwd() / pkg_name.split("/")[-1] if name else Path.cwd()

    if name:
        pkg_dir.mkdir(parents=True, exist_ok=True)

    for atype in selected_types:
        (pkg_dir / atype).mkdir(parents=True, exist_ok=True)

    # -----
    # Step 5: Generate aam.yaml
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

    platforms_config: dict[str, Any] = {}
    if "cursor" in selected_platforms:
        platforms_config["cursor"] = {
            "skill_scope": "project",
            "deploy_instructions_as": "rules",
        }
    if "claude" in selected_platforms:
        platforms_config["claude"] = {"merge_instructions": True}
    if "copilot" in selected_platforms:
        platforms_config["copilot"] = {"merge_instructions": True}
    if "codex" in selected_platforms:
        platforms_config["codex"] = {"skill_scope": "project"}

    manifest_data["platforms"] = platforms_config

    dump_yaml(manifest_data, pkg_dir / "aam.yaml")

    # -----
    # Step 6: Register default community sources
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
    # Step 7: Summary
    # -----
    display_name = pkg_name.split("/")[-1] if "/" in pkg_name else pkg_name

    console.print(f"\nCreated {display_name}/")
    console.print("  ├── aam.yaml")
    for idx, atype in enumerate(selected_types):
        prefix = "└──" if idx == len(selected_types) - 1 else "├──"
        console.print(f"  {prefix} {atype}/")

    console.print(f"\n[green]✓[/green] Package initialized: [bold]{pkg_name}[/bold]")

    logger.info(f"Initialized new package: name='{pkg_name}', dir='{pkg_dir}'")
