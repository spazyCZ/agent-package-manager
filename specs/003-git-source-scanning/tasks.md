# Tasks: Git Repository Source Scanning & Artifact Discovery

**Input**: Design documents from `/specs/003-git-source-scanning/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-commands.md, contracts/mcp-tools.md, quickstart.md  
**Key Reference**: [`docs/work/git_repo_skills.md`](../../docs/work/git_repo_skills.md) — Contains URL parsing regex, YAML schemas, detection patterns, MCP tool signatures, CLI output examples

**Tests**: Included per Constitution Principle IV (Test-Driven Quality, 80%+ coverage target).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **CLI source**: `apps/aam-cli/src/aam_cli/`
- **CLI tests**: `apps/aam-cli/tests/`
- **Docs**: `docs/`
- All paths relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new module stubs, directories, and shared test infrastructure

- [ ] T001 Create `apps/aam-cli/src/aam_cli/services/` directory with `__init__.py` (if not created by spec 002)
- [ ] T002 [P] Create module stub `apps/aam-cli/src/aam_cli/utils/git_url.py` with section headers and module docstring
- [ ] T003 [P] Create module stub `apps/aam-cli/src/aam_cli/services/git_service.py` with section headers and module docstring
- [ ] T004 [P] Create module stub `apps/aam-cli/src/aam_cli/services/source_service.py` with section headers and module docstring
- [ ] T005 [P] Create module stub `apps/aam-cli/src/aam_cli/services/checksum_service.py` with section headers and module docstring
- [ ] T006 [P] Add shared test fixtures to `apps/aam-cli/tests/conftest.py`: `cli_runner`, `tmp_aam_home`, `tmp_git_repo` (local bare repo factory), `sample_source_config`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, URL parsing, git wrapper, and scanner extension that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

### Models & URL Parsing

- [ ] T007 Implement `GitSourceURL` frozen dataclass and `parse()` factory in `apps/aam-cli/src/aam_cli/utils/git_url.py` — handle HTTPS, SSH, `git+https://`, tree URL, shorthand formats per reference doc Section 4.1.1 regex
- [ ] T008 Implement URL scheme validation (allowlist: `https://`, `git@`, `git+https://`) and display name generation (`{owner}/{repo}` vs `{owner}/{repo}:{suffix}`) in `apps/aam-cli/src/aam_cli/utils/git_url.py`
- [ ] T009 [P] Write unit tests for all URL parsing formats in `apps/aam-cli/tests/unit/test_unit_git_url.py` — shorthand, HTTPS, SSH, tree URL, `git+https://`, `@branch`, `#sha`, custom name override, invalid URLs
- [ ] T010 Add `SourceEntry` Pydantic model to `apps/aam-cli/src/aam_cli/core/config.py` — fields: name, type, url, ref, path, last_commit, last_fetched, artifact_count, default
- [ ] T011 Extend `AamConfig` in `apps/aam-cli/src/aam_cli/core/config.py` — add `sources: list[SourceEntry]` and `removed_defaults: list[str]` fields with empty defaults
- [ ] T012 [P] Add `FileChecksums` Pydantic model to `apps/aam-cli/src/aam_cli/core/workspace.py` — fields: algorithm (default "sha256"), files (dict[str, str])
- [ ] T013 Extend `LockedPackage` in `apps/aam-cli/src/aam_cli/core/workspace.py` — add `file_checksums: FileChecksums | None = None` with backward compatibility
- [ ] T014 [P] Add `Provenance` Pydantic model to `apps/aam-cli/src/aam_cli/core/manifest.py` — fields: source_type, source_url, source_ref, source_path, source_commit, fetched_at
- [ ] T015 Extend `PackageManifest` in `apps/aam-cli/src/aam_cli/core/manifest.py` — add `provenance: Provenance | None = None`

### Git Subprocess Wrapper

- [ ] T016 Implement `git_service.py` core functions in `apps/aam-cli/src/aam_cli/services/git_service.py`: `_run_git()`, `clone_shallow()` (with fallback to full clone when shallow clone fails due to server restrictions), `fetch()`, `get_head_sha()`, `diff_file_names()`, `check_git_available()`, `validate_cache()` (detect corrupted cache via `git status`, delete and trigger re-clone)
- [ ] T017 Implement retry logic with exponential backoff (3 attempts, 1s/2s/4s delays) in `apps/aam-cli/src/aam_cli/services/git_service.py` per research R-011
- [ ] T018 Implement cache path computation (`url → ~/.aam/cache/git/{host}/{owner}/{repo}/`) in `apps/aam-cli/src/aam_cli/services/git_service.py`
- [ ] T019 [P] Write unit tests for git_service in `apps/aam-cli/tests/unit/test_unit_git_service.py` — mock subprocess, test clone (including shallow-to-full fallback), fetch, head sha, diff, retry logic, cache path computation, validate_cache (corrupted cache detection), error handling

