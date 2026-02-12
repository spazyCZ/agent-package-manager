# Feature Specification: CLI Local Repository

**Feature Branch**: `001-cli-local-repository`  
**Created**: 2026-02-08  
**Status**: Implemented (local only)  
**Input**: User description: "Implement aam-cli for local usage with local file repository"

## Implementation Status

**Only the local workflow is implemented.** Remote/HTTP registries are not supported.

| Component | Status | Notes |
|-----------|--------|-------|
| Local file-based registry (`registry init`, `registry add`) | ✅ Implemented | `file://` URLs only |
| Package authoring (`pkg create`, `pkg init`, `pkg validate`, `pkg pack`) | ✅ Implemented | From existing project or scratch |
| Publish to local registry (`pkg publish`) | ✅ Implemented | Writes to local `packages/` |
| Search | ✅ Implemented | Local registry + git sources (materialized to local) |
| Install | ✅ Implemented | From local registry, local path, or `.aam` archive |
| HTTP/remote registry (e.g. test.aamregistry.io) | ❌ Not implemented | Out of scope for this spec; CLI factory supports `local` type only |

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories are PRIORITIZED as user journeys ordered by importance.
  Each user story/journey is INDEPENDENTLY TESTABLE — implementing just ONE of them
  delivers a viable MVP that provides value.
-->

### User Story 1 - Initialize a Local Registry (Priority: P1)

A practitioner wants to start using AAM without any server infrastructure. They run a single command to create a local file-based registry on their filesystem, then configure it as their default registry. This is the foundational step that enables all subsequent local workflows.

**Why this priority**: Without a local registry, no other local workflow (publish, search, install) can function. This is the absolute prerequisite.

**Independent Test**: Can be fully tested by running the init and add commands, then verifying the expected directory structure and configuration files are created. Delivers the value of having a working registry location on disk.

**Acceptance Scenarios**:

1. **Given** the CLI is installed and no registry exists, **When** the user runs `aam registry init ~/my-packages`, **Then** a new directory is created at the specified path containing `registry.yaml`, an empty `index.yaml`, and an empty `packages/` directory.
2. **Given** a local registry has been initialized, **When** the user runs `aam registry add local file:///home/user/my-packages --default`, **Then** the registry is saved to the user's configuration (`~/.aam/config.yaml`) and marked as the default.
3. **Given** a local registry has been initialized, **When** the user runs `aam registry init` at a path that already contains a registry, **Then** the system informs the user that a registry already exists and does not overwrite it.
4. **Given** the `--default` flag is used during `aam registry init`, **When** the command completes, **Then** the registry is both created and set as the default in one step.

---

### User Story 2 - Create and Validate a Package from an Existing Project (Priority: P1)

A practitioner has been working on a project and has organically created skills, agents, prompts, or instructions in platform-specific locations (e.g., `.cursor/skills/`, `.cursor/rules/`). They want to bundle these into an AAM package that can be published and shared.

**Why this priority**: Package creation is the entry point for all authoring workflows. Without the ability to create packages, there is nothing to publish or install.

**Independent Test**: Can be tested by running `aam create-package` in a project that contains artifacts in known locations, selecting artifacts interactively, and verifying that `aam.yaml` and the correct directory structure are produced. `aam validate` then confirms the package is well-formed.

**Acceptance Scenarios**:

1. **Given** a project containing artifacts in `.cursor/skills/`, `.cursor/rules/`, and `.cursor/prompts/`, **When** the user runs `aam create-package`, **Then** the CLI auto-detects all artifacts, presents an interactive selection list, and creates the package with an `aam.yaml` manifest.
2. **Given** a project with detected artifacts, **When** the user selects "copy" mode (default), **Then** files are copied into the standard AAM directory structure (`skills/`, `agents/`, `prompts/`, `instructions/`) while originals remain untouched.
3. **Given** a project with detected artifacts, **When** the user selects "reference" mode, **Then** only `aam.yaml` is created and it points to files at their current locations.
4. **Given** a valid `aam.yaml` exists, **When** the user runs `aam validate`, **Then** the CLI validates the manifest structure, checks that all referenced artifact paths exist, and reports success or lists specific errors.
5. **Given** a user wants to skip prompts, **When** they run `aam create-package --all --name my-pkg --yes`, **Then** the package is created non-interactively with all detected artifacts included.
6. **Given** a user wants to preview, **When** they run `aam create-package --dry-run`, **Then** the CLI shows what would be detected and created without writing any files.

