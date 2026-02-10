# Feature Specification: CLI Interface Scaffolding & npm-Style Source Workflow

**Feature Branch**: `004-npm-style-source-workflow`  
**Created**: 2026-02-09  
**Updated**: 2026-02-09  
**Status**: Draft  
**Depends on**: Spec 003 (Git Repository Source Scanning)  
**Input**: CLI Restructure Analysis (`docs/CLI_RESTRUCTURE_ANALYSIS.md`), original spec 004 (npm-Style Source Workflow)

**Key Reference Document**: [`docs/CLI_RESTRUCTURE_ANALYSIS.md`](../../docs/CLI_RESTRUCTURE_ANALYSIS.md) — This is the primary source of truth for the complete command inventory, persona analysis, gap analysis, and migration path. It MUST be used during the planning phase.

## Problem Statement

The AAM CLI has three structural problems that degrade the user experience for both consumers and creators:

### 1. Source-to-Install Workflow Friction

The current spec 003 workflow requires **5 steps** to go from "I found a
repository with skills" to "those skills are deployed to my AI agent":

```
# Current (spec 003) — 5 steps
aam source add openai/skills        # 1. clone + scan
aam source scan openai/skills       # 2. browse artifacts
aam source candidates               # 3. see what's unpackaged
aam create-package --from-source    # 4. build a package
aam install ./my-package            # 5. install the package
```

Users expect an npm/apt-style experience:

```
# Desired — 2 steps
aam source add openai/skills        # 1. register source
aam install code-review             # 2. install directly
```

There is also **no way** to check if installed packages have updates (`outdated`)
or to upgrade them (`upgrade`). Users must manually `uninstall` + `install`.

### 2. Creator Commands Lack Consistent Grouping

Six authoring commands (`init`, `create-package`, `validate`, `pack`, `publish`,
`build`) sit at root level alongside consumer commands with no shared prefix.
All other functional areas (`source`, `config`, `registry`, `mcp`) already use
proper subcommand groups. Consumers see 6 irrelevant creator commands in
`--help`; creators have no discoverability.

### 3. `aam init` Is Misused

Users universally expect `init` to set up the tool (like `git init`, `npm init`),
but `aam init` currently scaffolds a new package — a creator action. A first-time
user runs `aam init` expecting to configure their environment, but instead gets
prompted to create a package. The actual client setup is scattered across
`aam config set`, `aam registry add`, and `aam source add`.

## Vision

**Sources are package registries.** When you add a git source, every discovered
artifact becomes an installable package — just like adding an npm registry makes
its packages available for `npm install`. The user never needs to think about
"creating a package" as a separate step.

**Consumer commands are top-level. Creator commands live under `aam pkg`.** The
CLI is organized by persona: consumers get the most common commands at root level,
while creators access authoring tools through a consistent `aam pkg` prefix.

**`aam init` is the first command a new user runs.** It configures the AAM client
interactively: choosing the AI platform, setting up registries, and adding
community artifact sources.

### Mental model comparison

| Concept | apt | npm | aam (proposed) |
|---------|-----|-----|----------------|
| Setup | `apt` (pre-configured) | `npm init` | `aam init` |
| Add source | `add-apt-repository` | `.npmrc` registry | `aam source add` |
| Refresh index | `apt update` | (automatic) | `aam source update` |
| Install | `apt install vim` | `npm install lodash` | `aam install code-review` |
| Check updates | `apt list --upgradable` | `npm outdated` | `aam outdated` |
| Upgrade | `apt upgrade` | `npm update` | `aam upgrade` |
| Create package | `dpkg-deb --build` | `npm init` + `npm pack` | `aam pkg init` + `aam pkg pack` |

### Target CLI hierarchy

```
aam
├── init                       Client initialization (platform, registries, sources)
│
├── install <pkg>              Install from registry or source
├── uninstall <pkg>            Remove installed package
├── upgrade [pkg]              Upgrade packages to latest
├── outdated                   Show packages with available updates
├── search <query>             Search registries AND sources
├── list                       List installed (+ --available for browse)
├── info <pkg>                 Show package details
├── verify [pkg|--all]         Verify file integrity
├── diff <pkg>                 Show modifications
│
├── pkg/                       Package authoring commands
│   ├── init [name]            Scaffold a new package
│   ├── create [path]          Create from existing artifacts
│   ├── validate [path]        Validate manifest
│   ├── pack [path]            Build .aam archive
│   ├── publish                Publish to registry
│   └── build --target         Build portable bundle
│
├── source/                    (unchanged from spec 003)
├── config/                    (unchanged)
├── registry/                  (unchanged)
├── mcp/                       (unchanged)
└── doctor                     (unchanged)
```

