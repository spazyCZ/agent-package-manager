# Tasks: MCP Server for AAM CLI

**Input**: Design documents from `/specs/002-mcp-server-cli/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/mcp-tools.md, contracts/mcp-resources.md

**Tests**: Included — unit tests with FastMCP in-memory `Client` and mocked services, integration tests with real local registry.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All paths are relative to `apps/aam-cli/` within the monorepo.

## Error Handling Convention (MCP)

- **Expected domain outcomes**: Return the tool’s documented output shape (e.g., `ValidationReport` with `valid=false`, `InstallResult` with entries in `failed`).
- **Tool failures (unexpected/unrecoverable)**: Raise an MCP tool error (so `CallToolResult.isError == true`). Error messages MUST be safe (no secrets) and MUST start with an error code in brackets, e.g. `[AAM_INTERNAL_ERROR] ...`.
- **Error codes (minimum set)**:
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

## Phase → User Story Mapping

| Phase | User Story | Priority | Title |
|-------|-----------|----------|-------|
| Phase 1 | — | — | Setup (Dependencies & Project Structure) |
| Phase 2 | — | — | Foundational (Service Layer Extraction) |
| Phase 3 | US4 | P1 | Start and Configure the MCP Server |
| Phase 4 | US1 | P1 | Agent Searches and Discovers Packages |
| Phase 5 | US3 | P2 | Agent Reads Project Context via Resources |
| Phase 6 | US2 | P2 | Agent Installs and Manages Packages |
| Phase 7 | US5 | P3 | Agent Validates and Creates Packages |
| Phase 8 | US6 | P3 | Agent Diagnoses AAM Environment Issues |
| Phase 9 | — | — | Testing |
| Phase 10 | — | — | Documentation & Polish |

---

## Phase 1: Setup (Dependencies & Project Structure)

**Purpose**: Add FastMCP dependency, create new module directories, and wire up the CLI command group.

- [x] T001 Add `fastmcp>=2.8.0,<3.0.0` to `dependencies` list in `pyproject.toml`
  - **Verify**: `npx nx run aam-cli:install` succeeds

- [x] T002 Create MCP module directory structure: `src/aam_cli/mcp/__init__.py`, `src/aam_cli/mcp/server.py`, `src/aam_cli/mcp/tools_read.py`, `src/aam_cli/mcp/tools_write.py`, `src/aam_cli/mcp/resources.py`
  - **Verify**: `npx nx lint aam-cli` passes after completing Phase 1

- [x] T003 [P] Create services module directory structure: `src/aam_cli/services/__init__.py`, `src/aam_cli/services/search_service.py`, `src/aam_cli/services/install_service.py`, `src/aam_cli/services/package_service.py`, `src/aam_cli/services/publish_service.py`, `src/aam_cli/services/validate_service.py`, `src/aam_cli/services/config_service.py`, `src/aam_cli/services/registry_service.py`, `src/aam_cli/services/doctor_service.py`
  - **Verify**: `npx nx lint aam-cli` passes after completing Phase 1

- [x] T004 [P] Create `src/aam_cli/commands/mcp_serve.py` — stub Click command group `mcp` with subcommand `serve` accepting `--transport`, `--port`, `--allow-write`, `--log-file`, `--log-level` options per contracts. Wire as placeholder (raises a Click exception like `[AAM_INTERNAL_ERROR] MCP server not implemented yet`). **Do not** use `print()` (stdio mode reserves stdout for JSON-RPC).
  - **Verify**: `npx nx run aam-cli:run -- mcp serve --help` shows all options

- [x] T005 Update `src/aam_cli/main.py` — import and register the `mcp` command group from `commands/mcp_serve.py`
  - **Verify**: `npx nx run aam-cli:run -- --help` shows `mcp` in the command list

- [x] T006 [P] Update `project.json` — add `mcp-serve` Nx target: `{"executor": "nx:run-commands", "options": {"cwd": "apps/aam-cli", "command": "python -m aam_cli.main mcp serve"}}`
  - **Verify**: `npx nx run aam-cli:mcp-serve -- --help` runs without Nx errors

**Checkpoint**: FastMCP installed, module structure created, CLI command wired. Ready for service extraction.

---

## Phase 2: Foundational (Service Layer Extraction)

**Purpose**: Extract pure business logic from Click command handlers into a shared service layer. Each service returns structured data (dicts/lists) instead of printing to Rich console. This is the BLOCKING prerequisite for all MCP tool/resource implementations.

**CRITICAL**: No MCP tool or resource task can begin until the services they depend on are complete.

### Service: Search

- [x] T007 [P] Create `src/aam_cli/services/search_service.py` — implement `search_packages(query: str, config: AamConfig, limit: int = 10, package_type: str | None = None) -> list[dict]`. Extract logic from `commands/search.py`: iterate configured registries via `registry/factory.py`, call `registry.search()`, aggregate results, return list of `SearchResult` dicts per data-model.md. No Click/Rich dependencies. Validate `limit` (`1 <= limit <= 50`) and raise `[AAM_INVALID_ARGUMENT]` if out of range.
  - **Verify**: Unit test — call with mocked registry returning fixtures, assert structured output

### Service: Package (List / Info / Uninstall / Create)

- [x] T008 [P] Create `src/aam_cli/services/package_service.py` — implement four functions:
  1. `list_installed_packages(project_dir: Path | None = None) -> list[dict]` — reads lock file via `core/workspace.py`, returns list of `InstalledPackageInfo` dicts
  2. `get_package_info(package_name: str, project_dir: Path | None = None, version: str | None = None) -> dict` — reads installed manifest + lock entry, returns `PackageDetail` dict
  3. `uninstall_package(package_name: str, config: AamConfig, project_dir: Path | None = None) -> dict` — removes package, undeploys artifacts, updates lock file, returns `UninstallResult` dict
  4. `create_package(path: Path, name: str | None = None, version: str | None = None, description: str | None = None, artifact_types: list[str] | None = None, include_all: bool = False) -> dict` — scans for artifacts via `detection/scanner.py`, generates manifest, returns `CreatePackageResult` dict
  - **Verify**: Unit test — call `list_installed_packages()` with mocked workspace, assert structured list

### Service: Validate

- [x] T009 [P] Create `src/aam_cli/services/validate_service.py` — implement `validate_package(path: Path) -> dict`. Extract logic from `commands/validate.py`: load `aam.yaml`, validate against Pydantic schema, check artifact paths exist, return `ValidationReport` dict per data-model.md. Validation failures are reported in the returned `ValidationReport` (`valid=false`, populated `errors` list) rather than raised as tool errors.
  - **Verify**: Unit test — call with temp dir containing valid/invalid aam.yaml, assert report structure

### Service: Config

- [x] T010 [P] Create `src/aam_cli/services/config_service.py` — implement three functions:
  1. `get_config(key: str | None = None, project_dir: Path | None = None) -> dict` — loads config via `core/config.py`, returns `ConfigData` dict with key, value, and source
  2. `set_config(key: str, value: str) -> dict` — updates global config, returns updated `ConfigData` dict
  3. `list_config(project_dir: Path | None = None) -> dict` — returns full merged config as dict
  - **Verify**: Unit test — call `get_config(key="default_platform")`, assert dict with value and source

### Service: Registry

- [x] T011 [P] Create `src/aam_cli/services/registry_service.py` — implement two functions:
  1. `list_registries(project_dir: Path | None = None) -> list[dict]` — loads config, returns list of `RegistryInfo` dicts
  2. `add_registry(name: str, url: str, set_default: bool = False) -> dict` — adds to global config, returns `RegistryInfo` dict. Validates name uniqueness and path/URL accessibility.
  - **Verify**: Unit test — call `list_registries()` with mocked config, assert list structure

### Service: Publish

- [x] T012 [P] Create `src/aam_cli/services/publish_service.py` — implement `publish_package(registry_name: str | None = None, tag: str = "latest", project_dir: Path | None = None) -> dict`. Extract logic from `commands/publish.py`: find `.aam` archive, verify checksum, get registry via factory, call `registry.publish()`, return `PublishResult` dict per data-model.md.
  - **Verify**: Unit test — call with mocked registry, assert result dict with package_name, version, checksum

### Service: Install

- [x] T013 Create `src/aam_cli/services/install_service.py` — implement `install_packages(packages: list[str], config: AamConfig, platform: str | None = None, force: bool = False, no_deploy: bool = False, project_dir: Path | None = None) -> dict`. Extract logic from `commands/install.py`: parse package specs, resolve dependencies via `core/resolver.py`, download/extract/deploy via `core/installer.py`, return `InstallResult` dict per data-model.md. Supports registry, local directory, and archive sources.
  - **Concurrency/locking**: serialize all workspace-mutating operations (install/uninstall/publish/config set/registry add) using an in-process lock to prevent race conditions.
  - **Atomicity**: perform installs via a staging directory (e.g., `.aam/.tmp/`) and only update `aam-lock.yaml` after successful extraction + deploy. Ensure staging cleanup on failure so partial installs are either rolled back or detectable.
  - **Detectability**: leave a clear marker for `doctor_service` to detect incomplete installs if the process is killed mid-operation.
  - **Verify**: Unit test — call with mocked registry + resolver, assert result dict

**Checkpoint**: All 8 service modules created. Pure functions with structured return types. Ready for MCP tool and resource wiring.

---

## Phase 3: User Story 4 — Start and Configure the MCP Server (Priority: P1) MVP

**Goal**: A user can launch the MCP server from the CLI and connect to it from an IDE.

**Independent Test**: Run `aam mcp serve --transport http --port 9000`, then use FastMCP Client to connect and verify `initialize` handshake succeeds and tools are listed.

### Implementation for User Story 4

- [x] T014 Implement `src/aam_cli/mcp/server.py` — `create_mcp_server(allow_write: bool = False) -> FastMCP` factory function:
  1. Create `FastMCP(name="aam", instructions="...", version=__version__)`
  2. When `allow_write=False`, set `exclude_tags={"write"}` to hide write tools
  3. Import and register all tools from `tools_read.py` and `tools_write.py`
  4. Import and register all resources from `resources.py`
  5. Export `mcp` server object at module level for `fastmcp run` compatibility
  - **Verify**: `npx nx run aam-cli:run -- mcp serve --help` runs without import errors

- [x] T015 Implement `src/aam_cli/mcp/__init__.py` — export `create_mcp_server` and the default `mcp` instance
  - **Verify**: `npx nx lint aam-cli` passes (imports + type checks succeed)

- [x] T016 Complete `src/aam_cli/commands/mcp_serve.py` — implement the `serve` subcommand:
  1. Configure logging: redirect to stderr by default, to `--log-file` if specified, at `--log-level` level
  2. Call `create_mcp_server(allow_write=ctx_allow_write)` to build the server
  3. Call `mcp.run(transport=transport)` for stdio or `mcp.run(transport="http", host="0.0.0.0", port=port)` for HTTP
  4. Handle SIGINT/SIGTERM for graceful shutdown: stop accepting new requests, allow any in-flight request to finish, flush logs, then exit cleanly
  - **Verify**: Start `npx nx run aam-cli:mcp-serve -- --transport http --port 9123` and use a FastMCP client to `list_tools()` successfully (handshake + tool listing)

- [x] T017 Verify safety model — write a manual test that:
  1. Starts server without `--allow-write`
  2. Connects with FastMCP Client
  3. Lists tools → only read tools visible (7 tools)
  4. Starts server with `--allow-write`
  5. Lists tools → all tools visible (13 tools)
  - **Verify**: Read-only server exposes exactly 7 tools; full-access server exposes exactly 13 tools

**Checkpoint**: User Story 4 complete. MCP server starts, responds to handshake, lists tools, and enforces safety model.

---

## Phase 4: User Story 1 — Agent Searches and Discovers Packages (Priority: P1) MVP

**Goal**: An IDE agent can search registries, list installed packages, and inspect package details through MCP tools.

**Independent Test**: Connect FastMCP Client, call `aam_search`, `aam_list`, `aam_info` — verify structured results returned.

### Implementation for User Story 1

- [x] T018 Implement `src/aam_cli/mcp/tools_read.py` — define all 7 read-only tools using `@mcp.tool(tags={"read"})` decorators. Each tool calls the corresponding service function and returns structured data:
  1. `aam_search(query: str, limit: int = 10, package_type: str | None = None) -> list[dict]` → calls `search_service.search_packages()` (enforce `1 <= limit <= 50`)
  2. `aam_list() -> list[dict]` → calls `package_service.list_installed_packages()`
  3. `aam_info(package_name: str, version: str | None = None) -> dict` → calls `package_service.get_package_info()`
  4. `aam_validate(path: str = ".") -> dict` → calls `validate_service.validate_package()`
  5. `aam_config_get(key: str | None = None) -> dict` → calls `config_service.get_config()`
  6. `aam_registry_list() -> list[dict]` → calls `registry_service.list_registries()`
  7. `aam_doctor() -> dict` → calls `doctor_service.run_diagnostics()` (stub initially, completed in Phase 8)
  - All tools must have Google-style docstrings with Args/Returns sections (FastMCP uses these for tool descriptions)
  - Tool failures MUST follow the **Error Handling Convention (MCP)** above
  - **Verify**: FastMCP Client `list_tools()` returns 7 tools with correct names, schemas, and descriptions

- [x] T019 Register read tools with server — update `src/aam_cli/mcp/server.py` to import tool definitions from `tools_read.py` so they are registered on the `FastMCP` instance. Use either direct import (decorators register on import) or explicit `mcp.tool()` registration.
  - **Verify**: `create_mcp_server()` returns server with 7 tools listed

- [x] T020 Verify `aam_search` end-to-end — with HTTP server running and a local registry configured:
  1. Call `aam_search` with query matching a published package
  2. Verify response contains package name, version, description, artifact_types
  3. Call with empty query → returns all packages (up to limit)
  4. Call with `package_type` filter → only matching types returned
  - **Verify**: Search results match packages in local registry

- [x] T021 Verify `aam_list` and `aam_info` end-to-end — with packages installed:
  1. Call `aam_list` → verify list of installed packages with artifact counts
  2. Call `aam_info` with installed package name → verify full metadata returned
  3. Call `aam_info` with non-existent package → verify MCP tool error (e.g., `[AAM_PACKAGE_NOT_FOUND] ...`)
  - **Verify**: Results match `.aam/aam-lock.yaml` and installed manifests

**Checkpoint**: User Story 1 complete. IDE agents can search, list, and inspect packages through MCP. Combined with US4, the core read-only MCP workflow is functional.

---

## Phase 5: User Story 3 — Agent Reads Project Context via Resources (Priority: P2)

**Goal**: An IDE agent can read passive MCP resources for project context (config, installed packages, manifest, registries).

**Independent Test**: Connect FastMCP Client, read each resource URI — verify structured data returned.

### Implementation for User Story 3

- [x] T022 Implement `src/aam_cli/mcp/resources.py` — define all 5 MCP resources using `@mcp.resource` decorators:
  1. `aam://config` → calls `config_service.get_config(key=None)`, returns merged config dict
  2. `aam://packages/installed` → calls `package_service.list_installed_packages()`, returns list
  3. `aam://packages/{name}` → calls `package_service.get_package_info(name)`, returns detail dict. Handle scoped names via double-hyphen convention.
  4. `aam://registries` → calls `registry_service.list_registries()`, returns list
  5. `aam://manifest` → reads `aam.yaml` from cwd, returns parsed dict or None. Handle missing file (return None) and parse errors (return error dict).
  - All resources read fresh from filesystem on each request (FR-014, no caching)
  - **Verify**: FastMCP Client `list_resources()` returns 5 resources (4 static + 1 template)

