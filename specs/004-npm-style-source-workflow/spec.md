# Feature Specification: npm-Style Source Workflow

**Feature Branch**: `004-npm-style-source-workflow`  
**Created**: 2026-02-09  
**Status**: Draft  
**Depends on**: Spec 003 (Git Repository Source Scanning)  
**Input**: Simplify the source-to-install workflow to match npm/apt mental models

## Problem Statement

The current spec 003 workflow requires too many steps to go from "I found a
repository with skills" to "those skills are deployed to my AI agent":

```
# Current (spec 003) — 5 steps
aam source add openai/skills        # 1. clone + scan
aam source scan openai/skills       # 2. browse artifacts
aam source candidates               # 3. see what's unpackaged
aam create-package --from-source    # 4. build a package
aam install ./my-package            # 5. install the package
```

This is more like building from source than installing a package. Users
expect an npm/apt-style experience:

```
# Desired — 2 steps
aam source add openai/skills        # 1. register source (like apt source)
aam install openai/skills/code-review  # 2. install directly
```

## Vision

**Sources are package registries.** When you add a git source, every
discovered artifact becomes an installable package — just like adding an
npm registry makes its packages available for `npm install`. The user
never needs to think about "creating a package" as a separate step.

### Mental model comparison

| Concept | apt | npm | aam (proposed) |
|---------|-----|-----|----------------|
| Add source | `add-apt-repository` | `.npmrc` registry | `aam source add` |
| Refresh index | `apt update` | (automatic) | `aam source update` |
| Install | `apt install vim` | `npm install lodash` | `aam install code-review` |
| Check updates | `apt list --upgradable` | `npm outdated` | `aam outdated` |
| Upgrade | `apt upgrade` | `npm update` | `aam upgrade` |

---

## User Scenarios & Testing

### User Story 1 — Add a Source and Install from It (Priority: P0)

A practitioner adds a git repository and then directly installs artifacts
from it as AAM packages, without any intermediate "create-package" step.
The installed package is deployed to the configured AI agent platform.

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
   - Deploys artifacts to the target platform (for example, copies
     `SKILL.md` to `.cursor/skills/code-review/`)
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

### User Story 2 — Source Update Refreshes Available Packages (Priority: P0)

A practitioner runs `aam source update` to refresh the package index from
all sources, similar to `apt update`. The output shows what's new,
changed, or removed in the available package list.

**Acceptance Scenarios:**

1. **Given** sources are configured, **When** the user runs
   `aam source update`, **Then** AAM fetches all sources, re-scans, and
   prints a summary:
   ```
   Fetching openai/skills... done (3 new, 1 updated, 0 removed)
   Fetching github/awesome-copilot... done (0 new, 0 updated, 0 removed)

   All sources up to date. 47 packages available.
   ```

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

### User Story 3 — Outdated: Compare Installed vs Available (Priority: P1)

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

### User Story 4 — Upgrade Installed Packages from Sources (Priority: P1)

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

### User Story 5 — List Available Packages (Priority: P1)

A practitioner wants to browse all packages available across sources
and registries.

**Acceptance Scenarios:**

1. **Given** sources are configured, **When** the user runs
   `aam list --available` (or `aam available`), **Then** AAM shows all
   installable artifacts grouped by source:
   ```
   openai/skills (12 packages):
     code-review         skill     Review code changes
     code-gen            skill     Generate code from descriptions
     architect           agent     Design system architectures
     ...

   github/awesome-copilot (8 packages):
     copilot-helper      skill     Enhance Copilot suggestions
     ...

   20 packages available from 2 sources.
   ```

2. **Given** the user runs `aam search code-review`, **Then** results
   include matches from both registries AND sources.

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

---

## Requirements

### Functional Requirements

#### Install from Source

- **FR-001**: `aam install <name>` MUST resolve package names against
  both registries and source artifact indexes.
- **FR-002**: When an artifact is found in a source, `aam install` MUST
  automatically create the package manifest, copy files, compute
  checksums, record in lock file, and deploy to platform — in a single
  command.
- **FR-003**: Qualified names (`source/name`) MUST be supported for
  disambiguation.
- **FR-004**: Registry packages MUST take priority over source artifacts
  when names conflict (unless qualified).

#### Source Update (apt-style)

- **FR-005**: `aam source update` MUST fetch all sources, re-scan
  artifacts, and print a per-source change summary.