### Scanner Extension

- [ ] T020 Extend `detection/scanner.py` in `apps/aam-cli/src/aam_cli/detection/scanner.py` — add `scan_directory()` function that accepts `root_path`, `scan_scope` (subdirectory), and `exclude_dirs` parameter; use `os.walk()` to handle dot-prefixed directories
- [ ] T021 Add vendor agent file detection heuristic to `apps/aam-cli/src/aam_cli/detection/scanner.py` — if dir has `SKILL.md` AND `agents/*.yaml`, treat vendor YAML as companion metadata; if `agents/*.yaml` without `SKILL.md`, treat as standalone agent
- [ ] T022 [P] Write unit tests for remote scanning in `apps/aam-cli/tests/unit/test_unit_scanner_remote.py` — mock directory structures: dot-prefixed dirs (`.curated/`, `.experimental/`, `.system/`), vendor agent files (`agents/openai.yaml`), exclusion rules, openai/skills layout

**Checkpoint**: Foundation ready — all models defined, URL parser working, git wrapper tested, scanner extended. User story implementation can begin.

---

## Phase 3: User Story 1 — Add a Remote Git Source and Discover Artifacts (Priority: P1) MVP

**Goal**: A user can run `aam source add openai/skills` to register a git repo, clone it, scan for artifacts, and see a summary. They can then run `aam source scan <name>` to list all discovered artifacts.

**Independent Test**: Run `aam source add` against a local bare git repo, verify source appears in config, then `aam source scan` returns correct artifact counts.

### Implementation for User Story 1

- [ ] T023 [US1] Implement `DiscoveredArtifact` (with `description` field extracted from first line of SKILL.md where available) and `ScanResult` dataclasses in `apps/aam-cli/src/aam_cli/services/source_service.py`
- [ ] T024 [US1] Implement `add_source()` in `apps/aam-cli/src/aam_cli/services/source_service.py` — parse URL, check for duplicates, call git_service.clone_shallow(), run scanner, save SourceEntry to config, return result dict
- [ ] T025 [US1] Implement `scan_source()` in `apps/aam-cli/src/aam_cli/services/source_service.py` — load source from config, resolve cache path, run scanner on cached clone with path scope, return ScanResult as dict
- [ ] T026 [US1] Create Click command group `source` and subcommands `add`, `scan` in `apps/aam-cli/src/aam_cli/commands/source.py` — Rich output formatting per contracts/cli-commands.md
- [ ] T027 [US1] Register `source` command group in `apps/aam-cli/src/aam_cli/main.py` via `cli.add_command(source.source)`
- [ ] T028 [P] [US1] Write unit tests for source_service add/scan in `apps/aam-cli/tests/unit/test_unit_source_service.py` — mock git_service and scanner, test duplicate detection, config persistence, scan with path scope, type filtering
- [ ] T029 [US1] Write integration test for source add+scan lifecycle in `apps/aam-cli/tests/integration/test_integration_source_lifecycle.py` — use local bare git repo with SKILL.md files, verify end-to-end from add to scan

**Checkpoint**: `aam source add` and `aam source scan` work end-to-end. MVP is functional.

---

## Phase 4: User Story 2 — Update Cached Sources and Detect Changes (Priority: P1)

**Goal**: A user can run `aam source update` to fetch upstream changes and see a report of new, modified, and removed artifacts.

**Independent Test**: Add a source, commit new files to the test repo, run `aam source update`, verify change report shows new/modified/removed correctly.

### Implementation for User Story 2

- [ ] T030 [US2] Implement `SourceChangeReport` dataclass in `apps/aam-cli/src/aam_cli/services/source_service.py`
- [ ] T031 [US2] Implement `update_source()` in `apps/aam-cli/src/aam_cli/services/source_service.py` — call git_service.fetch(), compare old/new commits via git diff, re-scan, produce change report; support `update_all` and `dry_run` modes; on network failure after retry exhaustion, fall back to cached scan data and display warning per FR-043
- [ ] T032 [US2] Add `update` subcommand to `apps/aam-cli/src/aam_cli/commands/source.py` — options: `--all`, `--dry-run`; Rich output showing new/modified/removed artifact summary
- [ ] T033 [P] [US2] Write unit tests for update/change detection in `apps/aam-cli/tests/unit/test_unit_source_service.py` — mock git fetch, test change report generation, --all mode, --dry-run, network failure with retry
- [ ] T034 [US2] Write integration test for update with changed files in `apps/aam-cli/tests/integration/test_integration_source_lifecycle.py` — add source, commit new SKILL.md to test repo, run update, verify change report

**Checkpoint**: Source update detects changes correctly. Combined with US1, practitioners can add sources and track upstream changes.

---

## Phase 5: User Story 3 — List Candidates and Create Packages from Remote Sources (Priority: P1)

