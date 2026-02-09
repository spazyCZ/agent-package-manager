"""MCP resource definitions for AAM.

Exposes read-only data endpoints that IDE agents can pull for project
context without invoking tools. All resources read fresh from filesystem
on each request (no caching).
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from aam_cli.services.config_service import get_config
from aam_cli.services.package_service import (
    get_package_info,
    list_installed_packages,
)
from aam_cli.services.registry_service import list_registries
from aam_cli.services.source_service import (
    list_candidates,
    list_sources,
    scan_source,
)
from aam_cli.utils.yaml_utils import load_yaml_optional

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# RESOURCE REGISTRATION                                                        #
#                                                                              #
################################################################################


def register_resources(mcp: FastMCP) -> None:
    """Register all MCP resources on the given FastMCP instance.

    Args:
        mcp: FastMCP server instance to register resources on.
    """

    @mcp.resource("aam://config")
    def resource_config() -> dict[str, Any]:
        """Read the merged AAM configuration.

        Returns the full merged configuration from global, project,
        and default sources.

        Returns:
            Full merged config dict.
        """
        logger.debug("MCP resource aam://config accessed")
        result = get_config(key=None)
        return result["value"]

    @mcp.resource("aam://packages/installed")
    def resource_packages_installed() -> list[dict[str, Any]]:
        """List all installed AAM packages.

        Returns a list of installed packages with version, source,
        and artifact counts.

        Returns:
            List of installed package info dicts.
        """
        logger.debug("MCP resource aam://packages/installed accessed")
        return list_installed_packages()

    @mcp.resource("aam://packages/{name}")
    def resource_package_detail(name: str) -> dict[str, Any] | None:
        """Read detailed metadata for a specific installed package.

        Scoped package names use double-hyphen convention in the URI:
        ``aam://packages/scope--my-package`` for ``@scope/my-package``.

        Args:
            name: Package name (use ``--`` for scope separator).

        Returns:
            Package detail dict, or None if not found.
        """
        logger.debug(f"MCP resource aam://packages/{name} accessed")

        # -----
        # Handle scoped names with double-hyphen convention
        # -----
        package_name = name
        if "--" in name:
            parts = name.split("--", 1)
            package_name = f"@{parts[0]}/{parts[1]}"

        try:
            return get_package_info(package_name=package_name)
        except ValueError:
            logger.debug(f"Package not found: {package_name}")
            return None

    @mcp.resource("aam://registries")
    def resource_registries() -> list[dict[str, Any]]:
        """List all configured AAM registries.

        Returns:
            List of registry info dicts.
        """
        logger.debug("MCP resource aam://registries accessed")
        return list_registries()

    @mcp.resource("aam://manifest")
    def resource_manifest() -> dict[str, Any] | None:
        """Read the aam.yaml manifest from the current directory.

        Returns the parsed manifest contents, or None if no aam.yaml
        exists in the current working directory.

        Returns:
            Parsed manifest dict, or None if not found.
        """
        logger.debug("MCP resource aam://manifest accessed")

        manifest_path = Path.cwd() / "aam.yaml"

        if not manifest_path.exists():
            return None

        try:
            data = load_yaml_optional(manifest_path)
            return data
        except Exception as exc:
            logger.warning(f"Failed to parse aam.yaml: {exc}")
            return {"error": f"Failed to parse aam.yaml: {exc}"}

    ############################################################################
    #                                                                          #
    # SOURCE RESOURCES (spec 003)                                              #
    #                                                                          #
    ############################################################################

    @mcp.resource("aam://sources")
    def resource_sources() -> list[dict[str, Any]]:
        """List all configured remote git sources.

        Returns source entries with name, URL, ref, last commit,
        last fetched time, artifact count, and default status.

        Returns:
            List of source info dicts.
        """
        logger.debug("MCP resource aam://sources accessed")
        result = list_sources()
        return result.get("sources", [])

    @mcp.resource("aam://sources/{source_id}")
    def resource_source_detail(source_id: str) -> dict[str, Any] | None:
        """Read detailed info for a specific source including artifacts.

        Source names containing ``/`` use double-hyphen convention in URI:
        ``aam://sources/openai--skills`` for source ``openai/skills``.

        Args:
            source_id: Source identifier (use ``--`` for ``/`` separator).

        Returns:
            Source detail dict with artifacts, or None if not found.
        """
        # -----
        # Convert double-hyphen URI convention back to slash name
        # -----
        source_name = source_id.replace("--", "/") if "--" in source_id else source_id
        logger.debug(f"MCP resource aam://sources/{source_id} accessed (name={source_name})")
        try:
            return scan_source(source_name)
        except ValueError:
            logger.debug(f"Source not found: {source_name}")
            return None

    @mcp.resource("aam://sources/{source_id}/candidates")
    def resource_source_candidates(source_id: str) -> list[dict[str, Any]]:
        """List unpackaged artifact candidates from a specific source.

        Source names containing ``/`` use double-hyphen convention in URI:
        ``aam://sources/openai--skills/candidates`` for source ``openai/skills``.

        Args:
            source_id: Source identifier (use ``--`` for ``/`` separator).

        Returns:
            List of candidate artifact dicts.
        """
        # -----
        # Convert double-hyphen URI convention back to slash name
        # -----
        source_name = source_id.replace("--", "/") if "--" in source_id else source_id
        logger.debug(
            f"MCP resource aam://sources/{source_id}/candidates accessed "
            f"(name={source_name})"
        )
        try:
            result = list_candidates(source_filter=source_name)
            return result.get("candidates", [])
        except ValueError:
            logger.debug(f"Source not found for candidates: {source_name}")
            return []

    logger.info("Registered 8 MCP resources")