---

## User Scenarios & Testing

### User Story 1 — First-Time Client Initialization (Priority: P0)

A new user installs AAM and runs `aam init` to set up their environment. The
command guides them through choosing their AI platform, optionally creating or
connecting a registry, and adding community artifact sources. After completion,
the user has a working `~/.aam/config.yaml` and can immediately search and
install packages.

**Why this priority**: This is the entry point for every new user. A poor
onboarding experience drives users away before they experience AAM's value.
The current `aam init` (package scaffolding) misleads new users.

**Independent Test**: Run `aam init` with a fresh `~/.aam/` directory, answer
the interactive prompts, then verify `~/.aam/config.yaml` contains the chosen
platform, any registered registries, and configured sources. Run `aam doctor`
to confirm the environment is healthy.

**Acceptance Scenarios:**

1. **Given** no `~/.aam/config.yaml` exists, **When** the user runs `aam init`,
   **Then** the CLI presents an interactive flow that asks for: AI platform
   selection (Cursor, Copilot, Claude, Codex), optional registry setup (create
   local, add existing, or skip), and optional community source registration.

2. **Given** the user selects "Cursor" as their platform, **When** init
   completes, **Then** `~/.aam/config.yaml` contains `default_platform: cursor`.

3. **Given** the user chooses to create a local registry, **When** init
   completes, **Then** the registry directory is created and registered as
   default in the config.

4. **Given** the user selects community sources, **When** init completes,
   **Then** the sources are added to config with `default: true` and the CLI
   suggests running `aam source update` to fetch artifacts.

5. **Given** `~/.aam/config.yaml` already exists, **When** the user runs
   `aam init`, **Then** the CLI detects the existing config and offers to
   reconfigure (overwrite) or skip each section that is already set.

6. **Given** the user runs `aam init --yes` (non-interactive), **When** defaults
   are applied, **Then** the CLI uses the first detected platform, skips registry
   setup, and adds all default community sources without prompting.

---

### User Story 2 — Add a Source and Install from It (Priority: P0)

A practitioner adds a git repository and then directly installs artifacts
from it as AAM packages, without any intermediate "create-package" step.
The installed package is deployed to the configured AI agent platform.

**Why this priority**: This is the core value proposition of the npm-style
workflow — collapsing 5 steps to 2.

**Independent Test**: Run `aam source add openai/skills` followed by
`aam install code-review` and verify the artifact is installed and deployed.

**Acceptance Scenarios:**

1. **Given** the user runs `aam source add openai/skills`, **When** the
   clone and scan complete, **Then** all discovered artifacts appear as
   available (installable) packages when the user runs `aam search` or
   `aam list --available`.

2. **Given** a source has been added, **When** the user runs
   `aam install code-review` (where `code-review` is a skill discovered
   in `openai/skills`), **Then** AAM:
   - Resolves `code-review` to the source artifact
   - Automatically creates the `aam.yaml` manifest with provenance
   - Copies files to `.aam/packages/code-review/`
   - Records per-file checksums in `aam-lock.yaml`
   - Deploys artifacts to the target platform
   - Reports the installation as successful

3. **Given** the same artifact name exists in multiple sources, **When**
   the user runs `aam install code-review`, **Then** AAM either:
   - Installs from the first matching source (ordered by config), or
   - Prompts the user to disambiguate:
     `aam install openai/skills/code-review`

4. **Given** the artifact is already installed, **When** the user runs
   `aam install code-review` again, **Then** AAM reports "already
   installed" (or reinstalls with `--force`).

5. **Given** a source artifact has companion files (for example, a skill
   with `SKILL.md` + `agents/openai.yaml`), **When** installed, **Then**
   all companion files are included in the installed package.

---

### User Story 3 — Source Update Refreshes Available Packages (Priority: P0)

A practitioner runs `aam source update` to refresh the package index from
all sources, similar to `apt update`.

**Acceptance Scenarios:**

1. **Given** sources are configured, **When** the user runs
   `aam source update`, **Then** AAM fetches all sources, re-scans, and
   prints a per-source change summary.

