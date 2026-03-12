# Plan: Restructure AAM CLI Commands Directory

## Context

The AAM CLI commands directory has accumulated structural debt: 6 duplicated command pairs (top-level files + `pkg/` wrappers), filenames that don't match CLI names, inline group definitions mixing 3-7 subcommands in single files, and inconsistent import patterns in `main.py`. This restructure normalizes the layout so every group is a directory, every filename matches its CLI name, and duplicated command pairs are consolidated.

**No business logic changes.** This is purely a file organization refactoring.

## Phase 1: Rename top-level files (filename → CLI name)

Three files have names that don't match their registered CLI command:

| Operation | File | CLI name |
|-----------|------|----------|
| Rename | `client_init.py` → `init.py` | `aam init` |
| Rename | `list_packages.py` → `list.py` | `aam list` |
| Rename | `show_package.py` → `info.py` | `aam info` |

**Import updates in `main.py`:**
- `from aam_cli.commands.client_init import client_init` → `from aam_cli.commands.init import client_init`
- `from aam_cli.commands.list_packages import list_packages` → `from aam_cli.commands.list import list_packages`
- `from aam_cli.commands.show_package import show_package` → `from aam_cli.commands.info import show_package`

Function names (`client_init`, `list_packages`, `show_package`) stay the same — they don't affect the CLI.

**Verify:** `pytest` + `aam init --help` + `aam list --help` + `aam info --help`

---

## Phase 2: Consolidate pkg/ (eliminate top-level duplicates)

Currently `pkg/*.py` files are thin wrappers that `ctx.invoke()` into top-level siblings. Invert this: move the full implementation INTO `pkg/*.py`, delete the top-level originals.

### For each of 6 pairs:

**2a. `pkg/create.py`** — Replace the `ctx.invoke(create_package, ...)` delegation with the full body from `create_package.py` (~1058 lines). Keep function name `pkg_create`, keep decorator `@click.command("create")`. Remove `from aam_cli.commands.create_package import create_package`.

**2b. `pkg/init.py`** — Already has `--migrate` logic (lines 69-92) that `init_package.py` lacks. Replace the `ctx.invoke(init_package, name=name)` call at line 97 with the inline body from `init_package.py`. Remove `from aam_cli.commands.init_package import init_package`.

**2c. `pkg/build.py`** — Replace wrapper with full body from `build.py`. Keep function `pkg_build`.

**2d. `pkg/pack.py`** — Replace wrapper with full body from `pack.py`. Keep function `pkg_pack`.

**2e. `pkg/publish.py`** — Replace wrapper with full body from `publish.py`. Keep function `pkg_publish`.

**2f. `pkg/validate.py`** — Replace wrapper with full body from `validate.py` (including `--permissions` flag). Keep function `pkg_validate`.

### Cascading updates:

- **`commands/init.py`** (renamed from `client_init.py`): Line 90 `from aam_cli.commands.init_package import init_package` → `from aam_cli.commands.pkg.init import pkg_init`. Line 92 `ctx.invoke(init_package, name=name)` → `ctx.invoke(pkg_init, name=name)`.
- **`pkg/__init__.py`**: No change needed — already imports `from aam_cli.commands.pkg.create import pkg_create` etc.
- **`tests/unit/test_unit_create_from_source.py`** line 22: `from aam_cli.commands.create_package import create_package` → `from aam_cli.commands.pkg.create import pkg_create` (+ update refs in file).
- **`main.py`**: Remove imports of `build`, `create_package`, `publish`, `pack`, `validate` (only used by deprecated aliases, which move in Phase 6).

### Delete top-level originals:
- `create_package.py`, `init_package.py`, `build.py`, `pack.py`, `publish.py`, `validate.py`

**Verify:** `pytest` + `aam pkg create --help` + `aam pkg init --help` + all 6 pkg subcommands

---

## Phase 3: Split `source.py` (717 lines) into `source/` directory

Follow the same registration pattern as `pkg/__init__.py` (explicit `add_command`).

### Create `commands/source/__init__.py`:
- Group definition `@click.group()` with console context setup (lines 36-48 of current `source.py`)
- Import and register 7 subcommands via `source.add_command(fn, "name")`

### Extract 7 subcommand files:
| File | Function | From lines (approx) |
|------|----------|---------------------|
| `source/add.py` | `add()` | 81-161 |
| `source/scan.py` | `scan()` | 170-253 |
| `source/update.py` | `update()` | 263-385 |
| `source/list.py` | `list_cmd()` → registered as `"list"` | 395-466 |
| `source/remove.py` | `remove()` | 476-513 |
| `source/candidates.py` | `candidates()` | 523-599 |
| `source/enable_defaults.py` | `enable_defaults()` → registered as `"enable-defaults"` | 609-717 |

Each file: change `@source.command()` → `@click.command()`, bring needed imports (services, Rich, etc).

**`main.py`**: `from aam_cli.commands.source import source` — unchanged (now resolves to `source/__init__.py`).

**Delete:** `commands/source.py`

**Verify:** `aam source --help` + each subcommand

---

## Phase 4: Split remaining inline groups

### 4a. `config.py` (215 lines) → `config/`
- `config/__init__.py`: Group definition, register 3 subcommands
- `config/set.py`: `config_set()` (lines 51-106)
- `config/get.py`: `config_get()` (lines 115-154)
- `config/list.py`: `config_list()` (lines 164-214)

