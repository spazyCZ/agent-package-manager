# Feature Specification: UAAPS v0.4.0 Update for aam-cli

**Feature Branch**: `006-uaaps-update`
**Created**: 2026-02-20
**Status**: Draft
**Input**: Update aam-cli to support Universal Agentic Artifact Package Specification (UAAPS) v0.4.0 — new `package.agent.json` manifest format, enhanced dependency resolution, artifact auto-discovery, new artifact types (Commands, Rules, Hooks, MCP), platform adapter updates, governance gates, and MCP server tool updates.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Author Universal Package with New Manifest (Priority: P1)

A package author wants to create a new agent package that works across multiple AI platforms. They initialize a new package and receive a `package.agent.json` manifest instead of the old `aam.yaml` format. The new manifest supports richer metadata: platform compatibility declarations, permissions, required environment variables, and custom component path overrides.

**Why this priority**: The manifest is the foundation of everything else. No other UAAPS feature works without a valid manifest. Existing users also need backward compatibility with `aam.yaml` so they are not forced to migrate immediately.

**Independent Test**: Run `aam pkg init` and verify a valid `package.agent.json` is generated. Run `aam pkg validate` against it and confirm it passes. Also confirm an existing `aam.yaml` package is still read correctly.

**Acceptance Scenarios**:

1. **Given** a developer runs `aam pkg init` in an empty directory, **When** the command completes, **Then** a `package.agent.json` is created with `name` and `version` fields populated and the file passes schema validation.
2. **Given** a developer runs `aam pkg validate` on a manifest with an invalid field (e.g., invalid SemVer, name exceeding 64 characters), **When** validation runs, **Then** the CLI reports each specific validation error with the field name and the rule violated.
3. **Given** an existing package directory contains only `aam.yaml`, **When** any CLI command reads the manifest, **Then** it parses `aam.yaml` successfully without requiring migration.
4. **Given** a package directory contains both `package.agent.json` and `package.agent.yaml`, **When** the CLI reads the manifest, **Then** `package.agent.json` takes precedence and `package.agent.yaml` is ignored.
5. **Given** a manifest declares required environment variables in the `env` field, **When** a developer installs the package and those variables are not set, **Then** the CLI prompts securely for each missing value before proceeding.
6. **Given** a manifest declares `permissions` (e.g., filesystem write, network access), **When** a developer installs the package, **Then** the CLI displays the full list of requested permissions and requires explicit confirmation before proceeding.

---

### User Story 2 - Install Packages with System Dependency Pre-flight Checks (Priority: P1)

A developer installs an agent package that requires system-level tools — a specific runtime version, OS binaries, package manager packages, or MCP servers. Before any package files are placed, the CLI verifies that all system requirements are met and guides the developer through resolving any gaps.

**Why this priority**: Without system dependency validation, packages silently fail at runtime after a successful-looking install. Pre-flight checks are a critical safety gate for package reliability.

**Independent Test**: Install a package with `systemDependencies` declared. Verify the CLI checks each requirement, reports which are satisfied, and blocks or warns on missing ones.

**Acceptance Scenarios**:

1. **Given** a package declares `systemDependencies`, **When** `aam install` runs, **Then** the CLI performs pre-flight checks for all declared system requirements before installing any package files.
2. **Given** all system dependencies are satisfied, **When** pre-flight checks complete, **Then** the CLI proceeds with installation and displays a summary of verified requirements.
3. **Given** one or more required system dependencies are missing, **When** pre-flight checks run, **Then** the CLI lists each missing item with human-readable install instructions and prompts the user to continue, abort, or auto-install.
4. **Given** the `--install-system-deps` flag is provided, **When** pip or npm packages are missing, **Then** the CLI automatically installs them without additional prompts.
5. **Given** the `--install-system-deps` flag is provided but brew or apt packages are missing, **When** the CLI would need elevated privileges, **Then** it prompts the user rather than auto-installing, unless `--allow-sudo` is also specified.
6. **Given** a package has optional system dependencies that are missing, **When** pre-flight checks run, **Then** the CLI warns about them but does not block installation.
7. **Given** a developer runs `aam check --system`, **When** the command completes, **Then** it verifies all system dependencies declared by installed packages and reports pass/fail status for each item.

