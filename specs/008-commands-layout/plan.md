# Implementation Plan: Restructure AAM CLI Commands Directory

**Branch**: `008-commands-layout` | **Date**: 2026-03-12 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/008-commands-layout/spec.md`  
**Reference**: Implementation details from `/specs/008a-commands-layout-improvements-archive/init.md`

## Summary

Restructure the AAM CLI `commands/` directory so every command group is a directory, every filename matches its CLI name, and duplicated command pairs are consolidated. This is purely a file-organization refactoring — zero business logic changes. The plan is structured as 8 sequential phases, each independently verifiable with `npx nx test aam-cli` and CLI `--help` smoke tests. User documentation and test import paths are updated as part of each phase.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Click 8.1+ (CLI framework), Rich 13.0+ (terminal UI)  
**Storage**: N/A (no data changes)  
**Testing**: `npx nx test aam-cli` (existing suite at `apps/aam-cli/tests/`, executed via Nx)  
**Target Platform**: Linux / macOS / Windows (CLI tool)  
**Project Type**: Monorepo app (`apps/aam-cli/`)  
**Performance Goals**: N/A (no runtime behavior changes)  
**Constraints**: Zero behavioral regressions; all existing tests must pass; all deprecated aliases must continue working  
**Scale/Scope**: ~40 files in `commands/`, ~58 test files, 1 `main.py` entry point, user docs in `docs/USER_GUIDE.md` and `docs/user_docs/`

## Constitution Check

*GATE: Must pass before implementation begins. Re-check after artifact updates.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Local-First Architecture | PASS | No network changes; file reorganization only |
| II. Platform Adapter Abstraction | PASS | No adapter code touched |
| III. Strict Code Quality & Observability | PASS (with exception) | All moved files retain logging, docstrings, type hints, 80-char section headers. Exception: `pkg/create.py` (~1053 lines) exceeds max 600 lines — this is pre-existing debt from `create_package.py`, not introduced by this refactoring. Follow-up spec required. |
| IV. Test-Driven Quality | PASS | Test imports updated; no test removals; all tests must pass per-phase |
| V. Security by Default (ASVS L2) | PASS | No security-sensitive code changes |
| VI. Monorepo Discipline (Nx) | PASS | Stays within `apps/aam-cli/`; Nx project config unchanged; test execution uses `npx nx test aam-cli` |
| VII. No Defensive Fallbacks | PASS | No fallback logic introduced |
| VIII. Documentation Alignment (MkDocs) | PASS | User docs updated to reflect new layout; `mkdocs.yml` nav unchanged (CLI names unchanged) |

**Gate result**: ALL PASS — proceed to implementation.

## Project Structure

### Documentation (this feature)

```text
specs/008-commands-layout/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Supporting research artifact
├── data-model.md        # Supporting directory layout model
├── quickstart.md        # Supporting verification guide
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code — Target Layout (after all phases)