- [x] T023 Register resources with server — update `src/aam_cli/mcp/server.py` to import resource definitions from `resources.py`
  - **Verify**: `create_mcp_server()` returns server with 5 resources

- [x] T024 Verify resources end-to-end:
  1. Read `aam://config` → verify merged config structure
  2. Read `aam://packages/installed` → verify list matches installed packages
  3. Read `aam://packages/{name}` with installed package → verify full metadata
  4. Read `aam://packages/{name}` with non-existent package → verify null/error
  5. Read `aam://registries` → verify registry list
  6. Read `aam://manifest` in dir with `aam.yaml` → verify parsed contents
  7. Read `aam://manifest` in dir without `aam.yaml` → verify null response
  - **Verify**: All resources return accurate, current data

**Checkpoint**: User Story 3 complete. IDE agents can read project context without tool calls.

---

## Phase 6: User Story 2 — Agent Installs and Manages Packages (Priority: P2)

**Goal**: An IDE agent with write permissions can install, uninstall, publish, and configure packages through MCP tools.

**Independent Test**: Start server with `--allow-write`, call `aam_install` with a package name, verify installation. Call `aam_uninstall`, verify removal.

### Implementation for User Story 2

- [x] T025 Implement `src/aam_cli/mcp/tools_write.py` — define all 6 write tools using `@mcp.tool(tags={"write"})` decorators:
  1. `aam_install(packages: list[str], platform: str | None = None, force: bool = False, no_deploy: bool = False) -> dict` → calls `install_service.install_packages()`
  2. `aam_uninstall(package_name: str) -> dict` → calls `package_service.uninstall_package()`
  3. `aam_publish(registry: str | None = None, tag: str = "latest") -> dict` → calls `publish_service.publish_package()`
  4. `aam_create_package(path: str = ".", name: str | None = None, version: str | None = None, description: str | None = None, artifact_types: list[str] | None = None, include_all: bool = False) -> dict` → calls `package_service.create_package()`
  5. `aam_config_set(key: str, value: str) -> dict` → calls `config_service.set_config()`
  6. `aam_registry_add(name: str, url: str, set_default: bool = False) -> dict` → calls `registry_service.add_registry()`
  - All tools must have Google-style docstrings with Args/Returns sections
  - Tool failures MUST follow the **Error Handling Convention (MCP)** above
  - **Verify**: FastMCP Client (with allow_write server) `list_tools()` returns 13 tools total

