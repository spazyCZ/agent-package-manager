# Tasks: CLI Local Repository

**Input**: Design documents from `/specs/001-cli-local-repository/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/cli-commands.md
**Scope**: Local registries only — remote/HTTP registries are out of scope.

**Tests**: Not explicitly requested in spec — test tasks are **excluded**. Tests should be written alongside implementation per the quickstart.md guidance.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All paths are relative to `apps/aam-cli/` within the monorepo.

## Phase → User Story Mapping

| Phase | User Story | Priority | Title |
|-------|-----------|----------|-------|
| Phase 1 | — | — | Setup (Shared Infrastructure) |
| Phase 2 | — | — | Foundational (Blocking Prerequisites) |
| Phase 3 | US1 | P1 | Initialize a Local Registry |
| Phase 4 | US2 | P1 | Create and Validate a Package from Existing Project |
| Phase 5 | US4 | P1 | Pack and Publish to Local Registry |
| Phase 6 | US6 | P1 | Install a Package from Local Registry |
| Phase 7 | US3 | P2 | Create a New Package from Scratch |
| Phase 8 | US5 | P2 | Search the Local Registry |
| Phase 9 | US7 | P2 | List and Inspect Installed Packages |
| Phase 10 | US8 | P2 | Configure Default Platform and Settings |
| Phase 11 | US9 | P3 | Uninstall a Package |
| Phase 12 | — | — | Polish & Cross-Cutting Concerns |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency installation, and base directory structure.

- [x] T001 Add `pyyaml>=6.0.0` dependency to `apps/aam-cli/pyproject.toml`
- [x] T002 Create package directory structure: `src/aam_cli/core/__init__.py`, `src/aam_cli/registry/__init__.py`, `src/aam_cli/adapters/__init__.py`, `src/aam_cli/detection/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
- [x] T003 [P] Create `src/aam_cli/utils/yaml_utils.py` — safe YAML load/dump wrappers using `yaml.safe_load()` / `yaml.safe_dump()` with `FileNotFoundError` and `yaml.YAMLError` handling per R-001
- [x] T004 [P] Create `src/aam_cli/utils/checksum.py` — `calculate_sha256(file_path)` and `verify_sha256(file_path, expected)` functions per R-002
- [x] T005 [P] Create `src/aam_cli/utils/paths.py` — path resolution helpers for `~/.aam/`, `.aam/`, platform directories, and `file://` URL parsing
- [x] T006 [P] Create `src/aam_cli/utils/archive.py` — `create_archive(source_dir, output_path, manifest)` and `extract_archive(archive_path, dest_dir)` with 50 MB size limit enforcement (FR-012), no symlinks outside package dir, no absolute paths per R-002

**Checkpoint**: Utility layer (Layer 0) complete. All foundation helpers available for core modules.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain models and infrastructure that ALL user stories depend on. These are Layer 1–4 modules from the dependency graph, plus command registration in `main.py`.

**CRITICAL**: No user story work can begin until this phase is complete.

### Layer 1: Core Models

- [x] T007 Create `src/aam_cli/core/version.py` — semver constraint parsing and matching using `packaging.version.Version` with custom `^` (caret) and `~` (tilde) operators per R-003
- [x] T008 Create `src/aam_cli/core/manifest.py` — Pydantic models `ArtifactRef`, `QualityTest`, `EvalMetric`, `QualityEval`, `QualityConfig`, `PlatformConfig`, `ArtifactsDeclaration`, `PackageManifest`, `AgentDefinition` with all validation rules from data-model.md Sections 1 and 5. Use Pydantic v2 standard validation (not `ConfigDict(strict=True)`) — the schema validation rules in data-model.md (regex patterns, max lengths, non-empty checks) provide sufficient strictness via field validators
- [x] T009 Create `src/aam_cli/core/config.py` — Pydantic models `RegistrySource`, `SecurityConfig`, `AuthorConfig`, `PublishConfig`, `AamConfig` plus `load_config()` with 4-level precedence: CLI flags > project `.aam/config.yaml` > global `~/.aam/config.yaml` > defaults per plan Key Decision 6 and FR-027
- [x] T010 Create `src/aam_cli/core/workspace.py` — `.aam/` directory management: `ensure_workspace()`, `get_workspace_path()`, `read_lock_file()`, `write_lock_file()`, `get_installed_packages()` with `LockFile` and `LockedPackage` models from data-model.md Section 4

### Layer 2: Interfaces and Detection

