"""Archive creation and extraction for ``.aam`` packages.

Uses Python's built-in ``tarfile`` module with gzip compression.
Security checks enforce:
  - No symlinks pointing outside the package directory
  - No absolute paths in the archive
  - Total archive size must not exceed 50 MB (FR-012)

Decision reference: R-002 in research.md.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import os
import tarfile
from pathlib import Path

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

# Maximum archive size in bytes (50 MB per FR-012)
MAX_ARCHIVE_SIZE_BYTES: int = 50 * 1024 * 1024

# Archive file extension
ARCHIVE_EXTENSION: str = ".aam"

################################################################################
#                                                                              #
# FUNCTIONS                                                                    #
#                                                                              #
################################################################################


def create_archive(source_dir: Path, output_path: Path) -> Path:
    """Create a gzipped tar archive from a package directory.

    The archive includes all files under *source_dir* relative to
    *source_dir* itself (so ``aam.yaml`` appears at the archive root).

    Args:
        source_dir: Directory containing the package (must contain ``aam.yaml``).
        output_path: Target path for the ``.aam`` file.

    Returns:
        The path to the created archive.

    Raises:
        FileNotFoundError: If *source_dir* does not exist or has no ``aam.yaml``.
        ValueError: If the archive exceeds the 50 MB limit or contains
            unsafe entries (symlinks outside package, absolute paths).
    """
    logger.info(f"Creating archive: source='{source_dir}', output='{output_path}'")

    # -----
    # Step 1: Validate source directory
    # -----
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    manifest_path = source_dir / "aam.yaml"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"No aam.yaml found in {source_dir}. Run 'aam create-package' or 'aam init' first."
        )

    # -----
    # Step 2: Collect files and validate safety
    # -----
    resolved_source = source_dir.resolve()
    files_to_add: list[tuple[Path, str]] = []

    for root, dirs, filenames in os.walk(source_dir):
        root_path = Path(root)

        # -----
        # Skip excluded directories
        # -----
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {
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
            }
        ]

        for filename in filenames:
            full_path = root_path / filename
            rel_path = full_path.relative_to(source_dir)
            arcname = str(rel_path)

            # -----
            # Security: reject absolute paths in the archive
            # -----
            if rel_path.is_absolute():
                raise ValueError(f"Absolute path detected in archive: {rel_path}")

            # -----
            # Security: reject symlinks pointing outside package dir
            # -----
            if full_path.is_symlink():
                link_target = full_path.resolve()
                if not str(link_target).startswith(str(resolved_source)):
                    raise ValueError(
                        f"Symlink points outside package directory: {rel_path} -> {link_target}"
                    )

            files_to_add.append((full_path, arcname))

    logger.debug(f"Collected {len(files_to_add)} files for archive")

    # -----
    # Step 3: Create the gzipped tar archive
    # -----
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(output_path, "w:gz") as tar:
        for full_path, arcname in files_to_add:
            tar.add(full_path, arcname=arcname)

    # -----
    # Step 4: Enforce 50 MB size limit (FR-012)
    # -----
    archive_size = output_path.stat().st_size
    if archive_size > MAX_ARCHIVE_SIZE_BYTES:
        # Remove the oversized archive
        output_path.unlink(missing_ok=True)
        size_mb = archive_size / (1024 * 1024)
        raise ValueError(
            f"Archive size ({size_mb:.1f} MB) exceeds maximum of 50 MB. "
            "Reduce the number of files or exclude large assets."
        )

    size_kb = archive_size / 1024
    logger.info(
        f"Archive created successfully: path='{output_path}', "
        f"size={size_kb:.1f} KB, files={len(files_to_add)}"
    )

    return output_path


def extract_archive(archive_path: Path, dest_dir: Path) -> Path:
    """Extract a ``.aam`` archive to a destination directory.

    Validates archive entries for security before extraction:
      - No absolute paths
      - No path traversal (``..``)

    Args:
        archive_path: Path to the ``.aam`` archive file.
        dest_dir: Directory to extract into (created if missing).

    Returns:
        Path to the extraction directory.

    Raises:
        FileNotFoundError: If the archive does not exist.
        ValueError: If the archive contains unsafe entries.
        tarfile.TarError: If the archive is corrupted or not a valid tar.gz.
    """
    logger.info(f"Extracting archive: archive='{archive_path}', dest='{dest_dir}'")

    if not archive_path.is_file():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    resolved_dest = dest_dir.resolve()

    with tarfile.open(archive_path, "r:gz") as tar:
        # -----
        # Security: validate all members before extracting
        # -----
        for member in tar.getmembers():
            member_path = (dest_dir / member.name).resolve()

            # Reject path traversal
            if ".." in member.name.split("/"):
                raise ValueError(f"Path traversal detected in archive: {member.name}")

            # Reject absolute paths
            if member.name.startswith("/"):
                raise ValueError(f"Absolute path in archive: {member.name}")

            # Ensure extraction stays within dest_dir
            if not str(member_path).startswith(str(resolved_dest)):
                raise ValueError(f"Archive entry escapes destination: {member.name}")

        # -----
        # Extract all members (safe after validation)
        # -----
        tar.extractall(path=dest_dir, filter="data")

    logger.info(f"Archive extracted successfully: dest='{dest_dir}'")
    return dest_dir