---

### User Story 3 - Resolve and Inspect Dependency Trees (Priority: P2)

A developer works with packages that have transitive dependencies. They need tools to understand the full resolved dependency graph — what is installed, why each package is present, whether anything is outdated or conflicting, and how to keep the tree clean.

**Why this priority**: Dependency tree transparency is essential for debugging, auditing, and maintaining complex multi-package setups. Without it, developers cannot understand what is installed or why.

**Independent Test**: Install a package with at least two levels of transitive dependencies. Run `aam tree` and `aam why <package>` and verify the output accurately reflects the installed graph.

**Acceptance Scenarios**:

1. **Given** a project has packages installed, **When** the developer runs `aam tree`, **Then** the CLI displays the full resolved dependency tree with package names and pinned versions.
2. **Given** a developer runs `aam tree --depth=1`, **When** the command completes, **Then** only direct dependencies are displayed, not transitive ones.
3. **Given** a transitive dependency is installed, **When** the developer runs `aam why <package-name>`, **Then** the CLI identifies which parent package requires it and the version constraint that triggered its inclusion.
4. **Given** a project has installed packages, **When** the developer runs `aam check`, **Then** the CLI verifies all dependencies are installed and mutually compatible, reporting any issues found.
5. **Given** a developer runs `aam outdated`, **When** newer versions are available for installed packages, **Then** the CLI lists each package with its currently installed version and the newest available version.
6. **Given** compatible duplicate package versions exist in the installed tree, **When** the developer runs `aam dedupe`, **Then** the CLI collapses them to a single shared version and reports what changed.
7. **Given** installed packages exist that are no longer declared in the manifest, **When** the developer runs `aam prune`, **Then** the CLI removes them and reports each package removed.
8. **Given** two installed packages require incompatible versions of the same transitive dependency, **When** the resolver detects the conflict, **Then** the CLI reports the conflict clearly — identifying both packages and the incompatible version requirements — and refuses to install until resolved.

---

### User Story 4 - Discover Artifacts Automatically by Convention (Priority: P2)

A package author creates a package following the standard directory layout (`skills/`, `agents/`, `commands/`, `rules/`, `hooks/`, `mcp/`) without listing each artifact explicitly in the manifest. The CLI discovers all artifacts automatically from their standard locations.

**Why this priority**: Convention over configuration eliminates repetitive manifest authoring and lowers the barrier to creating correct packages. It also enables package evolution without manifest updates.

**Independent Test**: Create a package with standard directory structure but no `artifacts` section in the manifest. Run `aam pkg validate` and `aam install` and confirm all artifacts in the standard directories are discovered and registered.

**Acceptance Scenarios**:

1. **Given** a package omits the `artifacts` section from its manifest, **When** the CLI processes the package, **Then** it scans `skills/`, `agents/`, `commands/`, `rules/`, `hooks/hooks.json`, and `mcp/servers.json` and registers all discovered artifacts.
2. **Given** a manifest declares a custom path for a component (e.g., `"skills": "./custom-skills"`), **When** the CLI discovers artifacts, **Then** it uses the declared path instead of the convention default.
3. **Given** a package includes lifecycle hooks in `hooks/hooks.json`, **When** the package is installed, **Then** the hooks are registered and activated for the appropriate lifecycle events.
4. **Given** a package includes an MCP server config in `mcp/servers.json`, **When** the package is installed, **Then** the MCP configuration is registered for the deployment target.
5. **Given** an agent is defined as a directory containing `agent.yaml` and `system-prompt.md`, **When** the package is installed, **Then** the agent definition is parsed correctly from both files.
6. **Given** a package uses the legacy single-file agent format (a single `.md` file), **When** the package is installed, **Then** the CLI accepts it for backward compatibility.

