# Feature Specification: Restructure AAM CLI Commands Directory

**Feature Branch**: `008-commands-layout`  
**Created**: 2026-03-12  
**Status**: Draft  
**Input**: User description: "Restructure AAM CLI commands directory — normalize layout so every group is a directory, every filename matches its CLI name, duplicated command pairs are consolidated, and inline group definitions are split into separate files."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Developer navigates commands by filename (Priority: P1)

A developer working on the AAM CLI opens the `commands/` directory to find the source for a specific CLI command. They expect that the filename matches the CLI command name — for example, `aam info` maps to `info.py`, not `show_package.py`. After the restructure, every file is named after its CLI command, enabling developers to locate command implementations instantly without cross-referencing `main.py` registrations.

**Why this priority**: This is the foundational improvement — filename-to-CLI-name parity eliminates the most frequent source of confusion and wasted time for contributors. Every subsequent story builds on this convention.

**Independent Test**: Can be fully tested by renaming three mismatched files and updating imports. A developer can then navigate to any command file by CLI name alone and verify the mapping.

**Acceptance Scenarios**:

1. **Given** the CLI has a command `aam init`, **When** a developer looks for its source, **Then** they find it at `commands/init.py` (not `commands/client_init.py`)
2. **Given** the CLI has a command `aam list`, **When** a developer looks for its source, **Then** they find it at `commands/list.py` (not `commands/list_packages.py`)
3. **Given** the CLI has a command `aam info`, **When** a developer looks for its source, **Then** they find it at `commands/info.py` (not `commands/show_package.py`)
4. **Given** any renamed file, **When** existing tests are run, **Then** all tests pass without modification (only import paths change)

---

### User Story 2 - Contributor eliminates duplicated command pairs (Priority: P1)

A contributor notices that 6 CLI commands exist as both a top-level file (e.g., `create_package.py`) and a thin wrapper in `pkg/` (e.g., `pkg/create.py` that just calls `ctx.invoke()`). After consolidation, each command has exactly one implementation — inside `pkg/` — and the top-level duplicates are removed. This eliminates the risk of diverging implementations and reduces the codebase surface area.

**Why this priority**: Duplicated code is a maintenance hazard — changes to one copy may not be reflected in the other. This consolidation is equally critical to the rename because it removes an entire class of bugs.

**Independent Test**: Can be tested by verifying that all 6 `aam pkg <subcommand>` commands work with their full implementation inside `pkg/`, and that the deleted top-level files no longer exist.

**Acceptance Scenarios**:

1. **Given** `pkg/create.py` previously delegated to `create_package.py`, **When** the consolidation is complete, **Then** `pkg/create.py` contains the full implementation and `create_package.py` no longer exists
2. **Given** all 6 pairs are consolidated, **When** a user runs `aam pkg create --help`, **Then** the output matches the original behavior
3. **Given** the top-level files are deleted, **When** `aam init` needs to invoke `init_package`, **Then** it correctly imports from `pkg/init.py` instead
4. **Given** existing tests reference old import paths, **When** imports are updated, **Then** all tests pass

---

### User Story 3 - Contributor splits multi-command files into directories (Priority: P2)

A contributor wants to edit one subcommand within the `source` group (717 lines in a single file). Currently they must navigate a monolithic file with 7 subcommands interleaved. After splitting, each subcommand lives in its own file under `source/`, making it easy to locate, edit, and review changes in isolation.

**Why this priority**: Splitting inline groups improves maintainability and code review quality, but depends on the conventions established in P1 stories. It covers `source.py`, `config.py`, `registry.py`, `auth.py`, `cache.py`, and `mcp_serve.py`.

**Independent Test**: Can be tested by verifying that `aam source --help` lists all 7 subcommands and each subcommand produces identical behavior to before the split.

**Acceptance Scenarios**:

1. **Given** `source.py` (717 lines) contains 7 subcommands, **When** the split is complete, **Then** a `source/` directory exists with `__init__.py` plus 7 individual subcommand files
2. **Given** `config.py` contains 3 subcommands, **When** the split is complete, **Then** a `config/` directory exists with `__init__.py` plus 3 individual files
3. **Given** `registry.py` contains 4 subcommands, **When** the split is complete, **Then** a `registry/` directory exists with `__init__.py` plus 4 individual files
4. **Given** `auth.py` exports `get_token()` used by `registry/factory.py`, **When** the split is complete, **Then** `from aam_cli.commands.auth import get_token` still resolves correctly (via `auth/__init__.py`)
5. **Given** `cache.py` contains 2 subcommands, **When** the split is complete, **Then** a `cache/` directory exists with `__init__.py` plus 2 individual files
6. **Given** `mcp_serve.py` contains the `mcp` group, **When** the split is complete, **Then** a `mcp/` directory exists with `__init__.py` plus `serve.py`
7. **Given** all splits are done, **When** `aam <group> --help` is run for each group, **Then** output is identical to the pre-split version

---

### User Story 4 - Developer reads clean, uniform imports in main.py (Priority: P2)

A developer opens `main.py` to understand how commands are registered. Currently the import block mixes styles — some import modules, others import functions, and registrations use different patterns. After cleanup, all imports follow a uniform convention: groups are imported from their package `__init__`, top-level commands are direct function imports, and all registrations use `cli.add_command(fn)`.

