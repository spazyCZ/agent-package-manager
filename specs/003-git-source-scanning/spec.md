# Feature Specification: Git Repository Source Scanning & Artifact Discovery

**Feature Branch**: `003-git-source-scanning`  
**Created**: 2026-02-08  
**Status**: Draft  
**Input**: User description: "Implement git repository source scanning and artifact discovery for AAM CLI and MCP server"

**Key Reference Document**: [`docs/work/git_repo_skills.md`](../../docs/work/git_repo_skills.md) — This is the primary source of truth for detailed requirements, use cases, data models, and implementation guidance. It MUST be used during the planning phase.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories are PRIORITIZED as user journeys ordered by importance.
  Each user story/journey is INDEPENDENTLY TESTABLE — implementing just ONE of them
  delivers a viable MVP that provides value.
-->

### User Story 1 - Add a Remote Git Source and Discover Artifacts (Priority: P1)

A practitioner discovers a public GitHub repository containing useful AI agent skills (e.g., `openai/skills`, `github/awesome-copilot`). They want to register this repository as a tracked artifact source in AAM so they can explore its contents and later package artifacts from it. They run a single command with a shorthand like `openai/skills` or a full URL, and AAM clones the repository, scans for artifacts, and reports what was found.

**Why this priority**: This is the foundational capability that enables all other git source workflows. Without the ability to add and scan a remote source, no other feature (update, candidates, packaging from source) can function.

**Independent Test**: Can be fully tested by running `aam source add openai/skills`, verifying the repository is cloned to the cache directory, the source entry appears in `~/.aam/config.yaml`, and the scan reports the correct count of discovered skills, agents, prompts, and instructions. Delivers the value of discovering artifacts in a remote repo.

**Acceptance Scenarios**:

1. **Given** the CLI is installed and no sources are configured, **When** the user runs `aam source add openai/skills`, **Then** the CLI clones the repository (shallow), scans for artifacts, saves the source entry to `~/.aam/config.yaml`, and displays a summary showing the number of discovered artifacts by type.
2. **Given** a full GitHub tree URL is provided, **When** the user runs `aam source add https://github.com/openai/skills/tree/main/skills/.curated`, **Then** the CLI parses the URL into owner, repo, ref, and path components, clones only the necessary content, and scopes the scan to the specified subdirectory.
3. **Given** a repository contains artifacts in dot-prefixed category directories (e.g., `.curated/`, `.experimental/`, `.system/`), **When** the source is scanned, **Then** all artifacts in those dot-prefixed directories are discovered — they are never skipped.
4. **Given** a source for `openai/skills` already exists, **When** the user runs `aam source add openai/skills` again, **Then** the CLI displays a message that the source is already configured and suggests `aam source update` instead.
5. **Given** the user wants to scope a source to a subdirectory, **When** they run `aam source add openai/skills --path skills/.curated`, **Then** the source is named `openai/skills:.curated` and only the specified path is scanned for artifacts.
6. **Given** the user provides a custom name, **When** they run `aam source add https://gitlab.com/team/artifacts --name team-artifacts`, **Then** the source is stored with the custom display name.

---

### User Story 2 - Update Cached Sources and Detect Changes (Priority: P1)

A practitioner has previously added remote sources and wants to check if anything changed upstream since the last fetch. They run an update command and get a clear report showing new, modified, and removed artifacts — enabling them to decide whether to re-package or adopt new artifacts.

**Why this priority**: Sources become stale over time. The ability to detect upstream changes is essential for keeping artifact inventories current and is a prerequisite for informed decision-making about what to package.

**Independent Test**: Can be tested by adding a source, modifying the remote (or simulating a commit change), then running `aam source update <name>` and verifying the output correctly reports new, modified, removed, and unchanged artifact counts.

**Acceptance Scenarios**:

