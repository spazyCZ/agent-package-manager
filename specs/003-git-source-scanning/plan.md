# Implementation Plan: Git Repository Source Scanning & Artifact Discovery

**Branch**: `003-git-source-scanning` | **Date**: 2026-02-08 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/003-git-source-scanning/spec.md`  
**Key Reference**: [`docs/work/git_repo_skills.md`](../../docs/work/git_repo_skills.md) — Primary implementation reference with detailed schemas, CLI output examples, URL parsing regex, detection patterns, and MCP tool definitions.

## Summary

Add remote git repository scanning and artifact discovery to the AAM CLI and MCP server. Practitioners can register public or private git repositories as named artifact sources, scan cached clones for skills/agents/prompts/instructions, detect upstream changes, list unpackaged candidates, and create AAM packages from remote artifacts with provenance tracking. Additionally, extend the lock file with per-file SHA-256 checksums to detect local modifications and warn users during upgrades. All new functionality is exposed as both CLI commands (`aam source *`, `aam verify`, `aam diff`) and MCP tools/resources.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Click 8.1+ (CLI), Rich 13.0+ (terminal UI), Pydantic v2 (models), PyYAML 6.0+ (config), FastMCP 2.8+ (MCP server — from spec 002)  
**Git Operations**: System `git` via `subprocess.run()` — no Python git library required  
**Storage**: Local filesystem (`~/.aam/cache/git/`, `~/.aam/config.yaml`, `.aam/aam-lock.yaml`)  
**Testing**: pytest 8.0+, pytest-cov 5.0+, Click `CliRunner` for CLI tests, FastMCP `Client` for MCP tests  
**Target Platform**: Linux, macOS, Windows (Python 3.11+, git on PATH)  
**Project Type**: Monorepo app (`apps/aam-cli/`)  
**Performance Goals**: Source scan <5s for 100 artifacts; update check <10s; checksum verify <2s for 50 files  
**Constraints**: Offline after initial clone; shallow clones by default; max 50MB archive; no code execution from scanned repos  
**Scale/Scope**: Up to 10 registered sources, ~500 artifacts per source, ~50 files per installed package

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Local-First Architecture | **PASS** | All operations work offline after initial clone. Git sources are cached locally. Network only needed for `source add` and `source update`. |
| II | Platform Adapter Abstraction | **PASS** | Source scanning and checksum verification are platform-agnostic. No platform-specific code paths introduced. |
| III | Strict Code Quality & Observability | **PASS** | All new modules will follow logging, typing, docstring, and visual separation standards. |
| IV | Test-Driven Quality | **PASS** | Unit tests (mocked git, mocked filesystem) + integration tests (local bare repos). Target 80%+ coverage. |
| V | Security by Default (ASVS L2) | **PASS** | URL validation against allowlist; SHA-256 checksums; no code execution from cloned repos; cache isolation. |
| VI | Monorepo Discipline (Nx) | **PASS** | All code in `apps/aam-cli/`. Tests run via `npx nx test aam-cli`. |
| VII | No Defensive Fallbacks | **PASS** | Explicit errors for network failures, auth failures, corrupt cache. No silent degradation. |
| VIII | Documentation Alignment (MkDocs) | **PASS** | USER_GUIDE.md, DESIGN.md, and CLI `--help` will be updated for all new commands. |

**No violations. All gates pass.**

## Project Structure

### Documentation (this feature)

```text
specs/003-git-source-scanning/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cli-commands.md  # CLI command contracts
│   └── mcp-tools.md     # MCP tool and resource contracts
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
apps/aam-cli/src/aam_cli/
├── commands/
│   ├── source.py              # NEW: aam source add/list/remove/scan/update/candidates
│   ├── verify.py              # NEW: aam verify [package]
│   ├── diff.py                # NEW: aam diff <package>
│   ├── create_package.py      # MODIFIED: add --from-source flag
│   ├── pack.py                # MODIFIED: add per-file checksum generation
│   └── install.py             # MODIFIED: add upgrade warning + write file checksums to lock
├── core/
│   ├── config.py              # MODIFIED: add SourceEntry model, sources list to AamConfig
│   ├── workspace.py           # MODIFIED: add FileChecksums to LockedPackage
│   └── manifest.py            # MODIFIED: add Provenance model
├── services/                  # NEW directory (established by spec 002)
│   ├── source_service.py      # NEW: source add/list/remove/update/scan/candidates logic
│   ├── checksum_service.py    # NEW: verify/diff/backup logic
│   └── git_service.py         # NEW: git clone/fetch/diff subprocess wrapper
├── detection/
│   └── scanner.py             # MODIFIED: extend for remote repo patterns, dot-prefixed dirs
├── mcp/                       # MODIFIED (established by spec 002)
│   ├── tools_read.py          # MODIFIED: add aam_source_list, aam_source_scan, etc.
│   ├── tools_write.py         # MODIFIED: add aam_source_add, aam_source_remove, etc.
│   └── resources.py           # MODIFIED: add aam://sources/* resources
└── utils/
    ├── checksum.py             # MODIFIED: extend for per-file checksum map
    └── git_url.py              # NEW: URL parsing, decomposition, validation

apps/aam-cli/tests/
├── unit/
│   ├── test_unit_git_url.py                  # NEW: URL parsing tests
│   ├── test_unit_scanner_remote.py           # NEW: remote artifact detection tests
│   ├── test_unit_source_service.py           # NEW: source management service tests
│   ├── test_unit_checksum_service.py         # NEW: checksum verification tests
│   ├── test_unit_git_service.py              # NEW: git subprocess wrapper tests
│   ├── test_unit_mcp_source_tools_read.py    # NEW: MCP read tool tests (spec 002 aligned)
│   ├── test_unit_mcp_source_tools_write.py   # NEW: MCP write tool tests (spec 002 aligned)
│   └── test_unit_mcp_source_resources.py     # NEW: MCP resource tests (spec 002 aligned)
├── integration/
│   ├── test_integration_source_lifecycle.py  # NEW: end-to-end source workflow
│   ├── test_integration_verify_diff.py       # NEW: checksum verification integration
│   ├── test_integration_default_sources.py   # NEW: default sources lifecycle
│   └── test_integration_mcp_source.py        # NEW: MCP source tools integration
└── conftest.py                # MODIFIED: add shared fixtures
```

**Structure Decision**: All new code lives within the existing `apps/aam-cli/` app structure, following the patterns established by spec 001 (CLI) and spec 002 (service layer + MCP). New modules are added in `commands/`, `services/`, `utils/`, and `mcp/`. The `detection/scanner.py` is extended rather than replaced.

## Dependency on Spec 002 (MCP Server)

This plan assumes spec 002's service layer and MCP infrastructure exist. If spec 002 is not yet implemented when this feature begins:

- **Phase 1-3** (source management, scanning, checksums) can proceed independently — they only touch CLI commands and core services.
- **Phase 4** (MCP tools) depends on the `mcp/` module structure from spec 002. If not ready, MCP tools can be deferred.
- **Services directory** (`services/`) can be created by this spec if spec 002 hasn't landed. The pattern is straightforward: pure functions returning dicts.

## Complexity Tracking

> No violations — no complexity justification needed.
