# Implementation Plan: MCP Server for AAM CLI

**Branch**: `002-mcp-server-cli` | **Date**: 2026-02-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-mcp-server-cli/spec.md`

## Summary

Add an MCP (Model Context Protocol) server mode to the AAM CLI so IDE agents (Cursor, VS Code, Claude Desktop, Windsurf) can invoke AAM operations programmatically. The MCP server exposes 13 tools (7 read-only + 6 write) and 5 resources, supports stdio (default) and HTTP transports, and is read-only by default with `--allow-write` enabling mutating tools.

The design emphasizes:
- A **thin MCP layer** (`aam_cli.mcp`) that wraps shared services
- A **pure service layer** (`aam_cli.services`) that is reusable by both MCP and Click CLI commands
- **Local-first** behavior with no required server infrastructure

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastMCP 2.x (`fastmcp>=2.8.0,<3.0.0`), Click 8.1+, Rich 13.0+, Pydantic 2.x  
**Storage**: Local filesystem (`.aam/` workspace), local file-based registries  
**Testing**: Pytest + pytest-asyncio, FastMCP in-memory `Client` (unit tests) + real local registry (integration)  
**Target Platform**: Linux, macOS, Windows  
**Project Type**: Extend existing `apps/aam-cli/` Python application  
**Performance Goals**: Tool responses < 2s; server startup/handshake < 3s  
**Constraints**:
- In stdio mode, **stdout is reserved for JSON-RPC** (no application logging to stdout)
- Read-only by default; write tools are hidden unless `--allow-write`
- Avoid caching workspace state; read filesystem fresh per request
- Serialize workspace mutations to avoid race conditions
**Scale/Scope**: 13 MCP tools, 5 MCP resources, new CLI group `aam mcp serve`, and CLI `aam doctor`

## Constitution Check

*GATE: Must pass before implementation.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Local-First Architecture** | PASS | MCP server wraps CLI core/services; no backend required. |
| **II. Platform Adapter Abstraction** | PASS | No platform-specific logic in MCP/services; deployment remains in adapters. |
| **III. Strict Code Quality & Observability** | PASS | No `print()`; module-level loggers; structured logging at tool entry/exit and on errors. |
| **IV. Test-Driven Quality** | PASS | Unit tests (mocked services) + integration tests (real local registry). Target ≥80% coverage. |
| **V. Security by Default (ASVS L2)** | PASS | Read-only-by-default safety model; strict input validation; safe error messages. |
| **VI. Monorepo Discipline (Nx)** | PASS | Verification and quality gates run via Nx targets (`npx nx ...`). |
| **VII. No Defensive Fallbacks** | PASS | No import fallbacks; failures are explicit with error codes. |
| **VIII. Documentation Alignment (MkDocs)** | PASS (planned) | Docs updates are explicit tasks (see `tasks.md` T044–T047, T051). |

## Project Structure

### Documentation (this feature)

```text
specs/002-mcp-server-cli/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── mcp-tools.md
│   └── mcp-resources.md
└── tasks.md
```

### Source Code (repository root)

```text
apps/aam-cli/
├── src/aam_cli/
│   ├── main.py                          # MODIFIED: register `mcp` and `doctor` commands
│   ├── commands/
│   │   ├── mcp_serve.py                 # NEW: `aam mcp serve`
│   │   ├── doctor.py                    # NEW: `aam doctor`
│   │   └── ...                          # existing commands
│   ├── mcp/                             # NEW: MCP server module
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── tools_read.py
│   │   ├── tools_write.py
│   │   └── resources.py
│   └── services/                        # NEW: shared pure service layer
│       ├── search_service.py
│       ├── install_service.py
│       ├── package_service.py
│       ├── publish_service.py
│       ├── validate_service.py
│       ├── config_service.py
│       ├── registry_service.py
│       └── doctor_service.py
├── tests/
│   ├── unit/
│   └── integration/
├── pyproject.toml                       # MODIFIED: add fastmcp dependency
└── project.json                         # MODIFIED: add Nx target for mcp serve
```

**Structure Decision**: Add `aam_cli.mcp` for MCP-specific concerns and `aam_cli.services` for shared logic. This keeps Click command modules thin and avoids embedding UI concerns into MCP handlers.

## Key Design Decisions

### 1) Safety model (read-only by default)

- Tag all tools as `read` or `write`.
- Construct the server with `exclude_tags={"write"}` unless `--allow-write` is provided.

### 2) Error handling

- Expected domain outcomes return the documented output shape (e.g., validation report).
- Unrecoverable/unexpected failures raise MCP tool errors with safe messages prefixed by error code (e.g., `[AAM_INTERNAL_ERROR] ...`).

### 3) Concurrency + atomicity

- Serialize workspace mutations (install/uninstall/publish/config changes) with an in-process lock.
- Perform installs via staging directories and atomic rename; update lock file only after successful completion.
- `doctor_service` detects partial/incomplete installs and provides recovery steps.

## Phased Delivery (high level)

1. Add dependency + wiring (`aam mcp serve` CLI, server factory)
2. Extract services (core logic without Click/Rich)
3. Implement read tools and resources
4. Implement write tools + safety model verification
5. Implement `doctor_service` + `aam doctor`
6. Add unit + integration test coverage
7. Update docs to match CLI help + design

## Complexity Tracking

No constitution violations to justify.