1. **Given** a source was previously added and cached, **When** the user runs `aam source update "openai/skills:.curated"`, **Then** the CLI fetches upstream changes, compares the new commit against the stored last-commit SHA, and displays a change report showing new, modified, and removed artifacts.
2. **Given** multiple sources are configured, **When** the user runs `aam source update --all`, **Then** all sources are updated and a summary line is shown for each source.
3. **Given** a source's remote repository is unreachable, **When** the update runs, **Then** the CLI retries with backoff, then reports the failure clearly while continuing to update other sources.
4. **Given** a private repository requires authentication, **When** the `GH_TOKEN` environment variable is not set, **Then** the CLI displays an actionable error message suggesting the user set the token or configure SSH keys.
5. **Given** the user wants to preview changes without updating the cache, **When** they run `aam source update "openai/skills:.curated" --dry-run`, **Then** the CLI shows what would change without modifying the local cache.

---

### User Story 3 - List Candidates and Create Packages from Remote Sources (Priority: P1)

A practitioner wants to see all artifacts discovered across their registered remote sources that are not yet managed by any AAM package. They then select specific artifacts and create a new AAM package from them, complete with provenance metadata tracking where the artifacts originated.

**Why this priority**: This is the end-to-end value delivery — practitioners use AAM to discover, select, and package artifacts from community repositories. Without this, the source scanning feature has no actionable outcome.

**Independent Test**: Can be tested by adding a source, running `aam source candidates` to see the list, then running `aam create-package --from-source "openai/skills:.curated" --artifacts gh-fix-ci,playwright` and verifying the package is created with correct `aam.yaml` including provenance metadata.

**Acceptance Scenarios**:

1. **Given** sources are configured and scanned, **When** the user runs `aam source candidates`, **Then** the CLI lists all artifacts from remote sources and the local project that are not yet in any AAM package, grouped by source.
2. **Given** the user wants to filter candidates, **When** they run `aam source candidates --source "openai/skills:.curated" --type skill`, **Then** only skill-type artifacts from the specified source are shown.
3. **Given** the user selects artifacts from a remote source, **When** they run `aam create-package --from-source "openai/skills:.curated" --artifacts gh-fix-ci,playwright`, **Then** the CLI copies the selected artifacts from the cache, creates `aam.yaml` with provenance metadata (source URL, ref, commit, path), and generates file checksums.
4. **Given** a repository contains skill directories with companion vendor agent files (e.g., `agents/openai.yaml`), **When** the skill is packaged, **Then** the vendor agent file is treated as companion metadata of the skill, not as a standalone agent.
5. **Given** the user runs `aam source candidates --json`, **When** the output is generated, **Then** it is valid JSON suitable for scripting and automation.

---

### User Story 4 - Verify Installed Package Integrity (Priority: P2)

