# Quickstart: Verifying the Commands Layout Restructure

**Branch**: `008-commands-layout` | **Date**: 2026-03-12

## Prerequisites

- Python 3.11+
- AAM CLI installed in development mode (`pip install -e apps/aam-cli`)
- Nx workspace set up (`npm install` at repo root)

## Phase-by-Phase Verification

### After Phase 0 (Documentation)

```bash
# Review docs changes
git diff docs/DESIGN.md
```

Confirm section 11.1 "Module Structure" shows the new target layout.

### After Phase 1 (Rename)

```bash
# Verify renamed files exist
ls apps/aam-cli/src/aam_cli/commands/init.py
ls apps/aam-cli/src/aam_cli/commands/list.py
ls apps/aam-cli/src/aam_cli/commands/info.py

# Verify old files are gone
! ls apps/aam-cli/src/aam_cli/commands/client_init.py 2>/dev/null
! ls apps/aam-cli/src/aam_cli/commands/list_packages.py 2>/dev/null
! ls apps/aam-cli/src/aam_cli/commands/show_package.py 2>/dev/null

# CLI smoke test
aam init --help
aam list --help
aam info --help

# Full test suite
npx nx test aam-cli
```

### After Phase 2 (Consolidate pkg/)

```bash
# Verify top-level originals are gone
for f in create_package init_package build pack publish validate; do
  ! ls "apps/aam-cli/src/aam_cli/commands/${f}.py" 2>/dev/null && echo "OK: ${f}.py deleted"
done

# Verify pkg/ subcommands work
aam pkg init --help
aam pkg create --help
aam pkg validate --help
aam pkg pack --help
aam pkg publish --help
aam pkg build --help

# Full test suite
npx nx test aam-cli
```

### After Phase 3 (Split source/)

```bash
# Verify source directory exists with 8 files
ls apps/aam-cli/src/aam_cli/commands/source/
# Expected: __init__.py add.py scan.py update.py list.py remove.py candidates.py enable_defaults.py

# Verify original is gone
! ls apps/aam-cli/src/aam_cli/commands/source.py 2>/dev/null

# CLI smoke test
aam source --help
aam source add --help
aam source scan --help
aam source update --help
aam source list --help
aam source remove --help
aam source candidates --help
aam source enable-defaults --help
```

### After Phase 4 (Split remaining groups)

```bash
# Verify all group directories exist
for group in config registry auth cache mcp; do
  ls "apps/aam-cli/src/aam_cli/commands/${group}/__init__.py" && echo "OK: ${group}/"
done

# Verify originals are gone
for f in config registry auth cache mcp_serve; do
  ! ls "apps/aam-cli/src/aam_cli/commands/${f}.py" 2>/dev/null && echo "OK: ${f}.py deleted"
done

# Verify auth public interface
python -c "from aam_cli.commands.auth import get_token; print('OK: get_token accessible')"

# Full test suite
npx nx test aam-cli
```

### After Phase 5 (Clean main.py imports)

```bash
# Full CLI help — all sections should render
aam --help

# Verify no old-style imports remain
rg 'from aam_cli\.commands import (build|create_package|publish|pack|validate)' apps/aam-cli/src/
# Expected: no matches (or only in _deprecated.py with lazy imports)
```

### After Phase 6 (Deprecated aliases)

```bash
# Verify _deprecated.py exists
ls apps/aam-cli/src/aam_cli/commands/_deprecated.py

# Test all deprecated aliases
aam create-package --help
aam validate --help
aam pack --help
aam publish --help
aam build --help
aam update --help
```

### After Phase 7 (Final verification)

```bash
# Orphan import scan — should find NO matches
rg 'aam_cli\.commands\.(client_init|list_packages|show_package|create_package|init_package|mcp_serve)' apps/aam-cli/

# Full test suite
npx nx test aam-cli -v

# Final CLI smoke test — every command --help
aam --help
for cmd in init install uninstall upgrade outdated search list info verify diff tree why check audit dedupe prune test eval doctor convert; do
  aam $cmd --help > /dev/null && echo "OK: aam $cmd"
done

for group_cmd in "pkg init" "pkg create" "pkg validate" "pkg pack" "pkg publish" "pkg build" \
  "source add" "source scan" "source update" "source list" "source remove" "source candidates" "source enable-defaults" \
  "config set" "config get" "config list" \
  "registry init" "registry add" "registry list" "registry remove" \
  "cache clean" "cache ls" \
  "mcp serve"; do
  aam $group_cmd --help > /dev/null && echo "OK: aam $group_cmd"
done

# Verify target file tree
find apps/aam-cli/src/aam_cli/commands/ -name '*.py' | sort
```

## Expected Final File Count

- **Top-level command files**: 20 (init, install, uninstall, upgrade, outdated, search, list, info, verify, diff, tree, why, check, audit, dedupe, prune, test, eval, doctor, convert)
- **Utility files**: 2 (`__init__.py`, `_deprecated.py`)
- **Group packages**: 7 directories (pkg, source, config, registry, auth, cache, mcp) with 31 total files
- **Grand total**: ~53 `.py` files (down from ~40 in `commands/` + duplicates)
