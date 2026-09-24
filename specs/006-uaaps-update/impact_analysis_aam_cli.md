# Impact Analysis: UAAPS Update on `aam-cli`

This document analyzes the impact of the Universal Agentic Artifact Package Specification (UAAPS) v0.4.0 update on the `aam-cli` application, comparing it against the current implementation described in `DESIGN.md` (v0.1.0-draft).

## 1. Package Manifest Changes (`aam.yaml` -> `package.agent.json`)

The most significant change is the transition from a YAML-based manifest (`aam.yaml`) to a JSON-based manifest (`package.agent.json`), with YAML supported as a secondary authoring format (`package.agent.yaml`).

### Impact on `aam-cli`:
*   **File Discovery:** The CLI must now look for `package.agent.json` first, then `package.agent.yaml`, instead of `aam.yaml`.
*   **Parsing:** The core manifest parsing logic needs to handle both JSON and YAML. If both exist, JSON must take precedence.
*   **Schema Updates:** The manifest schema has been significantly expanded:
    *   `artifacts` is now optional (auto-discovered by default).
    *   New dependency types: `optionalDependencies`, `peerDependencies`, `systemDependencies`.
    *   New fields: `category`, `engines`, `env`, `permissions`, `skills`, `commands`, `agents`, `rules`, `hooks`, `mcp`, and vendor extensions via `x-*` (e.g., `x-claude`, `x-cursor`).
*   **CLI Commands:**
    *   `aam pkg init`: Must generate `package.agent.json` by default.
    *   `aam pkg create`: Must generate `package.agent.json`.
    *   `aam pkg validate`: Must validate against the new UAAPS schema.

## 2. Dependency Resolution Enhancements

UAAPS introduces a much more sophisticated dependency resolution system, moving closer to `npm` or `cargo`.

### Impact on `aam-cli`:
*   **New Dependency Types:** The resolver must handle `optionalDependencies` (don't fail if missing) and `peerDependencies` (verify they exist in the host environment).
*   **System Dependencies:** A new pre-flight check system is required to verify `systemDependencies` (Python/Node versions, OS binaries, pip/npm packages, MCP servers) before installation.
*   **Auto-Install:** The CLI needs a new `--install-system-deps` flag to automatically install supported system dependencies (pip, npm, mcp-servers).
*   **Lock File:** The lock file format (`aam-lock.yaml` -> `package.agent.lock`) changes to JSON and includes `systemChecks`.
*   **Resolution Strategies:** New flags for `aam install`: `--frozen`, `--minimal`, `--latest`, `--dry-run`.
*   **New Commands:**
    *   `aam tree`: Display the resolved dependency tree.
    *   `aam why <pkg>`: Explain why a package is installed.
    *   `aam check`: Verify dependencies (with `--system` flag).
    *   `aam audit`: Check for security issues.
    *   `aam dedupe`: Flatten the tree.
    *   `aam prune`: Remove unused packages.
*   **Install Directory:** The install root changes from `.aam/packages/` to `.agent-packages/`.
*   **Hoisting:** The resolver must implement dependency hoisting (flattening the tree where possible) similar to `npm`.

## 3. Artifact Structure and Auto-Discovery

UAAPS emphasizes "Convention over Configuration" with standard directory names and auto-discovery.

### Impact on `aam-cli`:
*   **Auto-Discovery:** If the `artifacts` section is omitted from the manifest, the CLI must automatically discover skills, agents, prompts, and commands in their respective default directories (`./skills`, `./agents`, `./prompts`, `./commands`).
*   **Component Overrides:** The CLI must respect custom paths defined in the manifest (e.g., `"skills": "./custom-skills"`).
*   **New Artifact Types:**
    *   **Commands:** Support for `commands/*.md`.
    *   **Rules:** Support for `rules/*/RULE.md` (replacing `instructions/`).
    *   **Hooks:** Support for lifecycle hooks (`hooks/hooks.json`).
    *   **MCP:** Support for MCP server configs (`mcp/servers.json`).
*   **Agent Structure:** Agents are now defined as a directory containing `agent.yaml` and `system-prompt.md` (legacy single-file format still supported).

## 4. Platform Adapters and Conversion

The mapping of artifacts to specific platforms has been formalized and expanded.

### Impact on `aam-cli`:
*   **Platform Adapters:** The deployment logic (`aam deploy`, `aam install`) must be updated to handle the new artifact types (Commands, Rules, Hooks, MCP) and map them correctly to Claude Code, Cursor, Copilot, and Codex according to the UAAPS matrix.
*   **`aam convert`:** The conversion logic needs significant updates to handle the new formats (e.g., converting `.instructions.md` to `RULE.md`, handling `hooks.json` differences).

## 5. Governance and Security

UAAPS introduces client-side policy gates and expanded signing capabilities.

### Impact on `aam-cli`:
*   **Policy Enforcement:** The CLI must read `governance` settings from `config.yaml` and enforce them *before* install/publish operations (e.g., `allowed_scopes`, `require_signature`, `require_tag`, `blocked_packages`).
*   **Environment Variables:** The CLI should securely prompt for required environment variables defined in the `env` manifest field during installation.
*   **Permissions:** The CLI should display requested permissions (`fs`, `network`, `shell`) during installation and potentially require user confirmation.

## 6. MCP Server Mode Updates

The MCP server exposed by `aam-cli` needs to reflect the new commands and capabilities.

### Impact on `aam-cli`:
*   **New Tools:** Add MCP tools for the new CLI commands (`aam_tree`, `aam_check`, `aam_audit`, etc.).
*   **Updated Tools:** Update existing tools (`aam_install`, `aam_validate`, `aam_info`) to handle the new manifest format, dependency types, and flags.
*   **Resources:** Update resources (e.g., `aam://manifest`) to serve `package.agent.json`.

## Summary of Required Changes

1.  **Rename/Refactor Manifest:** `aam.yaml` -> `package.agent.json` (with YAML fallback).
2.  **Implement Auto-Discovery:** Scan default directories if `artifacts` is missing.
3.  **Overhaul Dependency Resolver:** Implement hoisting, `optionalDependencies`, `peerDependencies`, and the new lock file format (`package.agent.lock`).
4.  **Implement System Dependencies:** Add pre-flight checks and auto-install capabilities for `systemDependencies`.
5.  **Add New CLI Commands:** `tree`, `why`, `check`, `audit`, `dedupe`, `prune`.
6.  **Update Platform Adapters:** Support Commands, Rules, Hooks, and MCP configs.
7.  **Implement Governance Gates:** Enforce client-side policies during install/publish.
8.  **Update MCP Server:** Expose new capabilities via FastMCP.