- [x] T011 [P] Create `src/aam_cli/registry/base.py` — `Registry` Protocol with methods: `search()`, `get_metadata()`, `get_versions()`, `download()`, `publish()` per contracts Section 8
- [x] T012 [P] Create `src/aam_cli/adapters/base.py` — `PlatformAdapter` Protocol with methods: `deploy_skill()`, `deploy_agent()`, `deploy_prompt()`, `deploy_instruction()`, `undeploy()`, `list_deployed()` per contracts Section 9
- [x] T013 [P] Create `src/aam_cli/detection/scanner.py` — `DetectedArtifact` model and `scan_project(root: Path) -> list[DetectedArtifact]` with all detection patterns from R-009 (skills, agents, prompts, instructions across Cursor, Codex, Copilot, Claude conventions)

### Layer 3: Implementations

- [x] T014 Create `src/aam_cli/registry/local.py` — `LocalRegistry` class implementing `Registry` Protocol using filesystem + YAML: `search()` reads `index.yaml` with case-insensitive substring matching per R-004, `get_metadata()` reads `packages/<name>/metadata.yaml`, `download()` copies `.aam` from `versions/`, `publish()` copies `.aam` + updates `metadata.yaml` + rebuilds `index.yaml`
- [x] T015 [P] Create `src/aam_cli/registry/factory.py` — `create_registry(source: RegistrySource) -> Registry` factory function that returns `LocalRegistry` for `type="local"` (raises error for unsupported types)
- [x] T016 [P] Create `src/aam_cli/adapters/cursor.py` — `CursorAdapter` implementing `PlatformAdapter`: skills → `.cursor/skills/<fs-name>/`, agents → `.cursor/rules/agent-<fs-name>.mdc` (YAML frontmatter + markdown, using `AgentDefinition` from `core/manifest.py` to read `agent.yaml` and `system-prompt.md` per R-008), prompts → `.cursor/prompts/<fs-name>.md`, instructions → `.cursor/rules/<fs-name>.mdc` per plan Key Decision 5

### Layer 4: Orchestration

- [x] T017 Create `src/aam_cli/core/resolver.py` — `resolve_dependencies(root_packages, registries) -> list[ResolvedPackage]` using greedy BFS algorithm per plan Key Decision 4: look up best version, check resolved map, raise on conflicts, no backtracking
- [x] T018 Create `src/aam_cli/core/installer.py` — `install_package(resolved_packages, workspace, adapter, config)` orchestrator: download archives, verify checksums, extract to `.aam/packages/`, deploy via adapter, write lock file

### Command Registration

- [x] T019 Update `src/aam_cli/main.py` — register new commands: `init_package`, `validate`, `pack`, `list_packages`, `show_package`, `uninstall`; remove inline `info`, `show`, and `list` commands. Import stubs/placeholders so the CLI entrypoint is wired up before individual command implementations.

**Checkpoint**: Foundation ready — all core modules, protocols, implementations, orchestrators, and command registration are in place. User story command implementation can begin.

---

## Phase 3: User Story 1 — Initialize a Local Registry (Priority: P1) MVP

**Goal**: A practitioner can create a local file-based registry and configure it as default. This is the absolute prerequisite for all other local workflows.

**Independent Test**: Run `aam registry init ~/test-reg`, then `aam registry add local file:///home/user/test-reg --default`, then `aam registry list` — verify directory structure, config file, and list output.

### Implementation for User Story 1

- [x] T020 [US1] Update `src/aam_cli/commands/registry.py` — implement `aam registry init <path> [--default] [--force]`: create directory with `registry.yaml`, empty `index.yaml`, empty `packages/` dir; handle existing registry (error unless `--force`); optionally register as default via config module per contracts Section 1
- [x] T021 [US1] Update `src/aam_cli/commands/registry.py` — implement `aam registry add <name> <url> [--default]`: validate URL, save to global config via `core/config.py`, handle duplicate name errors per contracts Section 1
- [x] T022 [US1] Update `src/aam_cli/commands/registry.py` — implement `aam registry list`: read config, display table of registries with Rich table formatting per contracts Section 1
- [x] T023 [US1] Update `src/aam_cli/commands/registry.py` — implement `aam registry remove <name>`: remove from config, handle not-found error per contracts Section 1

**Checkpoint**: User Story 1 complete. Local registry can be created, registered, listed, and removed.

---

## Phase 4: User Story 2 — Create and Validate a Package from Existing Project (Priority: P1)

**Goal**: A practitioner can scan an existing project for artifacts, interactively select them, and generate a valid `aam.yaml` manifest. They can also validate the package.