2. **Given** a source has new artifacts since the last update, **When**
   the update completes, **Then** those new artifacts immediately become
   installable via `aam install`.

3. **Given** a source artifact was removed upstream, **When** the update
   runs, **Then** the artifact is no longer listed as available, but
   already-installed packages are NOT automatically removed.

4. **Given** the network is unavailable, **When** `aam source update`
   runs, **Then** AAM reports the failure per source but keeps the
   cached index intact (stale data is better than no data).

---

### User Story 4 — Outdated: Compare Installed vs Available (Priority: P0)

A practitioner wants to see which installed packages have newer versions
available in their sources, similar to `npm outdated`.

**Acceptance Scenarios:**

1. **Given** packages are installed from sources, **When** the user runs
   `aam outdated`, **Then** AAM compares each installed package's
   source commit against the current source HEAD and reports:
   ```
   Package         Installed    Available   Source
   code-review     abc123       def456      openai/skills
   architect       abc123       abc123      openai/skills  (up to date)

   1 package outdated. Run 'aam upgrade' to update.
   ```

2. **Given** an installed package was not installed from a source (for
   example, manually created or from a registry), **When** `aam outdated`
   runs, **Then** that package is skipped with a note "(no source)".

3. **Given** the user runs `aam outdated --json`, **When** the output
   is generated, **Then** it is valid JSON for scripting.

---

### User Story 5 — Upgrade Installed Packages from Sources (Priority: P0)

A practitioner wants to update installed packages to the latest version
from their sources, similar to `apt upgrade` or `npm update`.

**Acceptance Scenarios:**

1. **Given** outdated packages exist, **When** the user runs
   `aam upgrade`, **Then** AAM:
   - Fetches latest from all sources (implicit `source update`)
   - Identifies outdated packages
   - For each: checks for local modifications, warns if found
   - Updates the package files from the source cache
   - Recomputes and stores checksums
   - Re-deploys to platform

2. **Given** the user runs `aam upgrade code-review`, **Then** only
   that specific package is upgraded.

3. **Given** the user runs `aam upgrade --dry-run`, **Then** AAM shows
   what would be upgraded without making changes.

4. **Given** a package has local modifications, **When** upgrade runs,
   **Then** the existing spec 003 upgrade warning flow applies
   (backup/skip/diff/force).

---

### User Story 6 — List Available Packages (Priority: P1)

A practitioner wants to browse all packages available across sources
and registries.

**Acceptance Scenarios:**

1. **Given** sources are configured, **When** the user runs
   `aam list --available`, **Then** AAM shows all installable artifacts
   grouped by source:
   ```
   openai/skills (12 packages):
     code-review         skill     Review code changes
     architect           agent     Design system architectures
     ...

   20 packages available from 2 sources.
   ```

2. **Given** the user runs `aam search code-review`, **Then** results
   include matches from both registries AND sources.

---

### User Story 7 — Creator Uses `aam pkg` Commands (Priority: P1)

A package author uses the `aam pkg` command group to scaffold, build,
validate, and publish packages. All authoring commands are consistently
accessed through the `pkg` prefix.

**Why this priority**: Grouping creator commands under `aam pkg` declutters
the root `--help` for consumers and provides creators with a discoverable,
consistent namespace. This is a UX improvement, not a new feature.

**Independent Test**: Run `aam pkg --help` and verify all authoring
subcommands are listed. Run `aam pkg init my-package`, `aam pkg validate`,
`aam pkg pack`, and verify they produce the same results as the old root-
level commands.

**Acceptance Scenarios:**

1. **Given** the user runs `aam pkg --help`, **Then** the CLI displays
   all package authoring subcommands: `init`, `create`, `validate`,
   `pack`, `publish`, `build`.

2. **Given** the user runs `aam pkg init my-skill`, **Then** the CLI
   scaffolds a new package with `aam.yaml` and artifact directories,
   identical to the current `aam init my-skill` behavior.

3. **Given** the user runs `aam pkg create --from-source openai/skills
   --artifacts code-review`, **Then** the CLI creates a package from
   the source artifact, identical to the current `aam create-package
   --from-source` behavior.

4. **Given** the user runs `aam pkg validate`, **Then** the CLI validates
   the manifest, identical to the current `aam validate` behavior.

5. **Given** the user runs `aam pkg pack`, **Then** the CLI builds a
   distributable `.aam` archive, identical to the current `aam pack`.