**Goal**: A user can list all unpackaged artifact candidates across sources and create AAM packages from them with provenance metadata.

**Independent Test**: Add a source, run `aam source candidates`, verify candidates listed. Then `aam create-package --from-source` creates a package with provenance in `aam.yaml`.

### Implementation for User Story 3

- [ ] T035 [US3] Implement `list_candidates()` in `apps/aam-cli/src/aam_cli/services/source_service.py` — scan all sources + local project, filter out already-packaged artifacts, support source and type filters
- [ ] T036 [US3] Add `candidates` subcommand to `apps/aam-cli/src/aam_cli/commands/source.py` — options: `--source`, `--type` (repeatable), `--json`; Rich output grouped by source
- [ ] T037 [US3] Extend `aam create-package` in `apps/aam-cli/src/aam_cli/commands/create_package.py` — add `--from-source`, `--artifacts`, and `--all` options per FR-026; when used, read artifacts from source cache, copy to package dir, generate aam.yaml with provenance section, and compute file checksums
- [ ] T038 [P] [US3] Write unit tests for candidates and from-source packaging in `apps/aam-cli/tests/unit/test_unit_source_service.py` — mock scanner results, test candidate filtering, test provenance metadata generation
- [ ] T039 [US3] Write integration test for create-package --from-source in `apps/aam-cli/tests/integration/test_integration_source_lifecycle.py` — add source, create package from it, verify aam.yaml has provenance section with correct fields

**Checkpoint**: End-to-end discovery-to-packaging workflow complete. All P1 stories done.

---

## Phase 6: User Story 7 — Manage Source Listings (Priority: P2)

**Goal**: A user can list all configured sources in a table and remove sources they no longer need.

**Independent Test**: Add sources, run `aam source list`, verify table output. Run `aam source remove`, verify source gone and default tracking works.

### Implementation for User Story 7

- [ ] T040 [US7] Implement `list_sources()` and `remove_source()` in `apps/aam-cli/src/aam_cli/services/source_service.py` — list returns all sources with metadata; remove deletes config entry, tracks removed defaults in `removed_defaults`, optionally purges cache
- [ ] T041 [US7] Add `list` and `remove` subcommands to `apps/aam-cli/src/aam_cli/commands/source.py` — Rich table output for list with (default) tag; remove with `--purge-cache` option
- [ ] T042 [P] [US7] Write unit tests for list/remove in `apps/aam-cli/tests/unit/test_unit_source_service.py` — test list formatting, remove with default tracking, purge cache behavior, source not found error

**Checkpoint**: Full source CRUD (add, list, scan, update, remove) operational.

---

## Phase 7: User Story 4 — Verify Installed Package Integrity (Priority: P2)

**Goal**: A user can run `aam verify <package>` to check if installed files have been modified locally.

**Independent Test**: Install a package (with checksums in lock file), modify one file, run `aam verify`, verify it reports the modified file correctly.

### Implementation for User Story 4

- [ ] T043 [US4] Extend `apps/aam-cli/src/aam_cli/utils/checksum.py` — add `compute_file_checksums(directory: Path, files: list[str]) -> dict[str, str]` for computing checksums across multiple files
- [ ] T044 [US4] Implement `verify_package()` in `apps/aam-cli/src/aam_cli/services/checksum_service.py` — load lock file, read file_checksums, recompute for each file, classify as ok/modified/missing/untracked, return VerifyResult dict; support `verify_all`
- [ ] T045 [US4] Implement `VerifyResult` dataclass in `apps/aam-cli/src/aam_cli/services/checksum_service.py`
- [ ] T046 [US4] Create Click command `verify` in `apps/aam-cli/src/aam_cli/commands/verify.py` — options: `--all`; Rich output with checkmarks/crosses per file
- [ ] T047 [US4] Register `verify` command in `apps/aam-cli/src/aam_cli/main.py`
- [ ] T048 [P] [US4] Write unit tests for checksum verification in `apps/aam-cli/tests/unit/test_unit_checksum_service.py` — test ok, modified, missing, untracked detection; no checksums available case; verify_all mode
- [ ] T049 [US4] Extend `aam pack` in `apps/aam-cli/src/aam_cli/commands/pack.py` — generate per-file SHA-256 checksums during pack and include in archive metadata
- [ ] T049b [US4] Extend install flow in `apps/aam-cli/src/aam_cli/commands/install.py` — during package installation, read per-file checksums from the pack archive and write them into `file_checksums` section in `aam-lock.yaml`

**Checkpoint**: `aam verify` correctly identifies modified, missing, and untracked files.

---

## Phase 8: User Story 5 — View Differences Between Installed and Modified Files (Priority: P2)

**Goal**: A user can run `aam diff <package>` to see exactly what changed in installed files.

**Independent Test**: Modify an installed file, run `aam diff`, verify unified diff output is correct.

