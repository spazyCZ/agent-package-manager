# Tasks: Restructure AAM CLI Commands Directory

**Input**: Design documents from `/specs/008-commands-layout/`  
**Branch**: `008-commands-layout` | **Date**: 2026-03-12  
**References**: plan.md, spec.md, data-model.md, research.md, quickstart.md, `specs/008a-commands-layout-improvements-archive/init.md`

**Tests**: Test import update tasks are included per user request. Each
implementation phase includes test verification steps.

**Organization**: Tasks follow the 8-phase implementation plan (Phases 1–8). Phases map to user stories in priority order (P1 → P3). Each phase is independently verifiable before the next begins.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on in-progress tasks)
- **[Story]**: Maps to user story from spec.md (US1–US5)
- Paths are relative to `apps/aam-cli/src/aam_cli/` unless noted

---

## Phase 1: Documentation (FIRST — before any source changes)

**Purpose**: Update user-facing docs to reflect the target layout. Constitution VIII requires docs to be updated alongside (or before) source changes. User explicitly requested this be done first.

**Independent Test**: `git diff docs/DESIGN.md` shows updated module structure tree; no broken links

- [X] T001 Update `docs/DESIGN.md` section 11.1 "Module Structure" (line 2465): replace the conceptual `aam/cli/` tree with the actual target layout from `plan.md` — show real `aam_cli/commands/` tree with groups-as-directories convention, add explanatory note: "every group is a directory, every filename matches its CLI name"
- [X] T002 [P] Scan `docs/USER_GUIDE.md` for any internal file path references (e.g. `client_init.py`, `list_packages.py`, `show_package.py`, `source.py`, `config.py`, `mcp_serve.py`) and update them to reflect the target layout; CLI command names are unchanged so user-facing command reference sections need no changes
- [X] T003 [P] Add a "Commands Layout Convention" subsection to `docs/DESIGN.md` section 11.1 describing the two rules: (1) every filename matches its CLI command name, (2) every group with 2+ subcommands is a `group/` directory with `__init__.py` + one file per subcommand

**Checkpoint**: Docs updated and reviewed. No source code touched yet.

---

## Phase 2: Rename Top-Level Files (US1 — P1)

**Purpose**: Three top-level files have names that don't match their CLI commands. Rename them so `aam <cmd>` → `commands/<cmd>.py` holds universally.

**Goal (US1)**: Developer finds the source for any CLI command by filename alone, without cross-referencing `main.py`.

**Independent Test**:
```bash
ls apps/aam-cli/src/aam_cli/commands/init.py   # exists
ls apps/aam-cli/src/aam_cli/commands/list.py   # exists
ls apps/aam-cli/src/aam_cli/commands/info.py   # exists
! ls apps/aam-cli/src/aam_cli/commands/client_init.py 2>/dev/null
! ls apps/aam-cli/src/aam_cli/commands/list_packages.py 2>/dev/null
! ls apps/aam-cli/src/aam_cli/commands/show_package.py 2>/dev/null
aam init --help && aam list --help && aam info --help
npx nx test aam-cli
```

### Test suite — Phase 2 import updates

- [X] T004 [US1] Run `rg 'aam_cli\.commands\.(client_init|list_packages|show_package)' apps/aam-cli/tests/` to enumerate all test files referencing the old module paths. For each match, update the import to use the new path (`commands.init`, `commands.list`, `commands.info` respectively). Known file: `test_unit_client_init.py`. Function names are unchanged (`client_init`, `list_packages`, `show_package`). Acceptance: zero matches when the `rg` scan is re-run after edits.

### Implementation — Phase 2

