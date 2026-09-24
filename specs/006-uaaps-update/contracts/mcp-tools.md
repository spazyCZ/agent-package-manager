# MCP Tool Contracts: UAAPS v0.4.0

**Feature**: 006-uaaps-update
**Date**: 2026-02-20

This document defines the complete MCP tool interface for all new and modified tools introduced by the UAAPS v0.4.0 update.

---

## New Read Tools

### `aam_tree`

Display the resolved dependency tree.

**Signature**:
```python
def aam_tree(
    depth: int = 0,           # 0 = unlimited; N = max levels to show
    project: str = ".",
) -> dict[str, Any]: ...
```

**Returns**:
```json
{
  "tree": [
    {
      "name": "code-review",
      "version": "1.3.2",
      "dep_type": "direct",
      "optional": false,
      "children": [
        {
          "name": "git-utils",
          "version": "1.0.1",
          "dep_type": "transitive",
          "optional": false,
          "children": []
        }
      ]
    }
  ],
  "total_packages": 3,
  "depth_limited": false
}
```

**Tags**: `read`

---

### `aam_why`

Explain why a package is installed.

**Signature**:
```python
def aam_why(
    package_name: str,        # required — package to look up
    project: str = ".",
) -> dict[str, Any]: ...
```

**Returns**:
```json
{
  "package": "git-utils",
  "version": "1.0.1",
  "required_by": [
    {
      "parent": "code-review",
      "parent_version": "1.3.2",
      "constraint": "^1.0.0",
      "dep_type": "direct"
    }
  ],
  "is_direct": false
}
```

**Error returns**:
```json
{
  "error": "Package 'unknown-pkg' is not in the lock file",
  "error_code": "AAM_PACKAGE_NOT_FOUND"
}
```

**Tags**: `read`

---

### `aam_check`

Verify installed dependencies and/or system dependencies.

**Signature**:
```python
def aam_check(
    system_only: bool = False,  # if True, only run system dep checks
    project: str = ".",
) -> dict[str, Any]: ...
```

**Returns** (package check):
```json
{
  "check_type": "packages",
  "all_passed": true,
  "results": [
    {"name": "code-review", "version": "1.3.2", "status": "ok", "note": null},
    {"name": "git-utils", "version": "1.0.1", "status": "missing", "note": "Directory not found"}
  ],
  "passed_count": 1,
  "failed_count": 1
}
```

**Returns** (system check with `system_only=True`):
```json
{
  "check_type": "system",
  "all_required_passed": false,
  "results": [
    {"name": "python", "dep_type": "python", "required": true, "found": true, "found_version": "3.12.1", "found_path": null, "install_hint": null},
    {"name": "pdfplumber", "dep_type": "pip", "required": true, "found": false, "found_version": null, "found_path": null, "install_hint": "Run: pip install pdfplumber"}
  ],
  "passed_count": 1,
  "failed_count": 1,
  "optional_failed_count": 0
}
```

**Tags**: `read`

---

### `aam_audit`

Check installed packages for security issues.

**Signature**:
```python
def aam_audit(
    severity: str = "all",    # critical, high, medium, low, all
    project: str = ".",
) -> dict[str, Any]: ...
```

**Returns**:
```json
{
  "findings": [
    {
      "package_name": "code-review",
      "version": "1.2.0",
      "severity": "critical",
      "title": "Integrity: hash mismatch",
      "description": "Installed archive hash does not match lock file integrity hash. Package may have been tampered with.",
      "finding_type": "integrity",
      "advisory_url": null
    }
  ],
  "total_findings": 1,
  "severity_counts": {"critical": 1, "high": 0, "medium": 0, "low": 0},
  "packages_scanned": 3,
  "advisory_source": "local_integrity"
}
```

**Tags**: `read`

---

### `aam_dedupe`

Flatten compatible duplicate package versions.

**Signature**:
```python
def aam_dedupe(
    dry_run: bool = True,     # default True for safety — MCP callers should be cautious
    project: str = ".",
) -> dict[str, Any]: ...
```

**Returns**:
```json
{
  "dry_run": true,
  "would_dedupe": [
    {"name": "git-utils", "version": "1.0.1", "from_paths": ["code-review/", "testing-utils/"], "to_path": "./"}
  ],
  "conflicts_skipped": [],
  "packages_changed": 1
}
```

