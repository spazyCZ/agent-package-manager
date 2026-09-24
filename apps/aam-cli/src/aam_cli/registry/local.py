"""Local file-based registry implementation.

Implements the ``Registry`` Protocol using filesystem operations and JSON.
The registry directory has this structure:

    <registry_root>/
    ├── registry.json          # Registry metadata
    ├── index.json             # Package search index
    └── packages/
        └── <name>/
            ├── meta.json      # Per-package version index
            ├── dist-tags.json # Dist-tag → version mapping
            └── versions/
                ├── <ver>.aam        # Archive files
                └── <ver>.aam.sha256 # SHA-256 sidecar

Backward-compatible: auto-migrates legacy YAML files on first access.

Decision reference: plan.md Key Decision 3.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import hashlib
import json
import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aam_cli.core.manifest import PackageManifest, load_manifest_universal
from aam_cli.registry.base import (
    PackageIndexEntry,
    PackageMetadata,
    VersionInfo,
)
from aam_cli.utils.archive import extract_archive
from aam_cli.utils.checksum import calculate_sha256
from aam_cli.utils.naming import parse_package_name, to_filesystem_name

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# JSON I/O HELPERS                                                             #
#                                                                              #
################################################################################


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON content as a dictionary.

    Raises:
        FileNotFoundError: If *path* does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_optional(path: Path) -> dict[str, Any]:
    """Load a JSON file, returning an empty dict if it does not exist.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed content or empty dict.
    """
    if not path.is_file():
        return {}
    return _load_json(path)


def _dump_json(data: dict[str, Any] | list[Any], path: Path) -> None:
    """Dump data to a JSON file.

    Args:
        data: Data to serialize.
        path: Target file path (parent directories must exist).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


################################################################################
#                                                                              #
# SHA-256 SIDECAR                                                              #
#                                                                              #
################################################################################


def _write_sha256_sidecar(archive_path: Path) -> Path:
    """Generate a SHA-256 sidecar file for a package archive.

    Args:
        archive_path: Path to the .aam archive file.

    Returns:
        Path to the generated .aam.sha256 sidecar file.
    """
    sha256_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    sidecar_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    sidecar_path.write_text(
        f"{sha256_hash}  {archive_path.name}\n", encoding="utf-8"
    )
    return sidecar_path


################################################################################
#                                                                              #
# LOCAL REGISTRY                                                               #
#                                                                              #
################################################################################