- [X] T005 [US1] Rename `commands/client_init.py` → `commands/init.py` (git mv to preserve history)
- [X] T006 [US1] Rename `commands/list_packages.py` → `commands/list.py` (git mv)
- [X] T007 [US1] Rename `commands/show_package.py` → `commands/info.py` (git mv)
- [X] T008 [US1] Update `main.py` import block: replace `from aam_cli.commands.client_init import client_init` → `from aam_cli.commands.init import client_init`, `from aam_cli.commands.list_packages import list_packages` → `from aam_cli.commands.list import list_packages`, `from aam_cli.commands.show_package import show_package` → `from aam_cli.commands.info import show_package` (function names unchanged)
- [X] T009 [US1] Run `npx nx test aam-cli` and confirm all tests pass; run `aam init --help`, `aam list --help`, `aam info --help`

**Checkpoint**: US1 complete. Developer can navigate to any renamed command by CLI name. All tests green.

---

## Phase 3: Consolidate pkg/ (US2 — P1)

**Purpose**: Eliminate 6 duplicated command pairs. Full implementation moves into `pkg/*.py`; top-level wrappers are deleted.

**Goal (US2)**: Each `aam pkg <subcommand>` has exactly one source file with its full implementation.

**Independent Test**:
```bash
for f in create_package init_package build pack publish validate; do
  ! ls "apps/aam-cli/src/aam_cli/commands/${f}.py" 2>/dev/null && echo "OK: ${f}.py deleted"
done
aam pkg init --help && aam pkg create --help && aam pkg validate --help
aam pkg pack --help && aam pkg publish --help && aam pkg build --help
npx nx test aam-cli
```

### Test suite — Phase 3 import updates

- [X] T010 [US2] Update `apps/aam-cli/tests/unit/test_unit_create_from_source.py` line 22: change `from aam_cli.commands.create_package import create_package` → `from aam_cli.commands.pkg.create import pkg_create`; update all references to `create_package` in the file to use `pkg_create`; update the class/test docstrings if they reference the old module path

### Implementation — Phase 3

- [X] T011 [US2] Consolidate `commands/pkg/create.py`: read `commands/create_package.py` (1058 lines) and replace the `ctx.invoke(create_package, ...)` delegation at the top of `pkg/create.py` with the full implementation body; keep function name `pkg_create` and decorator `@click.command("create")`; remove the `from aam_cli.commands.create_package import create_package` import
- [X] T012 [US2] Consolidate `commands/pkg/init.py`: the file already contains `--migrate` logic (lines 69-92); replace the `ctx.invoke(init_package, name=name)` call (approx line 97) with the inline body from `commands/init_package.py`; remove `from aam_cli.commands.init_package import init_package`
- [X] T013 [P] [US2] Consolidate `commands/pkg/build.py`: replace the `ctx.invoke` wrapper with full body from `commands/build.py` (~96 lines); keep function name `pkg_build`
- [X] T014 [P] [US2] Consolidate `commands/pkg/pack.py`: replace wrapper with full body from `commands/pack.py` (~161 lines); keep function name `pkg_pack`
- [X] T015 [P] [US2] Consolidate `commands/pkg/publish.py`: replace wrapper with full body from `commands/publish.py` (~150 lines); keep function name `pkg_publish`
- [X] T016 [P] [US2] Consolidate `commands/pkg/validate.py`: replace wrapper with full body from `commands/validate.py` (~165 lines, including `--permissions` flag); keep function name `pkg_validate`
- [X] T017 [US2] Update `commands/init.py` (renamed from `client_init.py`): change `from aam_cli.commands.init_package import init_package` → `from aam_cli.commands.pkg.init import pkg_init`; change `ctx.invoke(init_package, name=name)` → `ctx.invoke(pkg_init, name=name)`
- [X] T018 [US2] Delete top-level originals: `commands/create_package.py`, `commands/init_package.py`, `commands/build.py`, `commands/pack.py`, `commands/publish.py`, `commands/validate.py`
- [X] T019 [US2] Update `main.py`: remove imports of `build`, `create_package`, `publish`, `pack`, `validate` modules from the bulk import block (lines 142-150 area); these will be handled by deprecated aliases in Phase 6
- [X] T020 [US2] Run `npx nx test aam-cli` and confirm all tests pass; run all 6 `aam pkg <subcommand> --help` commands

