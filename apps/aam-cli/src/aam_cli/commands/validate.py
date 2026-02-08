"""Validate command for AAM CLI.

Validates a package's ``aam.yaml`` manifest against the Pydantic schema
and checks that all referenced artifact paths exist on disk.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import click
from pydantic import ValidationError
from rich.console import Console

from aam_cli.core.manifest import load_manifest

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.pass_context
def validate(ctx: click.Context, path: str) -> None:
    """Validate the package manifest and artifacts.

    Checks that ``aam.yaml`` is syntactically correct, all required fields
    are present, and all artifact paths exist.

    Examples::

        aam validate
        aam validate ./my-package/
    """
    console: Console = ctx.obj["console"]
    pkg_path = Path(path).resolve()
    manifest_file = pkg_path / "aam.yaml" if pkg_path.is_dir() else pkg_path

    if not manifest_file.exists():
        console.print(
            "[red]Error:[/red] No aam.yaml found. Run 'aam create-package' or 'aam init' first."
        )
        ctx.exit(1)
        return

    errors: list[str] = []
    pkg_dir = manifest_file.parent

    # -----
    # Step 1: Parse and validate the manifest schema
    # -----
    try:
        manifest = load_manifest(pkg_dir)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return
    except ValidationError as exc:
        console.print("Validating package...\n")
        console.print("[bold]Manifest:[/bold]")
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            errors.append(f"{field}: {msg}")
            console.print(f"  [red]✗[/red] {field}: {msg}")

        console.print(f"\n[red]✗[/red] {len(errors)} errors found. Fix them before packing.")
        ctx.exit(1)
        return
    except Exception as exc:
        console.print(f"[red]Error:[/red] Failed to parse aam.yaml: {exc}")
        ctx.exit(1)
        return

    console.print(f"Validating [bold]{manifest.name}@{manifest.version}[/bold]...\n")

    # -----
    # Step 2: Report manifest field validations
    # -----
    console.print("[bold]Manifest:[/bold]")
    console.print("  [green]✓[/green] name: valid format")
    console.print("  [green]✓[/green] version: valid semver")

    if manifest.description:
        console.print("  [green]✓[/green] description: present")
    else:
        errors.append("description: empty")
        console.print("  [red]✗[/red] description: empty")

    if manifest.author:
        console.print("  [green]✓[/green] author: present")
    else:
        console.print("  [dim]  ⚠ author: not set (optional)[/dim]")

    # -----
    # Step 3: Validate artifact paths exist
    # -----
    console.print("\n[bold]Artifacts:[/bold]")

    for artifact_type, ref in manifest.all_artifacts:
        artifact_path = pkg_dir / ref.path
        label = f"{artifact_type}: {ref.name}"

        if artifact_path.exists():
            console.print(f"  [green]✓[/green] {label}")
            console.print(f"    [green]✓[/green] {ref.path} exists")
        else:
            errors.append(f"{ref.path}: file not found")
            console.print(f"  [red]✗[/red] {label}")
            console.print(f"    [red]✗[/red] {ref.path}: file not found")

    # -----
    # Step 4: Validate dependencies
    # -----
    console.print("\n[bold]Dependencies:[/bold]")
    if manifest.dependencies:
        for dep_name, constraint in manifest.dependencies.items():
            console.print(f"  [green]✓[/green] {dep_name}: {constraint}")
    else:
        console.print("  [green]✓[/green] No dependencies declared")

    # -----
    # Step 5: Summary
    # -----
    if errors:
        console.print(f"\n[red]✗[/red] {len(errors)} errors found. Fix them before packing.")
        ctx.exit(1)
    else:
        console.print("\n[green]✓[/green] Package is valid and ready to publish")