- [x] T026 Register write tools with server — update `src/aam_cli/mcp/server.py` to import tool definitions from `tools_write.py`
  - **Verify**: `create_mcp_server(allow_write=True)` returns server with 13 tools; `create_mcp_server(allow_write=False)` returns server with 7 tools

- [x] T027 Verify `aam_install` end-to-end:
  1. Start server with `--allow-write` and a local registry with published packages
  2. Call `aam_install` with package name → verify package installed in `.aam/packages/`, lock file updated
  3. Call `aam_install` with `force=True` → verify reinstall
  4. Call `aam_install` with non-existent package → verify `failed` contains an error with code `AAM_PACKAGE_NOT_FOUND` and a safe message
  - **Verify**: `.aam/aam-lock.yaml` contains installed package entry

- [x] T028 Verify `aam_uninstall` and `aam_publish` end-to-end:
  1. With installed package, call `aam_uninstall` → verify removed from `.aam/packages/` and lock file
  2. With valid package in cwd, call `aam_publish` → verify archive appears in registry
  - **Verify**: Package lifecycle (install → uninstall) works through MCP

**Checkpoint**: User Story 2 complete. IDE agents can fully manage packages with write permissions.

---

## Phase 7: User Story 5 — Agent Validates and Creates Packages (Priority: P3)

