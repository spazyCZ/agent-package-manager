# Implementation Plan: CLI Local Repository

**Branch**: `001-cli-local-repository` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-cli-local-repository/spec.md`

## Summary

Implement the full AAM CLI local-first workflow: local file-based registry management, package authoring (create-package, init, validate, pack), publishing to local registries, searching, installing with dependency resolution and Cursor platform deployment, listing/inspecting installed packages, configuration management, and uninstallation. The entire workflow operates with zero network dependencies — no Docker, database, or server required.

The existing CLI codebase has the Click command structure scaffolded with mock/stub implementations. This plan converts those stubs into working implementations, adds the missing core modules (manifest parsing, registry abstraction, dependency resolver, installer, Cursor adapter), and delivers a fully functional local workflow.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Click 8.1+ (CLI framework), Rich 13.0+ (terminal UI), Pydantic 2.0+ (validation), PyYAML (YAML I/O), packaging 24.0+ (semver)
**Storage**: Local filesystem (YAML files + `.aam` gzipped tar archives)
**Testing**: Pytest 8.0+ with pytest-cov, Ruff for linting, MyPy for type checking
**Target Platform**: Cross-platform (Linux, macOS, Windows) — CLI tool installed via pip
**Project Type**: Single Python application within Nx monorepo (`apps/aam-cli/`)
**Performance Goals**: All operations on packages with up to 20 artifacts complete within 5 seconds
**Constraints**: Max 50 MB archive size, no symlinks outside package dir, no absolute paths in archives, offline-capable (zero network dependencies)
**Scale/Scope**: Single-developer to small-team usage; local registry with up to ~100 packages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Local-First Architecture | **PASS** | Entire feature is local-only. No HTTP imports. No server dependencies. |
| II. Platform Adapter Abstraction | **PASS** | Cursor adapter isolated in `adapters/cursor.py`. Core modules have no platform-specific code. |
| III. Strict Code Quality & Observability | **PASS** | All modules use `logging.getLogger(__name__)`, type hints, Google-style docstrings, 80-char section headers. No `print()`. |
| IV. Test-Driven Quality | **PASS** | Tests in `tests/unit/` and `tests/integration/`. 80%+ coverage target. Naming conventions followed. |
| V. Security by Default (ASVS L2) | **PASS** | SHA-256 checksums on all archives. Pydantic v2 for input validation. No hardcoded secrets. No signing in scope (deferred to Phase 2). |
| VI. Monorepo Discipline (Nx) | **PASS** | All within `apps/aam-cli/`. Tasks via `npx nx test aam-cli`. PyYAML added to `pyproject.toml`. |
| VII. No Defensive Fallbacks | **PASS** | No `try/except ImportError`. No `os.getenv` with defaults. Strict `require_env()` where needed. Explicit errors on missing config. |

## Project Structure

### Documentation (this feature)

```text
specs/001-cli-local-repository/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI contract specs)
│   └── cli-commands.md  # Command signatures and expected I/O
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
apps/aam-cli/
├── pyproject.toml                    # Add pyyaml dependency
├── src/aam_cli/
│   ├── __init__.py                   # Existing (version)
│   ├── main.py                       # Existing — update inline commands
│   ├── commands/
│   │   ├── __init__.py               # Existing
│   │   ├── build.py                  # Existing (out of scope, keep stub)
│   │   ├── config.py                 # UPDATE: implement persistence
│   │   ├── create_package.py         # UPDATE: implement file operations
│   │   ├── init_package.py           # NEW: aam init command
│   │   ├── install.py                # UPDATE: implement full install flow
│   │   ├── list_packages.py          # NEW: aam list command (replaces inline)
│   │   ├── pack.py                   # NEW: aam pack command
│   │   ├── publish.py                # UPDATE: implement local publish
│   │   ├── registry.py               # UPDATE: implement init, add, list
│   │   ├── search.py                 # UPDATE: implement local search
│   │   ├── show_package.py           # NEW: aam info/show command (replaces inline)
│   │   ├── uninstall.py              # NEW: aam uninstall command
│   │   └── validate.py               # NEW: aam validate command
│   ├── core/
│   │   ├── __init__.py               # NEW
│   │   ├── manifest.py               # NEW: aam.yaml parsing + pydantic models
│   │   ├── config.py                 # NEW: config loading + precedence
│   │   ├── resolver.py               # NEW: dependency resolution
│   │   ├── installer.py              # NEW: download + extract + deploy orchestration
│   │   ├── version.py                # NEW: semver constraint matching
│   │   └── workspace.py              # NEW: .aam/ directory management
│   ├── registry/
│   │   ├── __init__.py               # NEW
│   │   ├── base.py                   # NEW: Registry Protocol (ABC)
│   │   ├── local.py                  # NEW: LocalRegistry implementation
│   │   └── factory.py                # NEW: registry instantiation from config
│   ├── adapters/
│   │   ├── __init__.py               # NEW
│   │   ├── base.py                   # NEW: PlatformAdapter Protocol
│   │   └── cursor.py                 # NEW: Cursor deployment adapter
│   ├── utils/
│   │   ├── __init__.py               # Existing
│   │   ├── naming.py                 # Existing (complete, no changes)
│   │   ├── archive.py                # NEW: .aam tar.gz creation/extraction
│   │   ├── yaml_utils.py             # NEW: safe YAML loading/dumping
│   │   ├── paths.py                  # NEW: path resolution helpers
│   │   └── checksum.py               # NEW: SHA-256 calculation
│   └── detection/
│       ├── __init__.py               # NEW
│       └── scanner.py                # NEW: artifact auto-detection logic
└── tests/
    ├── __init__.py                   # Existing
    ├── test_main.py                  # Existing — update for new commands
    ├── unit/
    │   ├── __init__.py               # NEW
    │   ├── test_unit_manifest.py     # NEW
    │   ├── test_unit_config.py       # NEW
    │   ├── test_unit_resolver.py     # NEW
    │   ├── test_unit_version.py      # NEW
    │   ├── test_unit_archive.py      # NEW
    │   ├── test_unit_checksum.py     # NEW
    │   ├── test_unit_scanner.py      # NEW
    │   ├── test_unit_local_registry.py # NEW
    │   └── test_unit_cursor_adapter.py # NEW
    └── integration/
        ├── __init__.py               # NEW
        ├── test_integration_registry_workflow.py  # NEW
        ├── test_integration_install_workflow.py   # NEW
        └── test_integration_full_lifecycle.py     # NEW