**Why this priority**: Clean imports in the entry point improve onboarding and reduce registration errors, but this is primarily a readability improvement that depends on the structural changes from P1 and P2 stories.

**Independent Test**: Can be tested by verifying that `aam --help` lists all commands and groups correctly, and that the import block follows the documented convention.

**Acceptance Scenarios**:

1. **Given** `main.py` has been updated, **When** a developer reads the import section, **Then** groups and top-level commands are clearly separated with uniform style
2. **Given** all registrations use `cli.add_command(fn)`, **When** `aam --help` is run, **Then** all commands and groups appear correctly

---

### User Story 5 - User runs deprecated aliases with clear warnings (Priority: P3)

A user has scripts or muscle memory using old command names like `aam create-package`. After the restructure, these deprecated aliases still work but display a clear deprecation warning directing users to the new command (`aam pkg create`). The alias definitions are centralized in a single `_deprecated.py` file rather than scattered across `main.py`.

**Why this priority**: Backwards compatibility is important for user trust, but the aliases are already implemented — this story only moves them to a dedicated file for better organization.

**Independent Test**: Can be tested by running each of the 6 deprecated aliases and verifying they produce the deprecation warning and then execute the correct new command.

**Acceptance Scenarios**:

1. **Given** a user runs `aam create-package`, **When** the command executes, **Then** a deprecation warning is shown recommending `aam pkg create`, and the command succeeds
2. **Given** all 6 aliases are defined in `_deprecated.py`, **When** `main.py` is inspected, **Then** the deprecated alias block is replaced by a single import and function call
3. **Given** `_deprecated.py` uses lazy imports, **When** the CLI starts, **Then** circular dependency issues are avoided

---

### Edge Cases

- What happens when a test file imports from a deleted module path? — The test must be updated to use the new import path; otherwise it fails with `ModuleNotFoundError`.
- What happens when `auth/__init__.py` is split but external code imports `get_token` from `aam_cli.commands.auth`? — The `__init__.py` re-exports `get_token`, preserving the existing import path.
- What happens when two subcommand files in different groups share the same name (e.g., `list.py` in `source/`, `config/`, `registry/`)? — No conflict since they reside in separate Python packages.
- What happens when a deprecated alias invokes a command that was moved? — Lazy imports inside `_deprecated.py` resolve to the new location at call time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every command file MUST be named to match its CLI command name (e.g., `aam init` → `init.py`, `aam info` → `info.py`)
- **FR-002**: Files with mismatched names (`client_init.py`, `list_packages.py`, `show_package.py`) MUST be renamed to match their CLI names (`init.py`, `list.py`, `info.py`)
- **FR-003**: The 6 duplicated command pairs (top-level file + `pkg/` wrapper) MUST be consolidated so the full implementation lives in `pkg/` and the top-level originals are deleted
- **FR-004**: All inline group definitions (`source.py`, `config.py`, `registry.py`, `auth.py`, `cache.py`, `mcp_serve.py`) MUST be split into directory-based packages with one file per subcommand
- **FR-005**: Each extracted subcommand file MUST use `@click.command()` instead of `@group.command()`, with registration handled by `add_command()` in the group's `__init__.py`
- **FR-006**: `main.py` MUST be updated to use uniform import conventions — groups from package `__init__`, top-level commands as direct function imports
- **FR-007**: All deprecated command aliases MUST be extracted from `main.py` into a dedicated `_deprecated.py` module with a `register_deprecated_aliases(cli)` function
- **FR-008**: Deprecated aliases MUST use lazy imports to avoid circular dependencies
- **FR-009**: External import paths that are part of the public interface (e.g., `from aam_cli.commands.auth import get_token`) MUST continue to resolve correctly after the restructure
- **FR-010**: All existing tests MUST pass after the restructure with only import path updates — no behavioral changes
- **FR-011**: No business logic MUST be added, removed, or modified — this is purely a file organization refactoring
- **FR-012**: The 6 deprecated aliases (`create-package`, `validate`, `pack`, `publish`, `build`, `update`) MUST continue to function and display deprecation warnings

### Key Entities *(include if feature involves data)*

- **Command File**: A Python module containing a single Click command or command group definition, named to match its CLI invocation name
- **Command Group Package**: A Python package (directory with `__init__.py`) representing a Click command group, with subcommands in individual files registered via `add_command()`
- **Deprecated Alias**: A hidden CLI command that delegates to a renamed/relocated command while displaying a deprecation warning

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of command filenames match their CLI command names — no file requires cross-referencing `main.py` to determine which command it implements
- **SC-002**: Zero duplicated command implementations — each CLI command has exactly one source file containing its logic
- **SC-003**: Zero inline group definitions — every command group with 2+ subcommands is a directory-based package
- **SC-004**: All existing tests pass after the restructure (test suite has 0 regressions)
- **SC-005**: All 6 deprecated aliases produce correct behavior and deprecation warnings
- **SC-006**: `main.py` import block follows a single uniform convention with clear visual separation between groups and top-level commands
- **SC-007**: No **newly created or split** file in the `commands/` directory exceeds 600 lines. Exception: `pkg/create.py` (~1053 lines) is pre-existing debt consolidated from `create_package.py` — it is not worsened by this refactoring. A separate follow-up spec MUST be created to decompose it.
- **SC-008**: A new contributor can locate the source for any CLI command by navigating the `commands/` directory structure alone (verified by file-tree review: every CLI name maps 1:1 to a filename or group directory)
