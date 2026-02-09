# Data Model: MCP Server for AAM CLI

**Branch**: `002-mcp-server-cli` | **Date**: 2026-02-08

This document defines the data entities used in the MCP server layer. These are the structured types returned by MCP tools and resources — they bridge the existing `core/` models and the MCP protocol's JSON responses.

## Entities

### 1. MCPServerConfig

Configuration for the MCP server instance, derived from CLI flags.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `transport` | `Literal["stdio", "http"]` | `"stdio"` | Transport protocol |
| `port` | `int` | `8000` | HTTP port (only used with http transport) |
| `allow_write` | `bool` | `False` | Enable write (mutating) tools |
| `log_file` | `str | None` | `None` | Path to log file |
| `log_level` | `str` | `"INFO"` | Log level: DEBUG, INFO, WARNING, ERROR |

**Validation rules**:
- `transport` must be one of `"stdio"` or `"http"`
- `port` must be 1-65535
- `log_level` must be one of `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`

---

### 2. SearchResult

Returned by `aam_search` tool. A list of these represents search results.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Full package name (e.g., `@scope/my-package`) |
| `version` | `str` | Latest version string |
| `description` | `str` | Package description |
| `author` | `str | None` | Package author |
| `artifact_types` | `list[str]` | Types of artifacts (skill, agent, prompt, instruction) |
| `registry` | `str` | Registry name where found |

**Source mapping**: Derived from `registry.base.PackageIndexEntry`

---

### 3. InstalledPackageInfo

Returned by `aam_list` tool and `aam://packages/installed` resource.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Package name |
| `version` | `str` | Installed version |
| `source` | `str` | Installation source (registry name, local path, archive path) |
| `artifact_count` | `int` | Total number of artifacts |
| `artifacts` | `dict[str, int]` | Count by type (e.g., `{"skills": 2, "prompts": 1}`) |
| `checksum` | `str | None` | SHA-256 checksum of the installed archive |

**Source mapping**: Derived from `core.workspace.LockedPackage`

---

### 4. PackageDetail

Returned by `aam_info` tool and `aam://packages/{name}` resource.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Full package name |
| `version` | `str` | Package version |
| `description` | `str` | Package description |
| `author` | `str | None` | Author |
| `license` | `str | None` | License |
| `repository` | `str | None` | Repository URL |
| `homepage` | `str | None` | Homepage URL |
| `keywords` | `list[str]` | Keywords |
| `artifacts` | `dict[str, list[ArtifactInfo]]` | Artifacts grouped by type |
| `dependencies` | `dict[str, str]` | Dependency name → version constraint |
| `platforms` | `dict[str, dict]` | Platform configurations |
| `installed` | `bool` | Whether currently installed in workspace |
| `installed_version` | `str | None` | Installed version (if different from latest) |

**Source mapping**: Derived from `core.manifest.PackageManifest` + `registry.base.PackageMetadata`

---

### 5. ArtifactInfo

Nested within `PackageDetail.artifacts`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Artifact name |
| `path` | `str` | Relative path within package |
| `description` | `str | None` | Artifact description |

**Source mapping**: Derived from `core.manifest.ArtifactRef`

---

### 6. ValidationReport

Returned by `aam_validate` tool.

| Field | Type | Description |
|-------|------|-------------|
| `valid` | `bool` | Whether the package is valid |
| `package_name` | `str | None` | Package name (if parseable) |
| `package_version` | `str | None` | Package version (if parseable) |
| `errors` | `list[str]` | Validation error messages |
| `warnings` | `list[str]` | Validation warning messages |
| `artifact_count` | `int` | Number of artifacts found |
| `artifacts_valid` | `bool` | Whether all artifact paths exist |

---

### 7. ConfigData

Returned by `aam_config_get` tool and `aam://config` resource.

| Field | Type | Description |
|-------|------|-------------|
| `key` | `str | None` | Config key requested (None = all) |
| `value` | `Any` | Config value(s) |
| `source` | `str` | Where value came from: "global", "project", "default" |

---

### 8. RegistryInfo

Returned by `aam_registry_list` tool and `aam://registries` resource.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Registry name |
| `url` | `str` | Registry URL or path |
| `type` | `str` | Registry type: "local", "git", "http" |
| `is_default` | `bool` | Whether this is the default registry |
| `accessible` | `bool | None` | Whether registry is accessible (None = not checked) |

**Source mapping**: Derived from `core.config.RegistrySource`

---

### 9. InstallResult

Returned by `aam_install` tool.

| Field | Type | Description |
|-------|------|-------------|
| `installed` | `list[InstalledPackageInfo]` | Packages successfully installed |
| `already_installed` | `list[str]` | Packages already at requested version |
| `failed` | `list[dict]` | Failed packages with error messages |
| `dependencies_resolved` | `int` | Total dependencies resolved |

---

### 10. UninstallResult

Returned by `aam_uninstall` tool.

| Field | Type | Description |
|-------|------|-------------|
| `package_name` | `str` | Package that was uninstalled |
| `version` | `str` | Version that was removed |
| `files_removed` | `int` | Number of files cleaned up |
| `dependents_warning` | `list[str]` | Packages that depended on this one |

---

### 11. PublishResult

Returned by `aam_publish` tool.

| Field | Type | Description |
|-------|------|-------------|
| `package_name` | `str` | Published package name |
| `version` | `str` | Published version |
| `registry` | `str` | Registry published to |
| `archive_size` | `int` | Archive size in bytes |
| `checksum` | `str` | SHA-256 checksum |

---

### 12. CreatePackageResult

Returned by `aam_create_package` tool.

| Field | Type | Description |
|-------|------|-------------|
| `manifest_path` | `str` | Path to created aam.yaml |
| `package_name` | `str` | Package name |
| `version` | `str` | Package version |
| `artifacts_included` | `dict[str, int]` | Count by artifact type |
| `total_artifacts` | `int` | Total artifacts included |

---

### 13. DoctorReport

Returned by `aam_doctor` tool.

| Field | Type | Description |
|-------|------|-------------|
| `healthy` | `bool` | Overall health status |
| `checks` | `list[DoctorCheck]` | Individual check results |
| `summary` | `str` | Human-readable summary |

---

### 14. DoctorCheck

Nested within `DoctorReport.checks`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Check name (e.g., "python_version", "config_valid") |
| `status` | `Literal["pass", "warn", "fail"]` | Check result |
| `message` | `str` | Human-readable result message |
| `suggestion` | `str | None` | Suggested fix (for warn/fail) |

---

## Entity Relationships

```
MCPServerConfig ─── creates ──→ FastMCP Server Instance
                                      │
                         ┌────────────┼────────────┐
                         ▼            ▼            ▼
                     MCP Tools   MCP Resources  Tag Filter
                         │            │
                         ▼            ▼
                    Services Layer (pure functions)
                         │
              ┌──────────┼──────────────┐
              ▼          ▼              ▼
         SearchResult  PackageDetail  ValidationReport
         InstallResult UninstallResult PublishResult
         ConfigData    RegistryInfo   DoctorReport
         InstalledPackageInfo         CreatePackageResult
```

## Notes

- All entities are returned as plain Python `dict` objects from MCP tools/resources (FastMCP serializes to JSON automatically).
- Pydantic models may be used internally for validation but the MCP response is always a dict.
- TypedDict or dataclass definitions are recommended for type safety in service layer signatures.
- No database entities — all data comes from filesystem (`.aam/`, registries, `aam.yaml`).
