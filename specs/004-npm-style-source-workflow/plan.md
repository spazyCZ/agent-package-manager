# Implementation Plan: CLI Interface Scaffolding & npm-Style Source Workflow

**Branch**: `004-npm-style-source-workflow` | **Date**: 2026-02-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-npm-style-source-workflow/spec.md`
**Key Reference**: [`docs/CLI_RESTRUCTURE_ANALYSIS.md`](../../docs/CLI_RESTRUCTURE_ANALYSIS.md)

## Summary

This feature transforms the AAM CLI from a 5-step source-to-install workflow into a 2-step npm/apt-style experience by treating git sources as virtual package registries. Simultaneously, it restructures the CLI by moving all creator commands under an `aam pkg` subgroup, repurposing `aam init` as client initialization, and adding categorized `--help` output. New commands include `aam outdated`, `aam upgrade`, and `aam list --available`. The MCP server gains three new tools (`aam_outdated`, `aam_available`, `aam_upgrade`). Documentation and web UI are updated to reflect the new command structure.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Click 8.1+ (CLI framework), Rich 13.0+ (terminal UI), Pydantic v2 (models), FastMCP (MCP server), PyYAML (config/lock files), GitPython/subprocess (git operations)
**Storage**: File-based — `~/.aam/config.yaml` (config), `aam-lock.yaml` (lock file), `~/.aam/sources-cache/` (git clones), `~/.aam/packages/` (installed packages)
**Testing**: pytest with Click's `CliRunner`, `unittest.mock` for unit tests, real git repos for integration tests. Nx orchestration via `npx nx test aam-cli`.
**Target Platform**: Linux, macOS, Windows (Python CLI — cross-platform)
**Project Type**: Nx monorepo with multiple apps (`apps/aam-cli/`, `apps/aam-web/`, `apps/aam-backend/`). This feature primarily touches `apps/aam-cli/` with minor updates to `apps/aam-web/` and `docs/`.
**Performance Goals**: `aam install <source-artifact>` < 5s for cached sources (NFR-001); `aam source update --all` < 30s for 10 sources (NFR-002); `aam init` interactive < 60s (NFR-004); deprecated alias overhead < 10ms (NFR-005)
**Constraints**: Offline-capable after initial source add (NFR-003); 80-column terminal rendering (NFR-006); no breaking changes to existing commands; backward-compatible lock file extension
**Scale/Scope**: 10 user stories, 39 functional requirements, 6 NFRs, ~15 new files, ~12 modified files across CLI/web/docs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Assessment |
|---|-----------|--------|------------|
| I | Local-First Architecture | **PASS** | All new commands (`install` from source, `outdated`, `upgrade`, `init`) operate against local file-based caches and config. No network required except `source update`. `httpx` remains lazy-import only. |
| II | Platform Adapter Abstraction | **PASS** | FR-030 explicitly fixes the `uninstall` adapter bug. New `install_from_source()` uses `create_adapter()` factory. No platform-specific code in core/services. |
| III | Strict Code Quality & Observability | **PASS** | All new modules will use `logging.getLogger(__name__)`, type hints, Google-style docstrings, structured logging. FR-031/FR-032 standardize console handling across all commands. |
| IV | Test-Driven Quality | **PASS** | Spec defines 7 new test files (SC-013: 80%+ coverage target). Unit tests use mocks; integration tests use real git repos. Test-first for critical paths (install-from-source, upgrade). |
| V | Security by Default (ASVS L2) | **PASS** | SHA-256 checksums enforced for source-installed packages. Pydantic v2 validates all inputs. No new secrets or auth flows. MCP write tool gated by `--allow-write`. |
| VI | Monorepo Discipline (Nx) | **PASS** | All work within existing Nx project `aam-cli`. Tests run via `npx nx test aam-cli`. No new projects created. |
| VII | No Defensive Fallbacks | **PASS** | No silent fallbacks introduced. `install` from source fails loudly if artifact not found. `outdated` reports stale index explicitly. `upgrade` preserves existing backup/skip/diff/force flow. |
| VIII | Documentation Alignment (MkDocs) | **PASS** | FR-036 through FR-039 mandate doc updates. USER_GUIDE.md, DESIGN.md, web homepage, and all `--help` text updated in same PR. |

**Pre-Phase 0 Gate: PASS** — No violations. Proceeding to research.

## Project Structure

### Documentation (this feature)

```text
specs/004-npm-style-source-workflow/
├── spec.md              # Feature specification (input)
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI contract definitions)
├── checklists/          # Specification quality checklists
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
apps/aam-cli/src/aam_cli/
├── main.py                          # MODIFY: OrderedGroup, pkg group, new commands, deprecated aliases
├── commands/
│   ├── client_init.py               # NEW: aam init (client initialization)
│   ├── outdated.py                  # NEW: aam outdated
│   ├── upgrade.py                   # NEW: aam upgrade
│   ├── install.py                   # MODIFY: add source resolution path
│   ├── uninstall.py                 # MODIFY: fix hardcoded CursorAdapter
│   ├── list_packages.py             # MODIFY: add --available flag
│   ├── search.py                    # MODIFY: include source artifacts
│   ├── source.py                    # MODIFY: ctx.obj["console"], ctx.exit()
│   └── pkg/                         # NEW: creator command group
│       ├── __init__.py              # Click group definition
│       ├── init.py                  # aam pkg init (was aam init)
│       ├── create.py               # aam pkg create (was aam create-package)
│       ├── validate.py             # aam pkg validate (was aam validate)
│       ├── pack.py                 # aam pkg pack (was aam pack)
│       ├── publish.py              # aam pkg publish (was aam publish)
│       └── build.py                # aam pkg build (was aam build)
├── services/
│   ├── client_init_service.py       # NEW: interactive client setup logic
│   ├── upgrade_service.py           # NEW: upgrade orchestration
│   ├── install_service.py           # MODIFY: install_from_source()
│   └── source_service.py            # MODIFY: resolve_artifact(), build_source_index()
├── core/
│   └── workspace.py                 # MODIFY: LockedPackage + source_name, source_commit
├── mcp/
│   ├── tools_read.py                # MODIFY: add aam_available, aam_outdated
│   └── tools_write.py               # MODIFY: add aam_upgrade