**Independent Test**: Create a project with artifacts in `.cursor/skills/`, `.cursor/rules/`, `.cursor/prompts/`, run `aam create-package`, select artifacts, verify `aam.yaml` and directory structure. Run `aam validate` to confirm validity.

### Implementation for User Story 2

- [x] T024 [P] [US2] Update `src/aam_cli/commands/create_package.py` — implement artifact detection and interactive selection: use `detection/scanner.py` to find artifacts, display Rich numbered table grouped by type, implement toggle selection UI (space-separated numbers, 'a' for all, enter to confirm), handle `--all` and `--type` filter options per contracts Section 2
- [x] T025 [P] [US2] Create `src/aam_cli/commands/validate.py` — implement `aam validate [path]`: load and validate `aam.yaml` against Pydantic schema, check all artifact paths exist, report per-field results with Rich formatting per contracts Section 2
- [x] T026 [US2] Update `src/aam_cli/commands/create_package.py` — implement file organization and manifest generation: handle `--organize` (copy/reference/move), `--include`/`--include-as`, `--name`, `--scope`, `--version`, `--description`, `--author`, `--dry-run`, `--output-dir`, `--yes` options; copy/reference/move files into AAM directory structure; generate `aam.yaml` using `core/manifest.py` per contracts Section 2. Depends on T024 for detection/selection logic.

**Checkpoint**: User Story 2 complete. Packages can be created from existing projects and validated.

---

## Phase 5: User Story 4 — Pack and Publish to Local Registry (Priority: P1)

**Goal**: A practitioner can build a `.aam` archive from a valid package and publish it to a local registry.

**Independent Test**: In a package directory, run `aam pack` → verify `.aam` file created with correct contents and checksum. Then `aam publish --registry local` → verify archive in registry's `packages/` dir with correct `metadata.yaml` and `index.yaml`.

**Note**: User Story 4 is implemented before User Story 3 because pack/publish is P1 and completes the core authoring-to-publishing pipeline needed by User Story 6.

### Implementation for User Story 4

- [x] T027 [P] [US4] Create `src/aam_cli/commands/pack.py` — implement `aam pack [path]`: run validation logic first (fail with clear error if invalid per FR-010), build `.aam` archive using `utils/archive.py`, enforce 50 MB limit (FR-012, fail with size error if exceeded), report size and SHA-256 checksum per contracts Section 2
- [x] T028 [P] [US4] Update `src/aam_cli/commands/publish.py` — implement `aam publish [--registry <name>] [--tag <tag>] [--dry-run]`: find `.aam` file, verify checksum, use `registry/factory.py` to get registry, call `registry.publish()`, handle duplicate version errors (FR-014) per contracts Section 3

**Checkpoint**: User Story 4 complete. Full author pipeline works: create → validate → pack → publish.

---

## Phase 6: User Story 6 — Install a Package from Local Registry (Priority: P1) MVP

**Goal**: A practitioner can install a package from a local registry, resolve dependencies, and have artifacts deployed to the Cursor platform.

**Independent Test**: Publish a package to local registry, then in a different directory run `aam install <package>` → verify `.aam/packages/` extraction, `.aam/aam-lock.yaml` creation, and `.cursor/` deployment.

### Implementation for User Story 6

Covers FR-016 (install command), FR-017 (multi source types), FR-018 (version specifiers), FR-019 (dep resolution), FR-020 (lock file), FR-021 (--no-deploy).

- [x] T029 [US6] Update `src/aam_cli/commands/install.py` — implement package spec parsing and resolution: parse package spec (name, `name@ver`, `@scope/name`, `@scope/name@ver`), load config, get registries via `registry/factory.py`, resolve via `core/resolver.py` per contracts Section 5
- [x] T030 [US6] Update `src/aam_cli/commands/install.py` — implement download, extraction, and deployment: call `core/installer.py` to download archives, verify checksums, extract to `.aam/packages/`, deploy via adapter; handle `--platform`, `--no-deploy`, `--force`, `--dry-run`; support local directory path (`./path/`) and `.aam` archive file source types (FR-017) per contracts Section 5

**Checkpoint**: User Story 6 complete. The core consumer workflow (install + deploy) is functional. Combined with US1, US2, US4 — the entire local-first pipeline from authoring to consumption works end-to-end.

---

## Phase 7: User Story 3 — Create a New Package from Scratch (Priority: P2)

**Goal**: A practitioner can scaffold a brand-new AAM package interactively using `aam init`.

**Independent Test**: Run `aam init my-pkg` in an empty directory, answer prompts → verify `aam.yaml` and artifact directories are created.

