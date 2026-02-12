# Implementation Plan: Improve Search Command UX

**Branch**: `005-improve-search-ux` | **Date**: 2026-02-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-improve-search-ux/spec.md`

## Summary

Overhaul the `aam search` command to deliver ranked, filterable results with a clean tabular display, unified service layer (shared by CLI and MCP), graceful error handling, and "Did you mean?" suggestions on empty results. No new dependencies required — uses Python stdlib `difflib` for fuzzy matching and existing Rich library for table output.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Click 8.1+ (CLI), Rich 13.0+ (display), Pydantic v2 (models), FastMCP (MCP server), PyYAML (config)
**Storage**: File-based — `~/.aam/config.yaml` (config), `index.yaml` (registry index), `~/.aam/sources-cache/` (git clones)
**Testing**: pytest 8.0+ with pytest-cov
**Target Platform**: Linux, macOS, Windows (CLI tool)
**Project Type**: Monorepo app (`apps/aam-cli/`)
**Performance Goals**: Search completes within 2 seconds for up to 500 indexed packages across local registries and cached sources
**Constraints**: No new PyPI dependencies; Python stdlib `difflib.SequenceMatcher` for approximate matching; `--json` output format changes from flat array to envelope object (breaking change, acceptable at v0.1.0 — see research.md R-007)
**Scale/Scope**: Typically 10-200 indexed packages across 1-5 registries and 1-10 git sources

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Local-First Architecture | **PASS** | All search logic operates on local registry files and cached source clones. No network calls. |
| II. Platform Adapter Abstraction | **PASS** | Search is platform-agnostic — no platform-specific code paths. |
| III. Strict Code Quality & Observability | **PASS** | Plan requires: module-level loggers, type hints on all signatures, Google-style docstrings, 80-char section headers, structured logging at entry/exit/error points. |
| IV. Test-Driven Quality | **PASS** | Plan includes unit tests for service layer (scoring, filtering, sorting, suggestions), unit tests for display formatting, and integration test for CLI end-to-end. Test-first for scoring algorithm. |
| V. Security by Default (ASVS L2) | **PASS** | No new security surfaces. Query input is used only for substring comparison (no regex, no SQL, no eval). |
| VI. Monorepo Discipline (Nx) | **PASS** | All changes within `apps/aam-cli/`. Tests run via `npx nx test aam-cli`. No new projects or cross-project dependencies. |
| VII. No Defensive Fallbacks | **PASS** | FR-020 requires visible warnings (not silent fallbacks) on source search failure. The spec explicitly mandates failing loudly. Source import in command file will be removed (no more try/except around import). |
| VIII. Documentation Alignment (MkDocs) | **PASS** | Plan includes updating `docs/user_docs/docs/cli/search.md` to reflect new options, table output format, and sorting/filtering. |

**Gate result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/005-improve-search-ux/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── search-service.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (files to create/modify)

```text
apps/aam-cli/
├── src/aam_cli/
│   ├── commands/
│   │   └── search.py              # MODIFY: thin to presentation-only
│   ├── services/
│   │   └── search_service.py      # MODIFY: major rewrite (unified search)
│   ├── mcp/
│   │   └── tools_read.py          # MODIFY: update to use new service API
│   └── utils/
│       └── text_match.py          # CREATE: scoring + fuzzy matching utilities
├── tests/
│   └── unit/
│       ├── test_services_search.py       # MODIFY: expand tests for new service
│       └── test_unit_text_match.py       # CREATE: scoring/fuzzy matching tests
└── docs/user_docs/docs/cli/
    └── search.md                  # MODIFY: update docs for new features
```

**Structure Decision**: All changes are within the existing `apps/aam-cli/` project. One new utility file (`utils/text_match.py`) is created for reusable scoring and fuzzy matching logic. No new projects, no cross-project changes.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.