**Goal**: An IDE agent can validate manifests and create packages from existing projects through MCP tools.

**Independent Test**: Call `aam_validate` against project with aam.yaml, verify report. Call `aam_create_package`, verify manifest created.

### Implementation for User Story 5

- [x] T029 Verify `aam_validate` tool (already registered in T018) works end-to-end:
  1. Call against valid package → `{"valid": true, ...}`
  2. Call against invalid package (missing artifact paths) → `{"valid": false, "errors": [...]}`
  3. Call against directory without aam.yaml → `{"valid": false, "errors": ["No aam.yaml found..."]}`
  - **Verify**: Validation reports match expected structure from contracts/mcp-tools.md T04

- [x] T030 Verify `aam_create_package` tool (already registered in T025) works end-to-end:
  1. Call against project with `.cursor/skills/` artifacts and `include_all=True`
  2. Verify `aam.yaml` created with detected artifacts
  3. Verify response contains `manifest_path`, `package_name`, `artifacts_included`
  - **Verify**: Created manifest validates successfully when passed to `aam_validate`

**Checkpoint**: User Story 5 complete. Package authoring tools work through MCP.

---

## Phase 8: User Story 6 — Agent Diagnoses AAM Environment Issues (Priority: P3)

**Goal**: An IDE agent can run environment diagnostics to identify and troubleshoot AAM setup issues.

