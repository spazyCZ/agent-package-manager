# Specification 007: Extract `aam-sdk`

**Feature Branch**: `007-aam-sdk-1`
**Status**: Draft
**Context**: The core business logic of AAM is currently tightly coupled within the `aam-cli` application. To support the upcoming HTTP registry backend (planned for 008) and enable programmatic access, this logic must be extracted into a standalone, reusable Python library (`libs/aam-sdk`). The MCP server will remain embedded within the CLI application.

## 1. Objectives

1. **Decouple Business Logic**: Extract manifest parsing, dependency resolution, registry interaction, platform adapters, and workspace management from `apps/aam-cli` into `libs/aam-sdk`.
2. **Enable Reusability**: Provide a clean, programmatic Python API that returns structured data (Pydantic models) instead of printing to a terminal, allowing the future `aam-backend` to consume it directly.
3. **Thin CLI & MCP Layers**: Refactor `aam-cli` (Click/Rich) and its embedded MCP server (FastMCP) to act as thin presentation/transport layers over the SDK.
4. **Remove UI from Core**: Eliminate all dependencies on `click` and `rich` from the core business logic.

## 2. Target Architecture

### `libs/aam-sdk` (New)
A pure Python library containing the domain models and business logic. The importable package name is `aam_sdk`; the PyPI/pip distribution name is `aam-sdk`.
* **Dependencies**: `pydantic`, `pyyaml`, `httpx`, `packaging`, `tomli` (Python <3.11), `tomli-w` (No `click`, `rich`, `fastmcp`, or `gitpython` — git operations use the stdlib `subprocess` directly).
* **Contents**:
  * `core/` (manifest, workspace, config, resolver, autodiscovery, version, installer)
  * `registry/` (HTTP and local registry clients)
  * `adapters/` (Platform deployment logic)
  * `converters/` (Platform format conversion: frontmatter, mappings)
  * `services/` (High-level orchestration, including `recommend_service`, `system_deps_service`, `governance_service`, `dependency_tree_service`, `convert_service`)
  * `utils/` (Checksums, archive handling)
  * `detection/` (Artifact scanning)

### `apps/aam-cli` (Refactored)
The end-user command-line interface and embedded MCP server.
* **Dependencies**: `aam-sdk` (local workspace dependency), `click`, `rich`, `fastmcp`.
* **Contents**:
  * `commands/` (Click command definitions, interactive prompts, Rich console formatting)
  * `mcp/` (FastMCP server initialization and tool definitions)
  * `main.py` (CLI entrypoint)

## 3. Implementation Plan

### Phase 1: Scaffold the SDK
1. Create the `libs/aam-sdk/src/aam_sdk/` directory structure.
2. Initialize `libs/aam-sdk/pyproject.toml` for the SDK with core dependencies (`pydantic`, `pyyaml`, `httpx`, `packaging`, `tomli`, `tomli-w`).
3. Add `libs/aam-sdk/project.json` to integrate the SDK into the Nx monorepo build/test graph.

### Phase 2: Purge UI Concerns In-Place (Pre-condition for Move)
> **This phase must complete before moving files.** Editing files in their original location keeps the git diff readable and avoids a broken intermediate state where the SDK imports `rich` or `click`.

1. **`core/installer.py` — primary target**: This file directly imports `from rich.console import Console`, `from rich.panel import Panel`, and `import click`. Refactor it to accept no console argument and to raise domain exceptions instead of calling `ctx.exit()`. Progress information must be returned as structured data.
   - **006 Migration Prompts**: The `migrate_packages_dir` function uses `click.confirm` to prompt the user to migrate `.aam/packages/` to `.agent-packages/`. This prompt must move to the CLI.
   - **006 System Deps**: The `_run_system_deps_preflight` function takes a `Console` and prints missing dependencies. This must return a structured `SystemCheckResults` object and let the CLI handle the printing and the `--install-system-deps` / `--allow-sudo` prompts.