`main.py`: `from aam_cli.commands import config` → `from aam_cli.commands.config import config`. Registration changes from `cli.add_command(config.config)` → `cli.add_command(config)`.

### 4b. `registry.py` (281 lines) → `registry/`
- `registry/__init__.py`: Group, register 4 subcommands
- `registry/init.py`, `registry/add.py`, `registry/list.py`, `registry/remove.py`

No naming collision — `aam_cli.commands.registry` is separate from `aam_cli.registry`.

`main.py`: Same pattern as config. `cli.add_command(registry.registry)` → `cli.add_command(registry)`.

### 4c. `auth.py` (153 lines) → `auth/`

Special case: exports `get_token()` used by `aam_cli/registry/factory.py` line 57.

- `auth/__init__.py`: Contains `AUTH_FILE`, `_load_auth()`, `_save_auth()`, `get_token()` (helpers). Re-exports `login`, `logout`, `whoami` from subfiles.
- `auth/login.py`: `login()` command, imports helpers from `aam_cli.commands.auth`
- `auth/logout.py`: `logout()` command
- `auth/whoami.py`: `whoami()` command

This preserves `from aam_cli.commands.auth import get_token` (factory.py) and `from aam_cli.commands.auth import login, logout, whoami` (main.py) unchanged.

### 4d. `cache.py` (94 lines) → `cache/`
- `cache/__init__.py`: Group, register 2 subcommands
- `cache/clean.py`: `cache_clean()` (lines 42-66)
- `cache/ls.py`: `cache_ls()` (lines 69-93)

### 4e. `mcp_serve.py` (215 lines) → `mcp/`
- `mcp/__init__.py`: Group definition (`mcp`)
- `mcp/serve.py`: `_configure_logging()` helper + `serve()` command. Change `@mcp.command("serve")` → `@click.command("serve")`.

`main.py`: `from aam_cli.commands.mcp_serve import mcp` → `from aam_cli.commands.mcp import mcp`.

**Delete originals:** `config.py`, `registry.py`, `auth.py`, `cache.py`, `mcp_serve.py`

**Verify:** `pytest` + `--help` for each group

---

## Phase 5: Clean up `main.py` imports

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

Also update registrations: `cli.add_command(install.install)` → `cli.add_command(install)`, `cli.add_command(search.search)` → `cli.add_command(search)`, `cli.add_command(config.config)` → `cli.add_command(config)`, `cli.add_command(registry.registry)` → `cli.add_command(registry)`.

---

## Phase 6: Extract deprecated aliases into `_deprecated.py`

Move all deprecated alias definitions from `main.py` lines 279-365 into `commands/_deprecated.py`.

Create `register_deprecated_aliases(cli)` function containing all 6 aliases (create-package, validate, pack, publish, build, update). Use lazy imports inside each function to avoid circular deps:
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

---

## Phase 7: Final verification

1. **Orphan import scan**: grep for all old module paths (`client_init`, `list_packages`, `show_package`, `create_package`, `init_package`, `mcp_serve`, top-level `build`/`pack`/`publish`/`validate`)
2. **Full test suite**: `pytest apps/aam-cli/tests/`
3. **CLI smoke test**: `aam --help` (verify all sections render), every command `--help`
4. **Deprecated aliases**: `aam create-package --help`, `aam validate --help`, `aam pack --help`, `aam publish --help`, `aam build --help`, `aam update --help`
5. **File tree**: verify against target layout

---

## Files Summary

### Files to create (new):
- `commands/init.py` (content from `client_init.py`)
- `commands/list.py` (content from `list_packages.py`)
- `commands/info.py` (content from `show_package.py`)
- `commands/source/__init__.py`, `add.py`, `scan.py`, `update.py`, `list.py`, `remove.py`, `candidates.py`, `enable_defaults.py`
- `commands/config/__init__.py`, `set.py`, `get.py`, `list.py`
- `commands/registry/__init__.py`, `init.py`, `add.py`, `list.py`, `remove.py`
- `commands/auth/__init__.py`, `login.py`, `logout.py`, `whoami.py`
- `commands/cache/__init__.py`, `clean.py`, `ls.py`
- `commands/mcp/__init__.py`, `serve.py`
- `commands/_deprecated.py`

### Files to modify:
- `commands/pkg/create.py` (replace wrapper with full implementation from `create_package.py`)
- `commands/pkg/init.py` (inline `init_package.py` body, keep `--migrate`)
- `commands/pkg/build.py` (replace wrapper with full implementation from `build.py`)
- `commands/pkg/pack.py` (replace wrapper with full implementation from `pack.py`)
- `commands/pkg/publish.py` (replace wrapper with full implementation from `publish.py`)
- `commands/pkg/validate.py` (replace wrapper with full implementation from `validate.py`)
- `main.py` (rewrite imports, update registrations, remove deprecated alias block)
- `tests/unit/test_unit_create_from_source.py` (update import path)

### Files to delete:
- `client_init.py`, `list_packages.py`, `show_package.py`
- `create_package.py`, `init_package.py`, `build.py`, `pack.py`, `publish.py`, `validate.py`
- `source.py`, `config.py`, `registry.py`, `auth.py`, `cache.py`, `mcp_serve.py`

### External refs preserved (no change needed):
- `registry/factory.py` line 57: `from aam_cli.commands.auth import get_token` — resolves to `auth/__init__.py`
- `tests/unit/test_commands_search.py`: imports from `search.py` — unchanged
- All `CliRunner`-based tests using `from aam_cli.main import cli` — unchanged