---

### User Story 5 - Enforce Governance Policies Before Install and Publish (Priority: P2)

An enterprise administrator configures policies that govern which packages may be installed in their environment — restricting by scope, requiring package signatures, mandating specific version tags, and blocking specific packages. These policies are checked automatically before any install or publish operation.

**Why this priority**: Enterprise compliance requires consistent, automatic enforcement of policy rules. Without client-side gates, violations can only be detected after the fact, increasing risk.

**Independent Test**: Configure each governance policy type in `config.yaml`. Attempt installs that violate each policy. Confirm each attempt is blocked with a policy-specific message.

**Acceptance Scenarios**:

1. **Given** `allowed_scopes` is configured with a list, **When** a developer attempts to install a package from an unlisted scope, **Then** the CLI blocks the install and names the violated policy.
2. **Given** `require_signature: true` is set, **When** an unsigned package is requested for install, **Then** the CLI blocks the install and explains that a valid signature is required.
3. **Given** `require_tag: "stable"` is configured, **When** a developer installs a package version that does not carry the `stable` dist-tag, **Then** the CLI blocks the install.
4. **Given** a package name matches an entry in `blocked_packages`, **When** an install is attempted, **Then** the CLI immediately rejects it and identifies the blocking rule.
5. **Given** `publish_policy.require_signature: true` is set, **When** a developer runs `aam pkg publish` without signing the package, **Then** the CLI blocks the publish operation and explains what is required.

---

### User Story 6 - Deploy All Artifact Types Across Platforms (Priority: P3)

A developer installs or deploys a universal package and the CLI correctly maps all artifact types — Skills, Commands, Rules, Hooks, and MCP configurations — to the platform-native locations for Claude Code, Cursor, Copilot, and Codex. The `aam convert` command correctly transforms artifacts between platform formats.

**Why this priority**: Platform adapter correctness is a product quality requirement. Incorrect mapping produces broken or incomplete installations on non-Claude Code platforms.

**Independent Test**: Deploy a package containing each artifact type to Claude Code and Cursor. Verify each artifact appears in the correct platform-specific location with the correct format.

**Acceptance Scenarios**:

1. **Given** a package includes `commands/*.md`, **When** deployed to Claude Code, **Then** the commands appear in the platform-expected commands location and are invocable.
2. **Given** a package includes `rules/*/RULE.md`, **When** deployed to Cursor, **Then** the rules are correctly converted to Cursor's native rule format in the correct directory.
3. **Given** a package includes `hooks/hooks.json`, **When** deployed to each supported platform, **Then** hook events are mapped to the platform's native event names and the config is placed in the platform's hook configuration location.
4. **Given** a package includes `mcp/servers.json`, **When** deployed to Claude Code, **Then** the MCP configuration is placed in the platform-expected location with the correct file format.
5. **Given** a developer runs `aam convert` between two platform formats, **When** the conversion completes, **Then** all supported artifact types are converted with correct field mappings and no artifacts are silently dropped.

---

### User Story 7 - Use New and Updated MCP Server Tools (Priority: P3)

An AI agent interacting with the aam-cli through the MCP server interface can call new tools for the new CLI commands (`tree`, `check`, `audit`, `why`, `dedupe`, `prune`) and can use updated tools that handle the new manifest format and dependency types.

**Why this priority**: The MCP server is the programmatic interface for AI-driven package management. New CLI capabilities must be accessible via MCP to keep both interfaces in sync.

**Independent Test**: Start the MCP server and call each new tool. Verify the response matches the equivalent CLI output for the same inputs.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** an agent calls the `aam_tree` tool, **Then** it returns the resolved dependency tree in a structured format equivalent to `aam tree` CLI output.
2. **Given** the MCP server is running, **When** an agent calls the `aam_check` tool, **Then** it returns dependency verification status for all installed packages.
3. **Given** the MCP server is running, **When** an agent calls the `aam_audit` tool, **Then** it returns security findings for installed packages with severity levels.
4. **Given** the MCP server is running, **When** an agent calls the existing `aam_install` tool with new optional/peer/system dependency declarations, **Then** the tool handles them correctly.
5. **Given** the MCP server is running and a manifest resource is requested, **When** the package uses `package.agent.json`, **Then** the resource returns the `package.agent.json` content.

