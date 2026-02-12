# MCP Tool Contracts

**Branch**: `002-mcp-server-cli` | **Date**: 2026-02-08

This document defines the contract for each MCP tool exposed by the AAM server. Each tool maps to an existing CLI command and wraps the service layer.

## Error Handling (All Tools)

- **Tool failures** are represented as MCP tool errors (`CallToolResult.isError == true`). FastMCP clients will raise `ToolError` by default when a tool fails.
- **Error message format**: MUST start with an error code in brackets, e.g. `[AAM_PACKAGE_NOT_FOUND] ...`.
- **No sensitive data**: Error messages must be safe to surface to IDE agents and must not include secrets or stack traces.
- **Recommended error codes (minimum set)**:
  - `AAM_INVALID_ARGUMENT`
  - `AAM_NOT_INITIALIZED`
  - `AAM_MANIFEST_NOT_FOUND`
  - `AAM_MANIFEST_INVALID`
  - `AAM_REGISTRY_NOT_CONFIGURED`
  - `AAM_REGISTRY_NOT_FOUND`
  - `AAM_REGISTRY_UNREACHABLE`
  - `AAM_PACKAGE_NOT_FOUND`
  - `AAM_PACKAGE_NOT_INSTALLED`
  - `AAM_DEPENDENCY_CONFLICT`
  - `AAM_PERMISSION_DENIED`
  - `AAM_INTERNAL_ERROR`

---

## Read-Only Tools (tag: `read`)

These tools are always available regardless of `--allow-write` flag.

### T01: `aam_search`

**Maps to CLI**: `aam search <query>`
**Service**: `search_service.search_packages()`

**Input Schema**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | `str` | Yes | — | Search terms to match against package names and descriptions |
| `limit` | `int` | No | `10` | Maximum number of results (1-50) |
| `package_type` | `str \| None` | No | `None` | Filter by artifact type: skill, agent, prompt, instruction |

**Output**: `list[SearchResult]`

```json
[
  {
    "name": "@author/my-skill",
    "version": "1.2.0",
    "description": "A helpful Cursor skill",
    "author": "author",
    "artifact_types": ["skill"],
    "registry": "local-dev"
  }
]
```

**Errors**:
- No registries configured → empty list (not an error)
- Registry unreachable → MCP tool error `[AAM_REGISTRY_UNREACHABLE] ...` (include registry name in message)

---

### T02: `aam_list`

**Maps to CLI**: `aam list`
**Service**: `package_service.list_installed_packages()`