```text
apps/aam-cli/src/aam_cli/
├── main.py                          # Entry point (cleaned imports)
└── commands/
    ├── __init__.py
    ├── _deprecated.py               # NEW: register_deprecated_aliases(cli)
    │
    │  ── Top-level commands (1 file = 1 command) ──
    ├── init.py                      # RENAMED from client_init.py
    ├── install.py
    ├── uninstall.py
    ├── upgrade.py
    ├── outdated.py
    ├── search.py
    ├── list.py                      # RENAMED from list_packages.py
    ├── info.py                      # RENAMED from show_package.py
    ├── verify.py
    ├── diff.py
    ├── tree.py
    ├── why.py
    ├── check.py
    ├── audit.py
    ├── dedupe.py
    ├── prune.py
    ├── test.py
    ├── eval.py
    ├── doctor.py
    ├── convert.py
    │
    │  ── Command groups (1 directory = 1 group) ──
    ├── pkg/
    │   ├── __init__.py              # Group def + add_command registration
    │   ├── init.py                  # CONSOLIDATED (full body, no ctx.invoke wrapper)
    │   ├── create.py                # CONSOLIDATED
    │   ├── validate.py              # CONSOLIDATED
    │   ├── pack.py                  # CONSOLIDATED
    │   ├── publish.py               # CONSOLIDATED
    │   └── build.py                 # CONSOLIDATED
    │
    ├── source/
    │   ├── __init__.py              # NEW: group def + 7 subcommand registrations
    │   ├── add.py                   # EXTRACTED from source.py
    │   ├── scan.py                  # EXTRACTED
    │   ├── update.py                # EXTRACTED
    │   ├── list.py                  # EXTRACTED
    │   ├── remove.py                # EXTRACTED
    │   ├── candidates.py            # EXTRACTED
    │   └── enable_defaults.py       # EXTRACTED
    │
    ├── config/
    │   ├── __init__.py              # NEW: group def + 3 subcommand registrations
    │   ├── set.py                   # EXTRACTED from config.py
    │   ├── get.py                   # EXTRACTED
    │   └── list.py                  # EXTRACTED
    │
    ├── registry/
    │   ├── __init__.py              # NEW: group def + 4 subcommand registrations
    │   ├── init.py                  # EXTRACTED from registry.py
    │   ├── add.py                   # EXTRACTED
    │   ├── list.py                  # EXTRACTED
    │   └── remove.py                # EXTRACTED
    │
    ├── auth/
    │   ├── __init__.py              # NEW: helpers (get_token, _load_auth, etc.) + re-exports
    │   ├── login.py                 # EXTRACTED from auth.py
    │   ├── logout.py                # EXTRACTED
    │   └── whoami.py                # EXTRACTED
    │
    ├── cache/
    │   ├── __init__.py              # NEW: group def + 2 subcommand registrations
    │   ├── clean.py                 # EXTRACTED from cache.py
    │   └── ls.py                    # EXTRACTED
    │
    └── mcp/
        ├── __init__.py              # NEW: group def
        └── serve.py                 # EXTRACTED from mcp_serve.py
```

### Files Deleted (after all phases)

```text
commands/client_init.py              # Phase 2: renamed to init.py
commands/list_packages.py            # Phase 2: renamed to list.py
commands/show_package.py             # Phase 2: renamed to info.py
commands/create_package.py           # Phase 3: consolidated into pkg/create.py
commands/init_package.py             # Phase 3: consolidated into pkg/init.py
commands/build.py                    # Phase 3: consolidated into pkg/build.py
commands/pack.py                     # Phase 3: consolidated into pkg/pack.py
commands/publish.py                  # Phase 3: consolidated into pkg/publish.py
commands/validate.py                 # Phase 3: consolidated into pkg/validate.py
commands/source.py                   # Phase 4: split into source/
commands/config.py                   # Phase 5a: split into config/
commands/registry.py                 # Phase 5b: split into registry/
commands/auth.py                     # Phase 5c: split into auth/
commands/cache.py                    # Phase 5d: split into cache/
commands/mcp_serve.py                # Phase 5e: split into mcp/
```

**Structure Decision**: Existing Nx monorepo structure preserved. Changes scoped entirely to `apps/aam-cli/src/aam_cli/commands/`, `apps/aam-cli/src/aam_cli/main.py`, `apps/aam-cli/tests/`, and `docs/`.

---

## Implementation Phases

### Phase 1: Update User Documentation (FIRST)

Per the user's request and Constitution VIII (Documentation Alignment), update user-facing documentation **before** touching source code so the target layout is documented and reviewable.

**Tasks:**

1. **Update `docs/DESIGN.md`** — Section 11.1 "Module Structure": replace the conceptual `aam/cli/` tree with the actual target layout shown above. Add a note explaining the convention: "every group is a directory, every filename matches its CLI name."

2. **Update `docs/USER_GUIDE.md`** — Any section referencing the internal commands structure should reflect the new layout. The CLI command names themselves do NOT change, so the user-facing command reference stays the same. Update any "developer/contributor" sections that reference file paths.

3. **`docs/user_docs/mkdocs.yml`** — No changes needed. The MkDocs nav references CLI command names (e.g., `aam source add`), not file paths. Since no CLI names change, the nav is stable.

**Verify**: Review docs diff for accuracy.

---

### Phase 2: Rename Top-Level Files (filename → CLI name)