---

### Edge Cases

- What happens when a package's dependency graph contains a cycle (A depends on B, B depends on A)?
- How does the resolver handle a conflict where two packages require incompatible versions of the same transitive dependency, and the user has not set a `resolutions` override?
- What happens when `aam install --frozen` is run but the lock file does not exist or is stale relative to the manifest?
- What happens when both `package.agent.json` and `aam.yaml` exist in the same package and the user has made changes only to `aam.yaml`?
- How does the CLI behave when a skill's `compatibility.requires` block is stricter than what the package-level `systemDependencies` declares?
- How does governance enforcement behave when a blocked package appears only as a transitive (not direct) dependency?
- What happens if an auto-install of a pip or npm package fails midway due to a network error or permission issue?
- How does the install directory migration from `.aam/packages/` to `.agent-packages/` handle projects that already have packages installed in the old location?
- What happens when a package uses the old `instructions/` directory convention instead of the new `rules/` structure?

## Requirements *(mandatory)*

### Functional Requirements

**Manifest & Package Initialization**

- **FR-001**: The CLI MUST generate `package.agent.json` as the default manifest format when running `aam pkg init` or `aam pkg create`.
- **FR-002**: The CLI MUST accept `package.agent.json` as the primary manifest format and `package.agent.yaml` as a secondary authoring format, with JSON taking precedence when both exist in the same directory.
- **FR-003**: The CLI MUST validate manifests against the full UAAPS schema, including all new fields: `category`, `engines`, `env`, `permissions`, component overrides (`skills`, `commands`, `agents`, `rules`, `hooks`, `mcp`), and vendor extensions (`x-*`).
- **FR-004**: During package installation, the CLI MUST securely prompt for any environment variables declared as `required: true` in the `env` manifest field that are not already present in the user's environment.
- **FR-005**: During package installation, the CLI MUST display all permissions declared in the `permissions` manifest field and require explicit user confirmation before proceeding.

**Dependency Resolution**

- **FR-006**: The dependency resolver MUST support four dependency types: `dependencies` (required — install fails if missing), `optionalDependencies` (install continues gracefully if missing), `peerDependencies` (must be satisfied by the host environment, not auto-installed), and `systemDependencies` (OS-level pre-flight checks).
- **FR-007**: The lock file MUST use the `package.agent.lock` JSON format, replacing `aam-lock.yaml`, and MUST include a `systemChecks` section recording system dependency verification results.
- **FR-008**: The resolver MUST implement dependency hoisting, flattening compatible shared transitive dependencies to the install root to minimize duplication.
- **FR-009**: The CLI MUST support resolution strategy flags on `aam install`: `--frozen` (use lock file exactly, fail if stale or missing), `--minimal` (lowest version satisfying each constraint), `--latest` (newest available version), and `--dry-run` (resolve and display without installing).
- **FR-010**: The resolver MUST detect circular dependency graphs and report them as errors, identifying the cycle path before refusing to install.
- **FR-011**: The install root MUST change from `.aam/packages/` to `.agent-packages/`. The CLI MUST detect existing installs in the old location and offer to migrate them.
- **FR-012**: The CLI MUST support a `resolutions` field in `package.agent.json` to force a specific version for any transitive dependency, bypassing normal constraint resolution.

**System Dependencies**

- **FR-013**: The CLI MUST run system dependency pre-flight checks before installing any package artifacts, covering: runtime versions (Python, Node), OS binaries on `$PATH`, pip/npm/brew/apt/cargo packages, and required MCP servers.
- **FR-014**: When system dependencies are missing, the CLI MUST list each missing item with human-readable installation instructions and present the user with options to continue, abort, or auto-install.
- **FR-015**: With `--install-system-deps`, the CLI MUST automatically install missing pip packages, npm packages, and MCP servers. Brew and apt installs MUST additionally require `--allow-sudo`.
- **FR-016**: The CLI MUST never invoke elevated privilege operations for automatic installs unless `--allow-sudo` is explicitly provided.

