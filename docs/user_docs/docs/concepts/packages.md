# Packages

A **package** is the fundamental unit of distribution in AAM. It bundles one or more artifacts (skills, agents, prompts, instructions) together with metadata, dependencies, and platform-specific configuration.

## What is a Package?

Think of a package as a self-contained bundle that provides reusable AI agent capabilities. A package contains:

- **Metadata** — Name, version, description, author, license
- **Artifacts** — One or more skills, agents, prompts, or instructions
- **Dependencies** — References to other packages this package requires
- **Configuration** — Platform-specific deployment settings
- **Lock file** — Pinned dependency versions for reproducible installs (optional)

Packages are the building blocks of the AAM ecosystem. They enable:

- **Distribution** — Share agent artifacts with others
- **Reuse** — Build on existing skills and agents
- **Versioning** — Track changes and manage compatibility
- **Composition** — Combine multiple packages into complex workflows

## The Manifest: `aam.yaml`

Every package must have an `aam.yaml` manifest at its root. This file describes the package contents, metadata, and dependencies.

### Complete Example

Here's a fully annotated `aam.yaml` example:

```yaml
# Package identity
name: "@author/asvc-auditor"        # Scoped package name
version: 1.0.0                      # Semantic version (MAJOR.MINOR.PATCH)
description: "ASVC audit agent with reporting skill and prompts"

# Metadata (all optional)
author: author                      # Package author
license: Apache-2.0                 # SPDX license identifier
repository: https://github.com/author/asvc-auditor  # Source code URL
homepage: https://asvc-auditor.dev  # Project homepage (docs, demo, etc.)
keywords:                           # Search keywords
  - audit
  - asvc
  - compliance
  - reporting

# Artifact declarations — what this package provides
artifacts:
  # Agents
  agents:
    - name: asvc-audit
      path: agents/asvc-audit/
      description: "Agent configured for ASVC compliance auditing"

  # Skills
  skills:
    - name: asvc-report
      path: skills/asvc-report/
      description: "Skill for generating ASVC audit reports"

  # Prompts
  prompts:
    - name: audit-finding
      path: prompts/audit-finding.md
      description: "Structured prompt for documenting audit findings"
    - name: audit-summary
      path: prompts/audit-summary.md
      description: "Prompt for generating executive audit summaries"

  # Instructions
  instructions:
    - name: asvc-coding-standards
      path: instructions/asvc-coding-standards.md
      description: "Coding standards for ASVC-compliant projects"

# Dependencies — other AAM packages this package requires
dependencies:
  "@author/generic-auditor": ">=1.0.0"  # Scoped dependency
  report-templates: "^2.0.0"            # Unscoped dependency

# Platform-specific deployment configuration
platforms:
  cursor:
    skill_scope: project        # "project" (.cursor/skills/) or "user" (~/.cursor/skills/)
    deploy_instructions_as: rules  # deploy instructions as .mdc rules
  copilot:
    merge_instructions: true    # merge all instructions into copilot-instructions.md
  claude:
    merge_instructions: true    # merge into CLAUDE.md
  codex:
    skill_scope: user           # deploy to ~/.codex/skills/

# Quality: tests and evals (optional)
quality:
  tests:
    - name: "unit-tests"
      command: "pytest tests/"
      description: "Unit tests for agent skills"
    - name: "lint-check"
      command: "ruff check ."
      description: "Code quality check"
  evals:
    - name: "accuracy-eval"
      path: "evals/accuracy.yaml"
      description: "Measures accuracy against benchmark dataset"
      metrics:
        - name: "accuracy"
          type: "percentage"
        - name: "latency_p95"
          type: "duration_ms"
```