### Implementation for User Story 5

- [ ] T050 [US5] Implement `diff_package()` in `apps/aam-cli/src/aam_cli/services/checksum_service.py` — for each modified file, generate unified diff using Python `difflib.unified_diff()`; list untracked and missing files
- [ ] T051 [US5] Create Click command `diff` in `apps/aam-cli/src/aam_cli/commands/diff.py` — Rich syntax-highlighted diff output
- [ ] T052 [US5] Register `diff` command in `apps/aam-cli/src/aam_cli/main.py`
- [ ] T053 [P] [US5] Write unit tests for diff in `apps/aam-cli/tests/unit/test_unit_checksum_service.py` — test diff output format, no modifications case, missing original file case

**Checkpoint**: `aam diff` shows content-level changes for modified files.

---

## Phase 9: User Story 6 — Receive Warnings During Upgrade When Local Changes Exist (Priority: P2)

**Goal**: During upgrade/reinstall, AAM warns the user about local modifications and offers backup/skip/diff/force options.

**Independent Test**: Install a package, modify files, attempt upgrade, verify warning appears with correct file list and interactive options work.

### Implementation for User Story 6

- [ ] T054 [US6] Implement `BackupRecord` dataclass and `check_modifications()`, `backup_files()` in `apps/aam-cli/src/aam_cli/services/checksum_service.py` — check_modifications returns modification status; backup_files copies to `~/.aam/backups/<pkg>--<date>/`
- [ ] T055 [US6] Modify `apps/aam-cli/src/aam_cli/commands/install.py` — before overwriting during upgrade/reinstall, call check_modifications(); if changes detected, display warning with Rich and present [b]ackup/[s]kip/[d]iff/[f]orce options; respect `--force` flag
- [ ] T056 [P] [US6] Write unit tests for backup and modification check in `apps/aam-cli/tests/unit/test_unit_checksum_service.py` — test backup directory creation, file copy, modification detection during upgrade
- [ ] T057 [US6] Write integration test for upgrade with modifications in `apps/aam-cli/tests/integration/test_integration_verify_diff.py` — install package, modify file, attempt upgrade, verify warning shown and backup works

**Checkpoint**: Users are protected from silent data loss during upgrades.

---

## Phase 10: User Story 8 — MCP Tool Integration for IDE Agents (Priority: P2)

**Goal**: IDE agents can programmatically manage sources, verify packages, and create packages from remote sources via MCP tools and resources.

**Independent Test**: Start MCP server, invoke each `aam_source_*` tool via FastMCP Client, verify correct structured responses. Write tools require `--allow-write`. Resources reflect source state changes.

**NOTE**: This phase depends on spec 002 MCP infrastructure (server factory, `mcp/` module, service layer pattern, error handling convention). If spec 002 is not yet implemented, defer this phase.

### Error Handling Convention (aligned with spec 002)

All MCP tools in this phase follow the error handling convention established in spec 002:
- **Expected domain outcomes**: Return the tool's documented output shape (e.g., `ScanResult` dict, `VerifyResult` dict with `has_checksums=false`).
- **Tool failures (unexpected/unrecoverable)**: Raise MCP tool error (`CallToolResult.isError == true`) with safe message prefixed by error code in brackets.

**New error codes** (extend spec 002 set):

| Error Code | Condition |
|---|---|
| `AAM_SOURCE_NOT_FOUND` | Named source not in config |
| `AAM_SOURCE_ALREADY_EXISTS` | Duplicate source name on add |
| `AAM_SOURCE_URL_INVALID` | URL failed scheme allowlist validation |
| `AAM_GIT_CLONE_FAILED` | Git clone operation failed after retries |
| `AAM_GIT_FETCH_FAILED` | Git fetch operation failed after retries |
| `AAM_NETWORK_ERROR` | Network unreachable after all retries exhausted |
| `AAM_CACHE_CORRUPTED` | Cached clone directory is corrupted |
| `AAM_CHECKSUMS_NOT_AVAILABLE` | No `file_checksums` in lock file for requested package |

### Implementation

- [ ] T058 [P] [US8] Implement 6 read-only MCP tools in `apps/aam-cli/src/aam_cli/mcp/tools_read.py` — add to existing file (from spec 002), each with `@mcp.tool(tags={"read"})`, Google-style docstrings with Args/Returns, error handling per convention above:
  1. `aam_source_list() -> list[dict]` → `source_service.list_sources()`
  2. `aam_source_scan(source_name: str, artifact_type: str | None = None) -> dict` → `source_service.scan_source()`; raise `[AAM_SOURCE_NOT_FOUND]` if source missing
  3. `aam_source_candidates(source_name: str | None = None, artifact_type: str | None = None) -> list[dict]` → `source_service.list_candidates()`
  4. `aam_source_diff(source_name: str) -> dict` → `source_service.update_source(source_name, dry_run=True)`; raise `[AAM_SOURCE_NOT_FOUND]` if missing
  5. `aam_verify(package_name: str | None = None, verify_all: bool = False) -> dict` → `checksum_service.verify_package()`; raise `[AAM_PACKAGE_NOT_INSTALLED]` if missing; return `has_checksums=false` if no checksums
  6. `aam_diff(package_name: str) -> dict` → `checksum_service.diff_package()`; raise `[AAM_PACKAGE_NOT_INSTALLED]` if missing