Three files have names that don't match their registered CLI command.

| Operation | Old File | New File | CLI name |
|-----------|----------|----------|----------|
| Rename | `client_init.py` | `init.py` | `aam init` |
| Rename | `list_packages.py` | `list.py` | `aam list` |
| Rename | `show_package.py` | `info.py` | `aam info` |

**Import updates in `main.py`:**
- `from aam_cli.commands.client_init import client_init` → `from aam_cli.commands.init import client_init`
- `from aam_cli.commands.list_packages import list_packages` → `from aam_cli.commands.list import list_packages`
- `from aam_cli.commands.show_package import show_package` → `from aam_cli.commands.info import show_package`

Function names (`client_init`, `list_packages`, `show_package`) stay the same.

**Test updates:**
- `tests/unit/test_unit_client_init.py`: Check if it imports from `aam_cli.commands.client_init` — update to `aam_cli.commands.init`

**Verify:** `npx nx test aam-cli` + `aam init --help` + `aam list --help` + `aam info --help`

---

### Phase 3: Consolidate pkg/ (eliminate top-level duplicates)

Currently `pkg/*.py` files are thin wrappers that `ctx.invoke()` into top-level siblings. Invert this: move the full implementation INTO `pkg/*.py`, delete the top-level originals.

**For each of the 6 pairs:**

| pkg/ file | Top-level original | Notes |
|-----------|-------------------|-------|
| `pkg/create.py` | `create_package.py` (~1058 lines) | Replace `ctx.invoke(create_package)` with full body |
| `pkg/init.py` | `init_package.py` (~183 lines) | Already has `--migrate` logic; inline `init_package` body |
| `pkg/build.py` | `build.py` (~96 lines) | Replace wrapper with full body |
| `pkg/pack.py` | `pack.py` (~161 lines) | Replace wrapper with full body |
| `pkg/publish.py` | `publish.py` (~150 lines) | Replace wrapper with full body |
| `pkg/validate.py` | `validate.py` (~165 lines) | Replace wrapper with full body (including `--permissions`) |

**Cascading updates:**
- `commands/init.py` (renamed from `client_init.py`): Change `from aam_cli.commands.init_package import init_package` → `from aam_cli.commands.pkg.init import pkg_init` and update `ctx.invoke(init_package, name=name)` → `ctx.invoke(pkg_init, name=name)`
- `pkg/__init__.py`: No change needed (already imports from `pkg.*`)
- `tests/unit/test_unit_create_from_source.py` line 22: `from aam_cli.commands.create_package import create_package` → `from aam_cli.commands.pkg.create import pkg_create` (+ update all refs in file)
- `main.py`: Remove imports of `build`, `create_package`, `publish`, `pack`, `validate` modules (deprecated aliases move to Phase 7)

**Delete top-level originals:** `create_package.py`, `init_package.py`, `build.py`, `pack.py`, `publish.py`, `validate.py`

**Verify:** `npx nx test aam-cli` + `aam pkg create --help` + all 6 pkg subcommands

---

### Phase 4: Split `source.py` (716 lines) into `source/` directory

Follow the same registration pattern as `pkg/__init__.py` (explicit `add_command`).

**Create `commands/source/__init__.py`:**
- Group definition `@click.group()` with console context setup (lines 36-48 of current `source.py`)
- Import and register 7 subcommands via `source.add_command(fn, "name")`

**Extract 7 subcommand files:**

| File | Function | Registered as | From lines (approx) |
|------|----------|---------------|---------------------|
| `source/add.py` | `add()` | `"add"` | 81-161 |
| `source/scan.py` | `scan()` | `"scan"` | 170-253 |
| `source/update.py` | `update()` | `"update"` | 263-385 |
| `source/list.py` | `list_cmd()` | `"list"` | 395-466 |
| `source/remove.py` | `remove()` | `"remove"` | 476-513 |
| `source/candidates.py` | `candidates()` | `"candidates"` | 523-599 |
| `source/enable_defaults.py` | `enable_defaults()` | `"enable-defaults"` | 609-716 |

Each file: change `@source.command()` → `@click.command()`, bring needed imports.