```

**Structure Decision**: Extends the existing `apps/aam-cli/` layout. New modules are organized by concern: `core/` for domain logic, `registry/` for storage backends, `adapters/` for platform deployment, `detection/` for artifact scanning, `utils/` for shared helpers. This follows the architecture specified in DESIGN.md Section 11.1.

## Complexity Tracking

No constitution violations. No complexity justifications needed.

---

## Module Dependency Order

Implementation should follow this dependency order (leaf modules first):

```
Layer 0 (no internal deps):  utils/yaml_utils, utils/checksum, utils/paths, utils/archive
Layer 1 (depends on L0):     core/version, core/manifest, core/config, core/workspace
Layer 2 (depends on L1):     registry/base, adapters/base, detection/scanner
Layer 3 (depends on L2):     registry/local, registry/factory, adapters/cursor
Layer 4 (depends on L3):     core/resolver, core/installer
Layer 5 (depends on L4):     commands/* (all CLI commands)
```

## Key Design Decisions

### 1. PyYAML for YAML I/O

PyYAML is the standard Python YAML library. Use `yaml.safe_load()` and `yaml.safe_dump()` exclusively (never `yaml.load()`) to prevent arbitrary code execution. Wrap in `utils/yaml_utils.py` for consistent error handling.

### 2. Pydantic v2 for Manifest Validation

`aam.yaml` is validated using Pydantic BaseModel classes with strict type checking. This provides:
- Automatic schema validation with clear error messages
- Type coercion and defaults
- Serialization back to dict for YAML output

### 3. Local Registry as Pure File I/O

The `LocalRegistry` class implements the `Registry` Protocol using only `pathlib.Path` operations and PyYAML. No database, no network, no external services. Operations:
- `search()` → read `index.yaml`, fuzzy-match
- `get_metadata()` → read `packages/<name>/metadata.yaml`
- `download()` → copy `.aam` file from `versions/`
- `publish()` → copy `.aam`, update `metadata.yaml`, rebuild `index.yaml`

### 4. Greedy Dependency Resolution

Resolver uses a BFS queue with a resolved map. For each dependency:
1. Look up best version satisfying the constraint
2. If already resolved and compatible, skip
3. If conflict, raise clear error
No backtracking (simplification for v1 — agent artifact packages have shallow dependency graphs).

### 5. Cursor Adapter Transformations

| Artifact | Source | Target |
|----------|--------|--------|
| Skill | `skills/<name>/` | `.cursor/skills/<fs-name>/` (copy entire directory) |
| Agent | `agents/<name>/agent.yaml` + `system-prompt.md` | `.cursor/rules/agent-<fs-name>.mdc` (convert to rule) |
| Prompt | `prompts/<name>.md` | `.cursor/prompts/<fs-name>.md` (copy) |
| Instruction | `instructions/<name>.md` | `.cursor/rules/<fs-name>.mdc` (convert to rule with globs) |

### 6. Configuration Precedence

```
CLI flags > Project (.aam/config.yaml) > Global (~/.aam/config.yaml) > Defaults
```

Defaults: `default_platform: cursor`, no registries configured, no author info.

### 7. New Dependency: PyYAML

Add `pyyaml>=6.0.0` to `pyproject.toml` dependencies. This is the only new dependency required. All other dependencies (Click, Rich, Pydantic, packaging) are already declared.
