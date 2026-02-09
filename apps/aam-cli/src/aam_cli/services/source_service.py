"""Source management service for remote git artifact sources.

Provides business logic for adding, scanning, updating, listing,
and removing remote git sources. Used by both CLI commands and
MCP tools.

Returns structured data (dicts/dataclasses) suitable for both
human-readable and machine-readable output.

Reference: spec.md User Stories 1–3, 7; data-model.md entities 4–6.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aam_cli.core.config import (
    AamConfig,
    SourceEntry,
    load_config,
    save_global_config,
)
from aam_cli.detection.scanner import scan_directory
from aam_cli.services.git_service import (
    GitCloneError,
    GitFetchError,
    clone_shallow,
    diff_file_names,
    fetch,
    get_cache_dir,
    get_head_sha,
    validate_cache,
)
from aam_cli.utils.git_url import GitSourceURL, parse

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# DATA MODELS                                                                  #
#                                                                              #
################################################################################


@dataclass
class DiscoveredArtifact:
    """An artifact discovered during source scanning.

    Attributes:
        name: Artifact name (e.g., ``gh-fix-ci``).
        type: Artifact type: ``skill``, ``agent``, ``prompt``,
            or ``instruction``.
        path: Relative path from source root.
        file_path: Path to the primary file (e.g., ``SKILL.md``).
        source_name: Name of the source this was found in.
        has_vendor_agent: True if companion ``agents/*.yaml`` exists.
        vendor_agent_file: Path to vendor agent file, if any.
        description: Extracted from first line of SKILL.md, if available.
    """

    name: str
    type: str
    path: str
    file_path: str
    source_name: str
    has_vendor_agent: bool = False
    vendor_agent_file: str | None = None
    description: str | None = None


@dataclass
class ScanResult:
    """Result of scanning a cached source for artifacts.

    Attributes:
        source_name: Display name of the scanned source.
        commit_sha: Current HEAD commit SHA.
        scan_path: Scoped subdirectory path (empty for full repo).
        artifacts: List of discovered artifacts.
        skills_count: Number of discovered skills.
        agents_count: Number of discovered agents.
        prompts_count: Number of discovered prompts.
        instructions_count: Number of discovered instructions.
        total_count: Total number of discovered artifacts.
    """

    source_name: str
    commit_sha: str
    scan_path: str
    artifacts: list[DiscoveredArtifact] = field(default_factory=list)
    skills_count: int = 0
    agents_count: int = 0
    prompts_count: int = 0
    instructions_count: int = 0
    total_count: int = 0


@dataclass
class SourceChangeReport:
    """Report of changes between old and new commits for a source.

    Attributes:
        source_name: Display name of the source.
        old_commit: Previous commit SHA.
        new_commit: New commit SHA.
        new_artifacts: Artifacts added since last fetch.
        modified_artifacts: Artifacts with content changes.
        removed_artifacts: Artifacts deleted since last fetch.
        unchanged_count: Number of unchanged artifacts.
        has_changes: True if any artifacts changed.
    """

    source_name: str
    old_commit: str
    new_commit: str
    new_artifacts: list[DiscoveredArtifact] = field(default_factory=list)
    modified_artifacts: list[DiscoveredArtifact] = field(default_factory=list)
    removed_artifacts: list[DiscoveredArtifact] = field(default_factory=list)
    unchanged_count: int = 0
    has_changes: bool = False


################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

# Default sources registered on first init (per spec 003 FR-040)
DEFAULT_SOURCES: list[dict[str, str]] = [
    {
        "name": "github/awesome-copilot",
        "url": "https://github.com/github/awesome-copilot.git",
        "ref": "main",
        "path": "skills",
    },
    {
        "name": "openai/skills:.curated",
        "url": "https://github.com/openai/skills.git",
        "ref": "main",
        "path": "skills/.curated",
    },
]


################################################################################
#                                                                              #
# INTERNAL HELPERS                                                             #
#                                                                              #
################################################################################


def _scan_cached_source(
    cache_dir: Path,
    source_name: str,
    scan_path: str,
    commit_sha: str,
) -> ScanResult:
    """Scan a cached clone directory for artifacts.

    Uses the extended ``scan_directory()`` function from the scanner
    module to traverse the cached repository.

    Args:
        cache_dir: Path to the cached clone.
        source_name: Display name of the source.
        scan_path: Subdirectory scope (empty for full repo).
        commit_sha: Current HEAD commit SHA.

    Returns:
        :class:`ScanResult` with all discovered artifacts.
    """
    logger.info(
        f"Scanning cached source: name='{source_name}', "
        f"path='{cache_dir}', scope='{scan_path}'"
    )

    # -----
    # Determine root to scan (apply scan_path scope)
    # -----
    scan_root = cache_dir / scan_path if scan_path else cache_dir

    if not scan_root.is_dir():
        logger.warning(
            f"Scan path does not exist in cache: path='{scan_root}'"
        )
        return ScanResult(
            source_name=source_name,
            commit_sha=commit_sha,
            scan_path=scan_path,
        )

    # -----
    # Run the scanner
    # -----
    detected = scan_directory(root=scan_root)

    # -----
    # Convert DetectedArtifact to DiscoveredArtifact
    # -----
    artifacts: list[DiscoveredArtifact] = []
    for det in detected:
        # -----
        # Extract description from SKILL.md first line if available
        # -----
        description: str | None = None
        if det.type == "skill":
            skill_md_path = scan_root / det.source_path / "SKILL.md"
            if skill_md_path.is_file():
                description = _extract_skill_description(skill_md_path)

        artifacts.append(
            DiscoveredArtifact(
                name=det.name,
                type=det.type,
                path=str(det.source_path),
                file_path=str(det.source_path),
                source_name=source_name,
                has_vendor_agent=det.source_dir == "vendor",
                description=description or det.description,
            )
        )

    # -----
    # Compute counts by type
    # -----
    skills = sum(1 for a in artifacts if a.type == "skill")
    agents = sum(1 for a in artifacts if a.type == "agent")
    prompts = sum(1 for a in artifacts if a.type == "prompt")
    instructions = sum(1 for a in artifacts if a.type == "instruction")

    result = ScanResult(
        source_name=source_name,
        commit_sha=commit_sha,
        scan_path=scan_path,
        artifacts=artifacts,
        skills_count=skills,
        agents_count=agents,
        prompts_count=prompts,
        instructions_count=instructions,
        total_count=len(artifacts),
    )

    logger.info(
        f"Scan complete: source='{source_name}', "
        f"total={result.total_count}, skills={skills}, "
        f"agents={agents}, prompts={prompts}, instructions={instructions}"
    )

    return result


def _extract_skill_description(skill_md_path: Path) -> str | None:
    """Extract a description from the first meaningful line of SKILL.md.

    Skips markdown heading markers (``#``) and empty lines.

    Args:
        skill_md_path: Path to the SKILL.md file.

    Returns:
        First line of content, or ``None`` if the file is empty.
    """
    try:
        with skill_md_path.open("r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                # -----
                # Remove heading markers for the description
                # -----
                if stripped.startswith("#"):
                    stripped = stripped.lstrip("#").strip()
                if stripped:
                    return stripped[:256]
    except OSError:
        logger.debug(f"Cannot read SKILL.md: {skill_md_path}")

    return None


def _find_source(config: AamConfig, name: str) -> SourceEntry | None:
    """Find a source entry by name in the configuration.

    Args:
        config: Loaded AAM configuration.
        name: Source display name to search for.

    Returns:
        Matching :class:`SourceEntry` or ``None``.
    """
    for source in config.sources:
        if source.name == name:
            return source
    return None


################################################################################
#                                                                              #
# PUBLIC API: ADD SOURCE                                                       #
#                                                                              #
################################################################################


def add_source(
    source_str: str,
    ref: str | None = None,
    path: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """Add a remote git repository as an artifact source.

    Parses the source URL, clones the repository (shallow), scans for
    artifacts, and saves the source entry to the global configuration.

    Args:
        source_str: Git source in any supported format.
        ref: Optional ref override (branch, tag, commit SHA).
        path: Optional subdirectory scope.
        name: Optional custom display name.

    Returns:
        Dict with source metadata: ``name``, ``url``, ``ref``,
        ``path``, ``commit``, ``artifact_count``, ``artifacts_by_type``.

    Raises:
        ValueError: If the source already exists or URL is invalid.
        GitCloneError: If cloning fails after retries.
    """
    logger.info(f"Adding source: source='{source_str}'")

    # -----
    # Step 1: Parse the source URL
    # -----
    parsed: GitSourceURL = parse(source_str, ref=ref, path=path, name=name)

    # -----
    # Step 2: Check for duplicates
    # -----
    config = load_config()
    existing = _find_source(config, parsed.display_name)
    if existing is not None:
        raise ValueError(
            f"[AAM_SOURCE_ALREADY_EXISTS] Source '{parsed.display_name}' "
            f"already exists. Use 'aam source update' to refresh it."
        )

    # -----
    # Step 3: Clone the repository
    # -----
    cache_dir = get_cache_dir(parsed.host, parsed.owner, parsed.repo)

    # If cache already exists for this repo, validate or re-clone
    if cache_dir.exists():
        if validate_cache(cache_dir):
            logger.info(
                f"Using existing cache for {parsed.owner}/{parsed.repo}"
            )
            # Fetch latest for the requested ref
            fetch(cache_dir, ref=parsed.ref)
        else:
            # Cache was corrupted and removed — re-clone
            clone_shallow(parsed.clone_url, cache_dir, ref=parsed.ref)
    else:
        clone_shallow(parsed.clone_url, cache_dir, ref=parsed.ref)

    # -----
    # Step 4: Get commit SHA and scan
    # -----
    commit_sha = get_head_sha(cache_dir)
    scan_result = _scan_cached_source(
        cache_dir, parsed.display_name, parsed.path, commit_sha
    )

    # -----
    # Step 5: Save to config
    # -----
    now_iso = datetime.now(UTC).isoformat()
    entry = SourceEntry(
        name=parsed.display_name,
        type="git",
        url=parsed.clone_url,
        ref=parsed.ref,
        path=parsed.path,
        last_commit=commit_sha,
        last_fetched=now_iso,
        artifact_count=scan_result.total_count,
    )
    config.sources.append(entry)
    save_global_config(config)

    logger.info(
        f"Source added: name='{parsed.display_name}', "
        f"artifacts={scan_result.total_count}"
    )

    return {
        "name": parsed.display_name,
        "url": parsed.clone_url,
        "ref": parsed.ref,
        "path": parsed.path,
        "commit": commit_sha,
        "artifact_count": scan_result.total_count,
        "artifacts_by_type": {
            "skills": scan_result.skills_count,
            "agents": scan_result.agents_count,
            "prompts": scan_result.prompts_count,
            "instructions": scan_result.instructions_count,
        },
    }


################################################################################
#                                                                              #
# PUBLIC API: SCAN SOURCE                                                      #
#                                                                              #
################################################################################


def scan_source(source_name: str) -> dict[str, Any]:
    """Scan a registered source for artifacts.

    Reads the source configuration, resolves the cache path, and runs
    the artifact scanner on the cached clone.

    Args:
        source_name: Display name of the source to scan.

    Returns:
        Dict with scan results: ``source_name``, ``commit``,
        ``scan_path``, ``total_count``, ``artifacts_by_type``,
        ``artifacts`` (list of dicts).

    Raises:
        ValueError: If the source is not found in config.
    """
    logger.info(f"Scanning source: name='{source_name}'")

    # -----
    # Load config and find source
    # -----
    config = load_config()
    source = _find_source(config, source_name)
    if source is None:
        raise ValueError(
            f"[AAM_SOURCE_NOT_FOUND] Source '{source_name}' not found. "
            f"Use 'aam source list' to see configured sources."
        )

    # -----
    # Resolve cache path from URL components
    # -----
    parsed = parse(source.url)
    cache_dir = get_cache_dir(parsed.host, parsed.owner, parsed.repo)

    if not validate_cache(cache_dir):
        raise ValueError(
            f"[AAM_CACHE_CORRUPTED] Cache for source '{source_name}' "
            f"is missing or corrupted. Run 'aam source update {source_name}' "
            f"to re-clone."
        )

    # -----
    # Get commit and scan
    # -----
    commit_sha = get_head_sha(cache_dir)
    scan_result = _scan_cached_source(
        cache_dir, source_name, source.path, commit_sha
    )

    # -----
    # Convert artifacts to dicts for output
    # -----
    artifacts_list = [
        {
            "name": a.name,
            "type": a.type,
            "path": a.path,
            "description": a.description,
            "has_vendor_agent": a.has_vendor_agent,
        }
        for a in scan_result.artifacts
    ]

    return {
        "source_name": source_name,
        "commit": commit_sha,
        "scan_path": source.path,
        "total_count": scan_result.total_count,
        "artifacts_by_type": {
            "skills": scan_result.skills_count,
            "agents": scan_result.agents_count,
            "prompts": scan_result.prompts_count,
            "instructions": scan_result.instructions_count,
        },
        "artifacts": artifacts_list,
    }


################################################################################
#                                                                              #
# PUBLIC API: UPDATE SOURCE                                                    #
#                                                                              #
################################################################################


def update_source(
    source_name: str | None = None,
    update_all: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update one or all sources by fetching upstream changes.

    Produces a change report showing new, modified, and removed
    artifacts.

    Args:
        source_name: Name of a specific source to update.
            Required if ``update_all`` is False.
        update_all: Update all configured sources.
        dry_run: If True, only preview changes without modifying cache.

    Returns:
        Dict with update results: ``reports`` (list of change report
        dicts), ``sources_updated`` count.

    Raises:
        ValueError: If the source is not found.
        GitFetchError: If fetch fails after retries (with cached
            fallback per FR-043).
    """
    logger.info(
        f"Updating sources: name='{source_name}', "
        f"update_all={update_all}, dry_run={dry_run}"
    )

    config = load_config()

    # -----
    # Determine which sources to update
    # -----
    if update_all:
        sources_to_update = list(config.sources)
    else:
        if source_name is None:
            raise ValueError(
                "[AAM_INVALID_ARGUMENT] Either source name or --all is required"
            )
        source = _find_source(config, source_name)
        if source is None:
            raise ValueError(
                f"[AAM_SOURCE_NOT_FOUND] Source '{source_name}' not found"
            )
        sources_to_update = [source]

    reports: list[dict[str, Any]] = []

    for source_entry in sources_to_update:
        report = _update_single_source(source_entry, dry_run)
        reports.append(report)

    # -----
    # Persist updated config (commit SHAs, timestamps)
    # -----
    if not dry_run:
        save_global_config(config)

    return {
        "reports": reports,
        "sources_updated": len(reports),
    }


def _update_single_source(
    source_entry: SourceEntry,
    dry_run: bool,
) -> dict[str, Any]:
    """Update a single source and produce a change report.

    Args:
        source_entry: The source to update (mutated in-place).
        dry_run: If True, skip actual fetch.

    Returns:
        Change report dict.
    """
    logger.info(f"Updating source: name='{source_entry.name}'")

    parsed = parse(source_entry.url)
    cache_dir = get_cache_dir(parsed.host, parsed.owner, parsed.repo)
    old_commit = source_entry.last_commit or ""

    # -----
    # Try to fetch; on network failure, fall back to cached data per FR-043
    # -----
    fetch_failed = False
    try:
        if not dry_run:
            if not validate_cache(cache_dir):
                # Cache is missing/corrupted — full re-clone required
                clone_shallow(parsed.clone_url, cache_dir, ref=source_entry.ref)
            else:
                fetch(cache_dir, ref=source_entry.ref)
    except (GitFetchError, GitCloneError) as e:
        logger.warning(
            f"Network failure updating source '{source_entry.name}': {e}. "
            f"Falling back to cached scan data per FR-043."
        )
        fetch_failed = True

    # -----
    # Get new commit SHA (may be same as old if fetch failed)
    # -----
    new_commit = old_commit
    if not fetch_failed and validate_cache(cache_dir):
        new_commit = get_head_sha(cache_dir)

    # -----
    # Compute diff if commits changed
    # -----
    change_report: dict[str, Any] = {
        "source_name": source_entry.name,
        "old_commit": old_commit,
        "new_commit": new_commit,
        "has_changes": old_commit != new_commit,
        "new_artifacts": [],
        "modified_artifacts": [],
        "removed_artifacts": [],
        "unchanged_count": 0,
        "fetch_failed": fetch_failed,
    }

    if old_commit and new_commit and old_commit != new_commit and validate_cache(cache_dir):
        # -----
        # Get file-level diff
        # -----
        diff = diff_file_names(cache_dir, old_commit, new_commit)

        # Re-scan to get current artifacts
        scan_result = _scan_cached_source(
            cache_dir, source_entry.name, source_entry.path, new_commit
        )

        # Classify artifacts based on changed files
        for artifact in scan_result.artifacts:
            is_new = any(
                f.startswith(artifact.path) for f in diff["added"]
            )
            is_modified = any(
                f.startswith(artifact.path) for f in diff["modified"]
            )

            if is_new:
                change_report["new_artifacts"].append(
                    {"name": artifact.name, "type": artifact.type, "path": artifact.path}
                )
            elif is_modified:
                change_report["modified_artifacts"].append(
                    {"name": artifact.name, "type": artifact.type, "path": artifact.path}
                )

        # Check for removed artifacts
        for deleted_file in diff["deleted"]:
            change_report["removed_artifacts"].append(
                {"path": deleted_file}
            )

        change_report["unchanged_count"] = (
            scan_result.total_count
            - len(change_report["new_artifacts"])
            - len(change_report["modified_artifacts"])
        )

    # -----
    # Update source entry metadata (if not dry_run)
    # -----
    if not dry_run and not fetch_failed:
        source_entry.last_commit = new_commit
        source_entry.last_fetched = datetime.now(UTC).isoformat()

        # Re-scan for artifact count update
        if validate_cache(cache_dir):
            scan_result = _scan_cached_source(
                cache_dir, source_entry.name, source_entry.path, new_commit
            )
            source_entry.artifact_count = scan_result.total_count

    return change_report


################################################################################
#                                                                              #
# PUBLIC API: LIST CANDIDATES                                                  #
#                                                                              #
################################################################################


def list_candidates(
    source_filter: str | None = None,
    type_filter: list[str] | None = None,
) -> dict[str, Any]:
    """List unpackaged artifact candidates across all sources.

    Scans all registered sources and returns artifacts that are not
    yet packaged.

    Args:
        source_filter: Only include artifacts from this source.
        type_filter: Only include artifacts of these types.

    Returns:
        Dict with ``candidates`` list and ``total_count``.
    """
    logger.info(
        f"Listing candidates: source_filter='{source_filter}', "
        f"type_filter={type_filter}"
    )

    config = load_config()
    all_candidates: list[dict[str, Any]] = []

    sources = config.sources
    if source_filter:
        sources = [s for s in sources if s.name == source_filter]
        if not sources:
            raise ValueError(
                f"[AAM_SOURCE_NOT_FOUND] Source '{source_filter}' not found"
            )

    for source_entry in sources:
        try:
            scan_result = scan_source(source_entry.name)
            for artifact in scan_result["artifacts"]:
                if type_filter and artifact["type"] not in type_filter:
                    continue
                all_candidates.append(artifact)
        except ValueError as e:
            logger.warning(f"Skipping source '{source_entry.name}': {e}")

    return {
        "candidates": all_candidates,
        "total_count": len(all_candidates),
    }


################################################################################
#                                                                              #
# PUBLIC API: LIST / REMOVE SOURCES                                            #
#                                                                              #
################################################################################


def list_sources() -> dict[str, Any]:
    """List all configured remote git sources.

    Returns:
        Dict with ``sources`` list and ``count``.
    """
    logger.info("Listing all sources")

    config = load_config()
    sources_list = [
        {
            "name": s.name,
            "type": s.type,
            "url": s.url,
            "ref": s.ref,
            "path": s.path,
            "last_commit": s.last_commit,
            "last_fetched": s.last_fetched,
            "artifact_count": s.artifact_count,
            "default": s.default,
        }
        for s in config.sources
    ]

    return {
        "sources": sources_list,
        "count": len(sources_list),
    }


def remove_source(
    source_name: str,
    purge_cache: bool = False,
) -> dict[str, Any]:
    """Remove a configured source.

    If the source was a default, records it in ``removed_defaults``
    to prevent re-addition on init.

    Args:
        source_name: Name of the source to remove.
        purge_cache: If True, delete the cached clone directory.

    Returns:
        Dict with ``name``, ``removed``, ``cache_purged``.

    Raises:
        ValueError: If the source is not found.
    """
    logger.info(
        f"Removing source: name='{source_name}', purge_cache={purge_cache}"
    )

    config = load_config()
    source = _find_source(config, source_name)
    if source is None:
        raise ValueError(
            f"[AAM_SOURCE_NOT_FOUND] Source '{source_name}' not found"
        )

    # -----
    # Track removed defaults so they aren't re-added on init
    # -----
    if source.default and source_name not in config.removed_defaults:
        config.removed_defaults.append(source_name)

    # -----
    # Remove from config
    # -----
    config.sources = [s for s in config.sources if s.name != source_name]
    save_global_config(config)

    # -----
    # Optionally purge the cache
    # -----
    cache_purged = False
    if purge_cache:
        try:
            parsed = parse(source.url)
            cache_dir = get_cache_dir(parsed.host, parsed.owner, parsed.repo)
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
                cache_purged = True
                logger.info(f"Cache purged: path='{cache_dir}'")
        except (ValueError, OSError) as e:
            logger.warning(f"Failed to purge cache: {e}")

    logger.info(f"Source removed: name='{source_name}'")

    return {
        "name": source_name,
        "removed": True,
        "cache_purged": cache_purged,
    }


################################################################################
#                                                                              #
# PUBLIC API: DEFAULT SOURCES                                                  #
#                                                                              #
################################################################################


def register_default_sources() -> dict[str, Any]:
    """Register community default sources during initialization.

    Called by ``aam init`` to pre-populate the source list with
    curated default sources. Skips sources that are already
    registered or have been previously removed by the user.

    Returns:
        Dict with ``registered`` list and ``skipped`` list.
    """
    logger.info("Registering default sources")

    config = load_config()
    registered: list[str] = []
    skipped: list[str] = []

    existing_names = {s.name for s in config.sources}

    for default in DEFAULT_SOURCES:
        name = default["name"]

        # -----
        # Skip if already registered
        # -----
        if name in existing_names:
            logger.debug(f"Default source already exists: {name}")
            skipped.append(name)
            continue

        # -----
        # Skip if user previously removed this default
        # -----
        if name in config.removed_defaults:
            logger.debug(f"Default source was previously removed: {name}")
            skipped.append(name)
            continue

        # -----
        # Register the default source (without cloning yet)
        # Clone will happen on first scan/update
        # -----
        entry = SourceEntry(
            name=name,
            type="git",
            url=default["url"],
            ref=default["ref"],
            path=default.get("path", ""),
            default=True,
        )
        config.sources.append(entry)
        registered.append(name)
        logger.info(f"Default source registered: {name}")

    if registered:
        save_global_config(config)

    return {
        "registered": registered,
        "skipped": skipped,
    }