**`main.py`**: `from aam_cli.commands.source import source` — unchanged (now resolves to `source/__init__.py`).

**Delete:** `commands/source.py`

**Verify:** `aam source --help` + each subcommand `--help`

---

### Phase 5: Split Remaining Inline Groups

#### 5a. `config.py` (214 lines) → `config/`

- `config/__init__.py`: Group definition, register 3 subcommands
- `config/set.py`: `config_set()` (lines 51-106)
- `config/get.py`: `config_get()` (lines 115-154)
- `config/list.py`: `config_list()` (lines 164-214)

**`main.py`**: `from aam_cli.commands import config` → `from aam_cli.commands.config import config`. Registration: `cli.add_command(config.config)` → `cli.add_command(config)`.

#### 5b. `registry.py` (280 lines) → `registry/`

- `registry/__init__.py`: Group, register 4 subcommands
- `registry/init.py`, `registry/add.py`, `registry/list.py`, `registry/remove.py`

No naming collision — `aam_cli.commands.registry` is separate from `aam_cli.registry`.

**`main.py`**: `cli.add_command(registry.registry)` → `cli.add_command(registry)`.

#### 5c. `auth.py` (152 lines) → `auth/`

Special case: exports `get_token()` used by `aam_cli/registry/factory.py` line 57.

- `auth/__init__.py`: Contains `AUTH_FILE`, `_load_auth()`,
  `_save_auth()`, and `get_token()` shared helpers. Re-exports `login`,
  `logout`, and `whoami` from subfiles. This is a package split for
  top-level auth commands, not a new `aam auth` CLI group.
- `auth/login.py`: `login()` command
- `auth/logout.py`: `logout()` command
- `auth/whoami.py`: `whoami()` command

This preserves `from aam_cli.commands.auth import get_token` (used by `factory.py`) and `from aam_cli.commands.auth import login, logout, whoami` (used by `main.py`) unchanged.

#### 5d. `cache.py` (93 lines) → `cache/`

- `cache/__init__.py`: Group, register 2 subcommands
- `cache/clean.py`: `cache_clean()` (lines 42-66)
- `cache/ls.py`: `cache_ls()` (lines 69-93)

#### 5e. `mcp_serve.py` (214 lines) → `mcp/`

- `mcp/__init__.py`: Group definition (`mcp`)
- `mcp/serve.py`: `_configure_logging()` helper + `serve()` command

**`main.py`**: `from aam_cli.commands.mcp_serve import mcp` → `from aam_cli.commands.mcp import mcp`.

**Delete originals:** `config.py`, `registry.py`, `auth.py`, `cache.py`, `mcp_serve.py`

**Verify:** `npx nx test aam-cli` + `--help` for each group

---

### Phase 6: Clean Up `main.py` Imports

Replace the mixed import block (lines 142-176) with a clean, uniform style:

```python
# Groups (from package __init__)
from aam_cli.commands.pkg import pkg
from aam_cli.commands.source import source
from aam_cli.commands.config import config
from aam_cli.commands.registry import registry
from aam_cli.commands.auth import login, logout, whoami
from aam_cli.commands.cache import cache
from aam_cli.commands.mcp import mcp

# Top-level commands (direct function imports)
from aam_cli.commands.init import client_init
from aam_cli.commands.install import install
from aam_cli.commands.uninstall import uninstall
from aam_cli.commands.upgrade import upgrade
from aam_cli.commands.outdated import outdated
from aam_cli.commands.search import search
from aam_cli.commands.list import list_packages
from aam_cli.commands.info import show_package
from aam_cli.commands.verify import verify
from aam_cli.commands.diff import diff_cmd
from aam_cli.commands.tree import tree
from aam_cli.commands.why import why
from aam_cli.commands.check import check
from aam_cli.commands.audit import audit
from aam_cli.commands.dedupe import dedupe
from aam_cli.commands.prune import prune
from aam_cli.commands.test import test
from aam_cli.commands.eval import eval_cmd
from aam_cli.commands.doctor import doctor
from aam_cli.commands.convert import convert
```