- [ ] T059 [P] [US8] Implement 3 write MCP tools in `apps/aam-cli/src/aam_cli/mcp/tools_write.py` — add to existing file (from spec 002), each with `@mcp.tool(tags={"write"})`, Google-style docstrings, error handling per convention:
  1. `aam_source_add(source: str, ref: str = "main", path: str | None = None, name: str | None = None) -> dict` → `source_service.add_source()`; raise `[AAM_SOURCE_ALREADY_EXISTS]` on duplicate, `[AAM_GIT_CLONE_FAILED]` on clone failure, `[AAM_SOURCE_URL_INVALID]` on bad URL
  2. `aam_source_remove(source_name: str, purge_cache: bool = False) -> dict` → `source_service.remove_source()`; raise `[AAM_SOURCE_NOT_FOUND]` if missing
  3. `aam_source_update(source_name: str | None = None, update_all: bool = False) -> dict` → `source_service.update_source()`; raise `[AAM_SOURCE_NOT_FOUND]` if named source missing

- [ ] T059b [US8] Extend `aam_create_package` write tool in `apps/aam-cli/src/aam_cli/mcp/tools_write.py` — add optional parameters `from_source: str | None = None` and `artifacts: list[str] | None = None` to existing `aam_create_package` tool (from spec 002); when `from_source` is provided, delegate to `source_service.scan_source()` for artifact retrieval, copy from cache, and include provenance metadata in result

- [ ] T060 [P] [US8] Implement 3 MCP resources in `apps/aam-cli/src/aam_cli/mcp/resources.py` — add to existing file (from spec 002), each with `@mcp.resource` decorator, fresh filesystem read per request:
  1. `aam://sources` → `source_service.list_sources()`, returns all sources with status
  2. `aam://sources/{name}` → source entry details + cached artifact list via `source_service.scan_source(name)`; return error dict if source not found
  3. `aam://sources/{name}/candidates` → `source_service.list_candidates(source_name=name)`, returns unpackaged candidates

### Server Registration & Safety Model

- [ ] T061 [US8] Register new tools and resources with MCP server — verify `apps/aam-cli/src/aam_cli/mcp/server.py` imports pick up new tools/resources from updated `tools_read.py`, `tools_write.py`, `resources.py`; verify updated tool counts: read-only mode shows 13 tools (7 spec-002 + 6 new read), full-access mode shows 22 tools (13 spec-002 + 6 new read + 3 new write; `aam_create_package` extension adds parameters, not a new tool), resource count: 8 (5 spec-002 + 3 new)

- [ ] T061b [US8] Verify safety model for new source tools — write verification test:
  1. Server without `--allow-write` → new read tools (`aam_source_list`, `aam_source_scan`, `aam_source_candidates`, `aam_source_diff`, `aam_verify`, `aam_diff`) are visible; new write tools (`aam_source_add`, `aam_source_remove`, `aam_source_update`) are hidden
  2. Server with `--allow-write` → all new tools visible
  3. Verify tool names, parameter schemas, and descriptions match contracts/mcp-tools.md

### Unit Tests (Mocked Services)

- [ ] T061c [P] [US8] Write unit tests for read MCP source tools in `apps/aam-cli/tests/unit/test_unit_mcp_source_tools_read.py` — mock source_service and checksum_service, use FastMCP in-memory `Client(transport=mcp_server)`:
  1. `test_unit_aam_source_list_returns_sources` — mock list_sources, verify list
  2. `test_unit_aam_source_list_empty` — verify empty list returned (not error)
  3. `test_unit_aam_source_scan_success` — mock scan_source, verify dict structure
  4. `test_unit_aam_source_scan_not_found` — verify `[AAM_SOURCE_NOT_FOUND]` error (`CallToolResult.isError == true`)
  5. `test_unit_aam_source_candidates_all` — mock list_candidates, verify list
  6. `test_unit_aam_source_candidates_filtered` — verify source_name + artifact_type filters work
  7. `test_unit_aam_source_diff_success` — mock update_source(dry_run=True), verify change report
  8. `test_unit_aam_source_diff_not_found` — verify error
  9. `test_unit_aam_verify_success` — mock verify_package, verify dict
  10. `test_unit_aam_verify_no_checksums` — verify `has_checksums=false` returned as domain outcome (not error)
  11. `test_unit_aam_verify_not_installed` — verify `[AAM_PACKAGE_NOT_INSTALLED]` error
  12. `test_unit_aam_diff_success` — mock diff_package, verify diff output
  13. `test_unit_aam_diff_not_installed` — verify error