---

### User Story 3 - Create a New Package from Scratch (Priority: P2)

A practitioner wants to create a brand-new AAM package from scratch — they have no existing artifacts yet. They use `aam init` to scaffold the package structure interactively.

**Why this priority**: Important for new package creation, but less common than packaging existing artifacts. Most users will start with `create-package`.

**Independent Test**: Can be tested by running `aam init` in an empty directory, answering prompts, and verifying the scaffolded directory structure and generated `aam.yaml`.

**Acceptance Scenarios**:

1. **Given** an empty directory, **When** the user runs `aam init`, **Then** the CLI prompts for name, version, description, author, license, artifact types, and platforms, then generates `aam.yaml` and the selected artifact directories.
2. **Given** the user provides a scoped name like `@author/my-package`, **When** initialization completes, **Then** the `aam.yaml` contains the full scoped name and the scope field is correctly set.
3. **Given** the user provides a package name as an argument (`aam init my-package`), **When** initialization completes, **Then** it skips the name prompt and uses the provided name.

---

### User Story 4 - Pack and Publish to Local Registry (Priority: P1)

A practitioner has a valid package and wants to build a distributable archive and publish it to their local registry so that other projects (or team members with access to the same filesystem) can install it.

**Why this priority**: Publishing is the bridge between authoring and consumption. Without publish, packages remain local to a single project.

**Independent Test**: Can be tested by running `aam pack` and verifying the `.aam` archive is created, then running `aam publish --registry local` and verifying the archive appears in the local registry's `packages/` directory with correct `metadata.yaml` and updated `index.yaml`.

**Acceptance Scenarios**:

1. **Given** a valid package with `aam.yaml`, **When** the user runs `aam pack`, **Then** a `.aam` archive (gzipped tar) is created in the current directory containing `aam.yaml` and all declared artifact files, with a SHA-256 checksum reported.
2. **Given** a `.aam` archive exists and a local registry is configured, **When** the user runs `aam publish --registry local`, **Then** the archive is copied to the registry's `packages/<name>/versions/` directory, `metadata.yaml` is created or updated with version info, and `index.yaml` is rebuilt.
3. **Given** a scoped package `@author/my-pkg`, **When** the user publishes, **Then** the archive is stored under `packages/@author/my-pkg/versions/` in the registry.
4. **Given** the user tries to publish a version that already exists, **When** the publish command runs, **Then** the CLI reports an error and does not overwrite the existing version.
5. **Given** `aam validate` reports errors, **When** the user runs `aam pack`, **Then** the pack operation fails and directs the user to fix validation errors first.

---

### User Story 5 - Search the Local Registry (Priority: P2)

A practitioner wants to discover packages available in their local registry by searching for keywords, names, or descriptions.

**Why this priority**: Search is essential for discovery, but practitioners can also install by name if they know the package. Less critical than core authoring/publishing.

**Independent Test**: Can be tested by publishing a package to a local registry, then running `aam search <query>` and verifying matching results are returned with name, version, and description.

**Acceptance Scenarios**:

1. **Given** packages have been published to a local registry, **When** the user runs `aam search "audit"`, **Then** the CLI returns a list of packages whose name, description, or keywords match the query.
2. **Given** no packages match a query, **When** the user runs `aam search "nonexistent"`, **Then** the CLI reports "No packages found" with a friendly message.
3. **Given** multiple registries are configured, **When** the user runs `aam search`, **Then** results are aggregated from all configured registries in priority order.

---

### User Story 6 - Install a Package from Local Registry (Priority: P1)