2. **`core/workspace.py`**: The `migrate_lock_file` function uses `click.confirm` to prompt the user to migrate `aam-lock.yaml` to `package.agent.lock`. This prompt must move to the CLI.
3. **Remove all `rich` imports from SDK-bound modules**: Audit every file in `core/`, `services/`, `registry/`, `adapters/`, `converters/`, `utils/`, and `detection/`. Replace any `Console` parameter with structured return values or `logging` calls.
4. **Remove all `click` imports from SDK-bound modules**: Replace `click.Abort`, `ctx.exit()`, and similar with specific domain exceptions (e.g., `AamResolutionError`, `AamValidationError`, `AamConflictError`).
5. **Interactive Prompts**: Move all user-input logic (e.g., the upgrade warning `[b]ackup, [s]kip, [d]iff, [f]orce` loop in `commands/install.py`) entirely into the CLI layer. The SDK service returns a status object; the CLI reads it and issues the prompt.

### Phase 3: Relocate Clean Modules
1. Move the following directories from `apps/aam-cli/src/aam_cli/` to `libs/aam-sdk/src/aam_sdk/`:
   - `adapters/`
   - `converters/`
   - `core/`
   - `detection/`
   - `registry/`
   - `services/`
   - `utils/`
2. Move the corresponding unit tests from `apps/aam-cli/tests/unit/` to `libs/aam-sdk/tests/unit/`. Only tests covering the relocated modules move — tests for `commands/`, `mcp/`, and `main.py` remain in `apps/aam-cli/tests/`. As a guide: any test file whose name does not include `_mcp_`, `_commands_`, or `_help_grouping_` is a candidate to move.

### Phase 4: Wire Local Dependency in Workspace
1. Declare `libs/aam-sdk` as a local path dependency in the root virtual environment so it resolves without publishing to PyPI:
   ```toml
   # In the root pyproject.toml or uv workspace config:
   [tool.uv.workspace.members]
   aam-sdk = { path = "libs/aam-sdk", editable = true }
   ```
2. Add the Nx project dependency edge so `aam-cli` and future `aam-backend` declare `implicitDependencies = ["aam-sdk"]` in their `project.json`.
3. Re-run `pip install -e libs/aam-sdk` (or `uv sync`) in the shared `.venv` to confirm resolution.

### Phase 5: Define the Public API
1. Create `libs/aam-sdk/src/aam_sdk/__init__.py`.
2. Expose the primary programmatic interfaces cleanly:
   ```python
   from .core.manifest import load_manifest, Manifest
   from .core.workspace import Workspace, LockedPackage
   from .registry.factory import create_registry
   from .services.install_service import install_packages
   from .services.source_service import build_source_index, resolve_artifact
   from .services.governance_service import check_governance
   # etc.
   ```

### Phase 6: Refactor CLI and MCP
1. Add `aam-sdk` (`aam_sdk`) as a dependency in `apps/aam-cli/pyproject.toml`.
2. Update all imports in `apps/aam-cli/src/aam_cli/commands/*` to use `aam_sdk` instead of `aam_cli.core`, `aam_cli.services`, etc.
3. Update all imports in `apps/aam-cli/src/aam_cli/mcp/*` to use `aam_sdk`.
4. Ensure the MCP server tools wrap SDK functions and return Pydantic models (FastMCP auto-serializes them to JSON).

### Phase 7: Testing & Validation
1. Run `npx nx test aam-sdk` to ensure all relocated core logic tests pass.
2. Run `npx nx test aam-cli` to ensure CLI commands and MCP integration tests pass.
3. Manually verify `aam install`, `aam search`, and `aam mcp serve` work end-to-end.

## 4. Future Context (008)
By completing this extraction, the upcoming `008-http-registry-backend` feature will be able to declare `aam-sdk` (importable as `aam_sdk`) as a local path dependency in its `pyproject.toml` and immediately gain the ability to parse `package.agent.json` manifests, validate UAAPS schemas, resolve dependencies, and interact with `.aam` archives — without duplicating any logic from the CLI.
