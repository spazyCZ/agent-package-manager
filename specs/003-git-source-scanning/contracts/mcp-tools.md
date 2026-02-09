# MCP Tool & Resource Contracts: Git Source Scanning & Artifact Discovery

**Feature**: 003-git-source-scanning | **Date**: 2026-02-08

## Overview

All new MCP tools and resources extend the existing set from spec 002. They follow the same patterns: tag-based safety model, structured dict returns, `aam://` URI scheme for resources, and the error handling convention from spec 002.

## Error Handling Convention (from spec 002)

- **Expected domain outcomes**: Return the tool's documented output shape (e.g., `ScanResult` dict, `VerifyResult` with `has_checksums=false`).
- **Tool failures (unexpected/unrecoverable)**: Raise MCP tool error (`CallToolResult.isError == true`). Error messages MUST be safe (no secrets) and MUST start with an error code in brackets.

### New Error Codes (extend spec 002 set)

| Error Code | When Raised | Used By |
|---|---|---|
| `AAM_SOURCE_NOT_FOUND` | Named source not in config | `aam_source_scan`, `aam_source_diff`, `aam_source_remove`, `aam_source_update` |
| `AAM_SOURCE_ALREADY_EXISTS` | Duplicate source name on add | `aam_source_add` |
| `AAM_SOURCE_URL_INVALID` | URL failed scheme allowlist | `aam_source_add` |
| `AAM_GIT_CLONE_FAILED` | Clone failed after retries | `aam_source_add` |
| `AAM_GIT_FETCH_FAILED` | Fetch failed after retries | `aam_source_update` |
| `AAM_NETWORK_ERROR` | Network unreachable after all retries | `aam_source_add`, `aam_source_update` |
| `AAM_CACHE_CORRUPTED` | Cached clone directory corrupted | `aam_source_scan`, `aam_source_update` |
| `AAM_CHECKSUMS_NOT_AVAILABLE` | No `file_checksums` in lock file | `aam_verify` (returned as domain outcome, not error) |

### Existing Error Codes (from spec 002, reused here)

| Error Code | Used By |
|---|---|
| `AAM_PACKAGE_NOT_INSTALLED` | `aam_verify`, `aam_diff` |
| `AAM_INVALID_ARGUMENT` | Any tool with invalid parameters |
| `AAM_INTERNAL_ERROR` | Unexpected failures |

---

## Read-Only Tools (tag: `"read"`)

### `aam_source_list`

```python
@mcp.tool(tags={"read"})
def aam_source_list() -> list[dict]:
    """List all configured remote git artifact sources.

    Returns:
        List of sources with name, URL, ref, artifact count, and last updated timestamp.
    """
```

**Return schema**:
```json
[
  {
    "name": "openai/skills:.curated",
    "type": "git",
    "url": "https://github.com/openai/skills",
    "ref": "main",
    "path": "skills/.curated",
    "artifact_count": 30,
    "last_fetched": "2026-02-08T10:30:00Z",
    "last_commit": "abc123def456",
    "default": false
  }
]
```

**Service call**: `source_service.list_sources()`

---

### `aam_source_scan`

```python
@mcp.tool(tags={"read"})
def aam_source_scan(
    source_name: str,
    artifact_type: str | None = None,
) -> dict:
    """Scan a remote git source and list all discovered artifacts.

    Args:
        source_name: Name of the registered source.
        artifact_type: Filter by type: 'skill', 'agent', 'prompt', 'instruction'.

    Returns:
        Scan results grouped by artifact type.
    """
```

**Return schema**:
```json
{
  "source_name": "openai/skills:.curated",
  "commit": "abc123d",
  "scan_path": "skills/.curated/",
  "artifacts": {
    "skills": [
      {"name": "gh-fix-ci", "path": "skills/.curated/gh-fix-ci/SKILL.md", "has_vendor_agent": true},
      {"name": "playwright", "path": "skills/.curated/playwright/SKILL.md", "has_vendor_agent": false}
    ],
    "agents": [],
    "prompts": [],
    "instructions": []
  },
  "total": 30
}
```

**Service call**: `source_service.scan_source(source_name, artifact_type)`

---

### `aam_source_candidates`

```python
@mcp.tool(tags={"read"})
def aam_source_candidates(
    source_name: str | None = None,
    artifact_type: str | None = None,
) -> list[dict]:
    """List artifacts across remote sources not yet in any AAM package.

    Args:
        source_name: Filter to a specific source (default: all).
        artifact_type: Filter by type.

    Returns:
        Candidate artifacts with source, name, type, and path.
    """
```