### Implementation for User Story 3

- [x] T031 [US3] Create `src/aam_cli/commands/init_package.py` — implement `aam init [name]`: interactive prompts for name, version, description, author, license, artifact types, platforms using Rich; generate `aam.yaml` and scaffold selected artifact directories per contracts Section 2

**Checkpoint**: User Story 3 complete. New packages can be created from scratch.

---

## Phase 8: User Story 5 — Search the Local Registry (Priority: P2)

**Goal**: A practitioner can discover packages in configured registries via keyword search.

**Independent Test**: Publish packages, then run `aam search "keyword"` → verify matching results displayed in Rich table.

### Implementation for User Story 5

- [x] T032 [US5] Update `src/aam_cli/commands/search.py` — implement `aam search <query> [--limit N] [--type TYPE] [--json]`: iterate configured registries, call `registry.search()` (case-insensitive substring matching per R-004), aggregate results, display Rich table per contracts Section 4

**Checkpoint**: User Story 5 complete. Packages are discoverable via search.

---

## Phase 9: User Story 7 — List and Inspect Installed Packages (Priority: P2)

**Goal**: A practitioner can see what packages are installed and get details about a specific package.

**Independent Test**: Install packages, then run `aam list` and `aam info <name>` → verify correct table/detail output.

### Implementation for User Story 7

- [x] T033 [P] [US7] Create `src/aam_cli/commands/list_packages.py` — implement `aam list [--tree]`: read lock file and `.aam/packages/`, display Rich table (flat) or tree view per contracts Section 6
- [x] T034 [P] [US7] Create `src/aam_cli/commands/show_package.py` — implement `aam info <package>`: read installed package manifest, display full metadata with Rich formatting per contracts Section 6

**Checkpoint**: User Story 7 complete. Installed packages can be listed and inspected.

---

## Phase 10: User Story 8 — Configure Default Platform and Settings (Priority: P2)

**Goal**: A practitioner can manage AAM configuration via CLI commands.

**Independent Test**: Run `aam config set default_platform cursor`, `aam config get default_platform`, `aam config list` → verify values are persisted and displayed.

### Implementation for User Story 8

- [x] T035 [US8] Update `src/aam_cli/commands/config.py` — implement `aam config set <key> <value>`, `aam config get <key>`, `aam config list`: read/write global config via `core/config.py`, display with source indication (global/project/default) per contracts Section 7

**Checkpoint**: User Story 8 complete. Configuration is fully manageable via CLI.

---

## Phase 11: User Story 9 — Uninstall a Package (Priority: P3)

**Goal**: A practitioner can remove an installed package and its deployed artifacts.

**Independent Test**: Install a package, then run `aam uninstall <name>` → verify `.aam/packages/` entry and `.cursor/` artifacts are removed, lock file updated.

### Implementation for User Story 9

- [x] T036 [US9] Create `src/aam_cli/commands/uninstall.py` — implement `aam uninstall <package>`: read lock file, check for dependents (warn with confirmation), remove from `.aam/packages/`, call adapter `undeploy()` for each artifact, update lock file per contracts Section 6

**Checkpoint**: User Story 9 complete. Full lifecycle management (install + uninstall) works.

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [x] T037 [P] Update `apps/aam-cli/tests/test_main.py` — update existing tests for new command registrations and removed inline commands
- [x] T038 [P] Review all commands for consistent error messaging and actionable suggestions per FR-029. Verify the following edge cases from spec.md are handled:
  - `aam install` with no registries configured → clear error with instructions
  - Local registry directory not writable → permission error with helpful message
  - Corrupted package archive → checksum verification catches and reports
  - Conflicting dependency versions → both constraints shown in error
  - `aam.yaml` references non-existent artifact paths → `aam validate` reports each
  - Authoring commands run without `aam.yaml` → "No aam.yaml found" with suggestion
  - `~/.aam/` directory doesn't exist → auto-created on first use
- [x] T039 [P] Verify scoped/unscoped naming works correctly across all commands (FR-023, FR-032): test that `@scope/name` and `name` are accepted everywhere, and `@scope/name` → `scope--name` filesystem conversion is consistent via `utils/naming.py`
- [x] T040 [P] Verify `~/.aam/` and `.aam/` auto-creation on first use across all commands per FR-030
- [x] T041 [P] Update `docs/USER_GUIDE.md` — update the local workflow sections with working examples that match the implemented commands (required for SC-001 testability)
- [x] T042 Run full end-to-end workflow from `quickstart.md` Section "Testing a Full Local Workflow" to verify the complete pipeline
- [x] T043 Run linter (`ruff check src/ tests/`), formatter (`ruff format --check src/ tests/`), and type checker (`mypy src/aam_cli/`) — fix all issues

