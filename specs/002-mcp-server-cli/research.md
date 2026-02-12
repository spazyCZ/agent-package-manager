# Research: MCP Server for AAM CLI

**Branch**: `002-mcp-server-cli` | **Date**: 2026-02-08

## R1: MCP Server Framework Selection

**Decision**: FastMCP 2.14.x (stable v2 line)

**Rationale**:
- FastMCP 2.0+ is the dominant Python MCP framework (~70% of MCP servers, 1M+ daily downloads).
- Provides `@mcp.tool` and `@mcp.resource` decorators that auto-generate JSON Schema from Python type hints — eliminates manual schema maintenance.
- Built-in tag-based filtering (`include_tags` / `exclude_tags`) maps directly to the read/write safety model in the design doc.
- Built-in `Client` class enables in-memory testing without network — perfect for pytest integration.
- Supports both stdio and HTTP transports out of the box via `mcp.run(transport=...)`.
- FastMCP 3.0 is in beta (v3.0.0 beta 2) — not suitable for production. Pin to `fastmcp>=2.8.0,<3.0.0` (tag filtering landed in 2.8.0).
- Already specified in `docs/DESIGN.md` section 5.3.

**Alternatives considered**:
1. **Raw `mcp` SDK** — Lower-level, requires manual handler classes, schema definition, transport setup, and test harness. Rejected: too much boilerplate for 13 tools + 5 resources.
2. **FastMCP 3.0 (beta)** — Has new provider/transform abstractions. Rejected: beta status violates constitution principle for production stability. Can migrate later.
3. **Custom JSON-RPC server** — Full control but no MCP protocol compliance out of the box. Rejected: reimplements what FastMCP already provides.

---

## R2: CLI Core Decoupling Strategy

**Decision**: Create a thin service layer (`aam_cli.services`) that extracts pure business logic from Click command handlers, then wrap services in MCP tool decorators.

**Rationale**:
- The existing `commands/*.py` modules are tightly coupled to Click (`click.Context`, `click.exit()`) and Rich (`Console`, `Table`, `Tree`, `Prompt`).
- The `core/` modules (`config.py`, `manifest.py`, `workspace.py`, `installer.py`, `resolver.py`) are already pure functions — ready for direct wrapping (19 functions identified).
- The 10 command modules need adapter logic to: (a) remove Click context dependency, (b) replace Rich printing with structured return values, (c) replace `click.exit()` with exceptions, (d) eliminate interactive prompts.
- A service layer is the cleanest separation: commands call services for presentation, MCP tools call services for structured data.

**Alternatives considered**:
1. **Inline extraction in MCP tools** — Write wrapping logic directly in each `@mcp.tool` function. Rejected: duplicates logic, hard to test, violates DRY.
2. **Refactor command modules in-place** — Make `commands/*.py` return structured data, add a presentation layer. Rejected: too invasive for the 001-cli-local-repository branch, risks regressions in existing CLI behavior.
3. **Call Click commands programmatically** — Use `CliRunner.invoke()` to call commands and parse output. Rejected: FR-012 explicitly prohibits wrapping Click commands; also fragile (string parsing) and slow.

---

## R3: Safety Model Implementation

**Decision**: Use FastMCP's `exclude_tags={"write"}` at server construction time. Tag all tools as `read` or `write`. Resources are untagged (always available).

**Rationale**:
- FastMCP's tag filtering (since v2.8.0) operates at the server level — excluded tools are invisible to clients (not listed, not callable). This matches FR-005.
- The `--allow-write` CLI flag controls a boolean passed to `create_mcp_server(allow_write=False)`.
- When `allow_write=False`, the server is constructed with `exclude_tags={"write"}`, hiding all write tools.
- When `allow_write=True`, no exclusion is applied — all tools visible.
- Resources are passive data endpoints — they have no side effects and are always exposed regardless of safety mode.

**Alternatives considered**:
1. **Runtime permission checks inside tool handlers** — Tools are visible but raise errors when called in read-only mode. Rejected: leaks tool names/schemas to agents that shouldn't know about them; violates "hidden not just blocked" principle.
2. **Two separate server instances** — One for reads, one for writes. Rejected: unnecessary complexity; tag filtering achieves the same result with one server.