- **FR-006**: `aam source update <name>` MUST update only the named
  source.
- **FR-007**: After update, newly discovered artifacts MUST be
  immediately available for `aam install`.

#### Outdated Detection

- **FR-008**: `aam outdated` MUST compare each installed source-based
  package's provenance commit against the current source HEAD.
- **FR-009**: Packages installed from registries (not sources) MUST be
  skipped with a "(no source)" indicator.
- **FR-010**: `aam outdated` MUST support `--json` output.

#### Upgrade

- **FR-011**: `aam upgrade [name]` MUST update installed packages from
  sources to the latest commit.
- **FR-012**: `aam upgrade` without arguments MUST update all outdated
  source-based packages.
- **FR-013**: `aam upgrade` MUST respect the existing upgrade warning
  flow from spec 003 (backup/skip/diff/force).
- **FR-014**: `aam upgrade --dry-run` MUST preview changes without
  modifying files.

#### Available Package Listing

- **FR-015**: `aam list --available` (or `aam available`) MUST show all
  installable artifacts from sources, grouped by source.
- **FR-016**: `aam search` MUST include source artifacts in search
  results alongside registry results.

### Non-Functional Requirements

- **NFR-001**: `aam install <source-artifact>` MUST complete in under
  5 seconds for cached sources (no network).
- **NFR-002**: `aam source update --all` MUST complete in under 30
  seconds for up to 10 sources.
- **NFR-003**: The source artifact index MUST be rebuilt from cache
  without network access (offline capable).

---

## Migration & Backward Compatibility

### Spec 003 commands remain functional

All spec 003 commands (`source scan`, `source candidates`,
`create-package --from-source`) continue to work. The new workflow is
an **additional path**, not a replacement.

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

---

## Affected Files (Estimated)

### Modified

| File | Change |
|------|--------|
| `commands/install.py` | Add source resolution before registry lookup |
| `services/install_service.py` | Add `install_from_source()` path |
| `services/source_service.py` | Add `resolve_artifact()`, `build_source_index()` |
| `core/workspace.py` | Extend `LockedPackage` with source fields |
| `commands/list_cmd.py` | Add `--available` flag |
| `commands/search.py` | Include source artifacts in results |
| `mcp/tools_read.py` | Add `aam_available`, `aam_outdated` |
| `mcp/tools_write.py` | Add `aam_upgrade` |

### New

| File | Purpose |
|------|---------|
| `commands/outdated.py` | `aam outdated` command |
| `commands/upgrade.py` | `aam upgrade` command |
| `services/upgrade_service.py` | Upgrade logic with diff/backup flow |
| `tests/unit/test_unit_outdated.py` | Outdated detection tests |
| `tests/unit/test_unit_upgrade.py` | Upgrade flow tests |
| `tests/unit/test_unit_install_from_source.py` | Source install tests |

---

## Open Questions

1. **Auto-deploy on install?** When installing from a source, should AAM
   automatically deploy to the configured platform (like `aam install`
   does for registry packages)? **Proposed: Yes** — this is the whole
   point. Install means "ready to use."

2. **Version display for source packages?** Source packages don't have
   semver versions. Options:
   - Show commit SHA short form (`abc123`)
   - Show date (`2026-02-08`)
   - Show `source@<commit>` format
   **Proposed: `source@abc123`** — clear about origin and version.

3. **`aam upgrade` vs `aam update`?** npm uses `update`, apt uses
   `upgrade`. Which term?
   **Proposed: `aam upgrade`** — distinguishes from `source update`
   (which refreshes the index, not packages).

4. **Should `aam install` auto-run `source update` if stale?** For
   example, if the source hasn't been updated in 24 hours.
   **Proposed: No** — keep it explicit like apt. Add `--refresh` flag
   for future convenience.

---

## Success Criteria

- **SC-001**: A user can run `aam source add openai/skills` followed by
  `aam install code-review` and have the skill deployed to their AI
  agent in under 10 seconds total.
- **SC-002**: `aam source update` correctly identifies new, modified,
  and removed packages across all sources.
- **SC-003**: `aam outdated` accurately reports which installed packages
  have newer commits available.
- **SC-004**: `aam upgrade` updates packages while respecting local
  modification warnings.
- **SC-005**: The entire workflow works offline after initial
  `source add` (except `source update`).
