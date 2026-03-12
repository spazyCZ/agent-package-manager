"""``aam pkg validate`` — Validate package manifest and artifacts.

Delegates to the existing validate command logic.

Reference: spec 004 US7.
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

from aam_cli.core.manifest import load_manifest_universal

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


@click.command("validate")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--permissions", is_flag=True, help="Include permissions security audit")
@click.pass_context
def pkg_validate(ctx: click.Context, path: str, permissions: bool) -> None:
    """Validate the package manifest and artifacts.

    Checks that ``aam.yaml`` is syntactically correct, all required fields
    are present, and all artifact paths exist.

    Examples::

        aam pkg validate
        aam pkg validate ./my-package/
    """
    console: Console = ctx.obj["console"]
    pkg_path = Path(path).resolve()

    # -----
    # Step 1: Parse and validate the manifest schema
    # -----
    errors: list[str] = []

    try:
        manifest = load_manifest_universal(pkg_path)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return
    except ValidationError as exc:
        console.print("Validating package...\n")
        console.print("[bold]Manifest:[/bold]")
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            errors.append(f"{field}: {message}")
            console.print(f"  [red]✗[/red] {field}: {message}")

        console.print(f"\n[red]✗[/red] {len(errors)} errors found. Fix them before packing.")
        ctx.exit(1)
        return
    except Exception as exc:
        console.print(f"[red]Error:[/red] Failed to parse manifest: {exc}")
        ctx.exit(1)
        return

    pkg_dir = pkg_path if pkg_path.is_dir() else pkg_path.parent

    console.print(f"Validating [bold]{manifest.name}@{manifest.version}[/bold]...\n")
    console.print(f"  [dim]manifest_format: {manifest.manifest_format}[/dim]")

    # -----
    # Show auto-discovery note when artifacts were not explicitly declared
    # -----
    if manifest.artifacts is None:
        console.print(
            "  [dim]artifacts_discovered: true "
            "(no artifacts section — auto-discovery active)[/dim]"
        )

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
        for dependency_name, constraint in manifest.dependencies.items():
            console.print(f"  [green]✓[/green] {dependency_name}: {constraint}")
    else:
        console.print("  [green]✓[/green] No dependencies declared")

    # -----
    # Step 4b: Permissions audit (optional or always shown)
    # -----
    if permissions or manifest.permissions is not None:
        from aam_cli.services.validate_service import _audit_permissions

        permission_warnings = _audit_permissions(manifest)

        console.print("\n[bold]Permissions Audit:[/bold]")
        if permission_warnings:
            for warning in permission_warnings:
                console.print(f"  [yellow]⚠[/yellow] {warning}")
        else:
            console.print("  [green]✓[/green] Permissions look reasonable")

    # -----
    # Step 5: Summary
    # -----
    if errors:
        console.print(f"\n[red]✗[/red] {len(errors)} errors found. Fix them before packing.")
        ctx.exit(1)
    else:
        console.print("\n[green]✓[/green] Package is valid and ready to publish")
