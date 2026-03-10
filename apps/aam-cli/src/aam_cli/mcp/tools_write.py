"""Write MCP tool definitions for AAM.

Defines tools tagged with 'write' that are only available when the
server is started with --allow-write. Each tool delegates to the
corresponding service function and returns structured data.
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
from aam_cli.services.upgrade_service import run_upgrade
from aam_cli.core.config import load_config
from aam_cli.mcp.error_boundary import mcp_error_boundary
from aam_cli.services import cache_service
from aam_cli.services.client_init_service import SUPPORTED_PLATFORMS, orchestrate_init
from aam_cli.services.config_service import set_config
from aam_cli.services.convert_service import run_conversion
from aam_cli.services.eval_service import run_evals
from aam_cli.services.init_service import init_package
from aam_cli.services.install_service import install_packages
from aam_cli.services.package_service import (
    create_package,
    create_package_from_source,
    uninstall_package,
)
from aam_cli.services.publish_service import publish_package
from aam_cli.services.registry_service import add_registry
from aam_cli.services.source_service import (
    add_source,
    remove_source,
    update_source,
)
from aam_cli.services.test_service import run_hook_tests, run_skill_tests

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


def register_write_tools(mcp: FastMCP) -> None:
    """Register all write (mutating) tools on the given FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools on.
    """

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_install(
        packages: list[str],
        platform: str | None = None,
        force: bool = False,
        no_deploy: bool = False,
        frozen: bool = False,
        minimal: bool = False,
        latest: bool = False,
        dry_run: bool = False,
        install_system_deps: bool = False,
        skip_checks: bool = False,
        install_mode: str | None = None,
    ) -> dict[str, Any]:
        """Install AAM packages from registries or local sources.

        Resolves dependencies, downloads/extracts packages, and deploys
        artifacts to the target platform.

        Args:
            packages: List of package specs (e.g., ["my-pkg", "other@1.0"]).
            platform: Target platform override (default: from config).
            force: Reinstall even if already present.
            no_deploy: Download only, skip deployment.
            frozen: Use exact versions from the lock file.
            minimal: Select the lowest satisfying version.
            latest: Use the newest available version.
            dry_run: Resolve and check without installing.
            install_system_deps: Auto-install missing system dependencies.
            skip_checks: Skip system dependency pre-flight checks (for CI).
            install_mode: Override install mode ("uaaps" or "plugin").

        Returns:
            Install result with lists of installed, already_installed,
            and failed packages.
        """
        logger.info(f"MCP tool aam_install: packages={packages}")
        config = load_config()
        return install_packages(
            packages=packages,
            config=config,
            platform=platform,
            force=force,
            no_deploy=no_deploy,
            frozen=frozen,
            minimal=minimal,
            latest=latest,
            dry_run=dry_run,
            install_system_deps=install_system_deps,
            skip_checks=skip_checks,
            install_mode=install_mode,
        )

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_uninstall(package_name: str) -> dict[str, Any]:
        """Uninstall an AAM package and remove deployed artifacts.

        Removes the package from the workspace, undeploys its artifacts
        from the platform, and updates the lock file.

        Args:
            package_name: Full package name to uninstall.

        Returns:
            Uninstall result with package name, version removed,
            files cleaned up, and any dependent package warnings.
        """
        logger.info(f"MCP tool aam_uninstall: package='{package_name}'")
        return uninstall_package(package_name=package_name)

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_publish(
        registry: str | None = None,
        tag: str = "latest",
    ) -> dict[str, Any]:
        """Publish a packed AAM archive to a registry.

        Must be run from a directory containing aam.yaml and a .aam archive.

        Args:
            registry: Target registry name (default: default registry).
            tag: Distribution tag (e.g., "latest", "beta").

        Returns:
            Publish result with package name, version, registry,
            archive size, and checksum.
        """
        logger.info(f"MCP tool aam_publish: registry='{registry}', tag='{tag}'")
        return publish_package(
            registry_name=registry,
            tag=tag,
        )

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_create_package(
        path: str = ".",
        name: str | None = None,
        version: str | None = None,
        description: str | None = None,
        artifact_types: list[str] | None = None,
        include_all: bool = False,
        from_source: str | None = None,
        artifacts: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create an AAM package manifest from an existing project or source.

        Scans the project directory (or a registered remote source) for
        artifacts and generates aam.yaml. When ``from_source`` is provided,
        artifacts are read from the cached source clone instead of a local
        directory, and provenance metadata is included.

        Args:
            path: Project directory to scan (default: current directory).
                Ignored when from_source is set.
            name: Package name (default: directory name or source name).
            version: Package version (default: "1.0.0").
            description: Package description.
            artifact_types: Filter for artifact types to include.
            include_all: Include all detected artifacts without filtering.
            from_source: Name of a registered remote source to create
                the package from. When set, artifacts are read from the
                cached source clone.
            artifacts: List of specific artifact names to include when
                using from_source (optional, defaults to all).

        Returns:
            Create result with manifest path, package name, version,
            and artifact counts. Includes provenance when from_source is used.
        """
        logger.info(
            f"MCP tool aam_create_package: path='{path}', "
            f"from_source={from_source}"
        )

        if from_source:
            return create_package_from_source(
                source_name=from_source,
                name=name,
                version=version,
                artifact_types=artifact_types,
                artifacts=artifacts,
            )

        return create_package(
            path=Path(path),
            name=name,
            version=version,
            description=description,
            artifact_types=artifact_types,
            include_all=include_all,
        )

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_config_set(key: str, value: str) -> dict[str, Any]:
        """Set an AAM configuration value.

        Updates the global configuration file.

        Args:
            key: Dotted config key (e.g., "default_platform", "author.name").
            value: Value to set.

        Returns:
            Updated config data dict with key, value, and source.
        """
        logger.info(f"MCP tool aam_config_set: key='{key}'")
        return set_config(key=key, value=value)

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_registry_add(
        name: str,
        url: str,
        set_default: bool = False,
    ) -> dict[str, Any]:
        """Add a new registry source to AAM configuration.

        Args:
            name: User-defined registry name.
            url: Registry URL (file:///path for local, https://... for remote).
            set_default: Set as the default registry.

        Returns:
            Registry info dict for the newly added registry.
        """
        logger.info(f"MCP tool aam_registry_add: name='{name}'")
        return add_registry(
            name=name,
            url=url,
            set_default=set_default,
        )

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_init_package(
        name: str,
        path: str | None = None,
        version: str = "1.0.0",
        description: str | None = None,
        author: str | None = None,
        license_name: str = "Apache-2.0",
        artifact_types: list[str] | None = None,
        platforms: list[str] | None = None,
    ) -> dict[str, Any]:
        """Scaffold a brand-new AAM package with directories and manifest.

        Creates a package directory with artifact subdirectories
        (skills/, agents/, commands/, instructions/) and a pre-populated
        aam.yaml manifest. Use this when starting a new package from scratch,
        as opposed to aam_create_package which scans existing files.

        Args:
            name: Package name (e.g., "my-skills" or "@org/my-skills").
                Must be lowercase with optional @scope/ prefix.
            path: Parent directory for the package folder (default: cwd).
            version: Semantic version string (default: "1.0.0").
            description: One-line package description.
            author: Package author or organisation.
            license_name: SPDX licence identifier (default: "Apache-2.0").
            artifact_types: Artifact directories to scaffold. Choices:
                skills, agents, commands, instructions. Default: all four.
            platforms: Target platforms to configure. Choices:
                cursor, claude, copilot, codex. Default: ["cursor"].

        Returns:
            Init result with package_name, package_dir, manifest_path,
            artifact_types, platforms, and directories_created.
        """
        logger.info(f"MCP tool aam_init_package: name='{name}'")
        return init_package(
            name=name,
            path=path,
            version=version,
            description=description,
            author=author,
            license_name=license_name,
            artifact_types=artifact_types,
            platforms=platforms,
        )

    ############################################################################
    #                                                                          #
    # SOURCE MANAGEMENT TOOLS (spec 003)                                       #
    #                                                                          #
    ############################################################################

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_source_add(
        source: str,
        ref: str | None = None,
        path: str | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Add a remote git repository as an artifact source.

        Parses the source URL, clones the repository (shallow), scans
        for artifacts, and saves the source entry to configuration.

        Args:
            source: Git source URL or shorthand. Supported formats:
                HTTPS (https://github.com/owner/repo),
                SSH (git@github.com:owner/repo),
                git+https (git+https://github.com/owner/repo),
                shorthand (owner/repo).
            ref: Branch, tag, or commit SHA to track (default: main).
            path: Subdirectory within the repo to scan (optional).
            name: Custom display name (default: derived from URL).

        Returns:
            Add result dict with source name, URL, artifact count.

        Raises:
            ValueError: If the source URL is invalid
                (error code: AAM_SOURCE_URL_INVALID), or if a source
                with the same name already exists
                (error code: AAM_SOURCE_ALREADY_EXISTS).
            RuntimeError: If the git clone fails
                (error code: AAM_GIT_CLONE_FAILED).
        """
        logger.info(f"MCP tool aam_source_add: source='{source}'")
        return add_source(
            source_str=source,
            ref=ref,
            path=path,
            name=name,
        )

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_source_remove(
        source_name: str,
        purge_cache: bool = False,
    ) -> dict[str, Any]:
        """Remove a configured remote source.

        Deletes the source entry from configuration. If the source was
        a default, records it in removed_defaults to prevent re-addition
        on init. Optionally purges the cached clone.

        Args:
            source_name: Display name of the source to remove.
            purge_cache: If True, also delete the cached clone directory.

        Returns:
            Removal result dict with source name and status.

        Raises:
            ValueError: If source_name is not found in config
                (error code: AAM_SOURCE_NOT_FOUND).
        """
        logger.info(
            f"MCP tool aam_source_remove: source='{source_name}', "
            f"purge_cache={purge_cache}"
        )
        return remove_source(
            source_name=source_name,
            purge_cache=purge_cache,
        )

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_source_update(
        source_name: str | None = None,
        update_all: bool = False,
    ) -> dict[str, Any]:
        """Update one or all sources by fetching upstream changes.

        Fetches the latest commits from the remote, re-scans for
        artifacts, and produces a change report showing new, modified,
        and removed artifacts.

        Args:
            source_name: Name of specific source to update.
                Required if update_all is False.
            update_all: If True, update all configured sources.

        Returns:
            Update result dict with change report per source.

        Raises:
            ValueError: If source_name is not found in config
                (error code: AAM_SOURCE_NOT_FOUND).
        """
        logger.info(
            f"MCP tool aam_source_update: source={source_name}, "
            f"update_all={update_all}"
        )
        return update_source(
            source_name=source_name,
            update_all=update_all,
        )

    ############################################################################
    #                                                                          #
    # UPGRADE TOOL (spec 004)                                                  #
    #                                                                          #
    ############################################################################

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_upgrade(
        package_name: str | None = None,
        dry_run: bool = False,
        force: bool = False,
    ) -> dict[str, Any]:
        """Upgrade outdated source-installed packages.

        Without package_name, upgrades all outdated packages. Specify
        a package_name to upgrade a single package. Checks for local
        modifications before overwriting; use force=True to skip.

        Args:
            package_name: Name of a specific package to upgrade.
                If None, upgrades all outdated packages.
            dry_run: If True, preview changes without applying.
            force: If True, skip modification warnings and overwrite.

        Returns:
            Upgrade result dict with upgraded, skipped, and failed
            package lists.
        """
        logger.info(
            f"MCP tool aam_upgrade: package={package_name}, "
            f"dry_run={dry_run}, force={force}"
        )
        return run_upgrade(
            package_name=package_name,
            dry_run=dry_run,
            force=force,
        )

    ############################################################################
    #                                                                          #
    # CLIENT INIT TOOL (spec 004)                                              #
    #                                                                          #
    ############################################################################

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_init(
        platform: str,
        skip_sources: bool = False,
    ) -> dict[str, Any]:
        """Initialize the AAM client for a specific AI platform.

        Sets the default platform in the global configuration and
        optionally registers community artifact sources.

        Args:
            platform: AI platform to configure. Choices:
                cursor, copilot, claude, codex.
            skip_sources: If True, skip registering default community
                sources.

        Returns:
            Init result dict with platform, config_path,
            sources_added, and is_reconfigure flag.
        """
        logger.info(
            f"MCP tool aam_init: platform='{platform}', "
            f"skip_sources={skip_sources}"
        )

        # -----
        # Validate platform
        # -----
        if platform not in SUPPORTED_PLATFORMS:
            return {
                "error": (
                    f"Unsupported platform '{platform}'. "
                    f"Choose from: {', '.join(SUPPORTED_PLATFORMS)}"
                ),
            }

        result = orchestrate_init(
            platform=platform,
            skip_sources=skip_sources,
        )

        return {
            "platform": result.platform,
            "config_path": str(result.config_path),
            "sources_added": result.sources_added,
            "registry_created": result.registry_created,
            "registry_name": result.registry_name,
            "is_reconfigure": result.is_reconfigure,
        }

    ############################################################################
    #                                                                          #
    # TEST, EVAL & CACHE TOOLS (UAAPS v0.5.0)                                 #
    #                                                                          #
    ############################################################################

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_test(
        skill_name: str | None = None,
        hooks: bool = False,
        event: str | None = None,
    ) -> dict[str, Any]:
        """Run deterministic tests for skills or hooks in the current package.

        Args:
            skill_name: Optional specific skill to test.
            hooks: If True, run hook tests instead of skill tests.
            event: Filter hook tests by event name.

        Returns:
            Dict with test results.
        """
        logger.info(
            f"MCP tool aam_test: skill_name={skill_name}, "
            f"hooks={hooks}, event={event}"
        )

        package_dir = Path.cwd().resolve()

        if hooks:
            suites = run_hook_tests(package_dir, event_name=event)
        else:
            suites = run_skill_tests(package_dir, skill_name=skill_name)

        return {"suites": [s.to_dict() for s in suites]}

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_eval(
        target: str | None = None,
        engine: str = "claude-code",
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Run LLM-judged evaluations for skills in the current package.

        Args:
            target: Optional specific skill to evaluate.
            engine: Eval engine to use (default: claude-code).
            dry_run: If True, parse and preview cases without executing.

        Returns:
            Dict with eval results.
        """
        logger.info(
            f"MCP tool aam_eval: target={target}, "
            f"engine='{engine}', dry_run={dry_run}"
        )

        package_dir = Path.cwd().resolve()

        suites = run_evals(
            package_dir,
            target=target,
            engine=engine,
            dry_run=dry_run,
        )

        return {"suites": [s.to_dict() for s in suites]}

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_cache_clean(
        package_spec: str | None = None,
    ) -> dict[str, Any]:
        """Clean the package download cache.

        Args:
            package_spec: Optional ``pkg@version`` to remove a specific entry.
                If omitted, removes all cached packages.

        Returns:
            Dict with cleanup result.
        """
        logger.info(f"MCP tool aam_cache_clean: package_spec={package_spec}")

        if package_spec and "@" in package_spec:
            parts = package_spec.rsplit("@", 1)
            if len(parts) == 2:
                removed = cache_service.clean(parts[0], parts[1])
                return {"removed": removed, "target": package_spec}

        removed = cache_service.clean()
        return {"removed": removed, "target": "all"}

    ############################################################################
    #                                                                          #
    # CONVERT TOOL (UAAPS v0.4.0)                                             #
    #                                                                          #
    ############################################################################

    @mcp.tool(tags={"write"})
    @mcp_error_boundary
    def aam_convert(
        from_platform: str,
        to_platform: str,
        path: str = ".",
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Convert artifacts between AI platform formats.

        Scans the project directory for artifacts belonging to
        ``from_platform`` and writes equivalent files for ``to_platform``.
        Supports instruction, agent, prompt, and skill artifact types.

        Args:
            from_platform: Source platform (cursor, copilot, claude, codex).
            to_platform: Target platform (cursor, copilot, claude, codex).
            path: Project root directory (default: current directory).
            dry_run: If True, preview changes without writing files.

        Returns:
            Dict with source_platform, target_platform, converted_count,
            failed_count, skipped_count, warning_count, and results list.
        """
        logger.info(
            f"MCP tool aam_convert: from='{from_platform}', "
            f"to='{to_platform}', path='{path}', dry_run={dry_run}"
        )
        report = run_conversion(
            project_root=Path(path).resolve(),
            source_platform=from_platform,
            target_platform=to_platform,
            dry_run=dry_run,
        )

        return {
            "source_platform": report.source_platform,
            "target_platform": report.target_platform,
            "converted_count": report.converted_count,
            "failed_count": report.failed_count,
            "skipped_count": report.skipped_count,
            "warning_count": report.warning_count,
            "results": [
                {
                    "source_path": r.source_path,
                    "target_path": r.target_path,
                    "artifact_type": r.artifact_type,
                    "warnings": r.warnings,
                    "error": r.error,
                    "skipped": r.skipped,
                }
                for r in report.results
            ],
        }