**Tags**: `read` (even with `dry_run=False` it writes to `.agent-packages/`, classified as read since it's project-local and reversible; write-flagged tools require `--allow-write`)

> **Note**: `aam_dedupe` with `dry_run=False` is a write operation on `.agent-packages/`. For MCP safety, it is tagged `read` but the dry_run default protects against accidental mutation. If the caller wants to apply deduplication, they should use the CLI directly or set `dry_run=False` explicitly.

---

### `aam_prune`

Remove installed packages not in the dependency tree.

**Signature**:
```python
def aam_prune(
    dry_run: bool = True,     # default True for safety
    project: str = ".",
) -> dict[str, Any]: ...
```

**Returns**:
```json
{
  "dry_run": true,
  "would_remove": [
    {"name": "old-tool", "version": "0.9.0", "path": ".agent-packages/old-tool/"},
    {"name": "legacy-utils", "version": "1.1.0", "path": ".agent-packages/legacy-utils/"}
  ],
  "packages_removed": 2,
  "bytes_freed": 49283072
}
```

**Tags**: `read` (same note as `aam_dedupe` — dry_run default protects against accidental mutation)

---

## Updated Read Tools

### `aam_validate` — updated for new schema

No signature change. Internally calls `load_manifest_universal()` and validates against UAAPS schema including new fields.

**Updated return** (new fields in report):
```json
{
  "valid": true,
  "package_name": "my-pkg",
  "package_version": "1.0.0",
  "manifest_format": "json",
  "errors": [],
  "warnings": ["permissions: declared but no platform adapter enforces them yet"],
  "artifact_count": 3,
  "artifacts_valid": true,
  "artifacts_discovered": true
}
```

---

### `aam_info` — updated for new manifest fields

No signature change. Returns new fields from `PackageManifest`:
```json
{
  "name": "my-pkg",
  "version": "1.0.0",
  "manifest_format": "json",
  "category": "Developer Tools",
  "engines": {"claude-code": ">=1.0"},
  "env": {"GITHUB_TOKEN": {"description": "...", "required": true}},
  "permissions": {"fs": ["read"], "network": [], "shell": false},
  "optional_dependencies": {},
  "peer_dependencies": {},
  "system_dependencies": null,
  "...": "existing fields unchanged"
}
```

---

## Updated Write Tools

### `aam_install` — new parameters

**Signature**:
```python
def aam_install(
    packages: list[str] | None = None,
    frozen: bool = False,
    minimal: bool = False,
    latest: bool = False,
    dry_run: bool = False,
    install_system_deps: bool = False,
    skip_checks: bool = False,
    no_deploy: bool = False,
    force: bool = False,
    platform: str | None = None,
    project: str = ".",
) -> dict[str, Any]: ...
```

**Returns** (updated with new fields):
```json
{
  "installed": ["code-review@1.3.2", "git-utils@1.0.1"],
  "failed": [],
  "skipped": [],
  "strategy": "default",
  "dry_run": false,
  "system_checks": {
    "all_required_passed": true,
    "passed_count": 3,
    "failed_count": 0
  },
  "env_vars_prompted": [],
  "permissions_confirmed": [],
  "lock_file": "package.agent.lock"
}
```

---

## Updated Resources

### `aam://manifest`

Updated to serve `package.agent.json` content when present.

```
Resource URI: aam://manifest
MIME type: application/json (for package.agent.json) or text/yaml (for aam.yaml)
```

**Content**: Full manifest content (JSON or YAML string depending on format).

New field `manifest_format` indicates which format was found:
```json
{
  "uri": "aam://manifest",
  "name": "Package Manifest",
  "description": "Current package.agent.json manifest",
  "manifest_format": "json"
}
```

---

## Tool Count Summary

| Category | Before | After | Delta |
|----------|--------|-------|-------|
| Read-only tools | 17 | 23 | +6 |
| Write tools | 12 | 12 | 0 |
| **Total** | **29** | **35** | **+6** |

**New read tools**: `aam_tree`, `aam_why`, `aam_check`, `aam_audit`, `aam_dedupe`, `aam_prune`

**Updated `server.py` constants**:
```python
# Read-only: 23 (was 17)
# Full access: 23 read + 12 write = 35 (was 29)
```