Also update registrations:
- `cli.add_command(install.install)` → `cli.add_command(install)`
- `cli.add_command(search.search)` → `cli.add_command(search)`
- `cli.add_command(config.config)` → `cli.add_command(config)`
- `cli.add_command(registry.registry)` → `cli.add_command(registry)`

**Verify:** `aam --help` (verify all sections render)

---

### Phase 7: Extract Deprecated Aliases into `_deprecated.py`

Move all deprecated alias definitions from `main.py` lines 279-365 into `commands/_deprecated.py`.

Create `register_deprecated_aliases(cli)` function containing all 6 aliases (`create-package`, `validate`, `pack`, `publish`, `build`, `update`). Use lazy imports inside each function to avoid circular deps:

```python
def register_deprecated_aliases(cli):
    @cli.command("create-package", hidden=True)
    # ... decorators ...
    def deprecated_create_package(ctx, /, **kwargs):
        print_deprecation_warning("aam create-package", "aam pkg create")
        from aam_cli.commands.pkg.create import pkg_create
        ctx.invoke(pkg_create, **kwargs)
    # ... etc for all 6 ...
```

In `main.py`, replace the alias block with:

```python
from aam_cli.commands._deprecated import register_deprecated_aliases
register_deprecated_aliases(cli)
```

**Verify:** `aam create-package --help` + all 6 deprecated aliases

---

### Phase 8: Final Verification & Test Cleanup

1. **Orphan import scan**: grep for all old module paths (`client_init`, `list_packages`, `show_package`, `create_package`, `init_package`, `mcp_serve`, top-level `build`/`pack`/`publish`/`validate`)
2. **Update test imports**: Ensure all test files use updated import paths.
   Specifically:
   - `tests/unit/test_unit_create_from_source.py`: update `from aam_cli.commands.create_package import create_package` → `from aam_cli.commands.pkg.create import pkg_create`
   - `tests/unit/test_unit_client_init.py`: verify imports reference `aam_cli.commands.init`
   - All `CliRunner`-based tests using `from aam_cli.main import cli` — verify these still work (no changes needed since they import from `main`)
3. **Full test suite**: `npx nx test aam-cli`
4. **CLI smoke test**: `aam --help` (verify all sections render), every command `--help`
5. **Deprecated aliases**: `aam create-package --help`, `aam validate --help`, `aam pack --help`, `aam publish --help`, `aam build --help`, `aam update --help`
6. **File tree**: verify against target layout above

---

## Test Impact Analysis

### Tests Requiring Import Path Updates

| Test File | Current Import | New Import |
|-----------|---------------|------------|
| `test_unit_create_from_source.py` | `from aam_cli.commands.create_package import create_package` | `from aam_cli.commands.pkg.create import pkg_create` |
| `test_unit_client_init.py` | May import from `aam_cli.commands.client_init` | `from aam_cli.commands.init import ...` |

### Tests Requiring NO Changes

All `CliRunner`-based tests that import `from aam_cli.main import cli` are unaffected — they test via the CLI interface, not direct module imports.

| Test File | Why No Change Needed |
|-----------|---------------------|
| `test_commands_search.py` | Imports from `search.py` — unchanged |
| `test_main.py` | Imports from `main.py` — unchanged |
| All `test_unit_*.py` using `CliRunner` | Tests CLI behavior, not module paths |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Missed import reference in test | Medium | Low | Phase 8 orphan import scan |
| `auth/__init__.py` missing re-export | Low | High | Explicit test: `from aam_cli.commands.auth import get_token` |
| Circular import in `_deprecated.py` | Low | Medium | Lazy imports inside each alias function |
| `source.py` split loses shared state | Low | Medium | Console/service setup in `__init__.py`, passed to subcommands |
| `pkg/create.py` exceeds 600-line limit | High | Low | Already ~1053 lines; accept as-is since init.md says "keep full body" — flag for future refactoring |

## Complexity Tracking

> No unresolved constitution blockers remain. The approved `pkg/create.py`
> size exception is documented and requires a follow-up spec.

| Item | Notes |
|------|-------|
| `pkg/create.py` at ~1053 lines | Exceeds 600-line principle III limit. This is pre-existing debt from `create_package.py`. Consolidation does not worsen it. Flag for future refactoring in a separate spec. |