apps/aam-cli/tests/
├── unit/
│   ├── test_unit_client_init.py     # NEW
│   ├── test_unit_outdated.py        # NEW
│   ├── test_unit_upgrade.py         # NEW
│   ├── test_unit_install_from_source.py  # NEW
│   ├── test_unit_pkg_group.py       # NEW
│   └── test_unit_help_grouping.py   # NEW
└── integration/
    └── test_integration_source_install.py  # NEW (optional)

apps/aam-web/src/pages/
└── HomePage.tsx                      # MODIFY: update CLI examples

docs/
├── USER_GUIDE.md                    # MODIFY: new command structure
└── DESIGN.md                        # MODIFY: updated hierarchy
```

**Structure Decision**: Existing Nx monorepo structure. All CLI changes within `apps/aam-cli/`. New `commands/pkg/` subdirectory for creator command group. No new Nx projects.

## Complexity Tracking

> No constitution violations to justify. All changes fit within existing architecture.

*No entries required.*

## Post-Design Constitution Re-Check

*Re-evaluated after Phase 1 design artifacts (data-model.md, contracts/, quickstart.md) are complete.*

| # | Principle | Status | Post-Design Assessment |
|---|-----------|--------|----------------------|
| I | Local-First Architecture | **PASS** | `ArtifactIndex` is built from local cache. `VirtualPackage` resolution uses no network. `OutdatedPackage` compares local lock file against local cache HEAD. |
| II | Platform Adapter Abstraction | **PASS** | `install_from_source()` deploys via `create_adapter()` factory. No platform-specific logic in `upgrade_service.py`, `source_service.py`, or data models. |
| III | Strict Code Quality & Observability | **PASS** | All new entities use Pydantic `BaseModel` or `@dataclass`. All new files specify `logger = logging.getLogger(__name__)`. Contracts define structured return types. |
| IV | Test-Driven Quality | **PASS** | 6 new unit test files defined. Data models are testable (pure data). Service functions return structured `@dataclass` results (easy to assert). |
| V | Security by Default (ASVS L2) | **PASS** | Source installs compute SHA-256 checksums during staging. `LockedPackage.source_commit` stores full 40-char SHA. MCP `aam_upgrade` gated by write permission. |
| VI | Monorepo Discipline (Nx) | **PASS** | No new Nx projects. All files within `apps/aam-cli/`. Tests run via `npx nx test aam-cli`. |
| VII | No Defensive Fallbacks | **PASS** | `resolve_artifact()` raises `ValueError` with actionable message if not found. `check_outdated()` warns about stale sources explicitly. No silent fallbacks in any data flow. |
| VIII | Documentation Alignment (MkDocs) | **PASS** | Contracts define exact `--help` text for all new commands. Quickstart provides user-facing examples. Doc files listed in project structure for update. |

**Post-Design Gate: PASS** — All principles satisfied. Ready for task generation (`/speckit.tasks`).

## Generated Artifacts Summary

| Artifact | Path | Purpose |
|----------|------|---------|
| Plan | `specs/004-npm-style-source-workflow/plan.md` | This file — technical context, constitution checks, project structure |
| Research | `specs/004-npm-style-source-workflow/research.md` | 8 research topics resolved — Click patterns, resolution, init, outdated/upgrade |
| Data Model | `specs/004-npm-style-source-workflow/data-model.md` | 7 entities — LockedPackage ext, VirtualPackage, ArtifactIndex, Outdated/Upgrade results, ClientInitResult |
| CLI Contracts | `specs/004-npm-style-source-workflow/contracts/cli-commands.md` | Command signatures, output formats, exit codes, MCP tool contracts, help text |
| Quickstart | `specs/004-npm-style-source-workflow/quickstart.md` | Consumer and creator workflows, dev setup, architecture notes |
| Agent Context | `CLAUDE.md` | Updated with spec 004 technology stack |