**Input Schema**: None (no parameters)

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
  }
]
```

**Errors**:
- No `.aam/` workspace → empty list (not an error)

---

### T03: `aam_info`

**Maps to CLI**: `aam info <package>`
**Service**: `package_service.get_package_info()`

**Input Schema**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `package_name` | `str` | Yes | — | Full package name (e.g., `my-pkg` or `@scope/my-pkg`) |
| `version` | `str \| None` | No | `None` | Specific version (default: latest/installed) |

**Output**: `PackageDetail`

```json
{
  "name": "my-package",
  "version": "1.0.0",
  "description": "Example package",
  "author": "author",
  "license": "Apache-2.0",
  "artifacts": {
    "skills": [{"name": "my-skill", "path": "skills/my-skill/", "description": "A skill"}]
  },
  "dependencies": {"other-pkg": "^1.0.0"},
  "platforms": {"cursor": {"skill_scope": "project"}},
  "installed": true,
  "installed_version": "1.0.0"
}
```

**Errors**:
- Package not found → MCP tool error `[AAM_PACKAGE_NOT_FOUND] ...`

---

### T04: `aam_validate`

**Maps to CLI**: `aam validate [path]`
**Service**: `validate_service.validate_package()`

**Input Schema**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `str` | No | `"."` | Path to package directory |

**Output**: `ValidationReport`

```json
{
  "valid": false,
  "package_name": "my-package",
  "package_version": "1.0.0",
  "errors": ["Artifact path 'skills/missing/' does not exist"],
  "warnings": ["No description provided"],
  "artifact_count": 3,
  "artifacts_valid": false
}
```

**Errors**:
- No `aam.yaml` found → `{"valid": false, "errors": ["No aam.yaml found at ..."]}`
- YAML parse error → `{"valid": false, "errors": ["YAML parse error: ..."]}`

---

### T05: `aam_config_get`

**Maps to CLI**: `aam config get [key]` / `aam config list`
**Service**: `config_service.get_config()`

**Input Schema**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `key` | `str \| None` | No | `None` | Dot-notation config key. If None, returns all config. |

**Output**: `ConfigData`

```json
{
  "key": "default_platform",
  "value": "cursor",
  "source": "global"
}
```

Or for all config (key=None):

```json
{
  "key": null,
  "value": {
    "default_platform": "cursor",
    "security": {"require_checksum": true}
  },
  "source": "merged"
}
```

**Errors**:
- Invalid key → MCP tool error `[AAM_INVALID_ARGUMENT] ...` (include key and list valid keys)

---

### T06: `aam_registry_list`

**Maps to CLI**: `aam registry list`
**Service**: `registry_service.list_registries()`

**Input Schema**: None (no parameters)

**Output**: `list[RegistryInfo]`

```json
[
  {
    "name": "local-dev",
    "url": "/home/user/my-registry",
    "type": "local",
    "is_default": true,
    "accessible": true
  }
]
```

**Errors**:
- No registries configured → empty list (not an error)

---

### T07: `aam_doctor`

**Maps to CLI**: `aam doctor` (new command)
**Service**: `doctor_service.run_diagnostics()`

**Input Schema**: None (no parameters)

**Output**: `DoctorReport`

```json
{
  "healthy": true,
  "checks": [
    {"name": "python_version", "status": "pass", "message": "Python 3.11.5", "suggestion": null},
    {"name": "config_valid", "status": "pass", "message": "Config loaded successfully", "suggestion": null},
    {"name": "registry_local-dev", "status": "pass", "message": "Registry accessible", "suggestion": null},
    {"name": "packages_integrity", "status": "warn", "message": "1 package missing checksum", "suggestion": "Run 'aam validate' to check packages"}
  ],
  "summary": "3 passed, 1 warning, 0 failed"
}
```

---

## Write Tools (tag: `write`)

These tools are only available when server is started with `--allow-write`.

### T08: `aam_install`

**Maps to CLI**: `aam install <package>`
**Service**: `install_service.install_packages()`

**Input Schema**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `packages` | `list[str]` | Yes | — | Package specifiers (e.g., `["my-pkg", "@scope/pkg@1.2.0"]`) |
| `platform` | `str \| None` | No | `None` | Deploy to specific platform only |
| `force` | `bool` | No | `False` | Force reinstall even if already installed |
| `no_deploy` | `bool` | No | `False` | Install without deploying to platform |

**Output**: `InstallResult`

```json
{
  "installed": [
    {"name": "my-pkg", "version": "1.0.0", "source": "local-dev", "artifact_count": 2, "artifacts": {"skills": 2}, "checksum": "sha256:..."}
  ],
  "already_installed": [],
  "failed": [],
  "dependencies_resolved": 1
}
```

**Errors**:
- Package not found → returned in `failed` list (tool does not crash).
  - `failed` item shape: `{"package": "<spec>", "code": "AAM_PACKAGE_NOT_FOUND", "message": "...", "hint": "...", "details": {}}`
- No workspace → MCP tool error `[AAM_NOT_INITIALIZED] ...` (suggest creating `.aam/` workspace)
- Dependency resolution failure → MCP tool error `[AAM_DEPENDENCY_CONFLICT] ...` (include conflicting constraints in message)

---

### T09: `aam_uninstall`

**Maps to CLI**: `aam uninstall <package>`
**Service**: `package_service.uninstall_package()`

**Input Schema**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `package_name` | `str` | Yes | — | Package name to uninstall |

**Output**: `UninstallResult`

```json
{
  "package_name": "my-pkg",
  "version": "1.0.0",
  "files_removed": 5,
  "dependents_warning": ["other-pkg"]
}
```

**Errors**:
- Package not installed → MCP tool error `[AAM_PACKAGE_NOT_INSTALLED] ...`

---

### T10: `aam_publish`

**Maps to CLI**: `aam publish`
**Service**: `publish_service.publish_package()`

**Input Schema**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `registry` | `str \| None` | No | `None` | Registry to publish to (default: default registry) |
| `tag` | `str` | No | `"latest"` | Distribution tag |

**Output**: `PublishResult`

```json
{
  "package_name": "my-package",
  "version": "1.0.0",
  "registry": "local-dev",
  "archive_size": 12345,
  "checksum": "sha256:abc123..."
}
```

**Errors**:
- No `aam.yaml` → MCP tool error `[AAM_MANIFEST_NOT_FOUND] ...`
- Validation failure → MCP tool error `[AAM_MANIFEST_INVALID] ...`
- Registry not found → MCP tool error `[AAM_REGISTRY_NOT_FOUND] ...`

---

### T11: `aam_create_package`

**Maps to CLI**: `aam create-package [path]`
**Service**: `package_service.create_package()`

**Input Schema**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `str` | No | `"."` | Project directory to scan |
| `name` | `str \| None` | No | `None` | Package name (auto-detected if not provided) |
| `version` | `str \| None` | No | `None` | Package version (default: "0.1.0") |
| `description` | `str \| None` | No | `None` | Package description |
| `artifact_types` | `list[str] \| None` | No | `None` | Filter to types: skill, agent, prompt, instruction |
| `include_all` | `bool` | No | `False` | Include all detected artifacts (no interactive selection) |

**Output**: `CreatePackageResult`

```json
{
  "manifest_path": "/path/to/project/aam.yaml",
  "package_name": "my-project",
  "version": "0.1.0",
  "artifacts_included": {"skills": 2, "prompts": 1},
  "total_artifacts": 3
}
```

**Errors**:
- No artifacts detected → MCP tool error `[AAM_INVALID_ARGUMENT] ...`
- `aam.yaml` already exists → error (suggest using `--force` in CLI)

---

### T12: `aam_config_set`

**Maps to CLI**: `aam config set <key> <value>`
**Service**: `config_service.set_config()`

**Input Schema**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `key` | `str` | Yes | — | Dot-notation config key |
| `value` | `str` | Yes | — | Value to set |

**Output**: `ConfigData`

```json
{
  "key": "default_platform",
  "value": "cursor",
  "source": "global"
}
```

**Errors**:
- Invalid key → MCP tool error `[AAM_INVALID_ARGUMENT] ...` (include key and list valid keys)

---

### T13: `aam_registry_add`

**Maps to CLI**: `aam registry add <name> <url>`
**Service**: `registry_service.add_registry()`

**Input Schema**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | `str` | Yes | — | Registry name |
| `url` | `str` | Yes | — | Registry URL or path |
| `set_default` | `bool` | No | `False` | Set as default registry |

**Output**: `RegistryInfo`

```json
{
  "name": "my-registry",
  "url": "/path/to/registry",
  "type": "local",
  "is_default": false,
  "accessible": true
}
```

**Errors**:
- Name already exists → MCP tool error `[AAM_INVALID_ARGUMENT] ...`
- Path/URL not accessible → MCP tool error `[AAM_REGISTRY_UNREACHABLE] ...`