**Return schema**:
```json
[
  {
    "source": "openai/skills:.curated",
    "source_type": "remote_git",
    "name": "gh-fix-ci",
    "type": "skill",
    "path": "skills/.curated/gh-fix-ci/SKILL.md",
    "has_vendor_agent": true
  },
  {
    "source": "local",
    "source_type": "local_project",
    "name": "my-custom-skill",
    "type": "skill",
    "path": ".cursor/skills/my-custom-skill/SKILL.md",
    "has_vendor_agent": false
  }
]
```

**Service call**: `source_service.list_candidates(source_name, artifact_type)`

---

### `aam_source_diff`

```python
@mcp.tool(tags={"read"})
def aam_source_diff(source_name: str) -> dict:
    """Preview upstream changes without fetching (dry-run).

    Args:
        source_name: Name of the registered source.

    Returns:
        Change summary with new, modified, and removed artifacts.
    """
```

**Return schema**:
```json
{
  "source_name": "openai/skills:.curated",
  "old_commit": "abc123d",
  "new_commit": "def456a",
  "new_artifacts": [
    {"name": "security-ownership-map", "type": "skill", "path": "..."}
  ],
  "modified_artifacts": [
    {"name": "gh-fix-ci", "type": "skill", "path": "..."}
  ],
  "removed_artifacts": [],
  "unchanged_count": 27,
  "has_changes": true
}
```

**Service call**: `source_service.update_source(source_name, dry_run=True)`

---

### `aam_verify`

```python
@mcp.tool(tags={"read"})
def aam_verify(
    package_name: str | None = None,
    verify_all: bool = False,
) -> dict:
    """Verify installed package integrity via file checksums.

    Args:
        package_name: Package to verify. Required if verify_all is False.
        verify_all: Verify all installed packages.

    Returns:
        Verification report with file statuses.
    """
```

**Return schema**:
```json
{
  "package_name": "@myorg/my-agent",
  "version": "1.0.0",
  "ok_files": ["skills/my-skill/SKILL.md", "agents/my-agent/agent.yaml"],
  "modified_files": ["skills/my-skill/scripts/helper.py"],
  "missing_files": [],
  "untracked_files": ["agents/my-agent/notes.md"],
  "has_checksums": true,
  "is_clean": false
}
```

**Service call**: `checksum_service.verify_package(package_name, verify_all)`

---

### `aam_diff`

```python
@mcp.tool(tags={"read"})
def aam_diff(package_name: str) -> dict:
    """Show local modifications vs installed package version.

    Args:
        package_name: Installed package name.

    Returns:
        Diff details with modified, untracked, and missing files.
    """
```

**Return schema**:
```json
{
  "package_name": "@myorg/my-agent",
  "version": "1.0.0",
  "modified_files": [
    {
      "path": "skills/my-skill/scripts/helper.py",
      "diff": "--- installed\n+++ local\n@@ -1,3 +1,3 @@\n-old_function()\n+new_function()"
    }
  ],
  "untracked_files": ["agents/my-agent/notes.md"],
  "missing_files": []
}
```

**Service call**: `checksum_service.diff_package(package_name)`

---

## Write Tools (tag: `"write"`, gated by `--allow-write`)

### `aam_source_add`

```python
@mcp.tool(tags={"write"})
def aam_source_add(
    source: str,
    ref: str = "main",
    path: str | None = None,
    name: str | None = None,
) -> dict:
    """Register a new remote git repository as an artifact source.

    Args:
        source: Git source — shorthand, URL, or git+https:// format.
        ref: Git reference (default: 'main').
        path: Subdirectory to scan (default: entire repo).
        name: Custom display name.

    Returns:
        Source entry with discovered artifact count.
    """
```

**Return schema**:
```json
{
  "name": "openai/skills:.curated",
  "url": "https://github.com/openai/skills",
  "ref": "main",
  "path": "skills/.curated",
  "cache_path": "~/.aam/cache/git/github.com/openai/skills/",
  "artifact_count": 30,
  "artifacts_by_type": {"skills": 30, "agents": 0, "prompts": 0, "instructions": 0}
}
```

**Service call**: `source_service.add_source(source, ref, path, name)`

---

### `aam_source_remove`

```python
@mcp.tool(tags={"write"})
def aam_source_remove(
    source_name: str,
    purge_cache: bool = False,
) -> dict:
    """Remove a registered remote git source.

    Args:
        source_name: Name of the source to remove.
        purge_cache: Also delete cached clone.

    Returns:
        Confirmation with removed source name.
    """
```