**Independent Test**: Call `aam_doctor`, verify structured health report with check results and suggestions.

### Implementation for User Story 6

- [x] T031 Implement `src/aam_cli/services/doctor_service.py` — implement `run_diagnostics(project_dir: Path | None = None) -> dict`:
  1. **python_version check**: Verify Python >= 3.11, return version string
  2. **config_valid check**: Attempt `load_config()`, catch errors, report
  3. **registry checks**: For each configured registry, verify accessibility (local: path exists and readable; http: defer to future)
  4. **packages_integrity check**: For each installed package, verify manifest exists and is parseable, verify checksum if available
  5. **incomplete_install check**: Detect staged/partial installs (e.g., leftover `.aam/.tmp/` entries, lockfile entries with missing package dirs) and report how to recover
  6. Return `DoctorReport` dict per data-model.md with `healthy` (all pass), `checks` list, and `summary` string
  - **Verify**: Unit test — call with mocked config + workspace, assert report structure

- [x] T032 Update `aam_doctor` tool stub in `src/aam_cli/mcp/tools_read.py` — replace stub with call to `doctor_service.run_diagnostics()`
  - **Verify**: FastMCP Client `call_tool("aam_doctor")` returns structured health report

- [x] T033 [P] Create `src/aam_cli/commands/doctor.py` — implement `aam doctor` CLI command that calls `doctor_service.run_diagnostics()` and displays results with Rich formatting. Register in `main.py`.
  - **Verify**: `npx nx run aam-cli:run -- doctor` displays formatted health report in terminal

**Checkpoint**: User Story 6 complete. Environment diagnostics available via MCP and CLI.

---

## Phase 9: Testing

**Purpose**: Comprehensive unit and integration tests for all MCP components.

### Unit Tests (Mocked Services)

- [x] T034 [P] Create `tests/unit/test_mcp_server.py` — test server factory:
  1. `test_unit_create_server_default` — verify server created with name "aam", version matches `__version__`
  2. `test_unit_create_server_read_only` — verify `exclude_tags={"write"}` applied, only 7 tools listed
  3. `test_unit_create_server_allow_write` — verify all 13 tools listed when `allow_write=True`
  4. `test_unit_server_resources` — verify 5 resources registered (4 static + 1 template)
  5. `test_unit_server_tool_names` — verify all tools prefixed with `aam_`
  - Use FastMCP in-memory `Client(transport=mcp_server)` for assertions
  - **Verify**: `npx nx test aam-cli` — all pass

- [x] T035 [P] Create `tests/unit/test_mcp_tools_read.py` — test read tools with mocked services:
  1. `test_unit_aam_search_returns_results` — mock search_service, verify tool returns list
  2. `test_unit_aam_search_empty_query` — verify empty results returned
  3. `test_unit_aam_list_no_workspace` — verify empty list (not error)
  4. `test_unit_aam_info_package_found` — mock package_service, verify detail dict
  5. `test_unit_aam_info_package_not_found` — verify tool failure (`CallToolResult.is_error == True`) and error message starts with `[AAM_PACKAGE_NOT_FOUND]`
  6. `test_unit_aam_validate_valid_package` — mock validate_service, verify report
  7. `test_unit_aam_validate_no_manifest` — verify error report
  8. `test_unit_aam_config_get_all` — mock config_service, verify full config
  9. `test_unit_aam_config_get_specific_key` — verify single value
  10. `test_unit_aam_registry_list` — mock registry_service, verify list
  11. `test_unit_aam_doctor` — mock doctor_service, verify report
  - Use `unittest.mock.patch` to mock service functions
  - **Verify**: `npx nx test aam-cli` — all pass