**Checkpoint**: US2 complete. Zero duplicated implementations. All pkg subcommands work. All tests green.

---

## Phase 4: Split source/ (US3 — P2)

**Purpose**: `source.py` (716 lines, 7 subcommands) is split into `source/` directory following the `pkg/` pattern.

**Goal (US3 partial)**: `aam source` subcommands each live in their own file.

**Independent Test**:
```bash
ls apps/aam-cli/src/aam_cli/commands/source/
# Expected: __init__.py add.py scan.py update.py list.py remove.py candidates.py enable_defaults.py
! ls apps/aam-cli/src/aam_cli/commands/source.py 2>/dev/null
aam source --help
aam source add --help && aam source scan --help && aam source update --help
aam source list --help && aam source remove --help && aam source candidates --help
aam source enable-defaults --help
npx nx test aam-cli
```

### Implementation — Phase 4

- [X] T021 [US3] Create `commands/source/__init__.py`: define `@click.group()` function `source` with console context setup (copy lines 36-48 from current `source.py`); import and register all 7 subcommands via `source.add_command(fn, "name")` following the exact pattern in `pkg/__init__.py`
- [X] T022 [P] [US3] Create `commands/source/add.py`: extract `add()` function (approx lines 81-161 of `source.py`); change `@source.command()` → `@click.command()`; bring all needed imports (services, Rich, etc.) into the file
- [X] T023 [P] [US3] Create `commands/source/scan.py`: extract `scan()` function (approx lines 170-253); change decorator; bring imports
- [X] T024 [P] [US3] Create `commands/source/update.py`: extract `update()` function (approx lines 263-385); change decorator; bring imports
- [X] T025 [P] [US3] Create `commands/source/list.py`: extract `list_cmd()` function (approx lines 395-466); register as `"list"` in `__init__.py`; change decorator; bring imports
- [X] T026 [P] [US3] Create `commands/source/remove.py`: extract `remove()` function (approx lines 476-513); change decorator; bring imports
- [X] T027 [P] [US3] Create `commands/source/candidates.py`: extract `candidates()` function (approx lines 523-599); change decorator; bring imports
- [X] T028 [P] [US3] Create `commands/source/enable_defaults.py`: extract `enable_defaults()` function (approx lines 609-716); register as `"enable-defaults"` in `__init__.py`; change decorator; bring imports
- [X] T029 [US3] Delete `commands/source.py`; verify `from aam_cli.commands.source import source` in `main.py` is unchanged (now resolves to `source/__init__.py`)
- [X] T030 [US3] Run `npx nx test aam-cli` and confirm all tests pass; smoke-test all 7 `aam source <subcommand> --help` commands

**Checkpoint**: source/ split complete. All 7 subcommands work. All tests green.

---

## Phase 5: Split Remaining Inline Groups (US3 continued — P2)

**Purpose**: Split `config.py`, `registry.py`, `auth.py`, `cache.py`, `mcp_serve.py` into their respective directories.

**Goal (US3)**: Every command group with 2+ subcommands is a directory-based package.

**Independent Test**:
```bash
for group in config registry auth cache mcp; do
  ls "apps/aam-cli/src/aam_cli/commands/${group}/__init__.py" && echo "OK: ${group}/"
done
python -c "from aam_cli.commands.auth import get_token; print('OK: get_token')"
aam config --help && aam registry --help
aam login --help && aam logout --help && aam whoami --help
aam cache --help && aam mcp --help
npx nx test aam-cli
```

### Implementation — Phase 5a: config/ (214 lines, 3 subcommands)

