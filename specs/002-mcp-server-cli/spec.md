# Feature Specification: MCP Server for AAM CLI

**Feature Branch**: `002-mcp-server-cli`  
**Created**: 2026-02-08  
**Status**: Draft  
**Input**: User description: "Create MCP server for aam-cli to simplify agent integration. Goal is to add the MCP server to agents and simplify use of command line."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
-->

### User Story 1 - Agent Searches and Discovers Packages (Priority: P1)

An AI agent running inside an IDE (Cursor, VS Code Copilot, Claude Desktop, Windsurf) wants to help a user find and explore AAM packages without the user having to leave the conversation or open a terminal. The agent connects to the AAM MCP server and uses read-only tools to search registries, list installed packages, and inspect package details — all through natural language.

**Why this priority**: Read-only discovery is the foundational use case. It delivers immediate value with zero risk (no filesystem writes), validates the MCP transport layer, and is the most frequently used agent interaction. Every other story depends on the server being operational with at least read tools.

**Independent Test**: Can be fully tested by configuring an IDE agent to connect to the MCP server and asking it "search for cursor skills" or "show me installed packages." The agent should return structured results without the user touching a terminal.

**Acceptance Scenarios**:

1. **Given** the AAM MCP server is running in stdio mode, **When** an IDE agent sends a `tools/call` request for `aam_search` with query "cursor", **Then** the server returns a list of matching packages with name, version, description, and artifact types.
2. **Given** the user has packages installed in the current project, **When** an IDE agent calls `aam_list`, **Then** it receives a structured list of all installed packages with version and artifact counts.
3. **Given** a specific package is installed, **When** an IDE agent calls `aam_info` with the package name, **Then** it receives full metadata including description, author, artifacts, dependencies, and platform configuration.
4. **Given** the server is started without `--allow-write`, **When** an IDE agent attempts to call `aam_install`, **Then** the server rejects the call and returns an error indicating write operations are not enabled.

---

### User Story 2 - Agent Installs and Manages Packages (Priority: P2)

A user asks their IDE agent to install or uninstall an AAM package. The agent, connected to the MCP server with write permissions enabled, orchestrates the installation — resolving dependencies, downloading archives, verifying checksums, and deploying artifacts to the correct platform locations — then reports the result conversationally.

**Why this priority**: Write operations are the second most valuable interaction — they let agents fully manage packages on behalf of the user. However, they carry more risk than reads and require the safety model to be in place, which is why they follow read-only tools.

**Independent Test**: Can be tested by starting the server with `--allow-write`, then having an agent call `aam_install` with a package name. Verify the package appears in `.aam/packages/`, the lock file is updated, and artifacts are deployed to the platform directory.

**Acceptance Scenarios**:

1. **Given** the server is started with `--allow-write`, **When** an IDE agent calls `aam_install` with a valid package name, **Then** the package and its dependencies are installed, the lock file is updated, and artifacts are deployed to the platform.
2. **Given** a package is installed, **When** an IDE agent calls `aam_uninstall` with the package name, **Then** the package is removed, artifacts are undeployed, and the lock file is updated.
3. **Given** the server has write access, **When** an IDE agent calls `aam_publish` for a valid package, **Then** the package archive is published to the specified registry and confirmation is returned.
4. **Given** the server has write access, **When** an IDE agent calls `aam_config_set` with a key and value, **Then** the configuration is updated and the new value is confirmed.

---

### User Story 3 - Agent Reads Project Context via Resources (Priority: P2)

An IDE agent needs to understand the current project's AAM context — what packages are installed, what registries are configured, and what the project manifest looks like — without making tool calls. The agent reads MCP resources (data endpoints) to build context about the user's environment before offering package management advice.

**Why this priority**: Resources provide passive context that enriches every agent interaction. They allow agents to understand the project state before suggesting actions, making tool calls more accurate and relevant. This is at P2 because it enhances the P1 experience significantly but isn't strictly required for basic operation.

**Independent Test**: Can be tested by connecting an MCP client and reading each resource URI. Verify that `aam://config` returns the merged configuration, `aam://packages/installed` returns installed packages, and `aam://manifest` returns the current aam.yaml contents.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** an IDE agent reads the `aam://config` resource, **Then** it receives the merged AAM configuration (global + project).
2. **Given** packages are installed in the project, **When** an IDE agent reads `aam://packages/installed`, **Then** it receives a list of all installed packages with metadata.
3. **Given** an `aam.yaml` exists in the current directory, **When** an IDE agent reads `aam://manifest`, **Then** it receives the parsed manifest contents.
4. **Given** no `aam.yaml` exists, **When** an IDE agent reads `aam://manifest`, **Then** it receives an empty/null response (not an error).