- [ ] T061d [P] [US8] Write unit tests for write MCP source tools in `apps/aam-cli/tests/unit/test_unit_mcp_source_tools_write.py` — mock source_service:
  1. `test_unit_aam_source_add_success` — verify result with artifact count
  2. `test_unit_aam_source_add_duplicate` — verify `[AAM_SOURCE_ALREADY_EXISTS]` error
  3. `test_unit_aam_source_add_invalid_url` — verify `[AAM_SOURCE_URL_INVALID]` error
  4. `test_unit_aam_source_add_clone_failed` — verify `[AAM_GIT_CLONE_FAILED]` error
  5. `test_unit_aam_source_remove_success` — verify removal dict
  6. `test_unit_aam_source_remove_not_found` — verify `[AAM_SOURCE_NOT_FOUND]` error
  7. `test_unit_aam_source_update_success` — verify update result
  8. `test_unit_aam_source_update_all` — verify all sources updated
  9. `test_unit_aam_source_update_not_found` — verify error
  10. `test_unit_write_tools_hidden_in_read_only` — verify new write tools not listed when `allow_write=False`
  11. `test_unit_aam_create_package_from_source` — verify `from_source` + `artifacts` parameters work

- [ ] T061e [P] [US8] Write unit tests for MCP source resources in `apps/aam-cli/tests/unit/test_unit_mcp_source_resources.py` — mock source_service:
  1. `test_unit_resource_sources_list` — verify list returned
  2. `test_unit_resource_sources_empty` — verify empty list (not error)
  3. `test_unit_resource_source_detail` — verify source entry + artifacts returned
  4. `test_unit_resource_source_not_found` — verify null/error dict response
  5. `test_unit_resource_source_candidates` — verify candidates list
  6. `test_unit_resource_source_candidates_empty` — verify empty list

### Integration Tests (Real Local Git Repo)

- [ ] T061f [US8] Write integration test for source MCP tools in `apps/aam-cli/tests/integration/test_integration_mcp_source.py` — use local bare git repo with SKILL.md fixtures, FastMCP in-memory Client:
  1. `test_integration_source_add_via_mcp` — add local git source, verify config updated
  2. `test_integration_source_scan_via_mcp` — scan added source, verify artifacts found
  3. `test_integration_source_candidates_via_mcp` — list candidates after scan
  4. `test_integration_source_update_via_mcp` — commit new SKILL.md to test repo, update source, verify change report shows new artifact
  5. `test_integration_source_remove_via_mcp` — remove source, verify config cleared
  6. `test_integration_resources_reflect_source_state` — add source, read `aam://sources` resource, verify listed; read `aam://sources/{name}`, verify detail; remove source, verify `aam://sources` no longer lists it
  7. `test_integration_safety_model_blocks_source_writes` — read-only server, attempt `aam_source_add`, verify tool not found or rejected
  8. `test_integration_verify_via_mcp` — install package with checksums, modify file, call `aam_verify`, verify modified file reported

**Checkpoint**: All MCP tools and resources operational, with error handling aligned to spec 002 conventions. IDE agents can discover, manage sources, verify packages, and create packages from remote sources.

---

## Phase 11: User Story 9 — Default Sources on Initialization (Priority: P3)

**Goal**: `aam init` automatically registers community default sources so new users can discover popular skills immediately.

**Independent Test**: Run `aam init` with fresh config, verify default sources appear. Remove one, re-init, verify it's not re-added.

### Implementation for User Story 9

- [ ] T062 [US9] Define `DEFAULT_SOURCES` constant list in `apps/aam-cli/src/aam_cli/services/source_service.py` — `github/awesome-copilot` (url: github.com/github/awesome-copilot, path: skills) and `openai/skills:.curated` (url: github.com/openai/skills, path: skills/.curated) per reference doc Section 4.1.5
- [ ] T063 [US9] Implement `register_default_sources()` in `apps/aam-cli/src/aam_cli/services/source_service.py` — check if `sources:` key exists in config; if not, add defaults with `default: true`; skip names in `removed_defaults`
- [ ] T064 [US9] Modify `aam init` in `apps/aam-cli/src/aam_cli/commands/init_package.py` (or equivalent init command) — call `register_default_sources()` after config initialization
- [ ] T065 [P] [US9] Write integration test for default sources lifecycle in `apps/aam-cli/tests/integration/test_integration_default_sources.py` — init → verify defaults → remove one → verify removed_defaults updated → re-init → verify removed not re-added

**Checkpoint**: New users get curated default sources out of the box.

---

## Phase 12: User Documentation

**Purpose**: Update all user-facing documentation to cover new commands, schemas, and workflows