A practitioner wants to install a package from their local registry into a project. The CLI downloads the package, resolves dependencies, extracts it, and deploys artifacts to the target platform (e.g., Cursor).

**Why this priority**: Installation is the primary consumer-facing workflow. It directly delivers value by making agent artifacts usable in the practitioner's IDE.

**Independent Test**: Can be tested by publishing a package to a local registry, then running `aam install <package>` in a different project directory and verifying the package is extracted to `.aam/packages/`, a lock file is written, and artifacts are deployed to `.cursor/` (or the configured platform).

**Acceptance Scenarios**:

1. **Given** a package exists in the local registry, **When** the user runs `aam install @author/my-package`, **Then** the CLI resolves the package, downloads the archive from the local registry, extracts it to `.aam/packages/`, writes/updates `.aam/aam-lock.yaml`, and deploys artifacts to the default platform.
2. **Given** a package with dependencies, **When** the user installs it, **Then** all transitive dependencies are resolved and installed automatically.
3. **Given** the user specifies a version (`aam install @author/my-package@1.0.0`), **When** the install runs, **Then** exactly that version is installed.
4. **Given** the user runs `aam install @author/my-package --no-deploy`, **When** the install completes, **Then** the package is downloaded and extracted but not deployed to any platform.
5. **Given** a package is already installed, **When** the user runs `aam install` for the same package and version, **Then** the CLI informs the user it is already installed and takes no action.
6. **Given** Cursor is the default platform, **When** a package is installed with deploy, **Then** skills are deployed to `.cursor/skills/`, agents to `.cursor/rules/`, prompts to `.cursor/prompts/`, and instructions to `.cursor/rules/`.
7. **Given** a package is installed from a local directory path (`aam install ./my-local-package/`), **When** the install completes, **Then** the package is installed as if it came from a registry.
8. **Given** a package is installed from a `.aam` archive file (`aam install package-1.0.0.aam`), **When** the install completes, **Then** the package is installed without requiring a registry.

---

### User Story 7 - List and Inspect Installed Packages (Priority: P2)

A practitioner wants to see what packages are installed in their project and get details about a specific package.

**Why this priority**: Useful for managing installed packages, but secondary to the core install/publish workflow.

**Independent Test**: Can be tested by installing packages, then running `aam list` and `aam info <name>` and verifying correct output.

**Acceptance Scenarios**:

1. **Given** packages are installed in a project, **When** the user runs `aam list`, **Then** the CLI displays a table of installed packages with name, version, and artifact counts.
2. **Given** packages with dependencies are installed, **When** the user runs `aam list --tree`, **Then** the CLI displays a dependency tree.
3. **Given** a specific package is installed, **When** the user runs `aam info <package-name>`, **Then** the CLI displays full metadata: name, version, description, author, license, artifacts, dependencies, and deployment paths.

---

### User Story 8 - Configure Default Platform and Settings (Priority: P2)

A practitioner wants to configure AAM settings like the default deployment platform, author defaults, and registry sources.

**Why this priority**: Configuration is necessary for a smooth experience but most settings have sensible defaults.

**Independent Test**: Can be tested by running `aam config set default_platform cursor`, then `aam config get default_platform` and verifying the value.

**Acceptance Scenarios**:

1. **Given** the CLI is installed, **When** the user runs `aam config set default_platform cursor`, **Then** the value is saved to `~/.aam/config.yaml`.
2. **Given** a config key is set, **When** the user runs `aam config get default_platform`, **Then** the current value is displayed.
3. **Given** the user wants to see all config, **When** they run `aam config list`, **Then** all configuration key-value pairs are displayed with their sources (global, project, default).

---

### User Story 9 - Uninstall a Package (Priority: P3)

A practitioner wants to remove an installed package and its deployed artifacts.

**Why this priority**: Important for lifecycle management, but lower urgency than install/publish.

**Independent Test**: Can be tested by installing a package, then running `aam uninstall <name>` and verifying both `.aam/packages/` and deployed platform artifacts are removed.

**Acceptance Scenarios**:

