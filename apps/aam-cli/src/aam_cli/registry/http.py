"""HTTP registry client for remote AAM package registries.

Implements the UAAPS Registry Protocol over HTTP, supporting
package search, metadata retrieval, download, and publish.

Reference: UAAPS v0.5.0 spec §11 packaging.
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

import httpx

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# HTTP REGISTRY CLIENT                                                         #
#                                                                              #
################################################################################


class HttpRegistry:
    """HTTP-based AAM package registry client.

    Communicates with a remote registry server implementing the
    UAAPS Registry Protocol.
    """

    def __init__(self, url: str, token: str | None = None) -> None:
        """Initialize the HTTP registry client.

        Args:
            url: Base URL of the registry (e.g. ``https://registry.aam.dev``).
            token: Optional Bearer token for authentication.
        """
        self.url = url.rstrip("/")
        self.token = token

        headers: dict[str, str] = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self._client = httpx.Client(
            base_url=self.url,
            headers=headers,
            timeout=30.0,
        )
        logger.info(f"HTTP registry client initialized: url={self.url}")

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search for packages.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of package metadata dicts.
        """
        logger.info(f"Searching registry: query='{query}', limit={limit}")
        response = self._client.get(
            "/-/v1/search",
            params={"text": query, "size": limit},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data.get("objects", [])

    def get_metadata(self, package_name: str) -> dict[str, Any]:
        """Get full metadata for a package.

        Args:
            package_name: Full package name (e.g. ``@scope/name``).

        Returns:
            Package metadata dict.
        """
        logger.info(f"Fetching metadata: package={package_name}")
        response = self._client.get(f"/{package_name}")
        response.raise_for_status()
        return response.json()

    def get_version(
        self, package_name: str, version: str,
    ) -> dict[str, Any]:
        """Get metadata for a specific version.

        Args:
            package_name: Full package name.
            version: Exact version string.

        Returns:
            Version metadata dict.
        """
        logger.info(f"Fetching version: {package_name}@{version}")
        response = self._client.get(f"/{package_name}/{version}")
        response.raise_for_status()
        return response.json()

    def download(
        self,
        package_name: str,
        version: str,
        dest_dir: Path,
    ) -> Path:
        """Download a package archive.

        Args:
            package_name: Full package name.
            version: Exact version string.
            dest_dir: Directory to save the archive.

        Returns:
            Path to the downloaded archive.
        """
        logger.info(f"Downloading: {package_name}@{version}")
        metadata = self.get_version(package_name, version)
        tarball_url = metadata.get("dist", {}).get("tarball", "")

        if not tarball_url:
            raise ValueError(
                f"No tarball URL found for {package_name}@{version}"
            )

        response = self._client.get(tarball_url)
        response.raise_for_status()

        safe_name = package_name.replace("@", "").replace("/", "-")
        archive_path = dest_dir / f"{safe_name}-{version}.aam"
        archive_path.write_bytes(response.content)

        logger.info(f"Downloaded: {archive_path}")
        return archive_path

    def publish(
        self,
        archive_path: Path,
        tag: str = "latest",
    ) -> dict[str, Any]:
        """Publish a package archive.

        Args:
            archive_path: Path to the .aam archive.
            tag: Dist-tag to apply (default ``latest``).

        Returns:
            Server response dict.
        """
        logger.info(f"Publishing: {archive_path} with tag={tag}")
        with archive_path.open("rb") as f:
            response = self._client.put(
                "/-/v1/publish",
                content=f.read(),
                headers={"Content-Type": "application/octet-stream"},
                params={"tag": tag},
            )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        logger.info(f"Published successfully: {result}")
        return result

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