- [x] T036 [P] Create `tests/unit/test_mcp_tools_write.py` — test write tools with mocked services:
  1. `test_unit_aam_install_success` — mock install_service, verify result dict
  2. `test_unit_aam_install_package_not_found` — verify error in failed list
  3. `test_unit_aam_uninstall_success` — mock package_service, verify result
  4. `test_unit_aam_uninstall_not_installed` — verify tool failure and error message starts with `[AAM_PACKAGE_NOT_INSTALLED]`
  5. `test_unit_aam_publish_success` — mock publish_service, verify result
  6. `test_unit_aam_create_package_success` — mock package_service, verify result
  7. `test_unit_aam_config_set_success` — mock config_service, verify updated value
  8. `test_unit_aam_registry_add_success` — mock registry_service, verify result
  9. `test_unit_write_tools_hidden_in_read_only` — verify write tools not listed when `allow_write=False`
  - **Verify**: `npx nx test aam-cli` — all pass

- [x] T037 [P] Create `tests/unit/test_mcp_resources.py` — test resources with mocked services:
  1. `test_unit_resource_config` — mock config_service, verify dict returned
  2. `test_unit_resource_packages_installed` — mock package_service, verify list
  3. `test_unit_resource_package_detail` — mock package_service with name param
  4. `test_unit_resource_package_not_found` — verify null/error response
  5. `test_unit_resource_registries` — mock registry_service, verify list
  6. `test_unit_resource_manifest_exists` — mock filesystem, verify parsed yaml
  7. `test_unit_resource_manifest_missing` — verify null response
  8. `test_unit_resource_manifest_invalid_yaml` — verify error dict
  - **Verify**: `npx nx test aam-cli` — all pass

- [x] T038 [P] Create `tests/unit/test_services_search.py` — test search service:
  1. `test_unit_search_single_registry` — mock LocalRegistry.search(), verify aggregation
  2. `test_unit_search_multiple_registries` — mock two registries, verify combined results
  3. `test_unit_search_with_type_filter` — verify filtering by artifact type
  4. `test_unit_search_with_limit` — verify result capping
  5. `test_unit_search_no_registries` — verify empty list returned
  - **Verify**: `npx nx test aam-cli` — all pass

- [x] T039 [P] Create `tests/unit/test_services_package.py` — test package service:
  1. `test_unit_list_packages_with_installed` — mock workspace, verify list structure
  2. `test_unit_list_packages_empty` — verify empty list
  3. `test_unit_get_package_info_found` — mock workspace + manifest, verify detail
  4. `test_unit_get_package_info_not_found` — verify error dict
  5. `test_unit_uninstall_success` — mock workspace + adapter, verify result
  - **Verify**: `npx nx test aam-cli` — all pass

- [x] T040 [P] Create `tests/unit/test_services_doctor.py` — test doctor service:
  1. `test_unit_doctor_all_healthy` — mock all checks passing, verify `healthy=True`
  2. `test_unit_doctor_config_error` — mock config load failure, verify `status="fail"`
  3. `test_unit_doctor_registry_inaccessible` — mock missing registry path, verify warning
  4. `test_unit_doctor_package_integrity_issue` — mock corrupt manifest, verify warning
  - **Verify**: `npx nx test aam-cli` — all pass

- [x] T041 [P] Create `tests/unit/test_services_config.py` — test config service:
  1. `test_unit_get_config_all` — verify full config dict
  2. `test_unit_get_config_key` — verify single value with source
  3. `test_unit_set_config` — verify config written and returned
  - **Verify**: `npx nx test aam-cli` — all pass

### Integration Tests (Real Local Registry)

- [x] T042 Create `tests/integration/conftest.py` — shared fixtures:
  1. `tmp_registry` — creates a temporary local registry with `LocalRegistry.init_registry()`
  2. `tmp_workspace` — creates a temporary `.aam/` workspace directory
  3. `sample_package` — creates a valid aam.yaml + artifacts in a temp dir
  4. `published_package` — packs and publishes sample_package to tmp_registry
  5. `installed_package` — installs published_package into tmp_workspace
  6. `mcp_server_read_only` — creates FastMCP server without allow_write, wired to tmp fixtures
  7. `mcp_server_full_access` — creates FastMCP server with allow_write
  8. `mcp_client_read_only` — FastMCP Client connected to read-only server
  9. `mcp_client_full_access` — FastMCP Client connected to full-access server
  - **Verify**: Fixtures create and clean up temp directories correctly