- [X] T031 [US3] Create `commands/config/__init__.py`: group definition `@click.group()`, register 3 subcommands via `config.add_command()`
- [X] T032 [P] [US3] Create `commands/config/set.py`: extract `config_set()` (approx lines 51-106 of `config.py`); `@click.command()`; bring imports
- [X] T033 [P] [US3] Create `commands/config/get.py`: extract `config_get()` (approx lines 115-154); `@click.command()`; bring imports
- [X] T034 [P] [US3] Create `commands/config/list.py`: extract `config_list()` (approx lines 164-214); `@click.command()`; bring imports
- [X] T035 [US3] Delete `commands/config.py`; update `main.py` import: `from aam_cli.commands import config` → `from aam_cli.commands.config import config`; update registration: `cli.add_command(config.config)` → `cli.add_command(config)`

### Implementation — Phase 5b: registry/ (280 lines, 4 subcommands)

- [X] T036 [US3] Create `commands/registry/__init__.py`: group definition, register 4 subcommands
- [X] T037 [P] [US3] Create `commands/registry/init.py`: extract `registry_init()` from `registry.py`; `@click.command()`; bring imports
- [X] T038 [P] [US3] Create `commands/registry/add.py`: extract `registry_add()`; `@click.command()`; bring imports
- [X] T039 [P] [US3] Create `commands/registry/list.py`: extract `registry_list()`; `@click.command()`; bring imports
- [X] T040 [P] [US3] Create `commands/registry/remove.py`: extract `registry_remove()`; `@click.command()`; bring imports
- [X] T041 [US3] Delete `commands/registry.py`; update `main.py` import: `from aam_cli.commands import registry` → `from aam_cli.commands.registry import registry`; update registration: `cli.add_command(registry.registry)` → `cli.add_command(registry)`

### Implementation — Phase 5c: auth/ (152 lines, 3 commands + helpers) ⚠️ Special case

- [X] T042 [US3] Create `commands/auth/__init__.py`: copy `AUTH_FILE`, `_load_auth()`, `_save_auth()`, `get_token()` helper functions directly into this file (NOT into subfiles); add group definition if needed; add re-exports: `from aam_cli.commands.auth.login import login`, `from aam_cli.commands.auth.logout import logout`, `from aam_cli.commands.auth.whoami import whoami` — this preserves `from aam_cli.commands.auth import get_token` used by `aam_cli/registry/factory.py` line 57
- [X] T043 [P] [US3] Create `commands/auth/login.py`: extract `login()` command from `auth.py`; import helpers from `aam_cli.commands.auth` (the `__init__.py`); `@click.command()`
- [X] T044 [P] [US3] Create `commands/auth/logout.py`: extract `logout()` command; import helpers from `aam_cli.commands.auth`; `@click.command()`
- [X] T045 [P] [US3] Create `commands/auth/whoami.py`: extract `whoami()` command; import helpers from `aam_cli.commands.auth`; `@click.command()`
- [X] T046 [US3] Delete `commands/auth.py`; verify `from aam_cli.commands.auth import get_token` resolves correctly: `python -c "from aam_cli.commands.auth import get_token; print('OK')"`; verify `from aam_cli.commands.auth import login, logout, whoami` still works from `main.py`

### Implementation — Phase 5d: cache/ (93 lines, 2 subcommands)

- [X] T047 [US3] Create `commands/cache/__init__.py`: group definition, register 2 subcommands
- [X] T048 [P] [US3] Create `commands/cache/clean.py`: extract `cache_clean()` (approx lines 42-66 of `cache.py`); `@click.command()`; bring imports
- [X] T049 [P] [US3] Create `commands/cache/ls.py`: extract `cache_ls()` (approx lines 69-93); `@click.command()`; bring imports
- [X] T050 [US3] Delete `commands/cache.py`; no `main.py` import changes needed (already imports `from aam_cli.commands.cache import cache`)

### Implementation — Phase 5e: mcp/ (214 lines, 1 subcommand)