### Manifest Schema Reference

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Package name (see [Naming Rules](#package-naming-rules)) |
| `version` | string | Semantic version (MAJOR.MINOR.PATCH) |
| `description` | string | Short description (max 256 characters) |

#### Optional Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `author` | string | Package author name or organization |
| `license` | string | SPDX license identifier (e.g., MIT, Apache-2.0) |
| `repository` | string | Source code repository URL |
| `homepage` | string | Project homepage/documentation URL |
| `keywords` | list[string] | Search keywords (used in `aam search`) |

#### Artifacts

At least one artifact type must be declared. Each artifact reference follows the `ArtifactRef` schema:

```yaml
artifacts:
  agents: list[ArtifactRef]
  skills: list[ArtifactRef]
  prompts: list[ArtifactRef]
  instructions: list[ArtifactRef]
```

**ArtifactRef schema:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Artifact identifier (lowercase, hyphens) |
| `path` | string | Relative path within the package |
| `description` | string | What this artifact does |

#### Dependencies

Dependencies map package names to version constraints:

```yaml
dependencies:
  <package-name>: <version-constraint>
```

Both scoped (`@scope/name`) and unscoped (`name`) package names are supported.

**Version constraint syntax:**

| Syntax | Meaning | Example Matches |
|--------|---------|-----------------|
| `1.0.0` | Exact version | Only `1.0.0` |
| `>=1.0.0` | Minimum version | `1.0.0`, `1.5.0`, `2.0.0` |
| `^1.0.0` | Compatible release | `>=1.0.0`, `<2.0.0` |
| `~1.0.0` | Approximate | `>=1.0.0`, `<1.1.0` |
| `*` | Any version | Latest available |
| `>=1.0.0,<2.0.0` | Range | Explicit range |

See [Dependencies](dependencies.md) for detailed resolution algorithm.

#### Platform Configuration

Platform-specific deployment settings (all optional):

```yaml
platforms:
  cursor: CursorConfig
  copilot: CopilotConfig
  claude: ClaudeConfig
  codex: CodexConfig
```

**CursorConfig:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `skill_scope` | string | `project` | `project` (.cursor/skills/) or `user` (~/.cursor/skills/) |
| `deploy_instructions_as` | string | `rules` | How to deploy instructions (always `rules`) |

**CopilotConfig:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `merge_instructions` | bool | `true` | Merge instructions into copilot-instructions.md |

**ClaudeConfig:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `merge_instructions` | bool | `true` | Merge instructions into CLAUDE.md |

**CodexConfig:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `skill_scope` | string | `user` | `project` or `user` deployment location |

#### Quality

Optional test and evaluation definitions:

```yaml
quality:
  tests:
    - name: string          # Test name
      command: string       # Shell command to run
      description: string   # What this test verifies
  evals:
    - name: string          # Eval name
      path: string          # Path to eval definition file
      description: string   # What this eval measures
      metrics:
        - name: string      # Metric name
          type: string      # percentage, score, duration_ms, boolean
```

## Package Naming Rules

Package names follow strict conventions for consistency and filesystem safety.

### Unscoped Names

Format: `^[a-z0-9][a-z0-9-]{0,63}$`

- Must start with lowercase letter or digit
- Can contain lowercase letters, digits, and hyphens
- Cannot start or end with a hyphen
- Maximum 64 characters

**Valid examples:**
- `asvc-auditor`
- `my-agent`
- `code-review-skill`
- `python-linter`

**Invalid examples:**
- `ASVC-Auditor` (uppercase)
- `-my-agent` (starts with hyphen)
- `my_agent` (underscore not allowed)
- `my.agent` (dot not allowed)

### Scoped Names

Format: `^@[a-z0-9][a-z0-9_-]{0,63}/[a-z0-9][a-z0-9-]{0,63}$`

- Starts with `@` followed by scope name
- Scope can contain lowercase letters, digits, hyphens, and underscores
- Package name follows unscoped rules
- Separated by `/`
- Maximum 130 characters total (including `@` and `/`)

**Valid examples:**
- `@author/asvc-auditor`
- `@myorg/code-reviewer`
- `@acme_corp/linter`

**Invalid examples:**
- `@Author/asvc-auditor` (uppercase in scope)
- `author/asvc-auditor` (missing `@`)
- `@myorg/My-Agent` (uppercase in name)

### Why Scoped Names?

Scopes prevent naming collisions and provide namespace ownership:

- **Personal scope:** `@yourname/` for your packages
- **Organization scope:** `@myorg/` for team packages
- **Clarity:** `@ml-team/sentiment-analyzer` vs `sentiment-analyzer`

Scopes are especially important in shared registries where multiple authors publish packages.

## Package Directory Structure

AAM uses a canonical directory layout that all packages should follow:

```
my-package/
├── aam.yaml                          # Package manifest (required)
├── README.md                         # Package documentation (recommended)
├── agents/                           # Agent artifacts
│   └── my-agent/
│       ├── agent.yaml                # Agent definition
│       └── system-prompt.md          # Agent system prompt
├── skills/                           # Skill artifacts
│   └── my-skill/
│       ├── SKILL.md                  # Skill definition (required)
│       ├── scripts/                  # Executable scripts (optional)
│       │   └── process.py
│       ├── templates/                # Output templates (optional)
│       │   └── report.j2
│       ├── references/               # Documentation (optional)
│       │   └── guide.md
│       └── assets/                   # Files used in output (optional)
│           └── logo.png
├── prompts/                          # Prompt artifacts
│   ├── task-prompt.md
│   └── analysis-prompt.md
├── instructions/                     # Instruction artifacts
│   ├── coding-standards.md
│   └── review-guidelines.md
├── evals/                            # Evaluation definitions (optional)
│   ├── accuracy.yaml
│   └── benchmark-dataset.jsonl
└── tests/                            # Tests (optional)
    └── test_skill.py
```

### Conventions

1. **Artifacts organized by type** — Each artifact type has its own top-level directory
2. **One artifact per subdirectory** — Skills and agents get their own folders
3. **Prompts and instructions are files** — Single markdown files with frontmatter
4. **Optional supporting files** — Scripts, templates, references, assets are organized within artifact directories
5. **Tests and evals at root** — Testing infrastructure at package root

## Distribution Format: `.aam` Archives

Packages are distributed as `.aam` files — gzipped tar archives (like npm's `.tgz` or Python's `.whl`).

### Archive Structure

```
asvc-auditor-1.0.0.aam
└── (tar.gz contents)
    ├── aam.yaml
    ├── agents/
    ├── skills/
    ├── prompts/
    └── instructions/
```

The archive contains the complete package directory tree.

### Creating an Archive

```bash
# Build a distributable .aam archive
aam pkg pack

# Output: dist/my-package-1.0.0.aam
```

The `pkg pack` command:

1. Validates `aam.yaml`
2. Verifies all artifact paths exist
3. Creates a gzipped tar archive
4. Writes to `dist/` directory
5. Reports the archive size

### Archive Constraints

AAM enforces limits to keep packages manageable:

| Constraint | Limit | Reason |
|------------|-------|--------|
| Maximum size | 50 MB | Registry bandwidth and storage |
| Must contain `aam.yaml` | Required | Package identification |
| No symlinks outside package | Forbidden | Security and portability |
| No absolute paths | Forbidden | Portability |

Attempting to pack a package that exceeds these limits will fail with a clear error message.

## Filesystem Mapping

When packages with scoped names are installed or deployed, the `@scope/name` format must be converted to a filesystem-safe name.

### Scoped Name Conversion

AAM uses the **double-hyphen convention**:

| Package Name | Filesystem Name | Example Path |
|-------------|-----------------|--------------|
| `asvc-report` (unscoped) | `asvc-report` | `.aam/packages/asvc-report/` |
| `@author/asvc-report` (scoped) | `author--asvc-report` | `.aam/packages/@author/asvc-report/` |

**Why double-hyphen (`--`)?**

- Single hyphens are valid within both scope and name segments
- Double-hyphens cannot appear in positions 0-1 of a valid name (names must start with `[a-z0-9]`)
- The mapping is reversible: split on `--` to recover `(scope, name)`
- Consistent across all platforms (Cursor, Copilot, Claude, Codex)

### Directory Structure for Scoped Packages

In `.aam/packages/`, scoped packages are nested under `@scope/`:

```
.aam/packages/
├── @author/                    # Scoped packages under @scope/
│   ├── asvc-auditor/
│   │   └── aam.yaml
│   └── generic-auditor/
│       └── aam.yaml
└── report-templates/           # Unscoped packages at root
    └── aam.yaml
```

When deployed to platforms, artifact names use the `scope--name` format:

```
.cursor/skills/
├── author--asvc-report/        # From @author/asvc-auditor
├── author--generic-auditor/    # From @author/generic-auditor
└── report-templates/           # Unscoped
```

This convention ensures filesystem compatibility and prevents name collisions.

## Size Limits and Optimization

### Recommended Sizes

| Package Type | Recommended Size | Rationale |
|--------------|-----------------|-----------|
| Skills-only | < 5 MB | Quick download, fast deploy |
| Agents + Skills | < 10 MB | Reasonable for typical use |
| Complex packages | < 25 MB | Consider splitting if larger |
| Maximum (enforced) | 50 MB | Hard limit for all packages |

### Reducing Package Size

If your package is approaching the 50 MB limit, consider:

1. **Split into multiple packages** — Separate independent capabilities
2. **Remove unnecessary files** — Check for large assets, datasets, or binaries
3. **Use external references** — Link to external docs instead of bundling
4. **Optimize assets** — Compress images, minify code
5. **Review dependencies** — Remove unused dependencies

```bash
# Check package size before packing
du -sh .

# See what's taking up space
du -sh * | sort -hr | head -n 10

# Pack and check archive size
aam pkg pack
ls -lh dist/
```

## Complete Package Example

Here's a complete, real-world package structure:

```
@author/asvc-auditor/
├── aam.yaml                          # Manifest
├── README.md                         # Package documentation
├── LICENSE                           # Apache-2.0 license
├── agents/
│   └── asvc-audit/
│       ├── agent.yaml                # Agent definition
│       └── system-prompt.md          # Agent prompt
├── skills/
│   └── asvc-report/
│       ├── SKILL.md                  # Skill definition
│       ├── scripts/
│       │   └── generate_report.py    # Report generation script
│       ├── templates/
│       │   └── report.j2             # Jinja2 template
│       └── references/
│           └── asvc-framework.md     # ASVC documentation
├── prompts/
│   ├── audit-finding.md              # Finding prompt
│   └── audit-summary.md              # Summary prompt
├── instructions/
│   └── asvc-coding-standards.md      # Coding standards
├── evals/
│   ├── accuracy.yaml                 # Eval definition
│   └── benchmark-dataset.jsonl       # Test data
└── tests/
    └── test_report_generation.py     # Unit tests
```

**Corresponding `aam.yaml`:**

```yaml
name: "@author/asvc-auditor"
version: 1.0.0
description: "ASVC audit agent with reporting skill and prompts"
author: author
license: Apache-2.0
repository: https://github.com/author/asvc-auditor
keywords: [audit, asvc, compliance, reporting]

artifacts:
  agents:
    - name: asvc-audit
      path: agents/asvc-audit/
      description: "Agent configured for ASVC compliance auditing"
  skills:
    - name: asvc-report
      path: skills/asvc-report/
      description: "Skill for generating ASVC audit reports"
  prompts:
    - name: audit-finding
      path: prompts/audit-finding.md
      description: "Structured prompt for documenting audit findings"
    - name: audit-summary
      path: prompts/audit-summary.md
      description: "Prompt for generating executive audit summaries"
  instructions:
    - name: asvc-coding-standards
      path: instructions/asvc-coding-standards.md
      description: "Coding standards for ASVC-compliant projects"

dependencies:
  "@author/generic-auditor": ">=1.0.0"

platforms:
  cursor:
    skill_scope: project
  copilot:
    merge_instructions: true
  claude:
    merge_instructions: true

quality:
  tests:
    - name: "unit-tests"
      command: "pytest tests/"
      description: "Unit tests for report generation"
  evals:
    - name: "accuracy-eval"
      path: "evals/accuracy.yaml"
      description: "Measures audit accuracy"
      metrics:
        - name: "accuracy"
          type: "percentage"
```

## Next Steps

- **Learn about artifact types:** See [Artifacts](artifacts.md) for detailed schemas
- **Understand dependencies:** See [Dependencies](dependencies.md) for resolution details
- **Publish your package:** See [CLI Reference - publish](../cli/publish.md)
- **Deploy to platforms:** See [Platform Adapters](platform-adapters.md)