**Return schema**:
```json
{
  "removed": "openai/skills:.curated",
  "cache_purged": false,
  "was_default": false
}
```

**Service call**: `source_service.remove_source(source_name, purge_cache)`

---

### `aam_source_update`

```python
@mcp.tool(tags={"write"})
def aam_source_update(
    source_name: str | None = None,
    update_all: bool = False,
) -> dict:
    """Fetch upstream changes and update local cache.

    Args:
        source_name: Source to update. Required if update_all is False.
        update_all: Update all registered sources.

    Returns:
        Update summary per source.
    """
```

**Return schema**:
```json
{
  "sources": [
    {
      "name": "openai/skills:.curated",
      "old_commit": "abc123d",
      "new_commit": "def456a",
      "new_count": 2,
      "modified_count": 1,
      "removed_count": 0,
      "status": "updated"
    }
  ],
  "total_new": 2,
  "total_modified": 1
}
```

**Service call**: `source_service.update_source(source_name, update_all, dry_run=False)`

---

## Extended Write Tool (from spec 002)

### `aam_create_package` Extension

The existing `aam_create_package` write tool (defined in spec 002) is extended with optional parameters for creating packages from remote sources:

```python
@mcp.tool(tags={"write"})
def aam_create_package(
    path: str = ".",
    name: str | None = None,
    version: str | None = None,
    description: str | None = None,
    artifact_types: list[str] | None = None,
    include_all: bool = False,
    # NEW parameters (spec 003)
    from_source: str | None = None,
    artifacts: list[str] | None = None,
) -> dict:
    """Create an AAM package from local project or remote source.

    Args:
        path: Project directory (default: current).
        name: Package name override.
        version: Package version override.
        description: Package description.
        artifact_types: Filter artifact types to include.
        include_all: Include all detected artifacts without prompting.
        from_source: Create from remote source (source name). NEW in spec 003.
        artifacts: Pre-select artifacts by name (comma-separated). NEW in spec 003.

    Returns:
        Created package details with provenance if from remote source.
    """
```

**Modified behavior**: When `from_source` is provided:
1. Read artifacts from the specified source's cache via `source_service.scan_source(from_source)`
2. Filter by `artifacts` list if provided, include all if `include_all=True`
3. Copy selected artifacts from cache to new package directory
4. Generate `aam.yaml` with `provenance:` section
5. Compute file checksums

**Return schema** (when `from_source` is used):
```json
{
  "manifest_path": ".aam/aam.yaml",
  "package_name": "@myorg/curated-skills",
  "version": "1.0.0",
  "artifacts_included": ["gh-fix-ci", "playwright"],
  "provenance": {
    "source_type": "git",
    "source_url": "https://github.com/openai/skills",
    "source_ref": "main",
    "source_path": "skills/.curated",
    "source_commit": "abc123def456",
    "fetched_at": "2026-02-08T10:30:00Z"
  }
}
```

**Error handling**:
- `[AAM_SOURCE_NOT_FOUND]` if `from_source` name not in config
- `[AAM_INVALID_ARGUMENT]` if `artifacts` contains names not found in source

**Service call**: `source_service.scan_source(from_source)` (for artifact list) + `package_service.create_package(...)` (for manifest generation)

---

## MCP Resources

### `aam://sources`

```python
@mcp.resource("aam://sources")
def get_sources() -> list[dict]:
    """All configured remote git artifact sources with status."""
```

Returns same schema as `aam_source_list` tool.

---

### `aam://sources/{name}`

```python
@mcp.resource("aam://sources/{name}")
def get_source_details(name: str) -> dict:
    """Detailed info for a specific source including cached artifact list."""
```

**Return schema**:
```json
{
  "name": "openai/skills:.curated",
  "type": "git",
  "url": "https://github.com/openai/skills",
  "ref": "main",
  "path": "skills/.curated",
  "last_commit": "abc123def456",
  "last_fetched": "2026-02-08T10:30:00Z",
  "artifact_count": 30,
  "default": false,
  "artifacts": [
    {"name": "gh-fix-ci", "type": "skill", "path": "...", "has_vendor_agent": true}
  ]
}
```

---

### `aam://sources/{name}/candidates`

```python
@mcp.resource("aam://sources/{name}/candidates")
def get_source_candidates(name: str) -> list[dict]:
    """Unpackaged artifact candidates from a specific source."""
```

Returns same schema as `aam_source_candidates` tool, filtered to the named source.
