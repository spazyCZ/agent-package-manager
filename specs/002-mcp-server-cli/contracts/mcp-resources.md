# MCP Resource Contracts

**Branch**: `002-mcp-server-cli` | **Date**: 2026-02-08

This document defines the contract for each MCP resource exposed by the AAM server. Resources provide passive, read-only data that IDE agents can pull for context.

Resources are **always available** regardless of the `--allow-write` flag (they have no side effects).

---

## R01: `aam://config`

**Description**: Current AAM configuration (global merged with project-level).
**Service**: `config_service.get_config(key=None)`

**URI**: `aam://config` (static resource)

**Output**: `dict`

```json
{
  "default_platform": "cursor",
  "security": {
    "require_checksum": true,
    "require_signature": false
  },
  "registries": [
    {
      "name": "local-dev",
      "url": "/home/user/my-registry",
      "type": "local",
      "default": true
    }
  ],
  "author": {
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

**Behavior**:
- Returns merged configuration (project > global > defaults precedence).
- If no config files exist, returns default configuration.
- Sensitive values (if any exist in future, e.g., API tokens) are redacted.

---

## R02: `aam://packages/installed`

**Description**: List of all installed AAM packages in the current workspace.
**Service**: `package_service.list_installed_packages()`

**URI**: `aam://packages/installed` (static resource)

**Output**: `list[InstalledPackageInfo]`

```json
[
  {
    "name": "my-package",
    "version": "1.0.0",
    "source": "local-dev",
    "artifact_count": 3,
    "artifacts": {"skills": 2, "prompts": 1},
    "checksum": "sha256:abc123..."
  },
  {
    "name": "@scope/other-pkg",
    "version": "2.1.0",
    "source": "local-dev",
    "artifact_count": 1,
    "artifacts": {"agents": 1},
    "checksum": "sha256:def456..."
  }
]
```

**Behavior**:
- Reads from `.aam/aam-lock.yaml` on each request (no caching).
- Returns empty list if no `.aam/` workspace exists (not an error).
- Returns empty list if lock file exists but has no packages.

---

## R03: `aam://packages/{name}`

**Description**: Detailed metadata for a specific installed package.
**Service**: `package_service.get_package_info()`

**URI**: `aam://packages/{name}` (resource template)

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Package name. For scoped packages, use `scope--name` format in the URI (e.g., `aam://packages/scope--my-pkg`). |

**Output**: `PackageDetail`

```json
{
  "name": "@scope/my-pkg",
  "version": "1.0.0",
  "description": "Example scoped package",
  "author": "scope",
  "license": "Apache-2.0",
  "repository": null,
  "homepage": null,
  "keywords": ["cursor", "skill"],
  "artifacts": {
    "skills": [
      {"name": "my-skill", "path": "skills/my-skill/", "description": "A helpful skill"}
    ]
  },
  "dependencies": {},
  "platforms": {"cursor": {"skill_scope": "project"}},
  "installed": true,
  "installed_version": "1.0.0"
}
```

**Behavior**:
- Looks up package in `.aam/packages/{fs-name}/aam.yaml`.
- Scoped package names use double-hyphen filesystem convention: `@scope/name` → `scope--name`.
- Returns null/error if package is not installed.
- Reads manifest fresh from filesystem on each request.

---

## R04: `aam://registries`

**Description**: All configured AAM registries.
**Service**: `registry_service.list_registries()`

**URI**: `aam://registries` (static resource)

**Output**: `list[RegistryInfo]`

```json
[
  {
    "name": "local-dev",
    "url": "/home/user/my-registry",
    "type": "local",
    "is_default": true,
    "accessible": null
  },
  {
    "name": "team-registry",
    "url": "/shared/team-registry",
    "type": "local",
    "is_default": false,
    "accessible": null
  }
]
```

**Behavior**:
- Reads from merged configuration (global + project registries).
- `accessible` is `null` by default (no connectivity check on resource read — use `aam_doctor` for health checks).
- Returns empty list if no registries configured.

---

## R05: `aam://manifest`

**Description**: Current project's `aam.yaml` manifest contents.
**Service**: Reads `aam.yaml` from current working directory.

**URI**: `aam://manifest` (static resource)

**Output**: `dict | None`

```json
{
  "name": "my-package",
  "version": "1.0.0",
  "description": "My AAM package",
  "author": "John Doe",
  "license": "Apache-2.0",
  "artifacts": {
    "skills": [
      {"name": "my-skill", "path": "skills/my-skill/", "description": "A helpful skill"}
    ],
    "prompts": [
      {"name": "code-review", "path": "prompts/code-review.md", "description": "Code review prompt"}
    ]
  },
  "dependencies": {
    "other-pkg": "^1.0.0"
  },
  "platforms": {
    "cursor": {
      "skill_scope": "project",
      "deploy_instructions_as": "rules"
    }
  }
}
```

**Behavior**:
- Reads `aam.yaml` from the current working directory.
- Returns `null` if no `aam.yaml` exists (not an error).
- Returns raw parsed YAML as a dict (not validated through Pydantic).
- If `aam.yaml` has syntax errors, returns `{"error": "YAML parse error: <details>"}`.
- Reads fresh from filesystem on each request.

---

## Resource Summary

| URI | Type | Always Fresh | Returns on Missing |
|-----|------|-------------|-------------------|
| `aam://config` | Static | Yes (reads config files) | Default config |
| `aam://packages/installed` | Static | Yes (reads lock file) | Empty list |
| `aam://packages/{name}` | Template | Yes (reads manifest) | Null/error |
| `aam://registries` | Static | Yes (reads config) | Empty list |
| `aam://manifest` | Static | Yes (reads aam.yaml) | Null |