---

### User Story 4 - User Starts and Configures the MCP Server (Priority: P1)

A user launches the MCP server from the command line to make AAM accessible to their IDE agent. They can choose between stdio transport (for direct IDE integration) or HTTP transport (for remote/multi-client access), control write permissions, and configure logging. The server integrates seamlessly with standard IDE MCP configuration files.

**Why this priority**: P1 because without a way to start the server, none of the other stories work. The CLI command is the entry point for all MCP functionality.

**Independent Test**: Can be tested by running `aam mcp serve` and verifying the server starts, responds to an MCP `initialize` handshake, and exits cleanly on signal.

**Acceptance Scenarios**:

1. **Given** the user runs `aam mcp serve`, **When** the server starts, **Then** it listens on stdio for JSON-RPC messages and responds to the MCP `initialize` handshake with server capabilities.
2. **Given** the user runs `aam mcp serve --transport http --port 9000`, **When** the server starts, **Then** it listens on HTTP at the specified port.
3. **Given** the user runs `aam mcp serve --allow-write`, **When** an agent lists available tools, **Then** both read and write tools are returned.
4. **Given** the user runs `aam mcp serve` without `--allow-write`, **When** an agent lists available tools, **Then** only read-tagged tools are returned (write tools are hidden).
5. **Given** the user specifies `--log-file /tmp/aam-mcp.log`, **When** the server operates, **Then** all logs are written to the specified file (not to stdout, which is reserved for JSON-RPC).

---

### User Story 5 - Agent Validates and Creates Packages (Priority: P3)

A developer asks their IDE agent to validate the current project's AAM package manifest or to scaffold a new package from existing project artifacts. The agent uses write-enabled MCP tools to run validation and package creation operations, reporting issues or results in the conversation.

**Why this priority**: Package authoring is less frequent than package discovery and installation. It's valuable for power users and package authors but not needed for the primary consumption workflow.

**Independent Test**: Can be tested by running `aam_validate` against a project with an `aam.yaml` and verifying the validation report is returned. Package creation can be tested by calling `aam_create_package` and verifying the manifest and file structure are generated.

**Acceptance Scenarios**:

1. **Given** the project has an `aam.yaml`, **When** an IDE agent calls `aam_validate`, **Then** it receives a validation report indicating pass/fail with specific issues listed.
2. **Given** the project has detectable artifacts (skills, prompts, etc.), **When** an IDE agent calls `aam_create_package` with appropriate options, **Then** a new `aam.yaml` is generated with detected artifacts included.
3. **Given** the project has an invalid `aam.yaml`, **When** an IDE agent calls `aam_validate`, **Then** it receives a detailed report of all validation errors with line-level context.

---

### User Story 6 - Agent Diagnoses AAM Environment Issues (Priority: P3)

A user reports that something isn't working with their AAM setup. Their IDE agent uses the `aam_doctor` tool to check the environment — verifying configuration, registry connectivity, installed package integrity, and platform adapter health — and reports findings with suggested fixes.

**Why this priority**: Diagnostics are a support and troubleshooting use case. They're valuable but infrequent compared to everyday package operations.

**Independent Test**: Can be tested by calling `aam_doctor` and verifying it returns a structured health report covering configuration, registries, and installed packages.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** an IDE agent calls `aam_doctor`, **Then** it receives a structured health report covering: configuration status, registry connectivity, installed package integrity, and platform adapter availability.
2. **Given** a registry is misconfigured, **When** `aam_doctor` runs, **Then** the report flags the registry issue with a suggested fix.

---

### Edge Cases