**Checkpoint**: All user stories complete. Full local-first AAM CLI workflow operational.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001, T002 complete; T003–T006 provide utilities used by T007–T019)
- **User Stories (Phases 3–11)**: All depend on Phase 2 completion
  - **P1 stories** (Phases 3, 4, 5, 6): Should be done sequentially in listed order as they build on each other for the core pipeline
  - **P2 stories** (Phases 7, 8, 9, 10): Can proceed in parallel after Phase 6 is complete
  - **P3 story** (Phase 11): Can start after Phase 6 is complete
- **Polish (Phase 12)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (Registry Init)**: First — no dependencies on other stories
- **US2 (Create Package)**: Independent of US1 (creates `aam.yaml` without a registry)
- **US4 (Pack & Publish)**: Depends on US1 (needs a registry to publish to) and US2 (needs a package to pack)
- **US6 (Install)**: Depends on US4 (needs published packages to install)
- **US3 (Init from Scratch)**: Independent — only needs foundational modules
- **US5 (Search)**: Depends on US1 (needs registry with packages)
- **US7 (List/Info)**: Depends on US6 (needs installed packages to list)
- **US8 (Config)**: Independent — only needs `core/config.py`
- **US9 (Uninstall)**: Depends on US6 (needs installed packages to remove)

### Recommended Execution Order

```
Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US4) → Phase 6 (US6)
                                                                          ↓
                                                      ┌─────────┬────────┬┴────────┐
                                                      ↓         ↓        ↓         ↓
                                                   Phase 7   Phase 8  Phase 9   Phase 10
                                                   (US3)     (US5)    (US7)     (US8)
                                                      ↓         ↓        ↓         ↓
                                                      └─────────┴────────┴─────────┘
                                                                  ↓
                                                              Phase 11 (US9)
                                                                  ↓
                                                              Phase 12 (Polish)
```

### Parallel Opportunities per Phase

**Phase 1**: T003, T004, T005, T006 can all run in parallel (different utility files)
**Phase 2 Layer 1**: T007, T008, T009, T010 are sequential (manifest depends on version, config is independent but simpler to do in order)
**Phase 2 Layer 2**: T011, T012, T013 can all run in parallel (different protocol/detection files)
**Phase 2 Layer 3**: T015 and T016 can run in parallel (factory and adapter are independent); T014 depends on T011
**Phase 4**: T024 and T025 can run in parallel (detection/selection and validate are separate); T026 depends on T024
**Phase 5**: T027 and T028 can run in parallel (pack and publish are separate commands)
**Phase 6**: T029 then T030 (sequential within install command)
**Phase 9**: T033 and T034 can run in parallel (list and info are separate commands)
**Phase 12**: T037, T038, T039, T040, T041 can all run in parallel
**Phases 7–10**: All four phases can run in parallel (independent user stories)

---

## Implementation Strategy

### MVP First (P1 User Stories: US1 + US2 + US4 + US6)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 — Registry Init
4. Complete Phase 4: US2 — Create Package + Validate
5. Complete Phase 5: US4 — Pack + Publish
6. Complete Phase 6: US6 — Install
7. **STOP and VALIDATE**: Run the full pipeline end-to-end (registry init → create-package → validate → pack → publish → install)

### Incremental Delivery (P2 + P3)

8. Add US3, US5, US7, US8 in parallel → Each independently testable
9. Add US9 (Uninstall)
10. Polish pass (Phase 12)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 43 |
| **Phase 1 (Setup)** | 6 tasks |
| **Phase 2 (Foundational)** | 13 tasks |
| **US1 (Registry Init)** | 4 tasks |
| **US2 (Create + Validate)** | 3 tasks |
| **US4 (Pack + Publish)** | 2 tasks |
| **US6 (Install)** | 2 tasks |
| **US3 (Init from Scratch)** | 1 task |
| **US5 (Search)** | 1 task |
| **US7 (List/Info)** | 2 tasks |
| **US8 (Config)** | 1 task |
| **US9 (Uninstall)** | 1 task |
| **Polish** | 7 tasks |
| **Parallel opportunities** | 20 tasks marked [P] |
| **MVP scope** | Phases 1–6 (US1 + US2 + US4 + US6) = 30 tasks |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after its checkpoint
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- All modules must follow project standards: `logging.getLogger(__name__)`, type hints, Google-style docstrings, 80-char section headers, no `print()`
