"""Local file-based registry implementation.

Implements the ``Registry`` Protocol using filesystem operations and YAML.
The registry directory has this structure:

    <registry_root>/
    ├── registry.yaml          # Registry metadata
    ├── index.yaml             # Package search index
    └── packages/
        └── <name>/
            ├── metadata.yaml  # Per-package version index
            └── versions/
                └── <ver>.aam  # Archive files

Decision reference: plan.md Key Decision 3.
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

from aam_cli.core.manifest import PackageManifest, load_manifest
from aam_cli.registry.base import (
    PackageIndexEntry,
    PackageMetadata,
    VersionInfo,
)
from aam_cli.utils.archive import extract_archive
from aam_cli.utils.checksum import calculate_sha256
from aam_cli.utils.naming import parse_package_name, to_filesystem_name
from aam_cli.utils.yaml_utils import dump_yaml, load_yaml, load_yaml_optional

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# LOCAL REGISTRY                                                               #
#                                                                              #
################################################################################


class LocalRegistry:
    """Local file-based registry implementation.

    All operations use only ``pathlib.Path`` and PyYAML — no database,
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

        meta_path = self._package_dir(name) / "metadata.yaml"
        if not meta_path.is_file():
            raise KeyError(f"Package '{name}' not found in registry '{self.name}'")

        data = load_yaml(meta_path)

        # -----
        # Parse versions list
        # -----
        versions: list[VersionInfo] = []
        for ver_data in data.get("versions", []):
            versions.append(VersionInfo(**ver_data))

        return PackageMetadata(
            name=data.get("name", name),
            description=data.get("description", ""),
            author=data.get("author"),
            license=data.get("license"),
            repository=data.get("repository"),
            keywords=data.get("keywords", []),
            dist_tags=data.get("dist_tags", {}),
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
          3. Update metadata.yaml
          4. Rebuild index.yaml

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
            manifest = load_manifest(tmp_path)

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
        # Step 4: Update metadata.yaml
        # -----
        checksum = calculate_sha256(version_archive)
        size = version_archive.stat().st_size
        now = datetime.now(UTC).isoformat()

        self._update_metadata(manifest, checksum, size, now)

        # -----
        # Step 5: Rebuild index.yaml
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

        registry_yaml = path / "registry.yaml"
        if registry_yaml.exists() and not force:
            raise ValueError(f"Registry already exists at {path}. Use --force to reinitialize.")

        # -----
        # Create directory structure
        # -----
        path.mkdir(parents=True, exist_ok=True)
        (path / "packages").mkdir(exist_ok=True)

        # -----
        # Write registry.yaml
        # -----
        now = datetime.now(UTC).isoformat()
        dump_yaml(
            {
                "name": path.name,
                "type": "local",
                "description": f"Local registry at {path}",
                "api_version": 1,
                "created_at": now,
            },
            registry_yaml,
        )

        # -----
        # Write empty index.yaml
        # -----
        dump_yaml({"packages": []}, path / "index.yaml")

        logger.info(f"Registry initialized: {path}")
        return cls(name=path.name, root=path)

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
        """Load the package index from ``index.yaml``."""
        index_data = load_yaml_optional(self.root / "index.yaml")
        entries: list[PackageIndexEntry] = []
        for pkg in index_data.get("packages", []):
            entries.append(PackageIndexEntry(**pkg))
        return entries

    def _update_metadata(
        self,
        manifest: PackageManifest,
        checksum: str,
        size: int,
        timestamp: str,
        tag: str = "latest",
    ) -> None:
        """Update or create the per-package metadata.yaml."""
        meta_path = self._package_dir(manifest.name) / "metadata.yaml"

        # -----
        # Load existing or create new
        # -----
        if meta_path.is_file():
            data = load_yaml(meta_path)
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
        # Update dist-tags
        # -----
        data.setdefault("dist_tags", {})[tag] = manifest.version

        dump_yaml(data, meta_path)

    def _rebuild_index(self) -> None:
        """Rebuild ``index.yaml`` from all per-package metadata files."""
        packages_dir = self.root / "packages"
        entries: list[dict[str, object]] = []

        if not packages_dir.is_dir():
            dump_yaml({"packages": []}, self.root / "index.yaml")
            return

        for pkg_dir in sorted(packages_dir.iterdir()):
            if not pkg_dir.is_dir():
                continue

            meta_path = pkg_dir / "metadata.yaml"
            if not meta_path.is_file():
                continue

            data = load_yaml(meta_path)
            latest_ver = data.get("dist_tags", {}).get("latest", "")

            # -----
            # Determine artifact types from the latest version's manifest
            # -----
            artifact_types: list[str] = []
            # We can infer from the version archive if needed, but for now
            # collect from the most recent metadata
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

        dump_yaml({"packages": entries}, self.root / "index.yaml")
        logger.debug(f"Index rebuilt: {len(entries)} packages")
