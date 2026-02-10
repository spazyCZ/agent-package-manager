# Tasks: CLI Interface Scaffolding & npm-Style Source Workflow

**Feature Branch**: `004-npm-style-source-workflow`
**Generated**: 2026-02-09
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Contracts**: [contracts/cli-commands.md](./contracts/cli-commands.md)
**Data Model**: [data-model.md](./data-model.md) | **Research**: [research.md](./research.md) | **Quickstart**: [quickstart.md](./quickstart.md)

---

## Implementation Strategy

**MVP scope**: Phase 1 (Setup) + Phase 2 (Bug Fixes) + Phase 4 (Source Resolution — US2/US3/US6). This delivers the core value: `aam install code-review` from a source.

**Incremental delivery**:
1. Foundation → Bug Fixes → Source Resolution (core value)
2. CLI Restructuring (UX improvement, can be parallel with #1)
3. Outdated + Upgrade (extends source resolution)
4. Client Init (onboarding)
5. MCP + Docs + Polish (completeness)

**Key parallelism opportunity**: Phase 3 (CLI Restructuring — US7/US8) and Phase 4 (Source Resolution — US2/US3/US6) are **fully independent** and can be implemented in parallel by separate agents.

---

## Dependency Graph

```
Phase 1 (Setup)
  ├──→ Phase 2 (Bug Fixes) ──────────────────────────────────────────────────┐
  ├──→ Phase 3 (CLI Restructuring — US7/US8)                                 │
  │      └──→ Phase 6 (Client Init — US1) ──→ Phase 8 (Docs — US10)         │
  └──→ Phase 4 (Source Resolution — US2/US3/US6)                             │
         └──→ Phase 5 (Outdated/Upgrade — US4/US5)                           │
                └──→ Phase 7 (MCP — US9) ──→ Phase 8 ──→ Phase 9 (MCP Init) │
                                                     ├──→ Phase 10 (DESIGN.md deep update)
                                                     ├──→ Phase 11 (User Docs / MkDocs)
                                                     └──→ Phase 12 (Polish)  ◄────────────┘
```

**Independent tracks**:
- Track A: Phase 1 → Phase 3 → Phase 6 (init + restructuring)
- Track B: Phase 1 → Phase 4 → Phase 5 (source workflow)
- Merge: Phase 7 + Phase 8 + Phase 9 (after both tracks complete)
- Docs: Phase 10, Phase 11 (parallel, after Phase 8)
- Final: Phase 12 (after all other phases)

---

## Phase 1: Setup — Data Models & Utilities

**Goal**: Create all new data structures and utility functions needed by later phases.
**Test**: Import each new dataclass/function, instantiate with sample data, verify field types.
**No story labels** — these are foundational building blocks.

- [x] T001 Extend LockedPackage with optional source_name (str | None) and source_commit (str | None) fields, add co-presence validator (both None or both set) in `apps/aam-cli/src/aam_cli/core/workspace.py`
- [x] T002 [P] Add VirtualPackage dataclass (name, qualified_name, source_name, type, path, commit_sha, cache_dir, description, has_vendor_agent, vendor_agent_file) and ArtifactIndex dataclass (by_name dict, by_qualified_name dict, total_count, sources_indexed, build_timestamp) to `apps/aam-cli/src/aam_cli/services/source_service.py`
- [x] T003 [P] Create upgrade_service.py with OutdatedPackage, OutdatedResult, and UpgradeResult dataclasses per data-model.md in `apps/aam-cli/src/aam_cli/services/upgrade_service.py`
- [x] T004 [P] Create client_init_service.py with ClientInitResult dataclass (platform, registry_created, registry_name, sources_added, config_path, is_reconfigure) in `apps/aam-cli/src/aam_cli/services/client_init_service.py`
- [x] T005 [P] Create deprecation utility with print_deprecation_warning(old_cmd, new_cmd, removal_version) using click.style(fg="yellow", bold=True) and click.echo(err=True) in `apps/aam-cli/src/aam_cli/utils/deprecation.py`

---

## Phase 2: Bug Fixes & Cleanup

**Goal**: Fix known bugs and standardize patterns before adding new features.
**Test**: `aam uninstall` works with non-Cursor platform config. `source` commands use context console.
**No story labels** — cross-cutting quality fixes (FR-030, FR-031, FR-032).

- [x] T006 [P] Fix uninstall.py — remove `from aam_cli.adapters.cursor import CursorAdapter`, replace with `from aam_cli.adapters.factory import create_adapter`, use `create_adapter(platform, project_dir)` reading platform from config in `apps/aam-cli/src/aam_cli/commands/uninstall.py`
- [x] T007 [P] Standardize source.py — replace module-level `console = Console()` with `ctx.obj["console"]` in all subcommands, replace all `sys.exit(1)` with `ctx.exit(1)` in `apps/aam-cli/src/aam_cli/commands/source.py`

---

## Phase 3: CLI Restructuring — US7 (pkg group) + US8 (help grouping)

**Goal**: Move all creator commands under `aam pkg`, add categorized `--help`, register deprecated aliases.
**Test**: `aam pkg --help` lists init/create/validate/pack/publish/build. `aam --help` shows categorized sections. Old commands like `aam validate` print deprecation warning and still work. `aam pkg init my-skill` scaffolds a package identically to the old `aam init my-skill`.

- [x] T008 [US7] Create pkg group Click command group with help text "Package authoring commands. Create, validate, pack, and publish AAM packages. For installing packages, use 'aam install'." in `apps/aam-cli/src/aam_cli/commands/pkg/__init__.py`
- [x] T009 [P] [US7] Create pkg/init.py — import existing scaffolding logic from init_package.py, expose as `aam pkg init [name]` subcommand with identical options in `apps/aam-cli/src/aam_cli/commands/pkg/init.py`
- [x] T010 [P] [US7] Create pkg/create.py — import existing create_package logic, expose as `aam pkg create [path]` with all existing flags (--all, --type, --platform, --from-source, --artifacts, etc.) in `apps/aam-cli/src/aam_cli/commands/pkg/create.py`
- [x] T011 [P] [US7] Create pkg/validate.py — wrap existing validate command as `aam pkg validate [path]` in `apps/aam-cli/src/aam_cli/commands/pkg/validate.py`
- [x] T012 [P] [US7] Create pkg/pack.py — wrap existing pack command as `aam pkg pack [path]` in `apps/aam-cli/src/aam_cli/commands/pkg/pack.py`
- [x] T013 [P] [US7] Create pkg/publish.py — wrap existing publish command as `aam pkg publish` with --registry, --tag, --dry-run in `apps/aam-cli/src/aam_cli/commands/pkg/publish.py`
- [x] T014 [P] [US7] Create pkg/build.py — wrap existing build command as `aam pkg build --target` in `apps/aam-cli/src/aam_cli/commands/pkg/build.py`
- [x] T015 [US7][US8] Restructure main.py — implement OrderedGroup(click.Group) with SECTIONS dict per research.md R1, change root cli group to use cls=OrderedGroup, register pkg group, add deprecated hidden aliases for create-package/validate/pack/publish/build using print_deprecation_warning from T005, reorder command registration by persona sections in `apps/aam-cli/src/aam_cli/main.py`
- [x] T016 [US7] Write unit tests — verify `aam pkg --help` lists all subcommands, verify each `aam pkg <subcmd>` produces same output as old root command, verify deprecated aliases print warning and delegate correctly in `apps/aam-cli/tests/unit/test_unit_pkg_group.py`
- [x] T017 [US8] Write unit tests — verify `aam --help` output contains section headers (Getting Started, Package Management, etc.), verify deprecated commands are hidden from help, verify 80-column rendering in `apps/aam-cli/tests/unit/test_unit_help_grouping.py`

---

## Phase 4: Source Resolution & Install — US2, US3, US6

**Goal**: Enable `aam install code-review` to resolve from source artifact indexes, auto-create manifest, deploy. Extend `search` and `list` to include source artifacts.
**Test**: After `aam source add` of a test repo, `aam install <artifact-name>` installs and deploys. `aam list --available` shows source artifacts. `aam search <query>` returns source matches.

- [x] T018 [US2] Implement build_source_index(config) — iterate configured sources, scan each cache using existing scan logic, create VirtualPackage for each artifact, populate ArtifactIndex with by_name and by_qualified_name lookups in `apps/aam-cli/src/aam_cli/services/source_service.py`
- [x] T019 [US2] Implement resolve_artifact(name, index) — handle qualified names (direct lookup), unqualified names (registry-first then source fallback), multi-match warning with suggestion to use qualified name, raise ValueError with actionable message if not found in `apps/aam-cli/src/aam_cli/services/source_service.py`
- [x] T020 [US2] Implement install_from_source(virtual_package, project_dir, platform, config) — stage to .aam/.tmp/, copy files from cache, generate aam.yaml with Provenance, compute SHA-256 checksums, move to .aam/packages/, deploy via create_adapter(), update aam-lock.yaml with source_name and source_commit in `apps/aam-cli/src/aam_cli/services/install_service.py`
- [x] T021 [US2] Modify install command — after registry lookup fails, call build_source_index() + resolve_artifact(), if resolved call install_from_source(), display "installed from source" message, handle "already installed" and --force cases in `apps/aam-cli/src/aam_cli/commands/install.py`
- [x] T022 [P] [US6] Add --available flag to list command — when set, call build_source_index(), display artifacts grouped by source name with type and description columns per contracts/cli-commands.md in `apps/aam-cli/src/aam_cli/commands/list_packages.py`
- [x] T023 [P] [US6] Extend search command — after registry search, also search source artifact index by name/description, tag source results with "[source]" indicator per contracts/cli-commands.md in `apps/aam-cli/src/aam_cli/commands/search.py`
- [x] T024 [US2] Write unit tests — test build_source_index with mocked sources, test resolve_artifact for unqualified/qualified/ambiguous/not-found cases, test install_from_source with mocked filesystem, test install command source fallback path in `apps/aam-cli/tests/unit/test_unit_install_from_source.py`

---

## Phase 5: Outdated & Upgrade — US4, US5

**Goal**: `aam outdated` compares installed commit SHAs against source HEAD. `aam upgrade` updates packages with spec 003 modification warning flow.
**Test**: Install from source, simulate commit change in cache, `aam outdated` reports the package. `aam upgrade` updates it. `--dry-run` previews without changes. Modified files trigger backup/skip/diff/force prompt.

- [x] T025 [US4] Implement check_outdated(lock_file, config) — read lock file, group packages by source_name, get HEAD SHA from each source cache, compare against stored source_commit, detect stale sources (>7 days), return OutdatedResult in `apps/aam-cli/src/aam_cli/services/upgrade_service.py`
- [x] T026 [US4] Create outdated command — call check_outdated(), render Rich table (Package/Current/Latest/Source/Status columns), support --json output per contracts/cli-commands.md, register in main.py under Package Management section in `apps/aam-cli/src/aam_cli/commands/outdated.py`
- [x] T027 [US4] Write unit tests — test outdated detection with mocked lock file and source caches, test JSON output format, test "(no source)" for registry packages, test stale source warning in `apps/aam-cli/tests/unit/test_unit_outdated.py`
- [x] T028 [US5] Implement upgrade_packages(names, config, force, dry_run) — run check_outdated, filter to requested packages, for each: check local modifications via checksum_service, handle backup/skip/diff/force flow (reuse spec 003 pattern), copy new files from cache, recompute checksums, update lock file source_commit, re-deploy via adapter, return UpgradeResult in `apps/aam-cli/src/aam_cli/services/upgrade_service.py`
- [x] T029 [US5] Create upgrade command — accept optional PACKAGE arg, --dry-run, --force flags, call upgrade_packages(), render results (upgraded/skipped/failed), register in main.py with "update" as hidden alias, per contracts/cli-commands.md in `apps/aam-cli/src/aam_cli/commands/upgrade.py`
- [x] T030 [US5] Write unit tests — test upgrade single and all packages, test --dry-run returns preview, test --force skips modification check, test partial failure handling, test backup creation for modified files in `apps/aam-cli/tests/unit/test_unit_upgrade.py`

---

## Phase 6: Client Initialization — US1

**Goal**: `aam init` guides new users through platform selection, registry setup, and source configuration.
**Test**: Run `aam init` with simulated input, verify config file written with correct platform/registries/sources. Run `aam init --yes`, verify defaults applied. Run in directory with existing config, verify reconfigure prompt.

- [x] T031 [US1] Implement client_init_service functions — detect_platform() checks for .cursor/, .github/copilot/, CLAUDE.md, .codex/ dirs; setup_registry() delegates to existing registry init/add logic; setup_sources() delegates to existing register_default_sources(); orchestrate_init() coordinates the full flow and returns ClientInitResult in `apps/aam-cli/src/aam_cli/services/client_init_service.py`
- [x] T032 [US1] Create client_init command — optional [name] arg for backward compat detection (if name provided: deprecation warning + delegate to pkg init), --yes flag for non-interactive, interactive flow using click.prompt + Rich per research.md R4, display "Next steps" summary, register as "init" in main.py replacing old init in `apps/aam-cli/src/aam_cli/commands/client_init.py`
- [x] T033 [US1] Update main.py — replace old init_package import with client_init, ensure "init" appears in OrderedGroup "Getting Started" section in `apps/aam-cli/src/aam_cli/main.py`
- [x] T034 [US1] Write unit tests — test interactive flow with mocked click.prompt, test --yes defaults, test existing config detection and reconfigure, test [name] arg delegation to pkg init in `apps/aam-cli/tests/unit/test_unit_client_init.py`

---

## Phase 7: MCP Tools — US9

**Goal**: IDE agents can check outdated, list available, and upgrade packages via MCP.
**Test**: Start MCP server, call each tool via test client, verify structured responses. Verify `aam_upgrade` requires `--allow-write`.

- [x] T035 [P] [US9] Add aam_outdated read tool (calls check_outdated, returns OutdatedResult as dict) and aam_available read tool (calls build_source_index, returns artifacts grouped by source) in `apps/aam-cli/src/aam_cli/mcp/tools_read.py`
- [x] T036 [P] [US9] Add aam_upgrade write tool (calls upgrade_packages with package_name/dry_run/force params, gated by allow-write) in `apps/aam-cli/src/aam_cli/mcp/tools_write.py`

---

## Phase 8: Documentation & Web — US10

**Goal**: All user-facing docs reflect new command structure. Web homepage shows updated CLI examples.
**Test**: Grep docs for stale command references (e.g., "aam create-package" without "pkg"). Verify homepage code examples use `aam pkg publish`.

- [x] T037 [P] [US10] Update USER_GUIDE.md — change quick start to use `aam init` for client setup, update all creator command references to `aam pkg *`, add outdated/upgrade examples, add `aam list --available` example in `docs/USER_GUIDE.md`
- [x] T038 [P] [US10] Update DESIGN.md — update command hierarchy tree, update roadmap to reflect spec 004 completion, update `aam init` description in `docs/DESIGN.md`
- [x] T039 [P] [US10] Update HomePage.tsx — change "Publish your package" example from `$ aam publish` to `$ aam pkg publish`, verify all CLI examples use current command names in `apps/aam-web/src/pages/HomePage.tsx`

---

## Phase 9: MCP Init Tools — US11

**Goal**: IDE agents can initialize AAM, detect platforms, and check init status via MCP.
**Test**: Call each tool/resource via MCP test client, verify structured responses.

- [x] T040 [P] [US11] Add aam_init write tool (calls orchestrate_init with platform/skip_sources, returns ClientInitResult) in `apps/aam-cli/src/aam_cli/mcp/tools_write.py`
- [x] T041 [P] [US11] Add aam_init_info read tool (calls detect_platform, returns detected platform/recommended defaults) in `apps/aam-cli/src/aam_cli/mcp/tools_read.py`
- [x] T042 [P] [US11] Add aam://init_status resource (returns ClientInitResult based on current config) in `apps/aam-cli/src/aam_cli/mcp/resources.py`
- [x] T043 [P] [US11] Write MCP unit tests for aam_init, aam_init_info, aam://init_status in `apps/aam-cli/tests/unit/test_unit_mcp_init_tools.py`

---

## Phase 10: DESIGN.md Deep Update — US10

**Goal**: All remaining stale command references in DESIGN.md are updated to reflect the `aam pkg *` restructuring. Command examples, file layout tree, roadmap checklist, and architecture description all use current command names.
**Test**: `rg 'aam (create-package|aam validate|aam pack|aam publish|aam build )' docs/DESIGN.md` returns zero matches (excluding inline prose about the concept of "publishing").

- [x] T044 [P] [US10] Update DESIGN.md CLI examples — change all `aam create-package` → `aam pkg create`, `aam validate` → `aam pkg validate`, `aam pack` → `aam pkg pack`, `aam publish` → `aam pkg publish`, `aam build` → `aam pkg build` in code blocks and inline examples (~58 occurrences) in `docs/DESIGN.md`
- [x] T045 [P] [US10] Update DESIGN.md file layout tree — rename `create_package.py` → `pkg/` group reference, update comment annotations to match current command names in `docs/DESIGN.md` §10 File Layout
- [x] T046 [P] [US10] Update DESIGN.md roadmap checklist — update milestone items to use `aam pkg *` names and add spec 004 features (outdated, upgrade, aam init, aam pkg group) to completed items in `docs/DESIGN.md` §13 Roadmap
- [x] T047 [US10] Update DESIGN.md MCP tool table — update CLI column from `aam validate`/`aam create-package`/`aam publish` to `aam pkg validate`/`aam pkg create`/`aam pkg publish` in §5.3 MCP Server Mode tool table in `docs/DESIGN.md`

---

## Phase 11: User Docs (MkDocs) — US10

**Goal**: All MkDocs user-facing documentation under `docs/user_docs/` reflects the new CLI structure (`aam pkg *` for authoring, `aam init` for client setup, new `aam outdated`/`aam upgrade` commands). Navigation is updated in `mkdocs.yml`.
**Test**: `rg 'aam create-package' docs/user_docs/` returns zero matches. New pages for `outdated`, `upgrade`, and `client-init` exist and are linked from nav.

### CLI Reference Pages (highest impact — users copy-paste from these)

- [x] T048 [P] [US10] Update `cli/init.md` — rewrite from package scaffolding to client setup (`aam init`), add `--yes` flag, add platform detection docs, add backward compat note ("aam init <name>" delegates to `aam pkg init`) in `docs/user_docs/docs/cli/init.md`
- [x] T049 [P] [US10] Update `cli/create-package.md` — add deprecation banner at top pointing to `aam pkg create`, update all command examples to `aam pkg create`, keep as redirect/compat page in `docs/user_docs/docs/cli/create-package.md`
- [x] T050 [P] [US10] Update `cli/validate.md` — add deprecation banner pointing to `aam pkg validate`, update all examples to `aam pkg validate` in `docs/user_docs/docs/cli/validate.md`
- [x] T051 [P] [US10] Update `cli/pack.md` — add deprecation banner pointing to `aam pkg pack`, update all examples to `aam pkg pack` in `docs/user_docs/docs/cli/pack.md`
- [x] T052 [P] [US10] Update `cli/publish.md` — add deprecation banner pointing to `aam pkg publish`, update all examples to `aam pkg publish` in `docs/user_docs/docs/cli/publish.md`
- [x] T053 [P] [US10] Update `cli/build.md` — add deprecation banner pointing to `aam pkg build`, update all examples to `aam pkg build` in `docs/user_docs/docs/cli/build.md`
- [x] T054 [P] [US10] Update `cli/index.md` — restructure command listing to match categorized help (Getting Started, Package Management, Package Integrity, Package Authoring via `aam pkg`, Source Management, Configuration, Utilities) in `docs/user_docs/docs/cli/index.md`
- [x] T055 [P] [US10] Create `cli/outdated.md` — new CLI reference page for `aam outdated` with synopsis, options (--json), output format, examples in `docs/user_docs/docs/cli/outdated.md`
- [x] T056 [P] [US10] Create `cli/upgrade.md` — new CLI reference page for `aam upgrade [PACKAGE]` with --dry-run, --force, output format, examples in `docs/user_docs/docs/cli/upgrade.md`
- [x] T057 [P] [US10] Create `cli/pkg-init.md` — new page for `aam pkg init [name]` (package scaffolding, moved from old `aam init`) in `docs/user_docs/docs/cli/pkg-init.md`

### Getting Started & Tutorials

- [x] T058 [P] [US10] Update `getting-started/quickstart.md` — change setup steps to use `aam init`, update authoring workflow to `aam pkg init`/`aam pkg create`/`aam pkg validate`/`aam pkg pack`/`aam pkg publish` in `docs/user_docs/docs/getting-started/quickstart.md`
- [x] T059 [P] [US10] Update `getting-started/first-package.md` — update package authoring examples to `aam pkg init`/`aam pkg create` in `docs/user_docs/docs/getting-started/first-package.md`
- [x] T060 [P] [US10] Update tutorials — update `package-existing-skills.md`, `build-code-review-package.md`, `share-with-team.md` to use `aam pkg *` commands throughout in `docs/user_docs/docs/tutorials/`

### Concepts & Configuration

- [x] T061 [P] [US10] Update concept pages — update `registries.md`, `packages.md`, `git-sources.md`, `security.md` command references to `aam pkg *` in `docs/user_docs/docs/concepts/`
- [x] T062 [P] [US10] Update configuration pages — update `global.md`, `manifest.md`, `security.md` command references to `aam pkg *` in `docs/user_docs/docs/configuration/`

### Advanced & Troubleshooting

- [x] T063 [P] [US10] Update advanced pages — update `dist-tags.md`, `signing.md`, `scoped-packages.md`, `http-registry.md`, `quality-evals.md` to use `aam pkg *` in `docs/user_docs/docs/advanced/`
- [x] T064 [P] [US10] Update troubleshooting pages — update `migration.md` and `faq.md` to reference `aam pkg *` names, add migration note for `aam init` change in `docs/user_docs/docs/troubleshooting/`

### Navigation & Index

- [x] T065 [US10] Update `mkdocs.yml` — add `cli/outdated.md`, `cli/upgrade.md`, `cli/pkg-init.md` to nav, restructure CLI section to group authoring commands under `Package Authoring (aam pkg)` in `docs/user_docs/mkdocs.yml`
- [x] T066 [US10] Update `docs/index.md` — update hero CLI examples to show `aam init`, `aam install`, `aam pkg create` in `docs/user_docs/docs/index.md`

---

## Phase 12: Polish & Cross-Cutting

**Goal**: Verify quality, coverage, and contract compliance across all changes.

- [x] T067 Run full test suite via `npx nx test aam-cli` and verify all tests pass
- [x] T068 Run ruff check + ruff format --check + mypy across all new and modified files in `apps/aam-cli/src/` and `apps/aam-cli/tests/`
- [x] T069 Verify `aam --help` output matches contract exactly in `specs/004-npm-style-source-workflow/contracts/cli-commands.md`
- [x] T070 Verify test coverage meets 80% target (SC-013) for all new modules

---

## Summary

| Metric | Count |
|--------|-------|
| **Total tasks** | 70 |
| **Phases** | 12 |
| **Parallelizable tasks** ([P] marker) | 44 |

### Tasks per User Story

| Story | Description | Tasks | Phase |
|-------|-------------|-------|-------|
| US1 | Client initialization (`aam init`) | T031–T034 (4) | 6 |
| US2 | Install from source | T018–T021, T024 (5) | 4 |
| US3 | Source update refreshes | Covered by US2 (existing spec 003 flow) | 4 |
| US4 | Outdated detection | T025–T027 (3) | 5 |
| US5 | Upgrade packages | T028–T030 (3) | 5 |
| US6 | List available + search sources | T022–T023 (2) | 4 |
| US7 | `aam pkg` group | T008–T016 (9) | 3 |
| US8 | Help text grouping | T015, T017 (shared T015 with US7) | 3 |
| US9 | MCP tools | T035–T036 (2) | 7 |
| US10 | Documentation + web | T037–T039 (3), T044–T066 (23) | 8, 10, 11 |
| US11 | MCP init tools | T040–T043 (4) | 9 |
| — | Setup (data models) | T001–T005 (5) | 1 |
| — | Bug fixes | T006–T007 (2) | 2 |
| — | Polish | T067–T070 (4) | 12 |

### Parallel Execution Examples

**Within Phase 1** (all independent files):
```
T001 ──┐
T002 ──┤
T003 ──┼── All run in parallel (different files)
T004 ──┤
T005 ──┘
```

**Within Phase 3** (pkg subcommands):
```
T008 ─→ T009 ──┐
        T010 ──┤
        T011 ──┼── All [P] (different files, same pattern)
        T012 ──┤
        T013 ──┤
        T014 ──┘─→ T015 (main.py depends on all subcommands existing)
```

**Within Phase 11** (user docs — all independent files):
```
T048 ──┐
T049 ──┤
T050 ──┤
T051 ──┼── All [P] (different doc files, same pattern)
...    ┤
T064 ──┘─→ T065 (mkdocs.yml depends on new pages existing)
```

**Across tracks** (Phase 3 and Phase 4 are independent):
```
Track A: Phase 1 → Phase 3 (CLI restructuring)
Track B: Phase 1 → Phase 4 (source resolution)
         ↘ Both merge at Phase 7 (MCP needs services from both)
```

### MVP Scope

**Minimum viable delivery**: Phase 1 + Phase 2 + Phase 4 (14 tasks)

This gives users `aam install code-review` from sources, `aam list --available`, and `aam search` with source results — the core npm-style workflow. The CLI restructuring (aam pkg, help grouping) and other features can follow incrementally.
