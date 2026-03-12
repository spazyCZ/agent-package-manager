# Research: Restructure AAM CLI Commands Directory

**Branch**: `008-commands-layout` | **Date**: 2026-03-12

## Summary

This is a pure file-organization refactoring. No NEEDS CLARIFICATION items existed in the Technical Context. Research focused on confirming the approach for three areas: Click group directory patterns, import preservation for public interfaces, and test impact analysis.

---

## R1: Click Group-as-Directory Pattern

**Decision**: Use explicit `add_command()` registration in `__init__.py`, matching the existing `pkg/__init__.py` pattern.

**Rationale**: The `pkg/` group already demonstrates this pattern with 70 lines of clean, working code. Using the same pattern across all groups ensures consistency and avoids introducing new conventions.

**Alternatives considered**:

| Alternative | Rejected Because |
|-------------|-----------------|
| Auto-discovery via `importlib` | Adds complexity; implicit registration makes it harder to audit which subcommands are registered |
| `@group.command()` decorators in subfiles | Requires importing the group object into each subfile, creating tight coupling and potential circular imports |
| Lazy loading via `click-lazy-group` | External dependency; not worth adding for a CLI that loads quickly |

**Reference**: Current working pattern in `apps/aam-cli/src/aam_cli/commands/pkg/__init__.py` (70 lines).

---

## R2: Preserving `auth.get_token()` Public Interface

**Decision**: Keep `get_token()`, `AUTH_FILE`, `_load_auth()`, and `_save_auth()` in `auth/__init__.py`. Command functions (`login`, `logout`, `whoami`) are imported from subfiles and re-exported.

**Rationale**: `aam_cli/registry/factory.py` line 57 imports `from aam_cli.commands.auth import get_token`. This import path must continue to resolve. Placing helpers in `__init__.py` preserves the path without requiring changes to `factory.py`.

**Alternatives considered**:

| Alternative | Rejected Because |
|-------------|-----------------|
| Move `get_token()` to a separate `auth/helpers.py` | Requires updating `factory.py` import path — unnecessary churn for an internal helper |
| Re-export from `auth/__init__.py` after moving to subfile | Adds indirection for no benefit; `get_token` is a 5-line function |

---

## R3: Test Import Impact Analysis

**Decision**: Only 1 test file requires import path changes. All `CliRunner`-based tests are unaffected.

**Rationale**: Comprehensive grep across `apps/aam-cli/tests/` found:
- `test_unit_create_from_source.py` line 22: directly imports `from aam_cli.commands.create_package import create_package`
- `test_unit_client_init.py`: name suggests it may reference `client_init` module — needs verification at implementation time
- All other test files either import from `aam_cli.main` (entry point) or from service/model modules — not from command files being moved

**Scan results**:

```
Matched: aam_cli.commands.create_package  →  test_unit_create_from_source.py:22
No match: aam_cli.commands.client_init    →  (not found in tests)
No match: aam_cli.commands.list_packages  →  (not found in tests)
No match: aam_cli.commands.show_package   →  (not found in tests)
No match: aam_cli.commands.init_package   →  (not found in tests)
No match: aam_cli.commands.mcp_serve      →  (not found in tests)
No match: aam_cli.commands.build import   →  (not found in tests)
No match: aam_cli.commands.pack import    →  (not found in tests)
No match: aam_cli.commands.publish import →  (not found in tests)
No match: aam_cli.commands.validate import→  (not found in tests)
```

---

## R4: `pkg/create.py` Size Concern

**Decision**: Accept the ~1053-line file as-is during this refactoring. Flag for a future separate spec to break it down.

**Rationale**: Constitution III mandates ≤600 lines per file. However, `create_package.py` is already 1058 lines. This refactoring consolidates it into `pkg/create.py` without adding lines. Breaking up the file's internal structure is out of scope for a file-organization refactoring and risks introducing behavioral regressions.

**Follow-up**: Create a separate spec to refactor `pkg/create.py` into smaller modules (e.g., `pkg/create/` with `from_source.py`, `from_project.py`, `interactive.py`).

---

## R5: Documentation Update Scope

**Decision**: Update `docs/DESIGN.md` section 11.1 "Module Structure" and any contributor-facing references to file paths. The user-facing command reference in `docs/USER_GUIDE.md` and `mkdocs.yml` nav require no changes because CLI command names are unchanged.

**Rationale**: The MkDocs nav (`docs/user_docs/mkdocs.yml`) references CLI command names like `aam source add`, not file paths. Since no CLI names change, the nav and all per-command doc pages remain valid. Only the internal "developer/contributor" sections that reference source file paths need updating.

**Scope**:

| Document | Change Needed | Reason |
|----------|--------------|--------|
| `docs/DESIGN.md` | YES — Section 11.1 | References internal module layout |
| `docs/USER_GUIDE.md` | MAYBE — check for file path refs | May reference source paths in contributor sections |
| `docs/user_docs/mkdocs.yml` | NO | Nav uses CLI names, not file paths |
| `docs/user_docs/docs/cli/*.md` | NO | Per-command docs reference CLI usage, not source files |