- [ ] T066 [P] Update `docs/USER_GUIDE.md` — add "Remote Git Sources" section covering: `aam source add/list/remove/scan/update/candidates` with examples, `aam verify` and `aam diff` usage, upgrade warning behavior, default sources
- [ ] T067 [P] Update `docs/DESIGN.md` — add `aam source` command group to Section 5.1 CLI Overview, add `sources:` config schema to Section 9.1, add `file_checksums` lock file extension to Section 7.3, add `~/.aam/cache/git/` to Section 10.1, add `~/.aam/backups/` to Section 10.1, add MCP tools/resources to Section 5.3
- [ ] T068 [P] Update `docs/HTTP_REGISTRY_SPEC.md` if needed — add provenance metadata schema to package manifest spec
- [ ] T069 [P] Create `docs/user_docs/git-sources.md` — dedicated deep-dive page for git source scanning: URL formats, naming conventions, scan patterns, dot-prefixed directory handling, vendor agent mapping, cache structure
- [ ] T070 Review all new CLI commands for consistent `--help` text in `apps/aam-cli/src/aam_cli/commands/source.py`, `verify.py`, `diff.py` — ensure help strings match docs/USER_GUIDE.md
- [ ] T070b [P] Update `docs/USER_GUIDE.md` MCP section (from spec 002 T044) — add 6 new read tools (`aam_source_list`, `aam_source_scan`, `aam_source_candidates`, `aam_source_diff`, `aam_verify`, `aam_diff`), 3 new write tools (`aam_source_add`, `aam_source_remove`, `aam_source_update`), extended `aam_create_package` with `from_source`, 3 new resources (`aam://sources`, `aam://sources/{name}`, `aam://sources/{name}/candidates`) to existing MCP tools/resources tables; add error codes table for source operations

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Final quality pass, coverage check, and quickstart validation

- [ ] T071 Run full test suite and verify 80%+ coverage across all new modules via `npx nx test aam-cli -- --cov --cov-report=term-missing`
- [ ] T072 Run Ruff lint + format check on all new and modified files: `ruff check apps/aam-cli/src/ apps/aam-cli/tests/` and `ruff format --check apps/aam-cli/src/ apps/aam-cli/tests/`
- [ ] T073 Run MyPy type check on new modules: `mypy apps/aam-cli/src/aam_cli/services/ apps/aam-cli/src/aam_cli/utils/git_url.py`
- [ ] T074 Validate quickstart.md end-to-end — follow developer quickstart instructions, verify local test source setup works
- [ ] T075 Final review: verify all 80-char section headers, Google docstrings, module-level loggers, type hints on every function signature across all new files

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ─────────────────────────────────────────────────▶ No deps
Phase 2: Foundational ──────────────────────────────────────────▶ Depends on Phase 1
Phase 3: US1 (Add + Scan) ─────────────────────────────────────▶ Depends on Phase 2
Phase 4: US2 (Update + Changes) ────────────────────────────────▶ Depends on Phase 3
Phase 5: US3 (Candidates + Package) ────────────────────────────▶ Depends on Phase 3
Phase 6: US7 (List + Remove) ───────────────────────────────────▶ Depends on Phase 2
Phase 7: US4 (Verify Checksums) ────────────────────────────────▶ Depends on Phase 2
Phase 8: US5 (Diff) ────────────────────────────────────────────▶ Depends on Phase 7
Phase 9: US6 (Upgrade Warning) ─────────────────────────────────▶ Depends on Phase 7
Phase 10: US8 (MCP Tools) ──────────────────────────────────────▶ Depends on Phases 3-9 + spec 002
Phase 11: US9 (Default Sources) ────────────────────────────────▶ Depends on Phase 3
Phase 12: User Documentation ───────────────────────────────────▶ Depends on Phases 3-11
Phase 13: Polish ───────────────────────────────────────────────▶ Depends on all phases
```

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only. **No dependencies on other stories.**
- **US2 (P1)**: Depends on US1 (needs a source to update). Sequenced after US1.
- **US3 (P1)**: Depends on US1 (needs scan results). Can run parallel with US2.
- **US7 (P2)**: Depends on Foundational only. **Can run parallel with US1.**
- **US4 (P2)**: Depends on Foundational only. **Can run parallel with US1, US7.**
- **US5 (P2)**: Depends on US4 (needs checksum infrastructure).
- **US6 (P2)**: Depends on US4 (needs modification detection).
- **US8 (P2)**: Depends on all services being complete + spec 002 MCP infra.
- **US9 (P3)**: Depends on US1 (needs source config infrastructure).

### Parallel Opportunities

After Phase 2 (Foundational) completes, these can run simultaneously:

```
 ┌─── Phase 3: US1 (Add + Scan) ────▶ Phase 4: US2 (Update)
 │                                   ────▶ Phase 5: US3 (Candidates)
 │                                   ────▶ Phase 11: US9 (Defaults)