- [X] T051 [US3] Create `commands/mcp/__init__.py`: define `@click.group()` function `mcp` with context setup; register `serve` subcommand via `mcp.add_command(serve, "serve")`
- [X] T052 [US3] Create `commands/mcp/serve.py`: extract `_configure_logging()` helper + `serve()` command (full 214-line body) from `mcp_serve.py`; change `@mcp.command("serve")` → `@click.command("serve")`; bring all imports
- [X] T053 [US3] Delete `commands/mcp_serve.py`; update `main.py` import: `from aam_cli.commands.mcp_serve import mcp` → `from aam_cli.commands.mcp import mcp`

### Test suite — Phase 5 verification

- [X] T054 [US3] Run `npx nx test aam-cli` and confirm all tests pass after all group splits; verify `auth.get_token()` public interface; run `--help` for each new group directory

**Checkpoint**: US3 complete. All 6 inline group files split. Zero monolithic command files. All tests green.

---

## Phase 6: Clean Up main.py Imports (US4 — P2)

**Purpose**: Replace the mixed import block in `main.py` with uniform conventions. Groups from `__init__`, top-level commands as direct function imports, all registrations use `cli.add_command(fn)`.

**Goal (US4)**: Developer reads `main.py` and sees a clean, self-documenting import section.

**Independent Test**:
```bash
aam --help  # all sections render: Getting Started, Package Management, etc.
rg 'from aam_cli\.commands import (build|create_package|publish|pack|validate)' apps/aam-cli/src/
# Expected: no matches
```

### Implementation — Phase 6

- [X] T055 [US4] Rewrite `main.py` import block (lines 142-176): replace with the clean uniform style from `plan.md` — first block is `# Groups (from package __init__)` with 7 imports; second block is `# Top-level commands (direct function imports)` with 20 imports; remove all deprecated module-level imports of `build`, `create_package`, `publish`, `pack`, `validate`
- [X] T056 [US4] Update command registrations in `main.py`: change `cli.add_command(install.install)` → `cli.add_command(install)`, `cli.add_command(search.search)` → `cli.add_command(search)`, `cli.add_command(config.config)` → `cli.add_command(config)`, `cli.add_command(registry.registry)` → `cli.add_command(registry)`
- [X] T057 [US4] Run `aam --help` and verify all 10 help sections render correctly (Getting Started, Package Management, Package Integrity, Dependency Management, Testing, Package Authoring, Source Management, Configuration, Authentication, Utilities)

**Checkpoint**: US4 complete. `main.py` imports are clean and uniform. `aam --help` renders all sections.

---

## Phase 7: Extract Deprecated Aliases (US5 — P3)

**Purpose**: Move all 6 deprecated alias definitions from `main.py` (lines 279-365) into a dedicated `_deprecated.py` module with lazy imports.

**Goal (US5)**: Deprecated aliases work and warn; `main.py` alias block is replaced by a single import and function call.

**Independent Test**:
```bash
ls apps/aam-cli/src/aam_cli/commands/_deprecated.py
aam create-package --help  # shows deprecation warning + aam pkg create
aam validate --help        # shows deprecation warning + aam pkg validate
aam pack --help            # shows deprecation warning + aam pkg pack
aam publish --help         # shows deprecation warning + aam pkg publish
aam build --help           # shows deprecation warning + aam pkg build
aam update --help          # shows hidden alias for aam upgrade
```

### Implementation — Phase 7

- [X] T058 [US5] Create `commands/_deprecated.py`: define `register_deprecated_aliases(cli: click.Group) -> None` function; move all 6 alias definitions (`deprecated_create_package`, `deprecated_validate`, `deprecated_pack`, `deprecated_publish`, `deprecated_build`, `update_alias`) from `main.py` into this function; update each alias to use lazy imports inside the alias body (e.g. `from aam_cli.commands.pkg.create import pkg_create`) instead of module-level imports; add module-level docstring and logger
- [X] T059 [US5] Update `main.py`: remove the entire deprecated aliases block (lines 279-365); replace with two lines: `from aam_cli.commands._deprecated import register_deprecated_aliases` and `register_deprecated_aliases(cli)`
- [X] T060 [US5] Run all 6 deprecated alias commands and verify each displays the deprecation warning message and delegates correctly; run `npx nx test aam-cli`