**New CLI Commands**

- **FR-017**: The CLI MUST provide `aam tree` to display the full resolved dependency tree with a `--depth=N` flag to limit display depth.
- **FR-018**: The CLI MUST provide `aam why <package>` to explain which installed packages depend on the named package and via what version constraint.
- **FR-019**: The CLI MUST provide `aam check` to verify all declared dependencies are installed and compatible, with a `--system` flag to run only system dependency pre-flight checks.
- **FR-020**: The CLI MUST provide `aam audit` to check installed packages against known security issues, with a `--severity` flag to filter by severity level.
- **FR-021**: The CLI MUST provide `aam dedupe` to flatten compatible duplicate package versions in the installed tree, reducing redundancy.
- **FR-022**: The CLI MUST provide `aam prune` to remove installed packages that are no longer declared in the dependency tree.

**Artifact Auto-Discovery**

- **FR-023**: When a manifest omits the `artifacts` section, the CLI MUST automatically discover artifacts by scanning the standard directories: `skills/`, `agents/`, `commands/`, `rules/`, `hooks/hooks.json`, and `mcp/servers.json`.
- **FR-024**: When a manifest declares custom component paths (e.g., `"skills": "./custom-skills"`), the CLI MUST use those declared paths instead of the convention defaults.
- **FR-025**: The CLI MUST support agents defined as directories containing `agent.yaml` + `system-prompt.md` (structured format), in addition to the legacy single-file agent format.

**Platform Adapters**

- **FR-026**: The install and deploy logic MUST correctly map all artifact types — Skills, Commands, Rules, Hooks, and MCP configurations — to the platform-native locations for Claude Code, Cursor, Copilot, and Codex.
- **FR-027**: The `aam convert` command MUST support conversions between platform formats including: `.instructions.md` to `RULE.md` frontmatter field mapping, hook event name translation between platforms, and MCP configuration format differences.

**Governance**

- **FR-028**: The CLI MUST read governance settings from `config.yaml` and enforce them before any `aam install` or `aam pkg publish` operation: `allowed_scopes`, `require_signature`, `require_tag`, `blocked_packages` (for install) and `require_signature` (for publish).
- **FR-029**: When a governance policy blocks an operation, the CLI MUST provide a clear message identifying the specific policy violated and the reason it applies.

**MCP Server**

- **FR-030**: The MCP server MUST expose new tools for all new CLI commands: `aam_tree`, `aam_check`, `aam_audit`, `aam_why`, `aam_dedupe`, and `aam_prune`.
- **FR-031**: Existing MCP tools (`aam_install`, `aam_validate`, `aam_info`) MUST be updated to handle `package.agent.json`, the new dependency types, and the new resolution strategy flags.
- **FR-032**: The MCP manifest resource MUST serve `package.agent.json` content when that format is present.

### Key Entities