- What happens when the MCP server is started in a directory with no `.aam/` workspace? Read tools should still work (returning empty results); write tools that require a workspace (like install) should return clear error messages.
- How does the server handle concurrent tool calls from the same IDE agent? The server should process requests sequentially or use appropriate locking to prevent race conditions on filesystem operations.
- What happens if the server process is killed mid-operation (e.g., during an install)? The lock file and package state should remain consistent — partial installs should be rolled back or detectable by `aam_doctor`.
- What happens when a tool call references a package that doesn't exist? The server should return a structured error response, not crash.
- How does the server handle very large search result sets? Results should be capped at a reasonable limit (default 10, maximum 50).
- What if the user's `aam.yaml` has syntax errors when reading the manifest resource? The resource should return an error description rather than failing silently.
- What if another process modifies the filesystem while the MCP server is running (e.g., user runs `aam install` in a separate terminal)? The server should read fresh state on each request rather than caching stale data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose AAM CLI capabilities as an MCP server accessible over stdio transport (JSON-RPC 2.0).
- **FR-002**: System MUST support HTTP transport as an alternative to stdio, configurable via command-line flag.
- **FR-003**: System MUST expose read-only tools: `aam_search`, `aam_list`, `aam_info`, `aam_validate`, `aam_config_get`, `aam_registry_list`, and `aam_doctor`.
- **FR-004**: System MUST expose write tools: `aam_install`, `aam_uninstall`, `aam_publish`, `aam_create_package`, `aam_config_set`, and `aam_registry_add`.
- **FR-005**: System MUST enforce a read-only-by-default safety model — write tools are hidden unless the server is started with `--allow-write`.
- **FR-006**: System MUST expose MCP resources for passive data access: `aam://config`, `aam://packages/installed`, `aam://packages/{name}`, `aam://registries`, and `aam://manifest`.
- **FR-007**: System MUST provide an `aam mcp serve` CLI command with options for transport, port, write permissions, log file, and log level.
- **FR-008**: System MUST prefix all tool names with `aam_` to avoid naming collisions when multiple MCP servers are active in an IDE.
- **FR-009**: System MUST auto-generate JSON Schema for tool inputs from Python type hints and Pydantic models.
- **FR-010**: System MUST redirect all logging to a file or stderr when running in stdio mode (stdout is reserved for JSON-RPC).
- **FR-011**: System MUST return structured error responses for tool failures (not crash or hang).
- **FR-012**: Tool handlers MUST wrap existing CLI core logic (services/functions), not Click commands directly, keeping the MCP layer thin and testable.
- **FR-013**: System MUST respond to the MCP `initialize` handshake with server name, version, and supported capabilities.
- **FR-014**: System MUST read fresh filesystem state on each request (no stale caching of workspace state).
- **FR-015**: System MUST handle graceful shutdown on SIGINT/SIGTERM, completing any in-progress operations before exiting.

### Key Entities

- **MCP Server**: The FastMCP server instance that manages transport, tool/resource registration, and request routing. Key attributes: name ("aam"), version, transport type, safety mode (read-only vs read-write).
- **MCP Tool**: A callable operation exposed to IDE agents, mapped from AAM CLI commands. Key attributes: name (aam_-prefixed), tag (read/write), input schema (auto-generated), handler function.
- **MCP Resource**: A read-only data endpoint exposed to IDE agents for passive context retrieval. Key attributes: URI (aam:// scheme), handler function, return type.
- **Safety Mode**: Configuration that controls which tools are exposed — read-only (default) hides write-tagged tools; read-write exposes all tools. Controlled via `--allow-write` flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An IDE agent can discover, search, and inspect AAM packages entirely through natural language conversation — the user never needs to open a terminal for read operations.
- **SC-002**: All 7 read-only tools respond to valid requests within 2 seconds under normal conditions.
- **SC-003**: All 6 write tools successfully perform their operations and return confirmation, matching the behavior of equivalent CLI commands.
- **SC-004**: The safety model prevents 100% of write operations when the server is started without `--allow-write` — no write tool is discoverable or callable.
- **SC-005**: The server starts and completes the MCP handshake within 3 seconds.
- **SC-006**: All 5 MCP resources return accurate, up-to-date data reflecting the current filesystem state.
- **SC-007**: 90% of users who configure the MCP server in their IDE can successfully issue their first package query through an agent on the first attempt.
- **SC-008**: The server runs stably for extended sessions (8+ hours) without memory leaks or degraded performance.

## Assumptions

- **A-001**: FastMCP 2.0+ is a stable, maintained framework suitable for production use.
- **A-002**: IDE agents (Cursor, VS Code, Claude Desktop) support MCP stdio transport natively and can be configured to spawn the `aam mcp serve` process.
- **A-003**: The existing CLI core logic (`aam_cli.core.*`, `aam_cli.registry.*`) can be called directly from MCP tool handlers without modification — the CLI core is already decoupled from Click.
- **A-004**: Users will primarily use stdio transport for local IDE integration; HTTP transport is a secondary use case for remote/shared environments.
- **A-005**: The `aam` CLI is already installed and on the user's PATH when configuring MCP server in their IDE.