**Checkpoint**: US5 complete. Aliases centralized. `main.py` is clean.

---

## Phase 8: Final Verification & Orphan Scan

**Purpose**: Confirm zero orphaned imports, full test suite green, complete CLI smoke test.

- [X] T061 Run orphan import scan — **acceptance: both commands exit with code 1 (no matches)**:
  ```bash
  rg 'aam_cli\.commands\.(client_init|list_packages|show_package|create_package|init_package|mcp_serve)' apps/aam-cli/
  rg 'from aam_cli\.commands import (build|pack|publish|validate)' apps/aam-cli/src/
  ```
  If either returns matches, the phase is not complete — fix the stale import before proceeding.
- [X] T062 Run full test suite: `npx nx test aam-cli` — confirm 0 failures, 0 errors
- [X] T063 [P] Run complete CLI smoke test for all 20 top-level commands — **acceptance: all 20 print "OK"**, zero failures:
  ```bash
  for cmd in init install uninstall upgrade outdated search list info verify diff tree why check audit dedupe prune test eval doctor convert; do
    aam $cmd --help > /dev/null && echo "OK: aam $cmd" || echo "FAIL: aam $cmd"
  done
  ```
- [X] T064 [P] Run complete CLI smoke test for all 23 group subcommands — **acceptance: all 23 print "OK"**, zero failures:
  ```bash
  for c in "pkg init" "pkg create" "pkg validate" "pkg pack" "pkg publish" "pkg build" \
    "source add" "source scan" "source update" "source list" "source remove" "source candidates" "source enable-defaults" \
    "config set" "config get" "config list" \
    "registry init" "registry add" "registry list" "registry remove" \
    "cache clean" "cache ls" "mcp serve"; do
    aam $c --help > /dev/null && echo "OK: aam $c" || echo "FAIL: aam $c"
  done
  ```
- [X] T065 [P] Run all 6 deprecated alias smoke tests — **acceptance: each prints deprecation warning AND shows help text** (exit code 0):
  ```bash
  for alias in create-package validate pack publish build update; do
    aam $alias --help 2>&1 | head -5 && echo "OK: aam $alias" || echo "FAIL: aam $alias"
  done
  ```
- [X] T066 Verify final file tree matches target layout:
  ```bash
  find apps/aam-cli/src/aam_cli/commands/ -name '*.py' | sort
  ```
  Confirm: `commands/__init__.py`, `commands/_deprecated.py`, 20 top-level command files, 7 group directories with correct subcommand files, no old filenames present

**Checkpoint**: All 8 phases complete. All success criteria met.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Docs)**: No dependencies — start immediately; MUST complete before source changes
- **Phase 2 (Rename)**: Depends on Phase 1 — foundation for all subsequent phases
- **Phase 3 (pkg/)**: Depends on Phase 2 (uses renamed `init.py` for cascading update T017)
- **Phase 4 (source/)**: Depends on Phase 2 — independent of Phase 3
- **Phase 5 (other groups)**: Depends on Phase 2 — can run after Phase 3 and 4 or in parallel with them
- **Phase 6 (main.py)**: Depends on Phase 3, 4, 5 — all groups must be directories first
- **Phase 7 (deprecated)**: Depends on Phase 6 — `main.py` must have clean imports first
- **Phase 8 (verification)**: Depends on all phases — final gate

### User Story Dependencies

- **US1 (Phase 2)**: Independent — can start immediately after docs
- **US2 (Phase 3)**: Depends on US1 (needs `commands/init.py` to exist for T017)
- **US3 (Phases 4+5)**: Can start after US1; independent of US2 (operates on different files)
- **US4 (Phase 6)**: Depends on US2 + US3 (needs groups-as-directories to already exist)
- **US5 (Phase 7)**: Depends on US4 (needs clean `main.py` imports)

