# AAM CLI Restructure Analysis

**Date:** 2026-02-09
**Branch:** `003-git-source-scanning`
**Status:** Analysis / Proposal
**Input specs:** DESIGN.md, spec-003 (Git Source Scanning), spec-004 (npm-Style Source Workflow)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current CLI State of the Art](#2-current-cli-state-of-the-art)
3. [Identified Problems](#3-identified-problems)
4. [Vision: Sources as Virtual Registries (spec 004)](#4-vision-sources-as-virtual-registries-spec-004)
5. [Proposed Command Grouping by Persona](#5-proposed-command-grouping-by-persona)
6. [Detailed Persona Analysis](#6-detailed-persona-analysis)
7. [Gap Analysis: Missing Capabilities](#7-gap-analysis-missing-capabilities)
8. [Improvement Recommendations](#8-improvement-recommendations)
9. [Migration Path](#9-migration-path)

---

## 1. Executive Summary

The AAM CLI currently registers **28 commands** (14 top-level + 14 subcommands across 4 groups) in a flat structure. Commands from different functional areas — consumer workflows, authoring workflows, source management, and infrastructure configuration — are intermixed at the root level with no logical grouping visible to the user.

**Two critical structural problems:**

1. **Creator commands have no prefix.** Six authoring commands (`init`, `create-package`, `validate`, `pack`, `publish`, `build`) sit at root level alongside consumer commands, providing no discoverability or logical grouping. All other functional areas (`source`, `config`, `registry`, `mcp`) already use proper subcommand groups.

2. **`aam init` is misused.** Users universally expect `init` to set up the tool (like `git init`, `npm init`), but `aam init` currently scaffolds a new package — a creator action that confuses first-time consumers.

Additionally, the current source-to-install workflow (spec 003) requires **5 manual steps** to go from "I found a repo with skills" to "those skills are deployed to my agent". Spec 004 proposes collapsing this to **2 steps** by treating git sources as virtual package registries — matching the mental model of `apt` / `npm`.

This analysis:

- Compiles the **complete state of the art** of every CLI command (implemented, stubbed, planned)
- Identifies **four distinct user personas** and maps every command to a persona
- Integrates spec 004's **npm-style workflow** vision (`outdated`, `upgrade`, install-from-source)
- Proposes `aam pkg` prefix for all creator commands and repurposed `aam init` for client setup
- Catalogs implementation gaps and proposes a restructured command hierarchy
- Provides a concrete migration path from the current flat layout to a grouped layout

---

## 2. Current CLI State of the Art

### 2.1 Complete Command Inventory

The table below is the **single source of truth** for every command — implemented, stubbed, and planned — across all specs and design documents.

#### Legend

| Status | Meaning |
|--------|---------|
| **Implemented** | Code exists and is functional |
| **Stub** | Command registered, handler has TODO placeholders |
| **Planned (DESIGN.md)** | Specified in DESIGN.md but no code exists |
| **Planned (spec 004)** | Specified in spec 004 (npm-style workflow) |
| **Proposed** | Not in any spec; identified as beneficial by this analysis |

#### 2.1.1 Consumer Commands (install, use, maintain packages)

| # | Command | Status | Flags / Args | Description |
|---|---------|--------|-------------|-------------|
| 1 | `aam install <pkg>` | **Implemented** | `--platform`, `--no-deploy`, `--force`, `--dry-run` | Install from registry, directory, `.aam` archive. Resolves deps, deploys to platform. |
| 2 | `aam uninstall <pkg>` | **Implemented** (bug: Cursor-only) | — | Remove installed package and undeploy artifacts. **Bug:** hardcodes `CursorAdapter`. |
| 3 | `aam list` | **Implemented** | `--tree` | List installed packages with artifact counts. `--tree` shows dependency graph. |
| 4 | `aam info <pkg>` | **Implemented** | — | Show detailed metadata for an installed package. |
| 5 | `aam search <query>` | **Implemented** | `--limit`, `--type`, `--json` | Search configured registries. **Gap:** does not search source artifacts. |
| 6 | `aam verify [pkg]` | **Implemented** | `--all`, `--json` | Verify file integrity against stored SHA-256 checksums. |
| 7 | `aam diff <pkg>` | **Implemented** | `--json` | Show unified diff for modified installed files. |
| 8 | `aam outdated` | **Planned (spec 004)** | `--json` | Compare installed packages against available versions in sources and registries. Show commit-based staleness for source packages, version-based for registry packages. |
| 9 | `aam upgrade [pkg]` | **Planned (spec 004)** | `--all`, `--dry-run`, `--force` | Update installed packages to latest from sources/registries. Respects upgrade warning flow (backup/skip/diff/force). Alias: `aam update` for npm familiarity. |
| 10 | `aam deploy` | **Planned (DESIGN.md)** | `--platform` | Re-deploy installed artifacts without re-downloading. |
| 11 | `aam undeploy` | **Planned (DESIGN.md)** | `--platform` | Remove deployed artifacts without uninstalling the package. |

> **`update` vs `upgrade` terminology (spec 004 open question #3):**
> - `aam source update` = refresh index (like `apt update`)
> - `aam upgrade` = upgrade installed packages (like `apt upgrade`)
> - `aam update` from DESIGN.md = alias for `aam upgrade` (npm convention)
>
> **Decision:** Use `aam upgrade` as the canonical name (avoids collision with `source update`). Register `aam update` as a hidden alias pointing to `aam upgrade`.

#### 2.1.2 Client Initialization

| # | Command | Status | Flags / Args | Description |
|---|---------|--------|-------------|-------------|
| 13 | `aam init` | **Implemented** (as package scaffolding) | `[name]` | Currently scaffolds a new package. **Proposed:** repurpose as client/workspace initialization — configure active platform, default registries, default sources, create `~/.aam/config.yaml`. See [section 5.4](#54-aam-init-repurposed-as-client-initialization). |

#### 2.1.3 Creator Commands — `aam pkg *` (author, build, publish packages)

> **Convention:** All package authoring commands use the `aam pkg` prefix for consistency and to separate the creator workflow from the consumer workflow. `pkg` is short, unambiguous, and avoids collision with the `package` argument used by consumer commands like `aam install <package>`.

| # | Command | Current Status | Proposed | Flags / Args | Description |
|---|---------|---------------|----------|-------------|-------------|
| 14 | `aam create-package [path]` | **Implemented** (root) | → `aam pkg create [path]` | `--all`, `--type`, `--platform`, `--organize`, `--include`, `--from-source`, `--artifacts`, `--name`, `--scope`, `--version`, `--description`, `--author`, `--dry-run`, `--output-dir`, `-y` | Create package from existing project or remote source. Autodetects artifacts. |
| 15 | `aam validate [path]` | **Implemented** (root) | → `aam pkg validate [path]` | — | Validate `aam.yaml` manifest and artifact references. |
| 16 | `aam pack [path]` | **Implemented** (root) | → `aam pkg pack [path]` | — | Build distributable `.aam` archive with SHA-256 checksums. |
| 17 | `aam publish` | **Implemented** (root) | → `aam pkg publish` | `--registry`, `--tag`, `--dry-run` | Publish `.aam` archive to a configured registry. |
| 18 | `aam build --target` | **Stub (TODO)** (root) | → `aam pkg build` | `--target` (required), `--output` | Build portable platform bundle. Handler exists but body is `TODO`. |
| 19 | — | **Planned (DESIGN.md)** | `aam pkg init [name]` | — | Scaffold a new AAM package (moved from `aam init`). Interactive prompts for name, version, artifact types, platforms. |
| 20 | `aam test` | **Planned (DESIGN.md)** | `aam pkg test` | — | Run declared tests from `aam.yaml` quality section. |
| 21 | `aam eval` | **Planned (DESIGN.md)** | `aam pkg eval` | `--publish` | Run declared evals and optionally publish results. |
| 22 | `aam yank <pkg>@<ver>` | **Planned (DESIGN.md)** | `aam pkg yank` | — | Mark a version as yanked (HTTP registry only). |
| 23 | `aam dist-tag add/rm/ls` | **Planned (DESIGN.md)** | `aam pkg dist-tag` | — | Manage distribution tags on published versions. |

#### 2.1.4 Source Curation Commands (manage git repo artifact feeds)

| # | Command | Status | Flags / Args | Description |
|---|---------|--------|-------------|-------------|
| 24 | `aam source add <url>` | **Implemented** | `--ref`, `--path`, `--name`, `--json` | Register remote git repo. Shallow clone + scan. Supports shorthand, HTTPS, SSH, tree URLs. |
| 25 | `aam source scan <name>` | **Implemented** | `--type`, `--json` | Scan cached clone for artifacts grouped by type. |
| 26 | `aam source update [name]` | **Implemented** | `--all`, `--dry-run`, `--json` | Fetch upstream changes, detect new/modified/removed artifacts. |
| 27 | `aam source list` | **Implemented** | `--json` | Show all configured sources with name, URL, ref, artifact count, last fetched. |
| 28 | `aam source remove <name>` | **Implemented** | `--purge-cache`, `--json` | Remove source config. Optionally delete cached clone. |
| 29 | `aam source candidates` | **Implemented** | `--source`, `--type`, `--json` | List unpackaged artifacts across all sources. |

#### 2.1.5 Configuration & Administration Commands

| # | Command | Status | Flags / Args | Description |
|---|---------|--------|-------------|-------------|
| 30 | `aam config set <key> <value>` | **Implemented** | — | Set a config value (dot-notation for nested keys). |
| 31 | `aam config get <key>` | **Implemented** | — | Get a config value. |
| 32 | `aam config list` | **Implemented** | — | List all config values. |
| 33 | `aam registry init <path>` | **Implemented** | `--default`, `--force` | Create a new local registry directory. |
| 34 | `aam registry add <name> <url>` | **Implemented** | `--default` | Register a registry source. |
| 35 | `aam registry list` | **Implemented** | — | Show all configured registries. |
| 36 | `aam registry remove <name>` | **Implemented** | — | Remove a configured registry. |
| 37 | `aam mcp serve` | **Implemented** | `--transport`, `--port`, `--allow-write`, `--log-file`, `--log-level` | Start MCP server for IDE agent integration (stdio or HTTP). |
| 38 | `aam doctor` | **Implemented** | — | Run environment diagnostics. |

#### 2.1.6 Planned Commands (not yet in codebase)

| # | Command | Source | Category | Priority | Description |
|---|---------|--------|----------|----------|-------------|
| 39 | `aam outdated` | spec 004 | Consumer | **P0** | Compare installed vs. available (commit-based for sources, semver for registries). |
| 40 | `aam upgrade [pkg]` | spec 004 | Consumer | **P0** | Upgrade installed packages from sources. Implicit `source update` + re-install. |
| 41 | `aam deploy` | DESIGN.md | Consumer | P1 | Re-deploy artifacts to platform without re-downloading. |
| 42 | `aam undeploy` | DESIGN.md | Consumer | P1 | Remove deployed artifacts without uninstalling. |
| 43 | `aam login` | DESIGN.md | Auth | P2 | Authenticate with HTTP registry. |
| 44 | `aam logout` | DESIGN.md | Auth | P2 | Revoke saved API token. |
| 45 | `aam completion` | DESIGN.md | Utility | P2 | Generate shell completion scripts. |
| 46 | `aam why <pkg>` | This analysis | Consumer | P3 | Explain why a package is installed (dependency chain). |

> **Note:** Creator-specific planned commands (`pkg build`, `pkg test`, `pkg eval`, `pkg yank`, `pkg dist-tag`) are listed in section 2.1.3 above under the `aam pkg` group.

### 2.2 Current Hierarchy (as registered in `main.py`)

```
aam
├── install            ← Consumer
├── uninstall          ← Consumer
├── list               ← Consumer
├── info               ← Consumer
├── search             ← Consumer
├── verify             ← Consumer
├── diff               ← Consumer
├── init               ← Creator (MISPLACED — should be client init or aam pkg init)
├── create-package     ← Creator (INCONSISTENT — no prefix)
├── validate           ← Creator (INCONSISTENT — no prefix)
├── pack               ← Creator (INCONSISTENT — no prefix)
├── publish            ← Creator (INCONSISTENT — no prefix)
├── build              ← Creator (stub, INCONSISTENT — no prefix)
├── doctor             ← Utility
├── config/            ← Configuration
│   ├── set
│   ├── get
│   └── list
├── registry/          ← Configuration
│   ├── init
│   ├── add
│   ├── list
│   └── remove
├── source/            ← Source Curator
│   ├── add
│   ├── scan
│   ├── update
│   ├── list
│   ├── remove
│   └── candidates
└── mcp/               ← Infrastructure
    └── serve
```

**Key observation:** All 6 creator commands (`init`, `create-package`, `validate`, `pack`, `publish`, `build`) sit at root level with no shared prefix, making them indistinguishable from consumer commands in `--help`. Meanwhile, source and config commands are already properly grouped.

### 2.3 Implementation Completeness Summary

```
Implemented & functional:    22 commands  (79%)
Implemented with bugs:        1 command   ( 4%)  ← uninstall (hardcoded adapter)
Stub / TODO:                  1 command   ( 4%)  ← build
Planned / not started:       15 commands  (spec 004 + DESIGN.md)
                             ──────────
Total surface (target):      46 commands
```

### 2.4 Command Registration Order (main.py)

The commands are registered in batches reflecting chronological development history, not logical grouping:

1. **"Existing commands"** — `build`, `create-package`, `install`, `registry`, `search`, `publish`, `config`
2. **"New commands for local-repository feature"** — `init`, `validate`, `pack`, `list`, `info`, `uninstall`
3. **"Source management commands (spec 003)"** — `source`, `verify`, `diff`
4. **"MCP server and diagnostic"** — `mcp`, `doctor`

---

## 3. Identified Problems

### 3.1 Flat Root Namespace Overload

14 commands at the root level creates a noisy `--help` output. Users must scan all 14 to find what they need. With planned additions (`outdated`, `upgrade`, `deploy`, `undeploy`, `yank`, `dist-tag`, `test`, `eval`, `login`, `logout`, `register`, `completion`), the root level would grow to **26+ commands** — unmanageable.

**Current `aam --help` shows 14+ root commands without clear categorization.**

### 3.2 Source Workflow Friction (spec 004 Problem Statement)

The spec 003 workflow requires **5 steps** to go from "I found a repository" to "skills are deployed":

```
aam source add openai/skills        # 1. clone + scan
aam source scan openai/skills       # 2. browse artifacts
aam source candidates               # 3. see what's unpackaged
aam create-package --from-source    # 4. build a package
aam install ./my-package            # 5. install the package
```

Users expect an npm/apt experience:

```
aam source add openai/skills           # 1. register source (like apt source)
aam install openai/skills/code-review  # 2. install directly
```

The `create-package` step is an **implementation detail** that should be invisible to consumers.

### 3.3 Mixed Personas at Root Level

Consumer commands (`install`, `search`) sit next to creator commands (`pack`, `publish`) and source-curator commands (`verify`, `diff`). A standard user who only consumes packages is exposed to the full authoring surface.

### 3.4 No `outdated` / `upgrade` Commands

There is currently **no way** to:
- Check if installed packages have newer versions (`outdated`)
- Upgrade installed packages to latest (`upgrade`)
- Compare installed source commit against HEAD (`outdated` for source packages)

Users must manually `uninstall` + `install` or use `install --force` as a workaround.

### 3.5 Creator Commands Lack Consistent Prefix

All 6 creator commands (`init`, `create-package`, `validate`, `pack`, `publish`, `build`) sit at root level with no shared prefix. They are indistinguishable from consumer commands in `--help`:

```
Commands:
  build             Build a portable platform bundle     ← creator
  create-package    Create a package from project        ← creator
  info              Show package details                 ← consumer
  init              Initialize a new package             ← creator (misleading!)
  install           Install a package                    ← consumer
  list              List installed packages              ← consumer
  pack              Build distributable archive          ← creator
  publish           Publish to registry                  ← creator
  search            Search for packages                  ← consumer
  validate          Validate package manifest            ← creator
  ...
```

**Problem:** Consumers see 6 irrelevant commands; creators have no discoverability. Compare with properly grouped commands like `source`, `config`, and `registry` which already use subcommand groups.

**Fix:** Move all creator commands under `aam pkg` prefix: `aam pkg init`, `aam pkg create`, `aam pkg validate`, `aam pkg pack`, `aam pkg publish`, `aam pkg build`.

### 3.6 `aam init` Conflates Package Scaffolding with Client Setup

`aam init` currently scaffolds a new package (`aam.yaml` + artifact directories). However, users universally expect `init` to be the **first-time setup** command for a tool:

| Tool | `init` meaning |
|------|---------------|
| `git init` | Initialize a repository |
| `npm init` | Initialize a project |
| `pip init` / `pipenv --python` | Initialize a virtual environment |
| `aam init` (current) | Scaffold a package **← inconsistent with user expectation** |

A first-time AAM user runs `aam init` expecting to set up their environment, but instead gets prompted to create a package. The actual client setup is scattered across `aam config set`, `aam registry add`, and `aam source add` — a poor onboarding experience.

**Fix:** Repurpose `aam init` as client initialization (choose platform, configure registries, add sources). Move package scaffolding to `aam pkg init`.

### 3.7 Naming Inconsistencies

| Issue | Example | Impact |
|-------|---------|--------|
| Hyphenated compound name | `create-package` — the word "package" is redundant when commands live under `aam pkg` | Solved by `aam pkg create` |
| `info` vs. `show` | `info` (registered name) vs. `show_package.py` (file name) | Confusing internal naming |
| `list` collision potential | Root `list` vs. `registry list` vs. `source list` vs. `config list` | Ambiguous without context |
| `diff` dual meaning | `diff` at root level (package integrity) vs. typical `git diff` expectation | Potential user confusion |

> **Naming principle for `aam pkg` subcommands:** The `pkg` prefix establishes the context (packages), so subcommand names drop the redundant "package" qualifier. `create-package` → `pkg create`, `validate` stays `pkg validate`, etc. Each subcommand is a short verb: `init`, `create`, `validate`, `pack`, `publish`, `build`, `test`, `eval`, `yank`.

### 3.8 Hardcoded Platform in Uninstall

`uninstall.py` directly imports and uses `CursorAdapter` instead of using the adapter factory, unlike `install.py` which properly uses `create_adapter()`. This means uninstall only works for Cursor regardless of configuration.

```python
# uninstall.py line 21 — hardcoded
from aam_cli.adapters.cursor import CursorAdapter
...
adapter = CursorAdapter(project_dir)
```

### 3.9 Inconsistent Console Handling

Some commands create their own `Console()` instance (e.g., `source.py`), while others use the shared context console from `ctx.obj["console"]` (e.g., `install.py`). Some commands use `sys.exit(1)` directly while others use `ctx.exit(1)`.

| Pattern | Used by |
|---------|---------|
| `ctx.obj["console"]` | install, list, uninstall, build, publish, search, validate, pack, init |
| `Console()` module-level | source (all subcommands) |
| `sys.exit(1)` | source (all subcommands) |
| `ctx.exit(1)` | install, publish, search |

### 3.10 `search` Does Not Include Source Artifacts

`aam search` only queries registries. Source artifacts are invisible to search, which breaks the spec 004 principle that "sources are package registries". A user who has added `openai/skills` cannot `aam search code-review` to find artifacts from that source.

### 3.11 `list` Has No `--available` Flag

There is no way to browse all installable artifacts across sources and registries. The closest is `aam source candidates`, which only shows artifacts not yet packaged — a curator concept, not a consumer concept.

### 3.12 No Help Text Grouping

Click supports command grouping in help text (via `cls=` or custom group classes), but the CLI does not use this. All root commands appear as a flat alphabetical list in `--help`.

---

## 4. Vision: Sources as Virtual Registries (spec 004)

Spec 004 introduces a fundamental shift in how sources relate to the consumer workflow. The key insight:

> **Sources are package registries.** When you add a git source, every discovered artifact becomes an installable package — just like adding an npm registry makes its packages available for `npm install`.

### 4.1 Mental Model Comparison

| Concept | apt | npm | aam (current spec 003) | aam (proposed spec 004) |
|---------|-----|-----|----------------------|------------------------|
| Add source | `add-apt-repository` | `.npmrc` registry | `aam source add` | `aam source add` (same) |
| Refresh index | `apt update` | (automatic) | `aam source update` | `aam source update` (same) |
| Browse available | `apt list` | `npm search` | `aam source candidates` | `aam search` / `aam list --available` |
| Install | `apt install vim` | `npm install lodash` | 5-step manual process | **`aam install code-review`** |
| Check updates | `apt list --upgradable` | `npm outdated` | (none) | **`aam outdated`** |
| Upgrade | `apt upgrade` | `npm update` | (none) | **`aam upgrade`** |

### 4.2 Current vs. Proposed Consumer Journey

**Current (spec 003) — 5 steps:**

```
aam source add openai/skills                  # 1. clone + scan
aam source scan openai/skills                 # 2. browse artifacts
aam source candidates                         # 3. see unpackaged
aam create-package --from-source openai/skills --artifacts code-review
                                              # 4. create package
aam install ./code-review                     # 5. install
```

**Proposed (spec 004) — 2 steps:**

```
aam source add openai/skills                  # 1. register source
aam install code-review                       # 2. install (auto-resolves from source)
```

### 4.3 Key Design Decisions from spec 004

| Decision | Description |
|----------|-------------|
| **D1: Virtual packages** | Source artifacts become installable "virtual packages" with commit SHA as version |
| **D2: Qualified names** | `aam install code-review` (auto-resolve), `aam install openai/skills/code-review` (explicit source) |
| **D3: Commit as version** | `source@abc123` format enables `outdated` and `upgrade` for source packages |
| **D4: Implicit packaging** | `aam install` internally generates `aam.yaml` + provenance — user never sees `create-package` |
| **D5: Explicit update** | `aam source update` is manual (like `apt update`), not automatic on install |

### 4.4 New Consumer Commands from spec 004

These three commands fill critical gaps in the consumer experience:

#### `aam outdated` (P0)

```
$ aam outdated
Package         Installed    Available   Source
code-review     abc123       def456      openai/skills
architect       abc123       abc123      openai/skills  (up to date)
my-agent        1.0.0        1.2.0       local-registry

1 source package outdated, 1 registry package outdated.
Run 'aam upgrade' to update.
```

- Compares installed source packages' commit SHA against current source HEAD
- Compares installed registry packages' version against latest available
- Packages not from sources show "(no source)" 
- `--json` output for scripting

#### `aam upgrade [pkg]` (P0)

```
$ aam upgrade
Fetching sources...
  openai/skills: 1 package outdated
Upgrading...
  code-review  abc123 → def456  ✓

$ aam upgrade code-review --dry-run
Would upgrade code-review from abc123 to def456
```

- Implicit `source update` to refresh index first
- Respects existing upgrade warning flow from spec 003 (backup/skip/diff/force)
- `--dry-run` previews changes
- Without args: upgrade all outdated packages

#### `aam list --available` (P1)

```
$ aam list --available
openai/skills (12 packages):
  code-review         skill     Review code changes
  architect           agent     Design system architectures
  ...

local-registry (3 packages):
  @myorg/my-agent     agent     ASVC compliance auditor

15 packages available from 2 sources + 1 registry.
```

- Shows all installable artifacts from sources AND registries
- Grouped by source/registry name
- Complementary to `aam search` (which also gains source results)

---

## 5. Proposed Command Grouping by Persona

### 5.1 Four Personas

| Persona | Description | Primary Workflow |
|---------|-------------|-----------------|
| **Consumer** | End user who installs and uses packages | `init → source add → search → install → outdated → upgrade` |
| **Creator** | Package author who builds and publishes | `pkg init → pkg create → pkg validate → pkg pack → pkg publish` |
| **Source Curator** | Power user who manages git sources and curates artifact feeds | `source add → source scan → source candidates → source update` |
| **Administrator** | User who configures registries, settings, and infrastructure | `config → registry → mcp → doctor` |

### 5.2 Proposed Hierarchy

```
aam
│
│  ── CLIENT INITIALIZATION ──
│
├── init                       Set up AAM client: choose platform, add registries,
│                              configure default sources, create ~/.aam/config.yaml
│
│  ── CONSUMER COMMANDS (top-level, most common) ──
│
├── install <pkg>              Install a package from registry or source
├── uninstall <pkg>            Remove an installed package
├── upgrade [pkg]              Upgrade packages to latest (NEW — spec 004)
├── outdated                   Show packages with updates available (NEW — spec 004)
├── search <query>             Search registries AND sources for packages
├── list                       List installed packages (+ --available for browse)
├── info <pkg>                 Show package details
├── verify [pkg|--all]         Verify installed file integrity
├── diff <pkg>                 Show file modifications vs. installed version
│
│  ── CREATOR COMMANDS (aam pkg *) ──
│
├── pkg/                       Package authoring commands
│   ├── init [name]            Scaffold a new AAM package (aam.yaml + dirs)
│   ├── create [path]          Create package from existing project artifacts
│   ├── validate [path]        Validate manifest and artifacts
│   ├── pack [path]            Build distributable .aam archive
│   ├── publish                Publish archive to registry
│   ├── build --target <plat>  Build portable platform bundle
│   ├── test                   Run declared tests (planned)
│   ├── eval                   Run declared evals (planned)
│   ├── yank <pkg>@<ver>       Mark a version as yanked (planned)
│   └── dist-tag add/rm/ls    Manage distribution tags (planned)
│
│  ── SOURCE MANAGEMENT (git artifact feeds) ──
│
├── source/                    Manage remote git artifact sources
│   ├── add <url>              Register a remote git source
│   ├── scan <name>            Scan source for artifacts
│   ├── update [name|--all]    Fetch upstream changes (apt update)
│   ├── list                   List configured sources
│   ├── remove <name>          Remove a source
│   └── candidates             List unpackaged artifact candidates
│
│  ── ADMINISTRATION ──
│
├── config/                    Manage AAM configuration
│   ├── set <key> <value>
│   ├── get <key>
│   └── list
│
├── registry/                  Manage registry connections
│   ├── init <path>
│   ├── add <name> <url>
│   ├── list
│   └── remove <name>
│
│  ── INFRASTRUCTURE & UTILITIES ──
│
├── mcp/                       MCP server for IDE integration
│   └── serve
│
├── doctor                     Environment diagnostics
│
│  ── FUTURE ──
│
└── auth/                      Authentication (planned — DESIGN.md)
    ├── login
    ├── logout
    └── register
```

### 5.3 Help Text Grouping

With Click's custom group support, the `--help` output would display:

```
$ aam --help

Usage: aam [OPTIONS] COMMAND [ARGS]...

  AAM - Agent Package Manager.
  A package manager for AI agents, skills, and tools.

Options:
  -v, --verbose  Enable verbose output
  --version      Show the version and exit.
  --help         Show this message and exit.

Getting Started:
  init        Set up AAM: choose platform, configure registries and sources

Package Management:
  install     Install a package and deploy artifacts
  uninstall   Remove an installed package
  upgrade     Upgrade installed packages to latest version
  outdated    Show packages with available updates
  search      Search registries and sources for packages
  list        List installed packages (--available for all)
  info        Show package details

Package Integrity:
  verify      Verify installed file checksums
  diff        Show modifications in installed packages

Package Authoring:
  pkg         Package creation and publishing commands (pkg init, pkg create, ...)

Source Management:
  source      Manage remote git artifact sources

Configuration:
  config      Manage AAM configuration
  registry    Manage registry connections

Utilities:
  mcp         MCP server for IDE integration
  doctor      Environment diagnostics
```

### 5.4 `aam init` Repurposed as Client Initialization

Currently `aam init` scaffolds a new package (creates `aam.yaml`, `skills/`, `agents/`, etc.). This is a **creator** action that belongs under `aam pkg init`.

The root-level `aam init` should instead be the **first command a new user runs** — configuring their AAM client for consuming packages:

```
$ aam init

Welcome to AAM - Agent Package Manager!

Which AI platform do you use?
  ✓ Cursor
  ✗ GitHub Copilot
  ✗ Claude
  ✗ Codex

Setting default platform to: cursor

Configure a package registry?
  (1) Create a local registry   → aam registry init ~/my-packages
  (2) Add an existing registry  → enter URL
  (3) Skip for now

  [default: 3] 1
  ✓ Created local registry at ~/my-packages
  ✓ Registered as default registry

Add community artifact sources?
  [x] openai/skills              OpenAI's curated Codex skills
  [x] github/awesome-copilot     GitHub's Copilot skills collection
  [ ] Skip community sources

  ✓ Added 2 default sources (aam source update to fetch)

✓ AAM initialized!
  Config:   ~/.aam/config.yaml
  Platform: cursor
  Registry: ~/my-packages (local)
  Sources:  2 configured

Next steps:
  aam source update               Fetch artifacts from sources
  aam search <query>              Find packages
  aam install <package>           Install a package
  aam pkg init                    Create your own package
```

**Key differences from current `init`:**

| Aspect | Current `aam init` | Proposed `aam init` |
|--------|-------------------|-------------------|
| **Purpose** | Scaffold a package | Set up client configuration |
| **Creates** | `aam.yaml` + artifact dirs | `~/.aam/config.yaml` |
| **Persona** | Creator | Consumer (first-time user) |
| **Frequency** | Per package | Once per machine/user |
| **Platform selection** | Which platforms the package supports | Which platform the user's IDE uses |
| **Registry** | Not involved | Optionally creates or registers a registry |
| **Sources** | Optionally registers default sources | Optionally registers default sources (primary home) |
| **Moved to** | `aam pkg init` | Stays as `aam init` |

---

## 6. Detailed Persona Analysis

### 6.1 Consumer Persona — "I want to install and use packages"

#### Current journey (spec 003 — registry packages):

```
aam search "code review"     → Find a package
aam install @org/reviewer    → Install it
aam list                     → See what's installed
aam info @org/reviewer       → Check details
aam verify @org/reviewer     → Check file integrity after edits
aam diff @org/reviewer       → See what changed
aam install @org/reviewer@2.0 --force  → Upgrade (workaround)
aam uninstall @org/reviewer  → Remove it
```

#### Proposed journey (spec 004 — source + registry unified):

```
aam init                            → Set up platform, registries, sources (first time)
aam source update                   → Refresh available packages (like apt update)
aam search "code review"            → Find packages across ALL sources + registries
aam list --available                → Browse everything installable
aam install code-review             → Install from source (auto-resolved, auto-deployed)
aam install @org/reviewer           → Install from registry (same command)
aam list                            → See what's installed
aam outdated                        → Check for updates across sources + registries
aam upgrade                         → Upgrade all outdated packages
aam upgrade code-review             → Upgrade a specific package
aam verify --all                    → Check integrity
aam uninstall code-review           → Remove
```

#### What works well today:
- `install` supports multiple source formats (registry, directory, archive)
- Upgrade warning with backup/diff/force options is well-implemented (spec 003)
- `verify` and `diff` provide useful integrity checking
- `list --tree` shows dependency graph

#### Consumer command gap analysis:

| Command | Status | Impact | Priority |
|---------|--------|--------|----------|
| `aam outdated` | **Missing** | No way to check for updates. Users cannot see which installed packages have newer versions in sources or registries. This is the #1 consumer gap. | **P0** |
| `aam upgrade [pkg]` | **Missing** | No way to upgrade. Users must `install --force` as a workaround, which doesn't check sources for newer commits. | **P0** |
| `aam install` from source | **Missing** | Install only resolves from registries. Source artifacts require the 5-step manual flow. This is the #1 workflow friction. | **P0** |
| `aam search` includes sources | **Missing** | Search only queries registries. Source artifacts are invisible to search. | **P0** |
| `aam list --available` | **Missing** | No way to browse all installable packages across sources + registries. | **P1** |
| `aam deploy` / `aam undeploy` | **Missing** | Cannot re-deploy without reinstalling. Cannot remove deployed files without uninstalling. | **P1** |
| `uninstall` multi-platform | **Bug** | Hardcodes CursorAdapter — only works for Cursor platform. | **P0 (bug fix)** |
| `uninstall --platform` | **Missing** | Cannot target a specific platform for undeploy. | **P2** |
| `install` deploy path display | **Missing** | User doesn't see where artifacts were deployed (DESIGN.md shows this in example output). | **P2** |
| `aam why <pkg>` | **Missing** | No way to explain why a transitive dependency is installed. | **P3** |
| `aam --global install` | **Missing** | Cannot install to user-level (e.g., `~/.cursor/skills/`). | **P3** |

#### Consumer priority roadmap:

1. **Fix `uninstall` adapter bug** (immediate — P0 bug fix)
2. **Extend `install` to resolve from sources** (spec 004 — P0)
3. **Extend `search` to include source artifacts** (spec 004 — P0)
4. **Implement `aam outdated`** (spec 004 — P0)
5. **Implement `aam upgrade`** (spec 004 — P0)
6. **Add `list --available`** (spec 004 — P1)
7. **Implement `deploy` / `undeploy`** (DESIGN.md — P1)

### 6.2 Creator Persona — "I want to package and distribute my artifacts"

#### Current journey (inconsistent — commands at root with no prefix):

```
aam init my-package          → Scaffold empty package     (root, no prefix)
  -- OR --
aam create-package           → Detect & package existing   (root, hyphenated)

aam validate                 → Check manifest validity     (root, no prefix)
aam pack                     → Build .aam archive          (root, no prefix)
aam publish --registry local → Publish to registry         (root, no prefix)
```

#### Proposed journey (consistent `aam pkg` prefix):

```
aam pkg init my-package      → Scaffold empty package
  -- OR --
aam pkg create               → Detect & package existing artifacts

aam pkg validate             → Check manifest validity
aam pkg pack                 → Build .aam archive
aam pkg publish              → Publish to registry
aam pkg build --target cursor → Build portable platform bundle
```

#### What works well:
- `create-package` with autodetection and interactive selection is powerful
- `validate → pack → publish` pipeline is clear
- Local registry support enables zero-infrastructure publishing
- `--from-source` flag on `create-package` bridges source curation and authoring

#### What needs improvement:

| Issue | Impact | Recommendation |
|-------|--------|----------------|
| Creator commands have no shared prefix | Mixed in with consumer commands in `--help`; confusing for users who only consume | Move all creator commands under `aam pkg` |
| `aam init` conflates package scaffolding with client setup | New users expect `init` to set up AAM, not create a package | Repurpose `aam init` as client setup; use `aam pkg init` for package scaffolding |
| `build` is a stub (TODO) | Portable bundles cannot be created | Implement `aam pkg build` |
| No `aam pkg test` / `aam pkg eval` | Cannot run declared quality checks | Implement quality commands under `pkg` |
| No `aam pkg yank` | Cannot mark versions as yanked | Implement under `pkg` for HTTP registry |
| No `aam pkg dist-tag` | Cannot manage distribution tags | Implement under `pkg` |
| `--organize move` is dangerous | No undo capability | Add `--confirm` requirement for move mode |
| No version bump utility | No way to bump `aam.yaml` version | Consider `aam pkg version patch/minor/major` |

#### Creator priority roadmap:

1. **Move all creator commands under `aam pkg`** — Consistent prefix, clean separation from consumer
2. **Implement `aam pkg build`** — Portable bundles are a key adoption driver
3. **Add `aam pkg test` / `aam pkg eval`** — Quality gate commands from DESIGN.md
4. **Version management** — `aam pkg version patch/minor/major` for bumping `aam.yaml`

### 6.3 Source Curator Persona — "I want to manage git repo artifact feeds"

#### Current journey:

```
aam source add openai/skills               → Register a git repo
aam source scan openai/skills              → See what artifacts exist
aam source update --all                    → Fetch upstream changes
aam source candidates                      → See unpackaged artifacts
aam pkg create --from-source openai/skills --artifacts skill1,skill2
                                          → Package selected artifacts
```

#### What works well:
- Complete lifecycle: add → scan → update → candidates → package
- Flexible URL formats (shorthand, HTTPS, SSH, tree URLs)
- `--json` output on all source commands enables scripting
- Change detection (new/modified/removed) on update
- Provenance metadata in created packages

#### Spec 004 impact on this persona:

With spec 004, the source curator persona **shrinks** because consumers no longer need the curator to package artifacts. The `source candidates` → `create-package --from-source` step becomes an internal detail of `aam install`. The curator role becomes focused on:

- Managing which sources are configured (add/remove)
- Monitoring upstream changes (update/scan)
- Advanced curation (filtering, organizing) for enterprise use cases

#### What still needs improvement:

| Issue | Impact | Recommendation |
|-------|--------|----------------|
| No `aam source info <name>` | Must use `scan` to see source details | Add `info` subcommand for source metadata |
| No `aam source status` | Cannot quickly see overall freshness | Add status summary |
| Default sources only set during `aam init` | No way to reset or manage defaults later | Add `aam source defaults` subcommand |
| Private repo auth error UX | Error suggests `GH_TOKEN` but no guided setup | Better error messages with docs links |

### 6.4 Administrator Persona — "I want to configure registries and infrastructure"

#### Current journey:

```
aam config set default_platform cursor     → Set configuration (manual, key-by-key)
aam registry init ~/my-packages            → Create local registry
aam registry add local file://...          → Register it
aam mcp serve                              → Start MCP server
aam doctor                                 → Check environment
```

#### Proposed journey (with `aam init`):

```
aam init                                   → Interactive setup (platform, registry, sources)
aam config set <key> <value>               → Fine-tune individual settings
aam registry add corp-registry https://... → Add additional registries
aam mcp serve                              → Start MCP server
aam doctor                                 → Check environment
```

#### What works well:
- `config` group is clean with `set/get/list`
- `registry` group covers full CRUD lifecycle
- `mcp serve` with `--allow-write` safety model is well-designed
- `doctor` for environment diagnostics
- **Proposed `aam init`** consolidates the scattered first-time setup into a single guided flow

#### What needs improvement:

| Issue | Impact | Recommendation |
|-------|--------|----------------|
| No auth commands | Cannot log in to HTTP registries | Implement `aam auth login/logout/register` |
| No `aam config edit` | Must know exact key names | Add `aam config edit` to open config in `$EDITOR` |
| No `aam config reset` | Cannot restore defaults | Add reset capability |
| No `aam registry check <name>` | Cannot test connectivity to a registry | Add health check command |
| `mcp serve --transport http` undocumented in CLI help | Users may not discover HTTP mode | Improve help text and documentation |
| No shell completion command | No tab-completion for any shell | Implement `aam completion bash/zsh/fish` |

---

## 7. Gap Analysis: Missing Capabilities

### 7.1 Consolidated Missing Commands (by priority)

This table unifies all gaps from DESIGN.md, spec 004, and this analysis into a single prioritized list.

#### P0 — Must Have (blocks core consumer workflow)

| Command | Source | Category | Effort | Description |
|---------|--------|----------|--------|-------------|
| `aam install` from sources | spec 004 | Consumer | High | Resolve package names against source artifact indexes, auto-create manifest, deploy |
| `aam outdated` | spec 004 | Consumer | Medium | Compare installed commit/version against available in sources and registries |
| `aam upgrade [pkg]` | spec 004 | Consumer | Medium | Upgrade installed packages from sources (implicit `source update` + re-install) |
| `aam search` includes sources | spec 004 | Consumer | Low | Extend search to query source artifact indexes alongside registries |
| Fix `uninstall` adapter | Bug fix | Consumer | Low | Replace hardcoded `CursorAdapter` with factory |

#### P1 — Should Have (significant UX improvement)

| Command | Source | Category | Effort | Description |
|---------|--------|----------|--------|-------------|
| `aam list --available` | spec 004 | Consumer | Medium | Browse all installable artifacts from sources + registries |
| Repurpose `aam init` | This analysis | Onboarding | Medium | Client initialization — platform, registries, sources setup |
| Create `aam pkg` group | This analysis | UX | Medium | Move creator commands under `aam pkg *` prefix |
| `aam deploy [--platform]` | DESIGN.md | Consumer | Medium | Re-deploy installed artifacts without re-downloading |
| `aam undeploy [--platform]` | DESIGN.md | Consumer | Low | Remove deployed artifacts without uninstalling |
| `aam pkg build --target` | DESIGN.md | Creator | High | Complete the stub — build portable platform bundles |
| Help text grouping | This analysis | UX | Low | Categorized `--help` output using custom Click group |

#### P2 — Nice to Have (polish and completeness)

| Command | Source | Category | Effort | Description |
|---------|--------|----------|--------|-------------|
| `aam pkg dist-tag add/rm/ls` | DESIGN.md | Creator | Medium | Manage distribution tags |
| `aam pkg test` | DESIGN.md | Creator | Medium | Run declared tests from `aam.yaml` |
| `aam login` / `aam logout` | DESIGN.md | Auth | Medium | Authenticate with HTTP registry |
| `aam register` | DESIGN.md | Auth | Medium | Create registry account |
| `aam completion` | DESIGN.md | Utility | Low | Shell completion scripts |
| `aam source info <name>` | This analysis | Source | Low | Show source metadata without re-scanning |
| `aam why <pkg>` | This analysis | Consumer | Low | Explain dependency chain |

#### P3 — Future (low urgency)

| Command | Source | Category | Effort | Description |
|---------|--------|----------|--------|-------------|
| `aam pkg eval [--publish]` | DESIGN.md | Creator | High | Run LLM evals and publish results |
| `aam pkg yank <pkg>@<ver>` | DESIGN.md | Creator | Low | Mark version as yanked (HTTP registry) |
| `aam config edit` | This analysis | Admin | Low | Open config in `$EDITOR` |

### 7.2 Implementation Quality Issues

| File | Issue | Severity |
|------|-------|----------|
| `uninstall.py` | Hardcoded `CursorAdapter` instead of factory | **High** — breaks multi-platform |
| `build.py` | Entire command is a stub (TODO) | **Medium** — feature gap |
| `search.py` | Does not query source artifact indexes | **Medium** — spec 004 gap |
| `install.py` | Does not resolve from source artifacts | **Medium** — spec 004 gap |
| `source.py` | Creates own `Console()` instead of using context | **Low** — inconsistent but functional |
| `source.py` | Uses `sys.exit(1)` instead of `ctx.exit(1)` | **Low** — inconsistent error handling |
| `install.py` | `_deploy_package` imported from `core.installer` as private function | **Low** — API boundary issue |
| `main.py` | Commands registered chronologically, not logically | **Low** — maintainability |

### 7.3 Spec 004 Affected Files (from spec)

#### Files to Modify

| File | Change |
|------|--------|
| `commands/install.py` | Add source resolution before registry lookup |
| `services/install_service.py` | Add `install_from_source()` path |
| `services/source_service.py` | Add `resolve_artifact()`, `build_source_index()` |
| `core/workspace.py` | Extend `LockedPackage` with `source_name`, `source_commit` |
| `commands/list_packages.py` | Add `--available` flag |
| `commands/search.py` | Include source artifacts in results |
| `mcp/tools_read.py` | Add `aam_available`, `aam_outdated` tools |
| `mcp/tools_write.py` | Add `aam_upgrade` tool |

#### New Files

| File | Purpose |
|------|---------|
| `commands/outdated.py` | `aam outdated` command |
| `commands/upgrade.py` | `aam upgrade` command |
| `services/upgrade_service.py` | Upgrade logic with diff/backup flow |
| `tests/unit/test_unit_outdated.py` | Outdated detection tests |
| `tests/unit/test_unit_upgrade.py` | Upgrade flow tests |
| `tests/unit/test_unit_install_from_source.py` | Source install tests |

### 7.4 CLI Restructuring Affected Files (`aam init` + `aam pkg`)

#### Files to Modify

| File | Change |
|------|--------|
| `main.py` | Replace flat creator commands with `aam pkg` group; register new `aam init` client command |
| `commands/init_package.py` | Rename/refactor — move package scaffolding logic to `commands/pkg/init.py`; repurpose as client init |

#### New Files

| File | Purpose |
|------|---------|
| `commands/pkg/__init__.py` | Click group for `aam pkg` subcommands |
| `commands/pkg/init.py` | `aam pkg init` — package scaffolding (was `aam init`) |
| `commands/pkg/create.py` | `aam pkg create` — wraps existing `create_package` logic |
| `commands/pkg/validate.py` | `aam pkg validate` — wraps existing validate logic |
| `commands/pkg/pack.py` | `aam pkg pack` — wraps existing pack logic |
| `commands/pkg/publish.py` | `aam pkg publish` — wraps existing publish logic |
| `commands/pkg/build.py` | `aam pkg build` — wraps existing build logic (stub) |
| `commands/client_init.py` | `aam init` — client initialization (platform, registries, sources) |
| `services/client_init_service.py` | Business logic for interactive client setup |

---

## 8. Improvement Recommendations

### 8.1 Phase 0: Bug Fixes (immediate)

1. **Fix `uninstall.py` hardcoded adapter** — Replace `CursorAdapter` with `create_adapter()` from factory. (~15 min fix)

2. **Standardize console handling** — Make all commands use `ctx.obj["console"]` and `ctx.exit()` consistently.

### 8.2 Phase 1: spec 004 Core (next sprint — npm-style workflow)

3. **Extend `install` to resolve from sources** — Source artifacts become virtual packages. `aam install code-review` resolves from sources when not found in registries.

4. **Extend `search` to include source artifacts** — Query source artifact indexes alongside registries.

5. **Implement `aam outdated`** — Compare installed packages against available versions (commit-based for sources, semver for registries).

6. **Implement `aam upgrade`** — Upgrade installed packages. Implicit `source update` + re-install with upgrade warning flow.

7. **Add `aam list --available`** — Browse all installable artifacts from sources + registries.

### 8.3 Phase 2: CLI Restructuring (parallel with spec 004)

8. **Repurpose `aam init`** — Convert from package scaffolding to client initialization (platform selection, registry setup, default sources). See [section 5.4](#54-aam-init-repurposed-as-client-initialization).

9. **Create `aam pkg` group** — Move all authoring commands under the `pkg` prefix:
    - `aam pkg init [name]` — package scaffolding (was `aam init`)
    - `aam pkg create [path]` — artifact detection (was `aam create-package`)
    - `aam pkg validate [path]` — manifest validation (was `aam validate`)
    - `aam pkg pack [path]` — build archive (was `aam pack`)
    - `aam pkg publish` — publish archive (was `aam publish`)
    - `aam pkg build --target` — portable bundle (was `aam build`, currently stub)
    - Keep root-level aliases with deprecation warnings during transition.

10. **Add help text grouping** — Implement a custom Click group class for categorized `--help` output.

11. **Reorganize `main.py` registration** — Group by persona with clear section headers.

### 8.4 Phase 3: Polish (v0.3+)

12. **Implement `deploy` / `undeploy`** — Separate deployment from installation.
13. **Implement `aam pkg build`** — Complete the portable bundle feature.
14. **Implement auth commands** — `aam auth login`, `aam auth logout`.
15. **Implement `aam completion`** — Shell completion for bash/zsh/fish.
16. **Implement quality commands** — `aam pkg test`, `aam pkg eval`.
17. **Implement distribution management** — `aam pkg yank`, `aam pkg dist-tag add/rm/ls`.

### 8.5 Help Output Grouping Implementation

```python
# Example Click custom group for categorized help
import click

class OrderedGroup(click.Group):
    """Click group that displays commands in categorized sections."""

    SECTIONS = {
        "Getting Started": [
            "init",
        ],
        "Package Management": [
            "install", "uninstall", "upgrade", "outdated",
            "search", "list", "info",
        ],
        "Package Integrity": [
            "verify", "diff",
        ],
        "Package Authoring": [
            "pkg",
        ],
        "Source Management": [
            "source",
        ],
        "Configuration": [
            "config", "registry",
        ],
        "Utilities": [
            "mcp", "doctor",
        ],
    }

    def format_commands(self, ctx, formatter):
        for section_name, cmd_names in self.SECTIONS.items():
            commands = []
            for name in cmd_names:
                cmd = self.commands.get(name)
                if cmd and not cmd.hidden:
                    commands.append((name, cmd))
            if commands:
                with formatter.section(section_name):
                    formatter.write_dl([
                        (name, cmd.get_short_help_str(limit=150))
                        for name, cmd in commands
                    ])
```

---

## 9. Migration Path

### Phase 0: Bug Fixes (v0.1.x — current)

- Fix `uninstall` adapter bug
- Standardize console/exit patterns
- Clean up `main.py` registration order

### Phase 1: npm-Style Workflow (spec 004 — v0.2.0)

- Extend `install` to resolve from source artifact indexes
- Extend `search` to include source artifacts
- Add `aam outdated` command
- Add `aam upgrade` command
- Add `aam list --available` flag
- Extend `LockedPackage` with `source_name`, `source_commit` fields
- Add `aam_outdated`, `aam_upgrade`, `aam_available` MCP tools

### Phase 2: CLI Restructuring (v0.2.x)

- **Repurpose `aam init`** — Convert to client initialization (platform, registries, sources)
- **Create `aam pkg` group** — Move all creator commands:
  - `aam pkg init` (was `aam init` for package scaffolding)
  - `aam pkg create` (was `aam create-package`)
  - `aam pkg validate` (was `aam validate`)
  - `aam pkg pack` (was `aam pack`)
  - `aam pkg publish` (was `aam publish`)
  - `aam pkg build` (was `aam build`)
- Keep root-level aliases with deprecation warnings during transition
- Add help text categorization (non-breaking)

### Phase 3: Full Restructure + Polish (v0.3.0)

- Remove deprecated root-level aliases
- Implement `deploy` / `undeploy`
- Implement `aam pkg build` (complete the stub)
- Implement auth commands
- Implement quality commands (`aam pkg test`, `aam pkg eval`)
- Implement distribution management (`aam pkg yank`, `aam pkg dist-tag`)
- Publish updated documentation and migration guide

### Backward Compatibility Strategy

For the transition period, use Click's `hidden=True` on deprecated aliases:

```python
# Keep old paths working but hidden from help
@cli.command(hidden=True, deprecated=True)
def create_package(...):
    """Deprecated: use 'aam pkg create' instead."""
    ctx.invoke(pkg_create, ...)

@cli.command(hidden=True, deprecated=True)
def validate(...):
    """Deprecated: use 'aam pkg validate' instead."""
    ctx.invoke(pkg_validate, ...)

# etc. for pack, publish, build
```

---

## Appendix A: Command-to-File Mapping

| Command | File | Service Layer |
|---------|------|--------------|
| `install` | `commands/install.py` | `core/installer.py`, `core/resolver.py`, `adapters/factory.py` |
| `uninstall` | `commands/uninstall.py` | `adapters/cursor.py` **(should be factory)** |
| `list` | `commands/list_packages.py` | `core/workspace.py`, `core/manifest.py` |
| `info` | `commands/show_package.py` | `core/workspace.py`, `core/manifest.py` |
| `search` | `commands/search.py` | `registry/factory.py` |
| `verify` | `commands/verify.py` | `services/checksum_service.py` |
| `diff` | `commands/diff.py` | `services/checksum_service.py` |
| `init` | `commands/init_package.py` | `services/source_service.py` |
| `create-package` | `commands/create_package.py` | `detection/scanner.py`, `services/source_service.py` |
| `validate` | `commands/validate.py` | `core/manifest.py` |
| `pack` | `commands/pack.py` | `services/checksum_service.py`, `utils/archive.py` |
| `publish` | `commands/publish.py` | `registry/factory.py` |
| `build` | `commands/build.py` | **(stub — no service layer)** |
| `doctor` | `commands/doctor.py` | `services/doctor_service.py` |
| `config` | `commands/config.py` | `core/config.py` |
| `registry` | `commands/registry.py` | `registry/local.py`, `core/config.py` |
| `source` | `commands/source.py` | `services/source_service.py` |
| `mcp serve` | `commands/mcp_serve.py` | `mcp/server.py` |

## Appendix B: Service Layer Completeness

| Service | File Exists | Used By Commands | Completeness |
|---------|------------|-----------------|--------------|
| `checksum_service.py` | Yes | verify, diff, pack, install | Complete |
| `config_service.py` | Yes | (unknown usage) | Needs audit |
| `doctor_service.py` | Yes | doctor | Complete |
| `git_service.py` | Yes | create-package (--from-source) | Complete |
| `init_service.py` | Yes | init | Complete |
| `install_service.py` | Yes | (partial — install uses core/installer directly) | Overlap with core |
| `package_service.py` | Yes | (unknown usage) | Needs audit |
| `publish_service.py` | Yes | (unknown — publish uses registry directly) | Overlap with command |
| `registry_service.py` | Yes | (unknown usage) | Needs audit |
| `search_service.py` | Yes | (unknown — search uses registry directly) | Overlap with command |
| `source_service.py` | Yes | source (all subcommands) | Complete |
| `validate_service.py` | Yes | (unknown — validate uses core/manifest directly) | Overlap with command |

**Note:** Several services exist but may not be wired to commands (commands call core modules directly). This suggests an incomplete service-layer refactoring — some commands use services properly (e.g., `source`, `doctor`), while others bypass services and call core modules directly (e.g., `install`, `publish`, `search`). This inconsistency should be resolved by routing all commands through the service layer.

## Appendix C: Platform Adapter Coverage

| Adapter | File | `install` | `uninstall` | `deploy` | `undeploy` |
|---------|------|-----------|-------------|----------|------------|
| Cursor | `cursor.py` | Via factory | **Hardcoded** | N/A (not implemented) | Via adapter |
| Copilot | `copilot.py` | Via factory | **Not used** | N/A | Not tested |
| Claude | `claude.py` | Via factory | **Not used** | N/A | Not tested |
| Codex | `codex.py` | Via factory | **Not used** | N/A | Not tested |

The adapter factory is used by `install` but not `uninstall`, which means only Cursor can properly uninstall packages. This is a **functional bug** that should be fixed immediately.
