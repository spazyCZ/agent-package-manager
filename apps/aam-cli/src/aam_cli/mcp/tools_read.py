"""Read-only MCP tool definitions for AAM.

Defines tools tagged with 'read' that are always available regardless
of the --allow-write flag. Each tool delegates to the corresponding
service function and returns structured data.
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

from aam_cli.commands.diff import diff_package
from aam_cli.core.config import load_config
from aam_cli.services.checksum_service import verify_all, verify_package
from aam_cli.services.config_service import get_config
from aam_cli.services.doctor_service import run_diagnostics
from aam_cli.services.package_service import (
    get_package_info,
    list_installed_packages,
)
from aam_cli.services.registry_service import list_registries
from aam_cli.services.recommend_service import recommend_skills_for_repo
from aam_cli.services.search_service import search_packages
from aam_cli.services.source_service import (
    list_candidates,
    list_sources,
    scan_source,
    update_source,
)
from aam_cli.services.validate_service import validate_package

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# TOOL REGISTRATION                                                            #
#                                                                              #
################################################################################


def register_read_tools(mcp: FastMCP) -> None:
    """Register all read-only tools on the given FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools on.
    """

    @mcp.tool(tags={"read"})
    def aam_search(
        query: str,
        limit: int = 255,
        package_types: list[str] | None = None,
        source_filter: str | None = None,
        registry_filter: str | None = None,
        sort_by: str = "relevance",
    ) -> dict[str, Any]:
        """Search configured registries and sources for AAM packages.

        Returns a structured response with scored, ranked results,
        total count, and any warnings.

        Args:
            query: Search query (case-insensitive). Empty string for browse mode.
            limit: Maximum results to return (1-255, default 255).
            package_types: Filter by artifact types (OR logic).
                Valid: skill, agent, prompt, instruction.
            source_filter: Limit to a specific git source name.
            registry_filter: Limit to a specific registry name.
            sort_by: Sort order — relevance, name, or recent (default: relevance).

        Returns:
            Dict with results, total_count, and warnings.
        """
        logger.info(
            f"MCP tool aam_search: query='{query}', limit={limit}, "
            f"types={package_types}, sort={sort_by}"
        )
        config = load_config()
        response = search_packages(
            query=query,
            config=config,
            limit=limit,
            package_types=package_types,
            source_filter=source_filter,
            registry_filter=registry_filter,
            sort_by=sort_by,
        )
        result = response.model_dump(mode="json")
        # Remove all_names — internal use only
        result.pop("all_names", None)
        return result

    @mcp.tool(tags={"read"})
    def aam_list() -> list[dict[str, Any]]:
        """List all installed AAM packages in the current workspace.

        Returns a list of installed packages with version, source,
        and artifact counts.

        Returns:
            List of installed package info dicts.
        """
        logger.info("MCP tool aam_list")
        return list_installed_packages()

    @mcp.tool(tags={"read"})
    def aam_info(
        package_name: str,
        version: str | None = None,
    ) -> dict[str, Any]:
        """Show detailed metadata about an installed package.

        Returns comprehensive information including description, author,
        artifacts, dependencies, and platform configuration.

        Args:
            package_name: Full package name (e.g., "my-pkg" or "@scope/my-pkg").
            version: Optional version filter.

        Returns:
            Detailed package metadata dict.
        """
        logger.info(f"MCP tool aam_info: package='{package_name}'")
        return get_package_info(
            package_name=package_name,
            version=version,
        )

    @mcp.tool(tags={"read"})
    def aam_validate(path: str = ".") -> dict[str, Any]:
        """Validate an AAM package manifest and artifacts.

        Checks that aam.yaml is syntactically correct, all required
        fields are present, and all referenced artifact paths exist.

        Args:
            path: Path to the package directory (default: current directory).

        Returns:
            Validation report with valid flag, errors, and warnings.
        """
        logger.info(f"MCP tool aam_validate: path='{path}'")
        return validate_package(Path(path))

    @mcp.tool(tags={"read"})
    def aam_config_get(key: str | None = None) -> dict[str, Any]:
        """Get AAM configuration value(s).

        Returns a single config value if key is specified, or the full
        merged configuration if key is None.

        Args:
            key: Dotted config key (e.g., "default_platform", "author.name").
                 If None, returns the full configuration.

        Returns:
            Config data dict with key, value, and source.
        """
        logger.info(f"MCP tool aam_config_get: key={key}")
        return get_config(key=key)

    @mcp.tool(tags={"read"})
    def aam_registry_list() -> list[dict[str, Any]]:
        """List all configured AAM registries.

        Returns information about each registry including name, URL,
        type, default status, and accessibility.

        Returns:
            List of registry info dicts.
        """
        logger.info("MCP tool aam_registry_list")
        return list_registries()

    @mcp.tool(tags={"read"})
    def aam_doctor() -> dict[str, Any]:
        """Run AAM environment diagnostics.

        Checks Python version, configuration validity, registry
        accessibility, package integrity, and detects incomplete
        installations.

        Returns:
            Doctor report with health status, individual check results,
            and a summary.
        """
        logger.info("MCP tool aam_doctor")
        return run_diagnostics()

    ############################################################################
    #                                                                          #
    # SOURCE & INTEGRITY TOOLS (spec 003)                                      #
    #                                                                          #
    ############################################################################

    @mcp.tool(tags={"read"})
    def aam_source_list() -> list[dict[str, Any]]:
        """List all configured remote git sources.

        Returns information about each source including name, URL, ref,
        last commit SHA, last fetch time, artifact count, and default
        status.

        Returns:
            List of source info dicts.
        """
        logger.info("MCP tool aam_source_list")
        result = list_sources()
        return result.get("sources", [])

    @mcp.tool(tags={"read"})
    def aam_source_scan(
        source_name: str,
        artifact_type: str | None = None,
    ) -> dict[str, Any]:
        """Scan a registered source for artifacts.

        Runs the artifact scanner on the cached clone and returns
        discovered artifacts grouped by type.

        Args:
            source_name: Display name of the source to scan.
            artifact_type: Optional filter by artifact type
                (skill, agent, prompt, instruction).

        Returns:
            Scan result dict with source info and artifact list.

        Raises:
            ValueError: If source_name is not found in config
                (error code: AAM_SOURCE_NOT_FOUND).
        """
        logger.info(
            f"MCP tool aam_source_scan: source='{source_name}', "
            f"type={artifact_type}"
        )
        result = scan_source(source_name)

        # -----
        # Apply optional type filter
        # -----
        if artifact_type and "artifacts" in result:
            result["artifacts"] = [
                a for a in result["artifacts"]
                if a.get("type") == artifact_type
            ]
            result["artifact_count"] = len(result["artifacts"])

        return result

    @mcp.tool(tags={"read"})
    def aam_source_candidates(
        source_name: str | None = None,
        artifact_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """List unpackaged artifact candidates across sources.

        Scans all (or a specific) registered source and returns artifacts
        that are not yet packaged in the current workspace.

        Args:
            source_name: Optional source name filter. If None, scan all sources.
            artifact_type: Optional filter by artifact type
                (skill, agent, prompt, instruction).

        Returns:
            List of candidate artifact dicts.
        """
        logger.info(
            f"MCP tool aam_source_candidates: source={source_name}, "
            f"type={artifact_type}"
        )
        type_filter = [artifact_type] if artifact_type else None
        result = list_candidates(
            source_filter=source_name,
            type_filter=type_filter,
        )
        return result.get("candidates", [])

    @mcp.tool(tags={"read"})
    def aam_source_diff(source_name: str) -> dict[str, Any]:
        """Preview upstream changes for a source without applying them.

        Performs a dry-run update to show which artifacts would be
        new, modified, or removed if the source were updated.

        Args:
            source_name: Display name of the source to check.

        Returns:
            Change report dict with new, modified, and removed artifacts.

        Raises:
            ValueError: If source_name is not found in config
                (error code: AAM_SOURCE_NOT_FOUND).
        """
        logger.info(f"MCP tool aam_source_diff: source='{source_name}'")
        return update_source(
            source_name=source_name,
            dry_run=True,
        )

    @mcp.tool(tags={"read"})
    def aam_verify(
        package_name: str | None = None,
        check_all: bool = False,
    ) -> dict[str, Any]:
        """Verify integrity of installed package files.

        Compares current file checksums against recorded checksums
        to detect modifications, missing files, and untracked files.

        Args:
            package_name: Name of the package to verify.
                Required if check_all is False.
            check_all: If True, verify all installed packages.

        Returns:
            Verify result dict with file status (ok, modified, missing,
            untracked) and a has_checksums flag.

        Raises:
            ValueError: If the package is not installed
                (error code: AAM_PACKAGE_NOT_INSTALLED).
        """
        logger.info(
            f"MCP tool aam_verify: package={package_name}, "
            f"check_all={check_all}"
        )
        if check_all:
            return verify_all()
        if package_name:
            return verify_package(package_name)
        return {"error": "Either package_name or check_all=True is required"}

    @mcp.tool(tags={"read"})
    def aam_diff(package_name: str) -> dict[str, Any]:
        """Show differences in installed package files.

        Generates unified diffs for each modified file in the installed
        package, plus lists of missing and untracked files.

        Args:
            package_name: Name of the installed package to diff.

        Returns:
            Diff result dict with diffs list, modified_count,
            missing_files, and untracked_files.

        Raises:
            ValueError: If the package is not installed
                (error code: AAM_PACKAGE_NOT_INSTALLED).
        """
        logger.info(f"MCP tool aam_diff: package='{package_name}'")
        return diff_package(package_name)

    ############################################################################
    #                                                                          #
    # OUTDATED & AVAILABLE TOOLS (spec 004)                                    #
    #                                                                          #
    ############################################################################

    @mcp.tool(tags={"read"})
    def aam_outdated() -> dict[str, Any]:
        """Check for outdated source-installed packages.

        Compares installed package commit SHAs against the source HEAD.
        Returns categorized results: outdated, up_to_date, no_source,
        and stale_sources.

        Returns:
            Outdated result dict with outdated packages, counts, and
            stale source warnings.
        """
        from aam_cli.commands.outdated import check_outdated
        from aam_cli.core.workspace import read_lock_file

        logger.info("MCP tool aam_outdated")
        config = load_config()
        lock = read_lock_file()

        result = check_outdated(lock, config)

        return {
            "outdated": [
                {
                    "name": o.name,
                    "current_commit": o.current_commit,
                    "latest_commit": o.latest_commit,
                    "source_name": o.source_name,
                    "has_local_modifications": o.has_local_modifications,
                }
                for o in result.outdated
            ],
            "up_to_date": result.up_to_date,
            "no_source": result.no_source,
            "stale_sources": result.stale_sources,
            "total_outdated": result.total_outdated,
        }

    @mcp.tool(tags={"read"})
    def aam_available() -> dict[str, Any]:
        """List all available artifacts from configured sources.

        Builds an in-memory index of all artifacts across registered
        sources and returns them grouped by source name.

        Returns:
            Dict with artifacts grouped by source, total count, and
            number of sources indexed.
        """
        from aam_cli.services.source_service import build_source_index

        logger.info("MCP tool aam_available")
        config = load_config()
        index = build_source_index(config)

        # -----
        # Group by source for structured output
        # -----
        by_source: dict[str, list[dict[str, Any]]] = {}
        for qname, vp in index.by_qualified_name.items():
            source_group = by_source.setdefault(vp.source_name, [])
            source_group.append({
                "name": vp.name,
                "qualified_name": vp.qualified_name,
                "type": vp.type,
                "path": vp.path,
                "description": vp.description,
            })

        return {
            "by_source": by_source,
            "total_count": index.total_count,
            "sources_indexed": index.sources_indexed,
            "build_timestamp": index.build_timestamp,
        }

    ############################################################################
    #                                                                          #
    # RECOMMEND SKILLS TOOL                                                    #
    #                                                                          #
    ############################################################################

    @mcp.tool(tags={"read"})
    def aam_recommend_skills(
        path: str | None = None,
        limit: int = 15,
    ) -> dict[str, Any]:
        """Recommend AAM skills based on repository analysis.

        Analyzes the project (package.json, pyproject.toml, structure)
        to detect frontend (React, Vue), backend (Python, FastAPI), LLM
        usage, docs, and tests. Returns a ranked list of skills from
        configured sources that match the repository needs.

        Best used when the user wants to find relevant skills for their
        project or asks "what skills should I use for this repo?"

        Args:
            path: Project root to analyze. Defaults to current directory.
            limit: Maximum number of recommendations (default 15).

        Returns:
            Dict with repo_context, recommendations (qualified_name,
            score, rationale), and install_hint.
        """
        logger.info(f"MCP tool aam_recommend_skills: path={path}, limit={limit}")
        return recommend_skills_for_repo(path=path, limit=limit)

    ############################################################################
    #                                                                          #
    # CLIENT INIT INFO TOOL (spec 004)                                         #
    #                                                                          #
    ############################################################################

    @mcp.tool(tags={"read"})
    def aam_init_info() -> dict[str, Any]:
        """Get client initialization information.

        Detects the current AI platform from project directory indicators
        and returns recommended defaults for ``aam init``.

        Returns:
            Dict with detected_platform, supported_platforms, and
            recommended defaults.
        """
        from aam_cli.services.client_init_service import (
            SUPPORTED_PLATFORMS,
            detect_platform,
        )

        logger.info("MCP tool aam_init_info")

        detected = detect_platform()
        config = load_config()

        return {
            "detected_platform": detected,
            "current_platform": config.default_platform,
            "supported_platforms": SUPPORTED_PLATFORMS,
            "has_config": config.default_platform is not None,
            "recommended_platform": detected or "cursor",
        }

    logger.info("Registered 17 read-only MCP tools")