### Within Each Phase

- `[P]` file extraction tasks can run in parallel (different output files)
- `__init__.py` creation must complete before the old file is deleted
- Test suite runs must follow all file changes in that phase

### Parallel Opportunities

```bash
# Phase 3 consolidations (T013-T016) — 4 pkg files, all independent:
Task: "Consolidate pkg/build.py"        # T013
Task: "Consolidate pkg/pack.py"         # T014
Task: "Consolidate pkg/publish.py"      # T015
Task: "Consolidate pkg/validate.py"     # T016

# Phase 4 source/ extractions (T022-T028) — 7 source subfiles, all independent:
Task: "Create source/add.py"            # T022
Task: "Create source/scan.py"           # T023
...

# Phase 5 group splits — 4 groups are independent of each other:
Task: "Split config/"    # T031-T035
Task: "Split registry/"  # T036-T041
Task: "Split cache/"     # T047-T050
Task: "Split mcp/"       # T051-T053
# Note: auth/ (T042-T046) must be done carefully — verify get_token() before deleting auth.py

# Phase 8 smoke tests (T063-T065) — all independent:
Task: "Top-level command smoke test"    # T063
Task: "Group subcommand smoke test"     # T064
Task: "Deprecated alias smoke test"     # T065
```

---

## Implementation Strategy

### MVP First (US1 only — Phase 2)

1. Complete Phase 1 (Docs) — ~1h
2. Complete Phase 2 (Rename 3 files) — ~30min
3. **STOP and VALIDATE**: `npx nx test aam-cli` passes, and
   `aam init/list/info --help` works
4. SC-001 is met: all filenames match CLI names

### Incremental Delivery (recommended)

1. Phase 1 → Docs updated (SC-VIII satisfied)
2. Phase 2 → US1 done, filenames match CLI names (SC-001)
3. Phase 3 → US2 done, no more duplicates (SC-002)
4. Phases 4+5 → US3 done, all groups are directories (SC-003, SC-007)
5. Phase 6 → US4 done, clean imports (SC-006)
6. Phase 7 → US5 done, aliases centralized (SC-005)
7. Phase 8 → All success criteria verified (SC-004, SC-008)

---

## Task Summary

| Phase | Tasks | User Story | Parallelizable |
|-------|-------|-----------|----------------|
| 1 — Documentation | T001–T003 | (pre-requisite) | T002, T003 [P] |
| 2 — Rename files | T004–T009 | US1 (P1) | none |
| 3 — Consolidate pkg/ | T010–T020 | US2 (P1) | T013–T016 [P] |
| 4 — Split source/ | T021–T030 | US3 (P2) | T022–T028 [P] |
| 5 — Split other groups | T031–T054 | US3 (P2) | T032–T034, T037–T040, T043–T045, T048–T049 [P] |
| 6 — Clean main.py | T055–T057 | US4 (P2) | none |
| 7 — Deprecated aliases | T058–T060 | US5 (P3) | none |
| 8 — Final verification | T061–T066 | (all stories) | T063–T065 [P] |
| **Total** | **66 tasks** | **5 stories** | **~20 parallel** |

---

## Notes

- `[P]` tasks modify different files — safe to run concurrently
- Each phase ends with `npx nx test aam-cli` — never proceed to next phase with failing tests. Within Phase 5, run the test suite once after all sub-phases (5a–5e) are complete (T054), not after each sub-phase individually
- `auth/` split (T042–T046) requires extra care: verify `get_token()` resolves BEFORE deleting `auth.py`
- `pkg/create.py` will be ~1053 lines after consolidation — this exceeds the 600-line limit but is pre-existing debt; flagged for future refactoring in a separate spec
- All function names stay the same throughout (`client_init`, `list_packages`, `show_package`, `pkg_create`, etc.) — only module paths change
- Use `git mv` for renames to preserve git history
