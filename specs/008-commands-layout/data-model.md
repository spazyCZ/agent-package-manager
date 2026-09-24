# Data Model: Restructure AAM CLI Commands Directory

**Branch**: `008-commands-layout` | **Date**: 2026-03-12

## Overview

This feature involves no database, API, or persistent data changes. The "data model" for this refactoring is the **directory layout** itself — the mapping between CLI command names and their source file locations.

---

## Entity: Command File Mapping

Every CLI command maps to exactly one source file. The table below defines the complete mapping after the restructure.

### Top-Level Commands (1 file = 1 command)

| CLI Command | Source File | Function Name |
|-------------|------------|---------------|
| `aam init` | `commands/init.py` | `client_init` |
| `aam install` | `commands/install.py` | `install` |
| `aam uninstall` | `commands/uninstall.py` | `uninstall` |
| `aam upgrade` | `commands/upgrade.py` | `upgrade` |
| `aam outdated` | `commands/outdated.py` | `outdated` |
| `aam search` | `commands/search.py` | `search` |
| `aam list` | `commands/list.py` | `list_packages` |
| `aam info` | `commands/info.py` | `show_package` |
| `aam verify` | `commands/verify.py` | `verify` |
| `aam diff` | `commands/diff.py` | `diff_cmd` |
| `aam tree` | `commands/tree.py` | `tree` |
| `aam why` | `commands/why.py` | `why` |
| `aam check` | `commands/check.py` | `check` |
| `aam audit` | `commands/audit.py` | `audit` |
| `aam dedupe` | `commands/dedupe.py` | `dedupe` |
| `aam prune` | `commands/prune.py` | `prune` |
| `aam test` | `commands/test.py` | `test` |
| `aam eval` | `commands/eval.py` | `eval_cmd` |
| `aam doctor` | `commands/doctor.py` | `doctor` |
| `aam convert` | `commands/convert.py` | `convert` |

### Command Groups (1 directory = 1 group)

#### `aam pkg` Group

| CLI Command | Source File | Function Name |
|-------------|------------|---------------|
| `aam pkg init` | `commands/pkg/init.py` | `pkg_init` |
| `aam pkg create` | `commands/pkg/create.py` | `pkg_create` |
| `aam pkg validate` | `commands/pkg/validate.py` | `pkg_validate` |
| `aam pkg pack` | `commands/pkg/pack.py` | `pkg_pack` |
| `aam pkg publish` | `commands/pkg/publish.py` | `pkg_publish` |
| `aam pkg build` | `commands/pkg/build.py` | `pkg_build` |

#### `aam source` Group

| CLI Command | Source File | Function Name |
|-------------|------------|---------------|
| `aam source add` | `commands/source/add.py` | `add` |
| `aam source scan` | `commands/source/scan.py` | `scan` |
| `aam source update` | `commands/source/update.py` | `update` |
| `aam source list` | `commands/source/list.py` | `list_cmd` |
| `aam source remove` | `commands/source/remove.py` | `remove` |
| `aam source candidates` | `commands/source/candidates.py` | `candidates` |
| `aam source enable-defaults` | `commands/source/enable_defaults.py` | `enable_defaults` |

#### `aam config` Group

| CLI Command | Source File | Function Name |
|-------------|------------|---------------|
| `aam config set` | `commands/config/set.py` | `config_set` |
| `aam config get` | `commands/config/get.py` | `config_get` |
| `aam config list` | `commands/config/list.py` | `config_list` |

#### `aam registry` Group

| CLI Command | Source File | Function Name |
|-------------|------------|---------------|
| `aam registry init` | `commands/registry/init.py` | `registry_init` |
| `aam registry add` | `commands/registry/add.py` | `registry_add` |
| `aam registry list` | `commands/registry/list.py` | `registry_list` |
| `aam registry remove` | `commands/registry/remove.py` | `registry_remove` |

#### `aam auth` Group (login/logout/whoami are registered as top-level)

| CLI Command | Source File | Function Name |
|-------------|------------|---------------|
| `aam login` | `commands/auth/login.py` | `login` |
| `aam logout` | `commands/auth/logout.py` | `logout` |
| `aam whoami` | `commands/auth/whoami.py` | `whoami` |

Helpers in `commands/auth/__init__.py`: `get_token()`, `AUTH_FILE`, `_load_auth()`, `_save_auth()`

#### `aam cache` Group

| CLI Command | Source File | Function Name |
|-------------|------------|---------------|
| `aam cache clean` | `commands/cache/clean.py` | `cache_clean` |
| `aam cache ls` | `commands/cache/ls.py` | `cache_ls` |

#### `aam mcp` Group

| CLI Command | Source File | Function Name |
|-------------|------------|---------------|
| `aam mcp serve` | `commands/mcp/serve.py` | `serve` |

### Deprecated Aliases

| CLI Alias | Delegates To | Source |
|-----------|-------------|--------|
| `aam create-package` | `aam pkg create` | `commands/_deprecated.py` |
| `aam validate` | `aam pkg validate` | `commands/_deprecated.py` |
| `aam pack` | `aam pkg pack` | `commands/_deprecated.py` |
| `aam publish` | `aam pkg publish` | `commands/_deprecated.py` |
| `aam build` | `aam pkg build` | `commands/_deprecated.py` |
| `aam update` | `aam upgrade` | `commands/_deprecated.py` |

---

## Public Interface Contracts

These import paths are used by code outside `commands/` and MUST continue to resolve after the restructure:

| Import Path | Used By | Resolves To |
|-------------|---------|-------------|
| `from aam_cli.commands.auth import get_token` | `aam_cli/registry/factory.py` | `commands/auth/__init__.py` |
| `from aam_cli.commands.auth import login, logout, whoami` | `aam_cli/main.py` | `commands/auth/__init__.py` (re-exports) |
| `from aam_cli.commands.source import source` | `aam_cli/main.py` | `commands/source/__init__.py` |
| `from aam_cli.commands.pkg import pkg` | `aam_cli/main.py` | `commands/pkg/__init__.py` |
| `from aam_cli.main import cli` | All `CliRunner`-based tests | `main.py` (unchanged) |