1. **Given** a package is installed, **When** the user runs `aam uninstall <package-name>`, **Then** the package is removed from `.aam/packages/`, its deployed artifacts are cleaned up from all platforms, and the lock file is updated.
2. **Given** a package has dependents, **When** the user tries to uninstall it, **Then** the CLI warns about dependent packages and asks for confirmation.

---

### Edge Cases

- What happens when the user runs `aam install` but no registries are configured? The CLI should display a clear error with instructions to configure a registry.
- What happens when the local registry directory is not writable? The CLI should catch the permission error and display a helpful message.
- What happens when a package archive is corrupted? Checksum verification should catch the corruption and report a clear error.
- What happens when two packages require conflicting versions of the same dependency? The CLI should report the conflict clearly with both constraints shown.
- What happens when the `aam.yaml` references artifacts that don't exist at the declared paths? `aam validate` should catch and report each missing path.
- What happens when the user runs commands in a directory without `aam.yaml` (for authoring commands)? The CLI should report "No aam.yaml found" with a suggestion to run `aam init` or `aam create-package`.
- What happens when the user's `~/.aam/` directory doesn't exist yet? The CLI should create it automatically on first use.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: CLI MUST provide a `registry init <path>` command that creates a local file-based registry with `registry.yaml`, `index.yaml`, and `packages/` directory.
- **FR-002**: CLI MUST provide a `registry add <name> <url> [--default]` command that saves registry sources to user configuration.
- **FR-003**: CLI MUST provide a `registry list` command that displays all configured registries.
- **FR-004**: CLI MUST provide a `create-package` command that auto-detects artifacts in known platform-specific locations and creates an `aam.yaml` manifest.
- **FR-005**: Artifact auto-detection MUST scan for skills (`**/SKILL.md`), agents (`**/agent.yaml`, `.cursor/rules/agent-*.mdc`), prompts (`prompts/*.md`, `.cursor/prompts/*.md`), and instructions (`.cursor/rules/*.mdc`, `CLAUDE.md`, `AGENTS.md`).
- **FR-006**: `create-package` MUST support copy (default), reference, and move file organization modes.
- **FR-007**: `create-package` MUST support non-interactive mode via `--all`, `--name`, `--version`, `--yes` flags.
- **FR-008**: `create-package` MUST support `--dry-run` to preview without writing files.
- **FR-009**: CLI MUST provide an `init` command for scaffolding new packages interactively.
- **FR-010**: CLI MUST provide a `validate` command that checks manifest schema, artifact path existence, and artifact file well-formedness.
- **FR-011**: CLI MUST provide a `pack` command that creates a `.aam` gzipped tar archive containing `aam.yaml` and all declared artifacts, with SHA-256 checksum.
- **FR-012**: Archive size MUST be enforced at a maximum of 50 MB.
- **FR-013**: CLI MUST provide a `publish` command that copies the `.aam` archive to a local registry, creates/updates `metadata.yaml`, and rebuilds `index.yaml`.
- **FR-014**: Publish MUST reject duplicate versions — the same version number cannot be published twice.
- **FR-015**: CLI MUST provide a `search <query>` command that performs case-insensitive substring matching against package name, description, and keywords in `index.yaml`.
- **FR-016**: CLI MUST provide an `install <package>` command that resolves packages from configured registries, downloads archives, extracts to `.aam/packages/`, writes a lock file, and deploys artifacts to the default platform.
- **FR-017**: Install MUST support multiple source types: registry name, local directory path, and `.aam` archive file.
- **FR-018**: Install MUST support version specifiers (`@author/pkg@1.0.0`) and both scoped and unscoped package names.
- **FR-019**: Install MUST resolve transitive dependencies recursively using a greedy algorithm.
- **FR-020**: Install MUST generate or update `.aam/aam-lock.yaml` with resolved versions and checksums.
- **FR-021**: Install MUST support `--no-deploy` to skip platform deployment.
- **FR-022**: CLI MUST implement a Cursor platform adapter that deploys skills to `.cursor/skills/`, agents as `.cursor/rules/agent-*.mdc`, prompts to `.cursor/prompts/`, and instructions as `.cursor/rules/*.mdc`.
- **FR-023**: Scoped package names MUST be mapped to filesystem-safe names using the double-hyphen convention (`@scope/name` → `scope--name`).
- **FR-024**: CLI MUST provide a `list` command showing installed packages with name, version, and artifact counts.
- **FR-025**: CLI MUST provide an `info <package>` command showing full package metadata.
- **FR-026**: CLI MUST provide `config set`, `config get`, and `config list` commands for managing configuration.
- **FR-027**: Configuration MUST follow the precedence: CLI flags > project (`.aam/config.yaml`) > global (`~/.aam/config.yaml`) > defaults.
- **FR-028**: CLI MUST provide an `uninstall <package>` command that removes the package from `.aam/packages/` and cleans up deployed platform artifacts.
- **FR-029**: All CLI commands MUST provide meaningful error messages with actionable suggestions when operations fail.
- **FR-030**: CLI MUST automatically create `~/.aam/` and `.aam/` directories as needed on first use.
- **FR-031**: Manifest parsing MUST validate against the `aam.yaml` schema using pydantic models with strict types.
- **FR-032**: CLI MUST support both scoped (`@author/package`) and unscoped (`package`) naming throughout all commands.