- **Package Manifest** (`package.agent.json` / `package.agent.yaml`): The central descriptor for an agent package. Contains identity (name, version), artifact declarations or convention-based auto-discovery, dependency declarations across four types, environment variable requirements, permission declarations, platform compatibility constraints, and vendor-specific extensions.
- **Lock File** (`package.agent.lock`): A deterministic, versioned snapshot of all resolved dependency versions and their integrity checksums, plus system dependency verification results. Enables reproducible installs across machines and CI environments.
- **Artifact**: A deployable unit within a package. Types: Skill (agent capability, model-invoked), Command (user-invoked prompt slash command), Agent (specialized persona with structured definition), Rule (persistent context — coding standards, conventions), Hook (lifecycle event handler, zero token cost), MCP Server Config (external tool access definition), Prompt (reusable parameterized template).
- **System Dependency**: An OS-level requirement — a runtime version, binary on `$PATH`, package manager package, or MCP server — that must be present on the host machine. Verified by pre-flight checks; auto-installed only for pip/npm/MCP with explicit flags.
- **Governance Policy**: An administrator-configured set of client-side rules that gate install and publish operations. Enforced locally before any network or filesystem operation. Rules include scope allowlists, signature requirements, version tag requirements, and package blocklists.
- **Dependency Resolution Graph**: The directed acyclic graph of all package dependencies (direct, optional, peer, and transitive) computed by the resolver before installation. Must be cycle-free.
- **Dist-tag**: A named alias for a specific package version (e.g., `stable`, `latest`, `bank-approved`) used by governance policies to control which versions may be installed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can initialize and validate a UAAPS-compliant `package.agent.json` package in under 60 seconds using `aam pkg init` followed by `aam pkg validate`.
- **SC-002**: System dependency pre-flight checks complete and display results in under 10 seconds for packages declaring up to 20 system requirements.
- **SC-003**: 100% of existing packages with `aam.yaml` manifests are processed by the updated CLI without requiring any changes to the package files.
- **SC-004**: All 6 new dependency management commands (`tree`, `why`, `check`, `audit`, `dedupe`, `prune`) are available and return accurate, verifiable results.
- **SC-005**: `aam install --frozen` produces identical installed artifact sets across at least two different machines when given the same `package.agent.lock`.
- **SC-006**: 100% of install and publish attempts that violate configured governance policies are blocked — no false negatives.
- **SC-007**: Platform adapters correctly deploy all artifact types (Skills, Commands, Rules, Hooks, MCP) to Claude Code and Cursor with no manual post-processing required by the developer.
- **SC-008**: All new CLI commands have corresponding MCP server tools that return equivalent data to the CLI commands.
- **SC-009**: The resolver correctly detects and rejects circular dependency graphs with an informative error that identifies the cycle.
- **SC-010**: Developers migrating from `.aam/packages/` to `.agent-packages/` can complete migration using a single CLI prompt with no manual file operations.

## Assumptions

- Backward compatibility with existing `aam.yaml` manifests is required. Users are not forced to migrate; the old format continues to work.
- The install root change from `.aam/packages/` to `.agent-packages/` requires a migration path. The CLI detects existing installs at the old location and offers a guided one-step migration.
- The `aam-lock.yaml` lock file is superseded by `package.agent.lock` (JSON). The CLI detects the old format and offers to convert it.
- System dependency auto-install is intentionally gated behind `--allow-sudo` for brew/apt as a security measure, not a limitation.
- Governance policy enforcement is client-side only in this release. Server-side approval workflows (via HTTP registry) are out of scope unless already supported by a connected registry.
- The UAAPS public registry (`registry.agentpkg.io`) is the default remote source. Direct installs, Git sources, and local paths remain supported distribution channels.
- Performance targets assume standard developer hardware and a reliable network connection.
- The UAAPS specification (`universal_package_specification.md` v0.4.0-draft) is the authoritative source of truth for this feature. Divergences from the spec during implementation must be documented.

## Dependencies and Constraints

- **UAAPS Specification**: This feature implements `universal_package_specification.md` (v0.4.0-draft). Changes to the spec during development must be assessed for impact on requirements.
- **Backward Compatibility**: Existing `aam.yaml` manifests, `aam-lock.yaml` lock files, and packages installed in `.aam/packages/` must remain usable without forced migration.
- **Platform Compatibility Boundaries**: Adapter correctness is bounded by what each target platform natively supports. Gaps (e.g., Cursor has no native commands support) are handled via the documented conversion strategies, not full emulation.
- **Security Constraint**: The CLI must never execute system package installs requiring elevated privileges without explicit user consent via `--allow-sudo`.
- **Dependency Graph Constraint**: The resolver must treat circular dependency graphs as hard errors; partial installs from cyclic graphs are not permitted.
