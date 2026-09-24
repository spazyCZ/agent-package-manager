"""Package download cache service for AAM.

Manages a shared download cache at ``~/.aam/cache/`` for ``.aam`` archives.
Cache entries are keyed by ``package@version`` with integrity hash verification.

Reference: UAAPS v0.5.0 spec §11 packaging.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Any

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

CACHE_DIR: Path = Path.home() / ".aam" / "cache" / "packages"

################################################################################
#                                                                              #
# CACHE SERVICE                                                                #
#                                                                              #
################################################################################


def _cache_key(package_name: str, version: str) -> str:
    """Generate a filesystem-safe cache key.

    Args:
        package_name: Full package name (e.g. ``@scope/name``).
        version: Package version.

    Returns:
        Filesystem-safe key string.
    """
    safe_name = package_name.replace("@", "").replace("/", "-")
    return f"{safe_name}-{version}"


def _cache_path(package_name: str, version: str) -> Path:
    """Get the cache path for a package archive.

    Args:
        package_name: Full package name.
        version: Package version.

    Returns:
        Path to the cached archive.
    """
    return CACHE_DIR / f"{_cache_key(package_name, version)}.aam"


def get(package_name: str, version: str) -> Path | None:
    """Look up a cached package archive.

    Args:
        package_name: Full package name.
        version: Package version.

    Returns:
        Path to cached archive, or None if not cached.
    """
    cached = _cache_path(package_name, version)
    if cached.is_file():
        logger.debug(f"Cache hit: {package_name}@{version}")
        return cached
    logger.debug(f"Cache miss: {package_name}@{version}")
    return None


def put(package_name: str, version: str, archive_path: Path) -> Path:
    """Store a package archive in the cache.

    Args:
        package_name: Full package name.
        version: Package version.
        archive_path: Path to the archive to cache.

    Returns:
        Path to the cached copy.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = _cache_path(package_name, version)

    shutil.copy2(archive_path, dest)

    # Write integrity hash sidecar
    sha256 = hashlib.sha256(dest.read_bytes()).hexdigest()
    dest.with_suffix(".aam.sha256").write_text(
        f"{sha256}  {dest.name}\n", encoding="utf-8"
    )

    logger.info(f"Cached: {package_name}@{version} -> {dest}")
    return dest


def verify(package_name: str, version: str) -> bool:
    """Verify integrity of a cached archive.

    Args:
        package_name: Full package name.
        version: Package version.

    Returns:
        True if integrity check passes, False otherwise.
    """
    cached = _cache_path(package_name, version)
    sidecar = cached.with_suffix(".aam.sha256")

    if not cached.is_file() or not sidecar.is_file():
        return False

    actual_hash = hashlib.sha256(cached.read_bytes()).hexdigest()
    expected_line = sidecar.read_text(encoding="utf-8").strip()
    expected_hash = expected_line.split()[0]

    return actual_hash == expected_hash


def clean(package_name: str | None = None, version: str | None = None) -> int:
    """Clean cached archives.

    If package_name and version are given, removes only that entry.
    Otherwise removes all cached packages.

    Args:
        package_name: Optional package name to clean.
        version: Optional version to clean.

    Returns:
        Number of entries removed.
    """
    if package_name and version:
        cached = _cache_path(package_name, version)
        removed = 0
        if cached.is_file():
            cached.unlink()
            removed += 1
        sidecar = cached.with_suffix(".aam.sha256")
        if sidecar.is_file():
            sidecar.unlink()
        logger.info(f"Cleaned cache entry: {package_name}@{version}")
        return removed

    if not CACHE_DIR.is_dir():
        return 0

    count = 0
    for entry in CACHE_DIR.iterdir():
        if entry.suffix == ".aam":
            entry.unlink()
            sidecar = entry.with_suffix(".aam.sha256")
            if sidecar.is_file():
                sidecar.unlink()
            count += 1

    logger.info(f"Cleaned {count} cached packages")
    return count


def list_cached() -> list[dict[str, Any]]:
    """List all cached package archives.

    Returns:
        List of dicts with ``name``, ``size_bytes``, and ``path`` keys.
    """
    if not CACHE_DIR.is_dir():
        return []

    entries: list[dict[str, Any]] = []
    for entry in sorted(CACHE_DIR.iterdir()):
        if entry.suffix == ".aam":
            entries.append({
                "name": entry.stem,
                "size_bytes": entry.stat().st_size,
                "path": str(entry),
            })

    return entries