### Key Entities

- **Package**: A distributable unit containing one or more artifacts, described by an `aam.yaml` manifest. Key attributes: name (scoped or unscoped), version (semver), description, author, license, artifacts, dependencies, platform configuration.
- **Artifact**: An individual skill, agent, prompt, or instruction within a package. Key attributes: name, path (relative to package root), description, type.
- **Registry**: A storage location for published packages. For this feature, a local file-based registry with `registry.yaml`, `index.yaml`, and per-package `metadata.yaml` + `versions/` directory.
- **Lock File**: A snapshot of resolved dependency versions and checksums (`.aam/aam-lock.yaml`) to ensure reproducible installs.
- **Configuration**: User and project-level settings stored in YAML files controlling default platform, registry sources, and behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from zero to a working local package workflow (create registry, create package, validate, pack, publish, install) in under 10 minutes following the User Guide.
- **SC-002**: All core CLI commands (`registry init`, `create-package`, `init`, `validate`, `pack`, `publish`, `search`, `install`, `list`, `info`, `config`, `uninstall`) complete successfully for the documented happy-path scenarios.
- **SC-003**: The entire local workflow operates with zero network dependencies — no Docker, no database, no server, no internet connection required.
- **SC-004**: A package published to a local registry can be installed in a different project directory and its artifacts are correctly deployed to the Cursor platform locations.
- **SC-005**: Dependency resolution correctly handles packages with 1-3 levels of transitive dependencies without errors.
- **SC-006**: The CLI provides clear, actionable error messages for all documented edge cases (missing config, invalid manifest, corrupted archive, version conflicts, missing paths).
- **SC-007**: Automated tests achieve at least 80% code coverage across the CLI codebase.
- **SC-008**: All CLI operations on a package with up to 20 artifacts complete within 5 seconds on a standard developer machine.

## Assumptions

- The primary deployment platform for Phase 1 is **Cursor**. Other platform adapters (Claude, Copilot, Codex) are out of scope for this feature and will be addressed in a later phase.
- The CLI framework is **Click 8.1+** with **Rich 13.0+** for terminal UI, as specified in the project's existing setup.
- The local registry uses a flat YAML-based structure (no database) as defined in the DESIGN.md Section 6.2.
- Package signing and verification are out of scope for this feature — only SHA-256 checksum verification is required.
- User authentication (`aam register`, `aam login`) is not needed for local registries and is out of scope.
- The MCP server mode (`aam mcp serve`) is out of scope for this feature.
- **Git-based and HTTP-based registries are out of scope** — only local file-based registries are supported. Skills from remote git repos are handled via a separate mechanism (spec 003/004: `aam source add` / sources), which materializes them into a local `~/.aam/sources-registry/`.
- Interactive selection in `aam create-package` will use Rich for the terminal UI (checkboxes, prompts).
