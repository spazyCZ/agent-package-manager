"""Pack command for AAM CLI.

Builds a distributable ``.aam`` archive from a valid package directory.
Runs validation first, then creates the gzipped tar archive.

Generates per-file SHA-256 checksums during packing and includes them
in the archive metadata for post-install integrity verification.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import click
from rich.console import Console

from aam_cli.core.manifest import load_manifest
from aam_cli.services.checksum_service import compute_file_checksums
from aam_cli.utils.archive import create_archive
from aam_cli.utils.checksum import calculate_sha256
from aam_cli.utils.yaml_utils import dump_yaml, load_yaml

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
def pack(ctx: click.Context, path: str) -> None:
    """Build a distributable ``.aam`` archive.

    Validates the package first, then creates a gzipped tar archive.

    Examples::

        aam pack
        aam pack ./my-package/
    """
    console: Console = ctx.obj["console"]
    pkg_path = Path(path).resolve()

    # -----
    # Step 1: Load and validate the manifest
    # -----
    try:
        manifest = load_manifest(pkg_path)
    except FileNotFoundError:
        console.print(
            "[red]Error:[/red] No aam.yaml found. Run 'aam init' or 'aam create-package' first."
        )
        ctx.exit(1)
        return
    except Exception as exc:
        console.print(
            f"[red]Error:[/red] Package validation failed. Run 'aam validate' for details.\n{exc}"
        )
        ctx.exit(1)
        return

    console.print(f"Building [bold]{manifest.name}@{manifest.version}[/bold]...")

    # -----
    # Step 2: Check artifact paths exist
    # -----
    missing_paths: list[str] = []
    for _artifact_type, ref in manifest.all_artifacts:
        artifact_path = pkg_path / ref.path
        if not artifact_path.exists():
            missing_paths.append(ref.path)

    if missing_paths:
        console.print(
            "[red]Error:[/red] Package validation failed. Run 'aam validate' for details."
        )
        for mp in missing_paths:
            console.print(f"  [red]✗[/red] Missing: {mp}")
        ctx.exit(1)
        return

    # -----
    # Step 3: Compute per-file SHA-256 checksums for integrity tracking
    # -----
    console.print("  Computing per-file checksums...")
    file_checksums = compute_file_checksums(pkg_path)

    if file_checksums:
        # -----
        # Write checksums into aam.yaml so they are included in the archive
        # -----
        manifest_yaml_path = pkg_path / "aam.yaml"
        manifest_raw = load_yaml(manifest_yaml_path)
        manifest_raw["file_checksums"] = {
            "algorithm": "sha256",
            "files": file_checksums,
        }
        dump_yaml(manifest_raw, manifest_yaml_path)

        console.print(
            f"  [dim]{len(file_checksums)} file checksum(s) computed[/dim]"
        )
        logger.info(
            f"File checksums computed and written: "
            f"count={len(file_checksums)}"
        )

    # -----
    # Step 4: Log what's being added
    # -----
    console.print("  Adding aam.yaml")
    for _artifact_type, ref in manifest.all_artifacts:
        console.print(f"  Adding {ref.path}")

    # -----
    # Step 5: Create the archive
    # -----
    archive_name = f"{manifest.base_name}-{manifest.version}.aam"
    if manifest.scope:
        archive_name = f"{manifest.scope}-{manifest.base_name}-{manifest.version}.aam"

    output_path = pkg_path / archive_name

    try:
        create_archive(pkg_path, output_path)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return

    # -----
    # Step 6: Report results
    # -----
    checksum = calculate_sha256(output_path)
    size_bytes = output_path.stat().st_size

    if size_bytes >= 1024 * 1024:
        size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        size_str = f"{size_bytes / 1024:.1f} KB"

    console.print(f"\n[green]✓[/green] Built {archive_name} ({size_str})")
    console.print(f"  Checksum: {checksum}")

    logger.info(f"Pack complete: archive='{output_path}', size={size_bytes}, checksum='{checksum}'")