Phase 2 ─┤
 │    ┌── Phase 6: US7 (List + Remove)
 │    │
 │    └── Phase 7: US4 (Verify) ─────▶ Phase 8: US5 (Diff)
 │                                    ────▶ Phase 9: US6 (Upgrade Warning)
 └────────────────────────────────────────▶ Phase 10: US8 (MCP) [after all services]
```

---

## Parallel Example: Phase 2 (Foundational)

```bash
# These can run in parallel (different files):
Task T007: "GitSourceURL in utils/git_url.py"
Task T012: "FileChecksums in core/workspace.py"
Task T014: "Provenance in core/manifest.py"

# These can run in parallel (different test files):
Task T009: "URL parsing tests in test_unit_git_url.py"
Task T019: "git_service tests in test_unit_git_service.py"
Task T022: "scanner remote tests in test_unit_scanner_remote.py"
```

## Parallel Example: After Foundational

```bash
# US1 and US4 can run in parallel (different services, different commands):
Task T024: "source_service.add_source() in services/source_service.py"
Task T044: "checksum_service.verify_package() in services/checksum_service.py"

# US7 can also run in parallel:
Task T040: "list_sources/remove_source in services/source_service.py"
```

---

## Implementation Strategy

### MVP First (US1 Only — Phases 1-3)

1. Complete Phase 1: Setup (6 tasks)
2. Complete Phase 2: Foundational (16 tasks)
3. Complete Phase 3: US1 — Add + Scan (7 tasks)
4. **STOP and VALIDATE**: `aam source add` and `aam source scan` work end-to-end
5. **29 tasks** delivers a usable MVP with discovery capability

### Core Workflow (US1 + US2 + US3 — Phases 1-5)

6. Complete Phase 4: US2 — Update (5 tasks)
7. Complete Phase 5: US3 — Candidates + Package (5 tasks)
8. **STOP and VALIDATE**: Full discovery-to-packaging workflow operational
9. **39 tasks** delivers the complete P1 workflow

### Full Feature (All Stories — Phases 1-13)

10. Complete Phases 6-9: US7, US4, US5, US6 (many can be parallel)
11. Complete Phase 10: US8 — MCP Tools (if spec 002 ready)
12. Complete Phase 11: US9 — Default Sources
13. Complete Phase 12: User Documentation
14. Complete Phase 13: Polish
15. **83 tasks** delivers the complete feature

### Suggested Execution Order (Single Developer)

1. **Phases 1-2**: Setup + Foundational (22 tasks)
2. **Phases 3-5**: P1 stories in order: US1 → US2 → US3 (17 tasks)
3. **Phase 6**: US7 — Source list/remove (3 tasks)
4. **Phases 7-9**: P2 integrity stories: US4 → US5 → US6 (11 tasks)
5. **Phase 10**: US8 — MCP tools (10 tasks, if spec 002 ready)
6. **Phase 11**: US9 — Default sources (4 tasks)
7. **Phases 12-13**: Docs + Polish (11 tasks)

---

## Task Summary

| Phase | Story | Tasks | Parallel | Purpose |
|-------|-------|-------|----------|---------|
| 1 | Setup | 6 | 5 | Module stubs, test fixtures |
| 2 | Foundational | 16 | 6 | Models, URL parser, git wrapper, scanner |
| 3 | US1 (P1) | 7 | 1 | Source add + scan |
| 4 | US2 (P1) | 5 | 1 | Source update + changes |
| 5 | US3 (P1) | 5 | 1 | Candidates + package from source |
| 6 | US7 (P2) | 3 | 1 | Source list + remove |
| 7 | US4 (P2) | 8 | 1 | Verify checksums |
| 8 | US5 (P2) | 4 | 1 | Diff command |
| 9 | US6 (P2) | 4 | 1 | Upgrade warnings |
| 10 | US8 (P2) | 10 | 6 | MCP tools, resources, tests (spec 002 aligned) |
| 11 | US9 (P3) | 4 | 1 | Default sources |
| 12 | Docs | 6 | 5 | User documentation |
| 13 | Polish | 5 | 0 | Quality, coverage, validation |
| **Total** | | **83** | **30** | |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after its checkpoint
- The key reference document `docs/work/git_repo_skills.md` contains implementation-level detail (regex, YAML schemas, CLI output examples) for every task
- MCP tasks (Phase 10) are deferrable if spec 002 hasn't landed
- MCP tools follow spec 002 error handling convention: error codes in brackets `[AAM_*]`, structured error messages, `CallToolResult.isError` for failures
- MCP tools are thin wrappers delegating to service layer; no business logic in tool functions
- FastMCP in-memory `Client(transport=mcp_server)` is the primary test harness for MCP unit tests (matches spec 002 pattern)
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