6. **Given** the user runs `aam pkg publish --registry local`, **Then**
   the CLI publishes the archive, identical to `aam publish`.

7. **Given** the user runs the deprecated root-level command
   `aam create-package`, **Then** the CLI prints a deprecation warning
   ("use 'aam pkg create' instead") and executes the command normally.

8. **Given** the user runs `aam validate`, **Then** the CLI prints a
   deprecation warning and delegates to `aam pkg validate`.

---

### User Story 8 — Categorized Help Text (Priority: P1)

A user runs `aam --help` and sees commands organized into logical sections
rather than a flat alphabetical list.

**Acceptance Scenarios:**

1. **Given** the user runs `aam --help`, **Then** the output groups
   commands into sections:
   - "Getting Started" (`init`)
   - "Package Management" (`install`, `uninstall`, `upgrade`, `outdated`,
     `search`, `list`, `info`)
   - "Package Integrity" (`verify`, `diff`)
   - "Package Authoring" (`pkg`)
   - "Source Management" (`source`)
   - "Configuration" (`config`, `registry`)
   - "Utilities" (`mcp`, `doctor`)

2. **Given** deprecated root-level aliases exist (e.g., `create-package`,
   `validate`, `pack`, `publish`), **Then** they are hidden from
   `--help` (using Click's `hidden=True`).

3. **Given** the user runs `aam pkg --help`, **Then** the output lists
   all authoring subcommands with short descriptions.

---

### User Story 9 — MCP Tools for New Commands (Priority: P1)

An IDE agent needs to programmatically check for outdated packages, list
available artifacts, and trigger upgrades through the MCP server.

**Acceptance Scenarios:**

1. **Given** the MCP server is running, **When** an agent calls
   `aam_outdated`, **Then** it receives a structured list of installed
   packages with their current and available versions.

2. **Given** the MCP server is running, **When** an agent calls
   `aam_available`, **Then** it receives a list of all installable
   artifacts from sources and registries.

3. **Given** write permissions are enabled, **When** an agent calls
   `aam_upgrade` with a package name, **Then** the package is upgraded
   and the result includes the old and new commit SHAs.

4. **Given** write permissions are NOT enabled, **When** an agent calls
   `aam_upgrade`, **Then** the tool returns a permission error.

---

### User Story 10 — Updated Documentation (Priority: P1)

All user-facing documentation reflects the new command structure,
including the `aam init` repurposing, `aam pkg` prefix, and new consumer
commands.

**Acceptance Scenarios:**

1. **Given** the user reads the User Guide, **Then** the quick start
   section shows `aam init` for client setup and `aam pkg init` for
   package creation.

2. **Given** the user reads CLI reference, **Then** all commands use the
   new naming (`aam pkg create` instead of `aam create-package`).

3. **Given** the user visits the web homepage, **Then** the Quick Start
   CLI examples use the updated command names (including `aam pkg publish`
   instead of `aam publish`).

4. **Given** the user reads `aam <command> --help`, **Then** the help
   text is consistent with the documentation.

---

### Edge Cases

- What happens when a user runs old `aam create-package` after the
  restructuring? The CLI prints a deprecation warning and delegates to
  `aam pkg create`. The command works identically.
- What happens when `aam init` is run in a directory with an existing
  `aam.yaml`? The CLI detects it and asks if the user wants client
  initialization (`aam init`) or package re-initialization
  (`aam pkg init`).
- What happens when `aam install <name>` matches both a registry
  package and a source artifact? Registry takes priority. The user can
  use `aam install openai/skills/code-review` to be explicit.
- What happens when `aam outdated` is run but no sources have been
  updated? The CLI warns that source indexes may be stale and suggests
  `aam source update`.
- What happens when `aam upgrade --all` encounters a package with local
  modifications? The upgrade warning flow from spec 003 applies per
  package — the user can backup/skip/diff/force for each.
- What happens when `aam pkg --help` is run but the user meant to use
  a consumer command? The help output includes a note: "For installing
  packages, use 'aam install'. For creating packages, use 'aam pkg'."

---

## Key Design Decisions

### D1: Source artifacts are virtual packages

When a source is added, each discovered artifact is registered as a
"virtual package" in an in-memory index. These virtual packages have:

- **Name**: Derived from the artifact directory name
- **Version**: The source commit SHA (short form, for example `abc123`)
- **Source**: The source display name (for example `openai/skills`)
- **Type**: skill, agent, prompt, instruction

Virtual packages are resolved during `aam install` alongside registry
packages. Source resolution is checked **after** registry resolution
(registries take priority), unless the user qualifies with the source
name: `aam install openai/skills/code-review`.

### D2: Qualified package names for disambiguation

When the same artifact name exists in multiple sources (or conflicts
with a registry package), the user can qualify:

```
aam install code-review                    # auto-resolve (first match)
aam install openai/skills/code-review      # explicit source
aam install @registry/code-review          # explicit registry
```

### D3: Source commit as version

Since git sources don't have semantic versions, the "version" is the
commit SHA. This enables:

- `aam outdated` to compare installed commit vs HEAD commit
- `aam verify` to check file integrity against the installed commit
- `aam upgrade` to pull files from the newer commit

### D4: Implicit package creation during install

When `aam install <artifact-from-source>` runs, AAM:

1. Resolves the artifact to a source
2. Reads files from the source cache
3. Generates `aam.yaml` with provenance metadata (invisible to user)
4. Copies to `.aam/packages/<name>/`
5. Writes checksums to `aam-lock.yaml`
6. Deploys to platform

The user never sees "create-package" — it's an internal step.

### D5: Source update is explicit (apt model, not npm model)

Like `apt update`, users must explicitly run `aam source update` to
refresh the index. This keeps the workflow predictable and works offline
after initial setup. Auto-update on install could be a future `--refresh`
flag.

### D6: `aam pkg` prefix for all creator commands

All package authoring commands use the `aam pkg` prefix:

| Old command | New command | Rationale |
|------------|------------|-----------|
| `aam init [name]` | `aam pkg init [name]` | Package scaffolding is a creator action |
| `aam create-package [path]` | `aam pkg create [path]` | `pkg` context makes "package" redundant |
| `aam validate [path]` | `aam pkg validate [path]` | Consistency |
| `aam pack [path]` | `aam pkg pack [path]` | Consistency |
| `aam publish` | `aam pkg publish` | Consistency |
| `aam build --target` | `aam pkg build --target` | Consistency |

Old root-level commands remain as hidden, deprecated aliases during the
transition period.

### D7: `aam init` repurposed as client initialization

The root-level `aam init` becomes client setup (choose platform,
configure registries, add sources). Package scaffolding moves to
`aam pkg init`. This matches user expectations from `git init`,
`npm init`, `pip init`.

### D8: `aam upgrade` is the canonical name (not `aam update`)

- `aam source update` = refresh index (like `apt update`)
- `aam upgrade` = upgrade installed packages (like `apt upgrade`)
- `aam update` is registered as a hidden alias for `aam upgrade`

This avoids collision with `source update` and matches the apt
convention where `update` and `upgrade` are different operations.

---

## Requirements

### Functional Requirements

#### Client Initialization (`aam init`)

- **FR-001**: `aam init` MUST present an interactive flow that configures:
  active AI platform, optional registry setup, and optional community
  source registration.
- **FR-002**: `aam init` MUST create or update `~/.aam/config.yaml` with
  the chosen settings.
- **FR-003**: `aam init` MUST detect an existing config and offer to
  reconfigure or skip each section that is already set.
- **FR-004**: `aam init --yes` MUST apply sensible defaults without
  interactive prompting.
- **FR-005**: `aam init` MUST display a "Next steps" summary showing
  the user what to do after initialization.

#### Install from Source

- **FR-006**: `aam install <name>` MUST resolve package names against
  both registries and source artifact indexes.
- **FR-007**: When an artifact is found in a source, `aam install` MUST
  automatically create the package manifest, copy files, compute
  checksums, record in lock file, and deploy to platform — in a single
  command.
- **FR-008**: Qualified names (`source/name`) MUST be supported for
  disambiguation.
- **FR-009**: Registry packages MUST take priority over source artifacts
  when names conflict (unless qualified).

#### Source Update (apt-style)

- **FR-010**: `aam source update` MUST fetch all sources, re-scan
  artifacts, and print a per-source change summary.
- **FR-011**: `aam source update <name>` MUST update only the named
  source.
- **FR-012**: After update, newly discovered artifacts MUST be
  immediately available for `aam install`.

#### Outdated Detection

- **FR-013**: `aam outdated` MUST compare each installed source-based
  package's provenance commit against the current source HEAD.
- **FR-014**: Packages installed from registries (not sources) MUST be
  skipped with a "(no source)" indicator.
- **FR-015**: `aam outdated` MUST support `--json` output.

#### Upgrade

- **FR-016**: `aam upgrade [name]` MUST update installed packages from
  sources to the latest commit.
- **FR-017**: `aam upgrade` without arguments MUST update all outdated
  source-based packages.
- **FR-018**: `aam upgrade` MUST respect the existing upgrade warning
  flow from spec 003 (backup/skip/diff/force).
- **FR-019**: `aam upgrade --dry-run` MUST preview changes without
  modifying files.

#### Available Package Listing

- **FR-020**: `aam list --available` MUST show all installable artifacts
  from sources, grouped by source.
- **FR-021**: `aam search` MUST include source artifacts in search
  results alongside registry results.

#### Creator Command Group (`aam pkg`)

- **FR-022**: A Click group named `pkg` MUST be registered under the
  root CLI, containing subcommands: `init`, `create`, `validate`,
  `pack`, `publish`, `build`.
- **FR-023**: `aam pkg init [name]` MUST produce identical output to
  the current `aam init [name]` (package scaffolding).
- **FR-024**: `aam pkg create [path]` MUST produce identical output to
  the current `aam create-package [path]`, accepting all existing flags.
- **FR-025**: `aam pkg validate`, `aam pkg pack`, `aam pkg publish`,
  `aam pkg build` MUST produce identical output to their current
  root-level counterparts.
- **FR-026**: The old root-level commands (`create-package`, `validate`,
  `pack`, `publish`, `build`) MUST remain functional as hidden,
  deprecated aliases that print a deprecation warning before delegating.

#### Help Text Grouping

- **FR-027**: The root CLI group MUST use a custom Click group class
  that organizes commands into labeled sections in `--help` output.
- **FR-028**: Sections MUST be: "Getting Started", "Package Management",
  "Package Integrity", "Package Authoring", "Source Management",
  "Configuration", "Utilities".
- **FR-029**: Deprecated aliases MUST be hidden from `--help` output
  (Click `hidden=True`).

#### Bug Fix: Uninstall Adapter

- **FR-030**: `uninstall.py` MUST use `create_adapter()` from the
  adapter factory instead of hardcoding `CursorAdapter`.

#### Consistent Console Handling

- **FR-031**: All commands MUST use `ctx.obj["console"]` for Rich
  console output instead of creating module-level `Console()` instances.
- **FR-032**: All commands MUST use `ctx.exit()` instead of
  `sys.exit()` for error exits.

#### MCP Tool Extensions

- **FR-033**: The MCP server MUST expose read-only tools: `aam_outdated`
  and `aam_available`.
- **FR-034**: The MCP server MUST expose a write tool: `aam_upgrade`
  (gated by `--allow-write`).
- **FR-035**: `aam_upgrade` MUST NOT be accessible unless write
  permissions are explicitly enabled.

#### Documentation Updates

- **FR-036**: The User Guide (`docs/USER_GUIDE.md`) MUST be updated to
  reflect the new command structure (`aam init` for client setup,
  `aam pkg` for authoring).
- **FR-037**: The Design Doc (`docs/DESIGN.md`) MUST be updated with
  the new command hierarchy.
- **FR-038**: All `--help` text across all commands MUST be consistent
  with the documentation.

#### Web UI Updates

- **FR-039**: The aam-web homepage Quick Start section MUST update CLI
  examples to use the new command names (`aam pkg publish` instead of
  `aam publish`).

### Non-Functional Requirements

- **NFR-001**: `aam install <source-artifact>` MUST complete in under
  5 seconds for cached sources (no network).
- **NFR-002**: `aam source update --all` MUST complete in under 30
  seconds for up to 10 sources.
- **NFR-003**: The source artifact index MUST be rebuilt from cache
  without network access (offline capable).
- **NFR-004**: `aam init` interactive flow MUST complete in under 60
  seconds for a user who accepts defaults.
- **NFR-005**: Deprecated command aliases MUST add less than 10ms
  overhead compared to direct `aam pkg` invocations.
- **NFR-006**: The categorized `--help` output MUST render correctly
  in terminals with 80-column width.

### Key Entities

- **Source**: A named reference to a remote git repository tracked by
  AAM. Key attributes: name, clone URL, git ref, path scope, last
  commit SHA, artifact count, default flag.
- **Virtual Package**: An artifact discovered in a source that is
  available for installation without explicit packaging. Key attributes:
  name, type, source name, commit SHA, file paths.
- **Client Configuration**: The `~/.aam/config.yaml` file that stores
  global settings. Key attributes: default_platform, registries list,
  sources list, removed_defaults list.
- **Package Group (`pkg`)**: A Click subcommand group that namespaces
  all package authoring commands under `aam pkg`.
- **Deprecated Alias**: A hidden root-level command that prints a
  deprecation warning and delegates to the corresponding `aam pkg`
  subcommand.

---

## Migration & Backward Compatibility

### Spec 003 commands remain functional

All spec 003 commands (`source scan`, `source candidates`,
`create-package --from-source`) continue to work. The new workflow is
an **additional path**, not a replacement.

### Root-level creator commands remain as deprecated aliases

| Old command | Alias target | Deprecation message |
|------------|-------------|-------------------|
| `aam init [name]` | `aam pkg init [name]` | "Use 'aam pkg init' for package scaffolding" |
| `aam create-package [path]` | `aam pkg create [path]` | "Use 'aam pkg create' instead" |
| `aam validate [path]` | `aam pkg validate [path]` | "Use 'aam pkg validate' instead" |
| `aam pack [path]` | `aam pkg pack [path]` | "Use 'aam pkg pack' instead" |
| `aam publish` | `aam pkg publish` | "Use 'aam pkg publish' instead" |
| `aam build --target` | `aam pkg build --target` | "Use 'aam pkg build' instead" |

Note: The old `aam init` is a special case. Since `aam init` is
repurposed as client initialization, the deprecated alias is only
activated when `aam init` is called with a `[name]` argument (which
signals package scaffolding intent).

### Lock file extension

The `aam-lock.yaml` `LockedPackage` model gains:

- `source_name: str | None` — Which source this was installed from
- `source_commit: str | None` — The commit SHA at install time

These fields are optional and backward compatible.

### MCP tool extensions

New/updated MCP tools:

| Tool | Mode | Description |
|------|------|-------------|
| `aam_available` | Read | List installable artifacts from sources |
| `aam_outdated` | Read | Compare installed vs available |
| `aam_upgrade` | Write | Upgrade packages from sources |

### `aam update` alias

`aam update` is registered as a hidden alias for `aam upgrade`, for
users coming from npm. It is not shown in `--help`.

---

## Affected Files (Estimated)

### Modified — CLI (`apps/aam-cli/`)

| File | Change |
|------|--------|
| `main.py` | Replace flat creator commands with `aam pkg` group; register new `aam init` client command; add `OrderedGroup` for categorized help; register `outdated`, `upgrade` commands; add `update` alias |
| `commands/install.py` | Add source resolution before registry lookup |
| `commands/uninstall.py` | Replace hardcoded `CursorAdapter` with `create_adapter()` factory |
| `commands/list_packages.py` | Add `--available` flag |
| `commands/search.py` | Include source artifacts in search results |
| `commands/init_package.py` | Extract package scaffolding logic to `commands/pkg/init.py` |
| `commands/source.py` | Replace `Console()` with `ctx.obj["console"]`; replace `sys.exit(1)` with `ctx.exit(1)` |
| `services/install_service.py` | Add `install_from_source()` path |
| `services/source_service.py` | Add `resolve_artifact()`, `build_source_index()` |
| `core/workspace.py` | Extend `LockedPackage` with `source_name`, `source_commit` |
| `mcp/tools_read.py` | Add `aam_available`, `aam_outdated` tools |
| `mcp/tools_write.py` | Add `aam_upgrade` tool |

### New — CLI (`apps/aam-cli/`)

| File | Purpose |
|------|---------|
| `commands/client_init.py` | `aam init` — interactive client initialization |
| `commands/outdated.py` | `aam outdated` command |
| `commands/upgrade.py` | `aam upgrade` command |
| `commands/pkg/__init__.py` | Click group for `aam pkg` subcommands |
| `commands/pkg/init.py` | `aam pkg init` — package scaffolding (moved from `init_package.py`) |
| `commands/pkg/create.py` | `aam pkg create` — wraps `create_package` logic |
| `commands/pkg/validate.py` | `aam pkg validate` — wraps validate logic |
| `commands/pkg/pack.py` | `aam pkg pack` — wraps pack logic |
| `commands/pkg/publish.py` | `aam pkg publish` — wraps publish logic |
| `commands/pkg/build.py` | `aam pkg build` — wraps build logic |
| `services/client_init_service.py` | Business logic for interactive client setup |
| `services/upgrade_service.py` | Upgrade logic with diff/backup flow |
| `tests/unit/test_unit_client_init.py` | Client init tests |
| `tests/unit/test_unit_outdated.py` | Outdated detection tests |
| `tests/unit/test_unit_upgrade.py` | Upgrade flow tests |
| `tests/unit/test_unit_install_from_source.py` | Source install tests |
| `tests/unit/test_unit_pkg_group.py` | `aam pkg` group and deprecation alias tests |
| `tests/unit/test_unit_help_grouping.py` | Categorized help output tests |

### Modified — Documentation (`docs/`)

| File | Change |
|------|--------|
| `docs/USER_GUIDE.md` | Update quick start, command reference, examples |
| `docs/DESIGN.md` | Update command hierarchy, roadmap |

### Modified — Web (`apps/aam-web/`)

| File | Change |
|------|--------|
| `apps/aam-web/src/pages/HomePage.tsx` | Update Quick Start CLI examples (`aam publish` → `aam pkg publish`) |

---

## Open Questions

1. **Auto-deploy on install?** When installing from a source, should AAM
   automatically deploy to the configured platform?
   **Proposed: Yes** — install means "ready to use."

2. **Version display for source packages?** Source packages don't have
   semver versions. Options:
   - Show commit SHA short form (`abc123`)
   - Show date (`2026-02-08`)
   - Show `source@<commit>` format
   **Proposed: `source@abc123`** — clear about origin and version.

3. **Should `aam init` detect existing `aam.yaml`?** If `aam init` is
   run in a directory with `aam.yaml`, should it:
   - (a) Proceed with client init (ignore the local manifest)
   - (b) Ask: "Did you mean `aam pkg init`?"
   - (c) Detect context and behave differently
   **Proposed: (b)** — Ask for clarification.

4. **Should `aam install` auto-run `source update` if stale?** For
   example, if the source hasn't been updated in 24 hours.
   **Proposed: No** — keep it explicit like apt. Add `--refresh` flag
   for future convenience.

5. **Deprecation timeline for root-level aliases?** When should old
   commands like `aam create-package` be removed?
   **Proposed: v0.3.0** — two minor versions of deprecation warnings
   before removal.

---

## Success Criteria

- **SC-001**: A new user can run `aam init`, select their platform and
  sources, then run `aam install code-review` and have the skill
  deployed to their AI agent in under 2 minutes.
- **SC-002**: `aam source update` correctly identifies new, modified,
  and removed packages across all sources.
- **SC-003**: `aam outdated` accurately reports which installed packages
  have newer commits available.
- **SC-004**: `aam upgrade` updates packages while respecting local
  modification warnings.
- **SC-005**: The entire workflow works offline after initial
  `source add` (except `source update`).
- **SC-006**: All `aam pkg` subcommands produce identical output to
  their old root-level counterparts.
- **SC-007**: Deprecated root-level commands print a deprecation warning
  and delegate correctly.
- **SC-008**: `aam --help` displays commands in categorized sections,
  not a flat alphabetical list.
- **SC-009**: The web homepage CLI examples use the updated command
  names.
- **SC-010**: User Guide and Design Doc reflect the new command
  structure with no stale references to old command names.
- **SC-011**: `aam uninstall` works correctly on all configured
  platforms (not just Cursor).
- **SC-012**: New MCP tools (`aam_outdated`, `aam_available`,
  `aam_upgrade`) respond correctly when invoked via an MCP test client.
- **SC-013**: Automated tests achieve at least 80% code coverage across
  all new modules.

## Assumptions

- The features defined in Spec 001 (CLI Local Repository), Spec 002
  (MCP Server CLI), and Spec 003 (Git Repository Source Scanning) are
  completed, providing the foundation for CLI commands, package
  management, source management, and MCP server infrastructure.
- The primary target repositories for initial testing and default
  sources are `github/awesome-copilot` and `openai/skills`, both of
  which are public and do not require authentication.
- Git is available on the system PATH.
- The aam-web application is a static frontend that references CLI
  commands in examples but does not execute them — changes are limited
  to updating display text.
- The `aam pkg` group is a non-breaking change: all existing command
  functionality is preserved, only the access path changes.
- The Click framework supports custom group classes and the `hidden`
  attribute on commands for deprecated aliases.