A practitioner has installed packages and wants to check whether any installed files have been modified locally (e.g., a team member tweaked a skill's prompt). They run a verification command that compares installed files against their stored checksums, identifying modifications, missing files, and untracked additions.

**Why this priority**: Integrity verification prevents silent drift between installed packages and their original content. This is important for reproducibility and upgrade safety, but does not block the core discovery-to-packaging workflow.

**Independent Test**: Can be tested by installing a package, manually modifying one of its files, then running `aam verify <package>` and verifying it correctly reports the modified file.

**Acceptance Scenarios**:

1. **Given** a package is installed with file checksums recorded in `aam-lock.yaml`, **When** the user runs `aam verify @myorg/my-agent`, **Then** the CLI recomputes checksums for all installed files and reports which are OK, modified, missing, or untracked.
2. **Given** no files have been modified, **When** the user verifies the package, **Then** the CLI reports all files as OK.
3. **Given** the user wants to verify all installed packages, **When** they run `aam verify --all`, **Then** every installed package is checked and a summary is displayed.
4. **Given** a file listed in checksums no longer exists on disk, **When** verification runs, **Then** it is reported as missing.

---

### User Story 5 - View Differences Between Installed and Modified Files (Priority: P2)

A practitioner has modified installed files and wants to see exactly what changed before deciding whether to upgrade. They run a diff command that shows the content differences between the installed version and the locally modified version.

**Why this priority**: Viewing diffs provides context for upgrade decisions and helps practitioners preserve intentional customizations. It extends the verify workflow with actionable detail.

**Independent Test**: Can be tested by installing a package, modifying a file, then running `aam diff <package>` and verifying it shows the correct content changes.

**Acceptance Scenarios**:

1. **Given** a package has locally modified files, **When** the user runs `aam diff @myorg/my-agent`, **Then** the CLI shows a unified diff for each modified file, lists untracked files, and lists missing files.
2. **Given** no files have been modified, **When** the user runs diff, **Then** the CLI reports that the package matches the installed version exactly.

---

### User Story 6 - Receive Warnings During Upgrade When Local Changes Exist (Priority: P2)

A practitioner upgrades or reinstalls a package that has locally modified files. Before overwriting, AAM warns them about the modifications and offers options to back up, skip, view the diff, or force the upgrade.

**Why this priority**: Protecting user customizations during upgrades builds trust. Users who lose local changes silently will lose confidence in the package manager.

**Independent Test**: Can be tested by installing a package, modifying files, then running `aam install @myorg/my-agent@2.0.0` (upgrade) and verifying the warning appears with the correct list of modified files and the interactive options.

**Acceptance Scenarios**:

1. **Given** a package is installed and local modifications are detected, **When** the user initiates an upgrade, **Then** the CLI displays a warning listing all modified and untracked files and presents options: backup and upgrade, skip upgrade, show diff, or force upgrade.
2. **Given** the user chooses backup, **When** the upgrade proceeds, **Then** modified files are saved to `~/.aam/backups/<package>--<date>/` before overwriting.
3. **Given** the user chooses skip, **When** the command completes, **Then** no files are changed.
4. **Given** the user runs the upgrade with `--force`, **When** the command executes, **Then** local changes are overwritten without prompting.

---

### User Story 7 - Manage Source Listings (Priority: P2)

A practitioner wants to view all their configured sources and remove ones they no longer need.

**Why this priority**: Source management is a housekeeping capability necessary for long-term usability but not blocking core discovery workflows.

**Independent Test**: Can be tested by adding sources, running `aam source list` to see them, then running `aam source remove <name>` and verifying the source is gone from configuration.

**Acceptance Scenarios**:

1. **Given** multiple sources are configured, **When** the user runs `aam source list`, **Then** the CLI displays a table with source name, URL, ref, artifact count, last updated timestamp, and a "(default)" tag for built-in sources.
2. **Given** a source exists, **When** the user runs `aam source remove openai/skills`, **Then** the source is removed from configuration. If it was a default source, it is recorded in `removed_defaults:` to prevent re-addition.
3. **Given** the user wants to also delete cached data, **When** they run `aam source remove openai/skills --purge-cache`, **Then** both the configuration entry and the cached clone are deleted.

---

### User Story 8 - MCP Tool Integration for IDE Agents (Priority: P2)

An IDE agent (e.g., Cursor, Claude) needs to programmatically discover, scan, and manage remote artifact sources on behalf of the practitioner. The AAM MCP server exposes tools and resources that mirror the CLI commands, enabling agents to list sources, scan for artifacts, preview changes, verify packages, and (with write permissions) add/remove/update sources.

**Why this priority**: MCP integration makes the git source features accessible to AI agents in IDEs, which is a core value proposition of AAM. However, the CLI must work first before MCP tools can wrap it.

**Independent Test**: Can be tested by starting the MCP server, invoking each `aam_source_*` tool via an MCP test client, and verifying correct responses. Write tools should only be accessible when `--allow-write` is configured.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** an agent calls `aam_source_list`, **Then** it receives a list of all configured sources with name, URL, ref, artifact count, and timestamp.
2. **Given** sources are configured, **When** an agent calls `aam_source_scan` with a source name, **Then** it receives a structured list of discovered artifacts grouped by type.
3. **Given** write permissions are not enabled, **When** an agent calls `aam_source_add`, **Then** the tool is not available or returns a permission error.
4. **Given** write permissions are enabled, **When** an agent calls `aam_source_add` with a valid source, **Then** the source is registered and the result includes the artifact count.
5. **Given** the MCP server exposes resources, **When** an agent reads `aam://sources`, **Then** it receives the full source configuration as structured data.

---

### User Story 9 - Default Sources on Initialization (Priority: P3)

A new user installs AAM and runs `aam init` for the first time. AAM automatically registers a curated set of community artifact sources (e.g., `github/awesome-copilot`, `openai/skills:.curated`) so the user can immediately discover and browse popular skills without manual configuration.

**Why this priority**: Default sources provide a polished out-of-box experience and drive adoption, but the system is fully functional without them — users can always add sources manually.

**Independent Test**: Can be tested by running `aam init` with a fresh configuration, then running `aam source list` and verifying the default sources appear marked with "(default)".

**Acceptance Scenarios**:

1. **Given** no `sources:` list exists in `~/.aam/config.yaml`, **When** the user runs `aam init`, **Then** the default community sources are added to the configuration with `default: true`.
2. **Given** the user has previously removed a default source, **When** a new version of AAM introduces additional defaults, **Then** the previously removed source is not re-added (tracked via `removed_defaults:` list).
3. **Given** the user already has sources configured, **When** `aam init` runs, **Then** existing sources are preserved and no duplicates are created.

---

### Edge Cases

- What happens when the user adds a source pointing to a repository that contains no recognizable artifacts? The system reports "0 artifacts found" with a suggestion to check the path or scan patterns.
- What happens when two sources point to the same repository with different path scopes? They share one cached clone, but each produces different scan results based on their respective path filters.
- What happens when a shallow clone fails due to server restrictions? The system falls back to a full clone with a warning about increased download size.
- What happens when the cached git directory is corrupted? The system detects the corruption, deletes the cache entry, and re-clones.
- What happens when a repository is very large (>100 MB)? The system logs a warning and proceeds, recommending the user scope to a subdirectory with `--path`.
- What happens when the user's network is unavailable? For `source add`, the command fails with a clear network error. For `source update`, the cached version is used with a warning.
- What happens when a `SKILL.md` file exists inside a dot-prefixed directory like `.curated/`? It is discovered normally — dot-prefixed category directories are never excluded from scanning.
- What happens when a skill directory contains `agents/openai.yaml` alongside `SKILL.md`? The vendor agent file is treated as companion metadata of the skill, not as a standalone agent artifact.
- What happens when a checksum algorithm other than SHA-256 is requested? Only SHA-256 is supported in v1. The system rejects unsupported algorithms with a clear error. The `FileChecksums.algorithm` field allows future extension to SHA-512 and others without schema changes.

## Requirements *(mandatory)*

### Functional Requirements

#### Remote Git Source Management

- **FR-001**: CLI MUST provide an `aam source add <source>` command that registers a remote git repository as an artifact source, performs a shallow clone, scans for artifacts, and saves the source entry to `~/.aam/config.yaml`.
- **FR-002**: The system MUST support multiple source input formats: HTTPS URLs, Git SSH URLs, `git+https://` URLs, GitHub/GitLab tree URLs with embedded branch and path, and `{owner}/{repo}` shorthand notation.
- **FR-003**: When a full GitHub/GitLab tree URL is provided (e.g., `https://github.com/owner/repo/tree/branch/path`), the system MUST decompose it into clone URL, owner, repo, ref, and scan path components.
- **FR-004**: Source display names MUST follow the convention `{owner}/{repo}` for full-repo sources and `{owner}/{repo}:{path-suffix}` for path-scoped sources, unless overridden with `--name`.
- **FR-005**: The system MUST cache cloned repositories under `~/.aam/cache/git/{host}/{owner}/{repo}/` and share one clone across multiple sources targeting the same repository.
- **FR-006**: The system MUST perform shallow clones (`--depth 1`) by default for performance.
- **FR-007**: The system MUST support authentication via SSH keys, personal access tokens (`GH_TOKEN`, `GITLAB_TOKEN`), and git credential helpers.

#### Source Lifecycle Commands

- **FR-008**: CLI MUST provide an `aam source list` command that displays all configured sources in a table with name, URL, ref, artifact count, last updated, and default status.
- **FR-009**: CLI MUST provide an `aam source remove <name>` command that removes a source from configuration, with an optional `--purge-cache` flag to delete the cached clone.
- **FR-010**: When a default source is removed, its name MUST be recorded in the `removed_defaults:` list to prevent re-addition on future initializations.
- **FR-011**: CLI MUST provide an `aam source scan <name>` command that scans the cached clone and lists all discovered artifacts grouped by type.
- **FR-012**: `aam source scan` MUST support `--type <type>` to filter by artifact type and `--json` for machine-readable output.
- **FR-013**: CLI MUST provide an `aam source update [name]` command that fetches upstream changes via `git fetch`, compares commits, and reports new, modified, and removed artifacts.
- **FR-014**: `aam source update` MUST support `--all` to update all sources and `--dry-run` to preview changes without modifying the cache.
- **FR-015**: CLI MUST provide an `aam source candidates` command that lists all artifacts across remote sources and the local project that are not yet managed by any AAM package.
- **FR-016**: `aam source candidates` MUST support `--source <name>` and `--type <type>` filters, and `--json` output.

#### Artifact Detection (Scanning)

- **FR-017**: The scan engine MUST detect skills by finding `**/SKILL.md` files, including inside platform-specific directories (`.cursor/skills/`, `.codex/skills/`) and dot-prefixed category directories (`.curated/`, `.experimental/`, `.system/`).
- **FR-018**: The scan engine MUST detect agents by finding `**/agent.yaml` and `agents/*.yaml` files.
- **FR-019**: The scan engine MUST detect prompts by finding files in `prompts/*.md`, `.cursor/prompts/*.md`, and `.github/prompts/*.md`.
- **FR-020**: The scan engine MUST detect instructions by finding files matching `.cursor/rules/*.mdc`, `instructions/*.md`, `CLAUDE.md`, `AGENTS.md`, and `.github/copilot-instructions.md`.
- **FR-021**: The scan engine MUST never skip dot-prefixed directories during traversal, except for the explicit exclusion list (`.git/`, `node_modules/`, `.venv/`, `__pycache__/`, `.aam/packages/`, `vendor/`, `dist/`, `build/`).
- **FR-022**: When a directory contains both `SKILL.md` and `agents/*.yaml`, the vendor agent file MUST be treated as companion metadata of the skill, not as a standalone agent.
- **FR-023**: The scan engine MUST skip binary files and only process text-based artifact files (`.md`, `.yaml`, `.yml`, `.mdc`).

#### Package Creation from Remote Sources

- **FR-024**: The existing `aam create-package` command MUST be extended with a `--from-source <name>` flag that creates packages from remote git source artifacts.
- **FR-025**: When `--from-source` is used, the generated `aam.yaml` MUST include a `provenance:` section with source type, URL, ref, path, commit SHA, and fetch timestamp.
- **FR-026**: `--from-source` MUST support `--artifacts <list>` to pre-select specific artifacts and `--all` to include all candidates without interactive selection.

#### File Checksums and Integrity

- **FR-027**: The `aam pack` command MUST generate SHA-256 checksums for all artifact files and store them in the package archive.
- **FR-028**: The `aam-lock.yaml` lock file MUST be extended with a `file_checksums:` section containing per-file checksums for each installed package.
- **FR-029**: CLI MUST provide an `aam verify [package]` command that recomputes checksums for installed files and reports OK, modified, missing, and untracked status for each file.
- **FR-030**: CLI MUST provide an `aam diff <package>` command that shows unified diff output for modified files compared to the installed version.
- **FR-031**: During upgrade or reinstall, the system MUST detect local modifications via checksum comparison and warn the user before overwriting, offering options to backup, skip, view diff, or force.
- **FR-032**: When the user chooses backup during upgrade, modified files MUST be saved to `~/.aam/backups/<package>--<date>/` before overwriting.
- **FR-033**: `aam verify --all` MUST verify all installed packages.

#### MCP Tools and Resources

- **FR-034**: The MCP server MUST expose read-only tools: `aam_source_list`, `aam_source_scan`, `aam_source_candidates`, `aam_source_diff`, `aam_verify`, and `aam_diff`.
- **FR-035**: The MCP server MUST expose write tools (gated by `--allow-write`): `aam_source_add`, `aam_source_remove`, `aam_source_update`, and extend the existing `aam_create_package` tool with `from_source` and `artifacts` parameters.
- **FR-036**: The MCP server MUST expose resources: `aam://sources`, `aam://sources/{name}`, and `aam://sources/{name}/candidates`.
- **FR-037**: Write MCP tools MUST NOT be accessible unless write permissions are explicitly enabled.

#### Default Sources

- **FR-038**: AAM MUST ship with pre-configured default remote sources: `github/awesome-copilot` (GitHub's Copilot skills) and `openai/skills:.curated` (OpenAI's curated Codex skills).
- **FR-039**: Default sources MUST be added to `~/.aam/config.yaml` during `aam init` only if no `sources:` list already exists.
- **FR-040**: Default sources MUST be marked with `default: true` and displayed with a "(default)" tag in `aam source list`.
- **FR-041**: Removed default sources MUST be tracked in `removed_defaults:` and never re-added by future initializations or upgrades.

#### Error Handling and Resilience

- **FR-042**: Network failures during git operations MUST be retried with exponential backoff (3 attempts).
- **FR-043**: When a network fetch fails but a cached version exists, the system MUST use the cached version and display a warning.
- **FR-044**: All repository URLs MUST be validated against an allowlist of schemes (`https://`, `git@`, `git+https://`) to prevent command injection.
- **FR-045**: The system MUST never execute scripts found in cloned repositories during scan or cache operations.

### Key Entities

- **Source**: A named reference to a remote git repository tracked by AAM. Key attributes: name, type (always `git`), clone URL, git ref (branch/tag/commit), optional subdirectory path scope, last commit SHA, last fetch timestamp, artifact count, default flag.
- **Artifact Candidate**: A skill, agent, prompt, or instruction discovered in a source that is not yet managed by any AAM package. Key attributes: name, type, file path relative to source root, source name.
- **File Checksum**: A SHA-256 hash of an artifact file stored in the lock file for integrity verification. Key attributes: file path, algorithm, hash value.
- **Provenance**: Metadata recording where a packaged artifact originated. Key attributes: source type, source URL, ref, path, commit SHA, fetch timestamp.
- **Source Configuration**: A YAML entry in `~/.aam/config.yaml` that persists source registration across sessions. Key attributes: all Source fields plus `removed_defaults` tracking.
- **Backup**: A timestamped copy of locally modified files created before an upgrade overwrites them. Key attributes: package name, date, file list.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can add a remote git source, scan it, list candidates, and create a package from selected artifacts in under 5 minutes following documentation.
- **SC-002**: The system correctly discovers all artifacts in repositories that use dot-prefixed category directories (`.curated/`, `.experimental/`, `.system/`), with zero false negatives.
- **SC-003**: Updating a cached source and detecting changes (new, modified, removed artifacts) completes within 10 seconds for repositories with up to 100 artifacts.
- **SC-004**: The `aam verify` command correctly identifies all modified, missing, and untracked files with 100% accuracy against stored checksums.
- **SC-005**: Users are always warned before an upgrade overwrites locally modified files — zero silent data loss incidents.
- **SC-006**: All 6 read-only MCP tools and 3 write MCP tools respond correctly when invoked via an MCP test client.
- **SC-007**: The feature works entirely offline after initial source cloning — scanning, candidate listing, and package creation use only the local cache.
- **SC-008**: Automated tests achieve at least 80% code coverage across all new modules (source management, scanning, checksums, MCP tools).
- **SC-009**: The CLI provides clear, actionable error messages for all documented edge cases (network failure, authentication failure, corrupt cache, large repositories, duplicate sources).
- **SC-010**: Default sources are correctly initialized on first run and respected across subsequent runs — removed defaults are never re-added.

## Assumptions

- The features defined in Spec 001 (CLI Local Repository) and Spec 002 (MCP Server CLI) are either completed or in progress, providing the foundation for CLI commands, package management, and MCP server infrastructure.
- The primary target repositories for initial testing and default sources are `github/awesome-copilot` and `openai/skills`, both of which are public and do not require authentication.
- Git is available on the system PATH. The CLI does not bundle or install git.
- The scan engine reuses and extends the existing artifact detection logic from `aam create-package` (Spec 001, DESIGN.md Section 5.2).
- Private repository support via `GH_TOKEN`/`GITLAB_TOKEN` and SSH keys relies on the user's existing git configuration — AAM does not implement its own credential storage for git.
- The `~/.aam/backups/` directory for upgrade safety is a new addition not covered by previous specs.
- The `file_checksums` extension to `aam-lock.yaml` is backward-compatible — lock files without checksums continue to work; verification simply reports "no checksums available" for those packages.
- The MCP tools for git sources follow the same patterns established in Spec 002 for MCP tool design and testing.