class LocalRegistry:
    """Local file-based registry implementation.

    All operations use only ``pathlib.Path`` and JSON — no database,
    no network, no external services.
    """

    def __init__(self, name: str, root: Path) -> None:
        """Initialize a local registry.

        Args:
            name: User-defined name for this registry.
            root: Root directory of the local registry.
        """
        self.name = name
        self.root = root.resolve()

        # Auto-migrate legacy YAML files if present
        self._migrate_yaml_to_json()

    # ------------------------------------------------------------------
    # Registry Protocol methods
    # ------------------------------------------------------------------

    def search(self, query: str) -> list[PackageIndexEntry]:
        """Search packages using case-insensitive substring matching.

        Matches against name, description, and keywords per R-004.

        Args:
            query: Search terms.

        Returns:
            List of matching index entries.
        """
        logger.info(f"Searching local registry '{self.name}': query='{query}'")

        index = self._load_index()
        query_lower = query.lower()

        results: list[PackageIndexEntry] = []
        for entry in index:
            if (
                query_lower in entry.name.lower()
                or query_lower in entry.description.lower()
                or any(query_lower in kw.lower() for kw in entry.keywords)
            ):
                results.append(entry)

        logger.info(f"Search returned {len(results)} results")
        return results

    def get_metadata(self, name: str) -> PackageMetadata:
        """Get detailed metadata for a specific package.

        Args:
            name: Full package name.

        Returns:
            Package metadata.

        Raises:
            KeyError: If the package does not exist.
        """
        logger.debug(f"Getting metadata: name='{name}'")

        meta_path = self._package_dir(name) / "meta.json"
        if not meta_path.is_file():
            raise KeyError(f"Package '{name}' not found in registry '{self.name}'")

        data = _load_json(meta_path)

        # -----
        # Parse versions list
        # -----
        versions: list[VersionInfo] = []
        for ver_data in data.get("versions", []):
            versions.append(VersionInfo(**ver_data))

        # -----
        # Load dist-tags from dedicated file, fall back to inline
        # -----
        dist_tags = self._load_dist_tags(name)
        if not dist_tags:
            dist_tags = data.get("dist_tags", {})

        return PackageMetadata(
            name=data.get("name", name),
            description=data.get("description", ""),
            author=data.get("author"),
            license=data.get("license"),
            repository=data.get("repository"),
            keywords=data.get("keywords", []),
            dist_tags=dist_tags,
            versions=versions,
        )

    def get_versions(self, name: str) -> list[str]:
        """List all available versions of a package.

        Args:
            name: Full package name.

        Returns:
            List of version strings.

        Raises:
            KeyError: If the package does not exist.
        """
        metadata = self.get_metadata(name)
        return [v.version for v in metadata.versions]

    def download(self, name: str, version: str, dest: Path) -> Path:
        """Copy a package archive to a destination directory.

        Args:
            name: Full package name.
            version: Exact version to download.
            dest: Destination directory.

        Returns:
            Path to the copied archive.

        Raises:
            KeyError: If the package/version does not exist.
        """
        logger.info(f"Downloading: name='{name}', version='{version}'")

        archive_path = self._version_archive_path(name, version)
        if not archive_path.is_file():
            raise KeyError(f"Version {version} of '{name}' not found in registry '{self.name}'")

        dest.mkdir(parents=True, exist_ok=True)
        dest_path = dest / archive_path.name
        shutil.copy2(archive_path, dest_path)

        logger.info(f"Downloaded: {dest_path}")
        return dest_path

    def publish(self, archive_path: Path) -> None:
        """Publish a package archive to this registry.

        Steps:
          1. Extract the archive to read aam.yaml
          2. Copy the archive to packages/<name>/versions/<ver>.aam
          3. Generate SHA-256 sidecar
          4. Update meta.json
          5. Update dist-tags.json
          6. Rebuild index.json

        Args:
            archive_path: Path to the ``.aam`` archive.

        Raises:
            ValueError: If the version already exists.
            FileNotFoundError: If the archive does not exist.
        """
        logger.info(f"Publishing to registry '{self.name}': {archive_path}")

        if not archive_path.is_file():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        # -----
        # Step 1: Extract to a temp directory to read aam.yaml
        # -----
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            extract_archive(archive_path, tmp_path)
            manifest = load_manifest_universal(tmp_path)

        # -----
        # Step 2: Check for duplicate version
        # -----
        pkg_dir = self._package_dir(manifest.name)
        versions_dir = pkg_dir / "versions"
        versions_dir.mkdir(parents=True, exist_ok=True)

        version_archive = versions_dir / f"{manifest.version}.aam"
        if version_archive.is_file():
            raise ValueError(
                f"{manifest.name}@{manifest.version} already published. "
                "Bump the version in aam.yaml."
            )

        # -----
        # Step 3: Copy archive
        # -----
        shutil.copy2(archive_path, version_archive)

        # -----
        # Step 4: Generate SHA-256 sidecar
        # -----
        sidecar = _write_sha256_sidecar(version_archive)
        logger.debug(f"SHA-256 sidecar written: {sidecar}")

        # -----
        # Step 5: Update meta.json
        # -----
        checksum = calculate_sha256(version_archive)
        size = version_archive.stat().st_size
        now = datetime.now(UTC).isoformat()

        self._update_metadata(manifest, checksum, size, now)

        # -----
        # Step 6: Update dist-tags.json
        # -----
        self._update_dist_tags(manifest.name, "latest", manifest.version)

        # -----
        # Step 7: Rebuild index.json
        # -----
        self._rebuild_index()

        logger.info(f"Published {manifest.name}@{manifest.version} to registry '{self.name}'")

    # ------------------------------------------------------------------
    # Registry initialization
    # ------------------------------------------------------------------

    @classmethod
    def init_registry(
        cls,
        path: Path,
        force: bool = False,
    ) -> "LocalRegistry":
        """Create a new local registry directory structure.

        Args:
            path: Directory for the new registry.
            force: Overwrite existing registry if True.

        Returns:
            Initialized :class:`LocalRegistry` instance.

        Raises:
            ValueError: If the registry already exists (and not force).
        """
        logger.info(f"Initializing local registry: path='{path}'")

        registry_json = path / "registry.json"
        if registry_json.exists() and not force:
            raise ValueError(f"Registry already exists at {path}. Use --force to reinitialize.")

        # -----
        # Create directory structure
        # -----
        path.mkdir(parents=True, exist_ok=True)
        (path / "packages").mkdir(exist_ok=True)

        # -----
        # Write registry.json
        # -----
        now = datetime.now(UTC).isoformat()
        _dump_json(
            {
                "name": path.name,
                "type": "local",
                "description": f"Local registry at {path}",
                "api_version": 1,
                "created_at": now,
            },
            registry_json,
        )

        # -----
        # Write empty index.json
        # -----
        _dump_json({"packages": []}, path / "index.json")

        logger.info(f"Registry initialized: {path}")
        return cls(name=path.name, root=path)

    # ------------------------------------------------------------------
    # YAML → JSON migration
    # ------------------------------------------------------------------

    def _migrate_yaml_to_json(self) -> None:
        """Auto-migrate legacy YAML registry files to JSON format.

        Checks for legacy ``registry.yaml``, ``index.yaml``, and per-package
        ``metadata.yaml`` files.  If found and corresponding JSON files do
        not yet exist, converts them in-place.
        """
        migrated = False

        # -----
        # Migrate registry.yaml → registry.json
        # -----
        yaml_registry = self.root / "registry.yaml"
        json_registry = self.root / "registry.json"
        if yaml_registry.is_file() and not json_registry.is_file():
            self._migrate_single_yaml(yaml_registry, json_registry)
            migrated = True

        # -----
        # Migrate index.yaml → index.json
        # -----
        yaml_index = self.root / "index.yaml"
        json_index = self.root / "index.json"
        if yaml_index.is_file() and not json_index.is_file():
            self._migrate_single_yaml(yaml_index, json_index)
            migrated = True

        # -----
        # Migrate per-package metadata.yaml → meta.json
        # -----
        packages_dir = self.root / "packages"
        if packages_dir.is_dir():
            for pkg_dir in packages_dir.iterdir():
                if not pkg_dir.is_dir():
                    continue
                yaml_meta = pkg_dir / "metadata.yaml"
                json_meta = pkg_dir / "meta.json"
                if yaml_meta.is_file() and not json_meta.is_file():
                    data = self._migrate_single_yaml(yaml_meta, json_meta)
                    # Extract dist_tags into separate file
                    dist_tags = data.get("dist_tags", {})
                    if dist_tags:
                        dist_tags_path = pkg_dir / "dist-tags.json"
                        if not dist_tags_path.is_file():
                            _dump_json(dist_tags, dist_tags_path)
                    migrated = True

        if migrated:
            logger.warning(
                "Legacy YAML registry files detected and auto-migrated to JSON. "
                "You may remove the old .yaml files."
            )

    @staticmethod
    def _migrate_single_yaml(yaml_path: Path, json_path: Path) -> dict[str, Any]:
        """Migrate a single YAML file to JSON.

        Args:
            yaml_path: Source YAML file.
            json_path: Destination JSON file.

        Returns:
            The parsed data dict.
        """
        import yaml

        logger.info(f"Migrating {yaml_path} → {json_path}")
        text = yaml_path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        if data is None:
            data = {}
        _dump_json(data, json_path)
        return data

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _package_dir(self, name: str) -> Path:
        """Get the filesystem directory for a package.

        Converts scoped names (``@scope/name``) to filesystem-safe
        format (``scope--name``).
        """
        scope, base_name = parse_package_name(name)
        fs_name = to_filesystem_name(scope, base_name)
        return self.root / "packages" / fs_name

    def _version_archive_path(self, name: str, version: str) -> Path:
        """Get the path to a specific version's archive."""
        return self._package_dir(name) / "versions" / f"{version}.aam"

    def _load_index(self) -> list[PackageIndexEntry]:
        """Load the package index from ``index.json``."""
        index_data = _load_json_optional(self.root / "index.json")
        entries: list[PackageIndexEntry] = []
        for pkg in index_data.get("packages", []):
            entries.append(PackageIndexEntry(**pkg))
        return entries

    def _load_dist_tags(self, name: str) -> dict[str, str]:
        """Load dist-tags for a package from ``dist-tags.json``.

        Args:
            name: Full package name.

        Returns:
            Dict mapping tag names to version strings.
        """
        dist_tags_path = self._package_dir(name) / "dist-tags.json"
        return _load_json_optional(dist_tags_path)

    def _update_dist_tags(self, name: str, tag: str, version: str) -> None:
        """Update a dist-tag for a package.

        Args:
            name: Full package name.
            tag: Tag name (e.g. ``latest``).
            version: Version string to associate with the tag.
        """
        dist_tags_path = self._package_dir(name) / "dist-tags.json"
        dist_tags = _load_json_optional(dist_tags_path)
        dist_tags[tag] = version
        _dump_json(dist_tags, dist_tags_path)

    def _update_metadata(
        self,
        manifest: PackageManifest,
        checksum: str,
        size: int,
        timestamp: str,
        tag: str = "latest",
    ) -> None:
        """Update or create the per-package meta.json."""
        meta_path = self._package_dir(manifest.name) / "meta.json"

        # -----
        # Load existing or create new
        # -----
        if meta_path.is_file():
            data = _load_json(meta_path)
        else:
            data = {
                "name": manifest.name,
                "description": manifest.description,
                "author": manifest.author,
                "license": manifest.license,
                "repository": manifest.repository,
                "keywords": manifest.keywords,
                "dist_tags": {},
                "versions": [],
            }

        # -----
        # Update metadata fields from latest publish
        # -----
        data["description"] = manifest.description
        data["author"] = manifest.author
        data["license"] = manifest.license
        data["keywords"] = manifest.keywords

        # -----
        # Add version entry
        # -----
        version_entry = {
            "version": manifest.version,
            "published": timestamp,
            "checksum": checksum,
            "size": size,
            "dependencies": manifest.dependencies,
        }
        data.setdefault("versions", []).append(version_entry)

        # -----
        # Update dist-tags inline (also maintained in dist-tags.json)
        # -----
        data.setdefault("dist_tags", {})[tag] = manifest.version

        _dump_json(data, meta_path)

    def _rebuild_index(self) -> None:
        """Rebuild ``index.json`` from all per-package metadata files."""
        packages_dir = self.root / "packages"
        entries: list[dict[str, object]] = []

        if not packages_dir.is_dir():
            _dump_json({"packages": []}, self.root / "index.json")
            return

        for pkg_dir in sorted(packages_dir.iterdir()):
            if not pkg_dir.is_dir():
                continue

            meta_path = pkg_dir / "meta.json"
            if not meta_path.is_file():
                continue

            data = _load_json(meta_path)
            latest_ver = data.get("dist_tags", {}).get("latest", "")

            artifact_types: list[str] = []
            versions = data.get("versions", [])
            last_published = ""
            if versions:
                last_published = versions[-1].get("published", "")

            entries.append(
                {
                    "name": data.get("name", pkg_dir.name),
                    "description": data.get("description", ""),
                    "latest": latest_ver,
                    "keywords": data.get("keywords", []),
                    "artifact_types": artifact_types,
                    "updated_at": last_published,
                }
            )

        _dump_json({"packages": entries}, self.root / "index.json")
        logger.debug(f"Index rebuilt: {len(entries)} packages")
