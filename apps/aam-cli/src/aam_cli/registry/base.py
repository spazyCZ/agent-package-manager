"""Registry Protocol — abstract interface for package registries.

All registry implementations (local file, git, HTTP) conform to this
Protocol so that commands can interact with any registry backend
through a unified API.

Contracts reference: cli-commands.md Section 8.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# INDEX MODELS                                                                 #
#                                                                              #
################################################################################


class PackageIndexEntry(BaseModel):
    """A single entry in the registry package index."""

    name: str
    description: str
    latest: str  # Latest version
    keywords: list[str] = []
    artifact_types: list[str] = []  # [agent, skill, prompt, instruction]
    updated_at: str = ""  # ISO 8601


class VersionInfo(BaseModel):
    """Version-level metadata for a published package."""

    version: str
    published: str  # ISO 8601
    checksum: str  # sha256:<hex>
    size: int  # bytes
    dependencies: dict[str, str] = {}  # name -> constraint


class PackageMetadata(BaseModel):
    """Full per-package metadata from the registry."""

    name: str
    description: str
    author: str | None = None
    license: str | None = None
    repository: str | None = None
    keywords: list[str] = []
    dist_tags: dict[str, str] = {}  # tag -> version
    versions: list[VersionInfo] = []


################################################################################
#                                                                              #
# REGISTRY PROTOCOL                                                            #
#                                                                              #
################################################################################


@runtime_checkable
class Registry(Protocol):
    """Abstract registry interface.

    All registry backends must implement these methods.
    """

    name: str

    def search(self, query: str) -> list[PackageIndexEntry]:
        """Search the registry for packages matching *query*.

        Args:
            query: Search terms (case-insensitive substring match).

        Returns:
            List of matching index entries.
        """
        ...

    def get_metadata(self, name: str) -> PackageMetadata:
        """Get detailed metadata for a specific package.

        Args:
            name: Full package name.

        Returns:
            Package metadata including all versions.

        Raises:
            KeyError: If the package does not exist.
        """
        ...

    def get_versions(self, name: str) -> list[str]:
        """List all available versions of a package.

        Args:
            name: Full package name.

        Returns:
            List of version strings, newest first.

        Raises:
            KeyError: If the package does not exist.
        """
        ...

    def download(self, name: str, version: str, dest: Path) -> Path:
        """Download a specific package version.

        Args:
            name: Full package name.
            version: Exact version to download.
            dest: Destination directory for the ``.aam`` file.

        Returns:
            Path to the downloaded archive file.

        Raises:
            KeyError: If the package/version does not exist.
        """
        ...

    def publish(self, archive_path: Path) -> None:
        """Publish a package archive to this registry.

        Args:
            archive_path: Path to the ``.aam`` archive file.

        Raises:
            ValueError: If the version already exists.
        """
        ...