---

## R4: Logging Strategy in stdio Mode

**Decision**: Redirect all Python logging to stderr by default; optionally to a file via `--log-file`. Never write non-JSON-RPC content to stdout.

**Rationale**:
- In MCP stdio mode, stdout is exclusively for JSON-RPC 2.0 messages between client and server. Any non-JSON-RPC content on stdout corrupts the protocol.
- FastMCP handles stdout framing automatically — application code must never write to stdout directly.
- Python's `logging` module supports `StreamHandler(sys.stderr)` for stderr output and `FileHandler` for file output.
- The `--log-file` flag provides a cleaner debugging experience (IDE agents won't see log noise on stderr).
- The `--log-level` flag allows DEBUG for development, INFO for normal operation.

**Alternatives considered**:
1. **Suppress all logging in stdio mode** — Simple but loses observability. Rejected: violates constitution principle III (strict observability).
2. **Log to a fixed location (e.g., `~/.aam/logs/mcp.log`)** — Consistent but inflexible. Rejected: users should control log location; could add as default fallback later.

---

## R5: Transport Configuration

**Decision**: Support `stdio` (default) and `http` transports via `--transport` flag. Use FastMCP's built-in `mcp.run(transport=...)`.

**Rationale**:
- stdio is the standard MCP transport for IDE-embedded servers (Cursor, VS Code, Claude Desktop spawn the process and communicate via stdin/stdout).
- HTTP enables remote access, multi-client scenarios, and development/testing convenience.
- FastMCP handles both transports natively — no custom transport code needed.
- SSE transport exists in FastMCP but is deprecated in favor of HTTP (Streamable HTTP). Not exposed.

**Alternatives considered**:
1. **stdio only** — Simpler, but prevents remote use cases. Rejected: HTTP is low-cost to add via FastMCP and useful for testing.
2. **Custom WebSocket transport** — More control over bidirectional streaming. Rejected: not standard MCP; would need custom client support.

---

## R6: `aam doctor` Command (Not Yet Implemented)

**Decision**: Implement a minimal `aam_doctor` tool that checks: Python version, AAM config validity, registry accessibility, and installed package integrity. Skip platform adapter health for v1.

**Rationale**:
- The `aam doctor` CLI command does not exist yet — it needs to be created as part of this feature (or as a prerequisite).
- For MCP, a diagnostic tool is valuable for agent-assisted troubleshooting.
- Minimal scope for v1: (1) check Python version >= 3.11, (2) validate config loads without errors, (3) check each configured registry is accessible, (4) verify installed packages have valid manifests and checksums.
- Platform adapter health (Cursor directory exists, permissions, etc.) deferred to v2.

**Alternatives considered**:
1. **Omit `aam_doctor` from MCP v1** — Ship without diagnostics, add later. Rejected: diagnostics are low-effort and high-value for agent interactions.
2. **Full system diagnostic** — Check everything including disk space, network, platform adapters. Rejected: over-scoped for v1; incremental addition is fine.

---

## R7: Testing Strategy

**Decision**: Use FastMCP's in-memory `Client` for unit tests. Use `pytest-asyncio` for async test support. Separate unit tests (mocked registries, fake filesystem) from integration tests (real local registry).

**Rationale**:
- FastMCP's `Client(transport=mcp_server)` enables in-memory testing without spawning processes or opening sockets.
- Tests can call `client.list_tools()`, `client.call_tool(...)`, `client.read_resource(...)` directly.
- Unit tests mock the service layer to test MCP tool registration, input validation, error handling, and tag filtering.
- Integration tests use real local registries and filesystem to test end-to-end tool behavior.
- Already have `pytest-asyncio>=0.24.0` in dev dependencies with `asyncio_mode = "auto"`.

**Alternatives considered**:
1. **MCP Inspector** — Official MCP debugging tool. Useful for manual testing but not automatable. Rejected for CI; can recommend for developer testing.
2. **Subprocess-based testing** — Spawn `aam mcp serve` and communicate via stdio. Rejected: slow, fragile, hard to debug.