- [x] T043 Create `tests/integration/test_mcp_integration.py` — end-to-end tests:
  1. `test_integration_search_published_package` — publish package, search via MCP, verify found
  2. `test_integration_list_installed_packages` — install package, list via MCP, verify listed
  3. `test_integration_info_installed_package` — install package, info via MCP, verify metadata
  4. `test_integration_install_via_mcp` — use aam_install tool, verify package in workspace
  5. `test_integration_uninstall_via_mcp` — install then uninstall via MCP, verify removed
  6. `test_integration_validate_via_mcp` — validate sample package via MCP, verify report
  7. `test_integration_resources_reflect_state` — install package, read `aam://packages/installed`, verify listed
  8. `test_integration_safety_model_blocks_writes` — read-only server, attempt aam_install, verify rejected
  9. `test_integration_config_via_mcp` — set then get config via MCP, verify persistence
  10. `test_integration_doctor_healthy` — run doctor on clean workspace, verify healthy report
  11. `test_integration_detect_incomplete_install` — simulate leftover staging (`.aam/.tmp/`) and verify doctor reports recovery steps
  - Use FastMCP in-memory Client with real local registry and filesystem
  - **Verify**: `npx nx test aam-cli` — all pass

**Checkpoint**: Full test coverage for MCP server. Unit tests with mocks + integration tests with real filesystem.

---

## Phase 10: Documentation & Polish

**Purpose**: Update user-facing documentation to reflect the new MCP server capability. CLI help text, user guide, and design doc must stay in sync per constitution principle VIII.

### User Documentation Updates

- [x] T044 [P] Update `docs/USER_GUIDE.md` — add new section "MCP Server Integration" covering:
  1. What the MCP server is and why to use it (enable AI agents to manage packages)
  2. Starting the server: `aam mcp serve` with all options explained
  3. IDE Configuration: Cursor (`.cursor/mcp.json`), VS Code (`.vscode/settings.json`), Claude Desktop examples
  4. Available tools table (read-only and write) with descriptions
  5. Available resources table with URI patterns
  6. Safety model explanation (read-only by default, `--allow-write`)
  7. Example agent conversations showing tool usage
  8. Troubleshooting: common issues (server not starting, tools not showing, write tools blocked)
  - **Verify**: Section renders correctly in MkDocs; all CLI flags match `npx nx run aam-cli:run -- mcp serve --help`

- [x] T045 [P] Update `docs/DESIGN.md` — verify section 5.3 "MCP Server Mode" is consistent with implementation:
  1. Check tool list matches implemented tools (13 total: 7 read + 6 write)
  2. Check resource list matches implemented resources (5 total)
  3. Check CLI flags match implemented `aam mcp serve` options
  4. Update any code examples if signatures changed during implementation
  5. Add reference to `aam_cli.services` layer in architecture section
  - **Verify**: No discrepancies between DESIGN.md section 5.3 and implemented code

- [x] T046 [P] Update `docs/USER_GUIDE.md` — add `aam doctor` command documentation:
  1. Command syntax and options
  2. What checks are performed
  3. Example output
  4. How to fix common issues flagged by doctor
  - **Verify**: `npx nx run aam-cli:run -- doctor --help` text matches doc

- [x] T047 [P] Update `docs/USER_GUIDE.md` — update CLI command reference to include:
  1. `aam mcp serve` in the command summary table
  2. `aam doctor` in the command summary table
  3. Update any existing sections that reference available commands to include MCP
  - **Verify**: All CLI commands listed in USER_GUIDE.md match `aam --help` output

### Code Quality & Polish

- [x] T048 [P] Verify all new files follow project coding standards:
  1. Module-level `logger = logging.getLogger(__name__)` in every `.py` file
  2. Type hints on all function signatures (parameters + return types)
  3. Google-style docstrings on all public functions and classes
  4. 80-char `#` block headers between logical sections (imports, constants, functions)
  5. No `print()` — all output via logging
  6. Max 600 lines per file, 100 lines per function
  - **Verify**: `npx nx lint aam-cli` — zero issues

- [x] T049 [P] Run linter, formatter, and type checker on all new code:
  1. `npx nx format aam-cli`
  2. `npx nx lint aam-cli`
  - Fix all issues found
  - **Verify**: Both commands pass with zero errors

- [x] T050 Run full test suite and coverage report:
  1. `npx nx test aam-cli`
  2. Verify MCP module coverage ≥ 80%
  3. Verify service module coverage ≥ 80%
  - **Verify**: All tests pass; coverage targets met (pytest coverage is configured via `pyproject.toml` addopts)

- [x] T051 Verify `npx nx run aam-cli:run -- mcp serve --help` output matches documentation:
  1. Compare `--help` text with docs/USER_GUIDE.md MCP section
  2. Compare with docs/DESIGN.md section 5.3
  3. Ensure all flags, defaults, and descriptions are consistent
  - **Verify**: No discrepancies between CLI help text and documentation

- [x] T052 Run quickstart.md validation — follow `specs/002-mcp-server-cli/quickstart.md` step-by-step:
  1. Install dependencies
  2. Start HTTP server
  3. Test with FastMCP Client script
  4. Configure Cursor IDE integration
  5. Verify all examples work as documented
  - **Verify**: Complete quickstart workflow succeeds without modifications

**Checkpoint**: All documentation updated, code quality verified, tests passing, quickstart validated. Feature complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion (T001 for FastMCP, T002-T003 for directories)
- **US4 Server Start (Phase 3)**: Depends on Phase 2 (needs server factory + at least stub tools)
- **US1 Read Tools (Phase 4)**: Depends on Phase 2 (services) + Phase 3 (server registration)
- **US3 Resources (Phase 5)**: Depends on Phase 2 (services) + Phase 3 (server registration). Can run in parallel with Phase 4.
- **US2 Write Tools (Phase 6)**: Depends on Phase 2 (services) + Phase 3 (server registration). Can run in parallel with Phases 4-5.
- **US5 Validate/Create (Phase 7)**: Depends on Phases 4 + 6 (tools already registered, just verification)
- **US6 Doctor (Phase 8)**: Depends on Phase 1 only (new service, no existing service dependency)
- **Testing (Phase 9)**: Depends on Phases 3-8 (all tools/resources/services implemented)
- **Documentation (Phase 10)**: Depends on Phases 3-8 (all features implemented to document accurately)

### Recommended Execution Order

```
Phase 1 (Setup) → Phase 2 (Services) → Phase 3 (US4: Server)
                                              ↓
                               ┌──────────────┼──────────────┐
                               ↓              ↓              ↓
                         Phase 4 (US1)  Phase 5 (US3)  Phase 6 (US2)
                         Read Tools     Resources      Write Tools
                               ↓              ↓              ↓
                               └──────────────┼──────────────┘
                                              ↓
                               ┌──────────────┼──────────────┐
                               ↓              ↓              ↓
                         Phase 7 (US5)  Phase 8 (US6)  Phase 9 (Tests)
                         Verify Auth    Doctor         Unit + Integration
                               ↓              ↓              ↓
                               └──────────────┴──────────────┘
                                              ↓
                                       Phase 10 (Docs)
```

### Parallel Opportunities per Phase

**Phase 1**: T002, T003 in parallel; T004, T006 in parallel (after T005)
**Phase 2**: T007, T008, T009, T010, T011, T012 all in parallel (independent service files); T013 sequential (depends on more complex extraction)
**Phase 3**: T014, T015 sequential; T016 after T014; T017 after T016
**Phase 4**: T018 then T019 sequential; T020, T021 can verify in parallel after T019
**Phase 5**: T022 then T023 sequential; T024 after T023
**Phase 6**: T025 then T026 sequential; T027, T028 can verify in parallel
**Phase 7**: T029, T030 in parallel
**Phase 8**: T031 then T032 sequential; T033 in parallel
**Phase 9**: T034–T041 all in parallel (independent test files); T042 then T043 sequential
**Phase 10**: T044–T049 all in parallel; T050–T052 sequential (final validation)

---

## Implementation Strategy

### MVP First (P1 User Stories: US4 + US1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Service Layer (at minimum: search, package, config, registry services)
3. Complete Phase 3: US4 — Server starts and enforces safety model
4. Complete Phase 4: US1 — Read tools work through MCP
5. **STOP and VALIDATE**: Connect from IDE, search for packages, list installed packages

### Incremental Delivery (P2 + P3)

6. Add Phase 5 (US3: Resources) + Phase 6 (US2: Write tools) — can be parallel
7. Add Phase 7 (US5: Validate/Create verification) + Phase 8 (US6: Doctor)
8. Phase 9: Testing
9. Phase 10: Documentation

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 52 |
| **Phase 1 (Setup)** | 6 tasks |
| **Phase 2 (Service Layer)** | 7 tasks |
| **US4 (Server Start)** | 4 tasks |
| **US1 (Read Tools)** | 4 tasks |
| **US3 (Resources)** | 3 tasks |
| **US2 (Write Tools)** | 4 tasks |
| **US5 (Validate/Create)** | 2 tasks |
| **US6 (Doctor)** | 3 tasks |
| **Testing** | 10 tasks |
| **Documentation & Polish** | 9 tasks |
| **Parallel opportunities** | 30+ tasks marked [P] |
| **MVP scope** | Phases 1–4 (US4 + US1) = 21 tasks |
| **New files created** | ~25 files (8 services, 5 MCP, 1 command, ~11 test files) |
| **Modified files** | 4 files (main.py, pyproject.toml, project.json, USER_GUIDE.md, DESIGN.md) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after its checkpoint
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- All modules must follow project standards: `logging.getLogger(__name__)`, type hints, Google-style docstrings, 80-char section headers, no `print()`
- Service layer returns `dict` not Pydantic models — FastMCP handles JSON serialization
- FastMCP in-memory `Client(transport=mcp_server)` is the primary test harness for unit tests
