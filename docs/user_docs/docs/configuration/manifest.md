# Package Manifest Reference (aam.yaml)

The package manifest (`aam.yaml`) is the **definitive package definition file** that describes your package's identity, contents, dependencies, and platform-specific configuration.

This is the authoritative reference for the `aam.yaml` schema.

## File Location

```
my-package/
├── aam.yaml  ← Package manifest (at package root)
├── agents/
├── skills/
├── prompts/
└── instructions/
```

## Creating a Manifest

### Automatic Creation

```bash
aam pkg init
# Interactive prompts, generates aam.yaml
```

Or:

```bash
aam pkg create
# Auto-detects artifacts, generates aam.yaml
```

### Manual Creation

```bash
touch aam.yaml
```

Edit with your preferred editor.

## Complete Schema Reference

### Top-Level Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | **Yes** | - | Package name (scoped or unscoped) |
| `version` | string | **Yes** | - | Semver version (MAJOR.MINOR.PATCH) |
| `description` | string | **Yes** | - | Package description (max 256 chars) |
| `author` | string | No | `null` | Author name and/or email |
| `license` | string | No | `null` | SPDX license identifier |
| `repository` | string | No | `null` | Source code repository URL |
| `homepage` | string | No | `null` | Project homepage or documentation URL |
| `keywords` | list[string] | No | `[]` | Search keywords for registry |
| `artifacts` | ArtifactsDeclaration | **Yes** | - | Artifact declarations |
| `dependencies` | dict[string, string] | No | `{}` | Package dependencies |
| `platforms` | dict[string, PlatformConfig] | No | `{}` | Platform-specific configuration |
| `quality` | QualityConfig | No | `null` | Tests and evaluations |

## Field: `name`

**Type:** `string`
**Required:** Yes
**Validation:** Must match regex `^(@[a-z0-9][a-z0-9_-]{0,63}/)?[a-z0-9][a-z0-9-]{0,63}$`

The unique package identifier.

### Unscoped Names

```yaml
name: my-package
```

**Format:** `[a-z0-9][a-z0-9-]{0,63}`
- Must start with lowercase letter or digit
- Can contain lowercase letters, digits, and hyphens
- Maximum 64 characters
- No uppercase, no underscores

**Examples:**
- `audit-agent` ✓
- `skill-v2` ✓
- `my-awesome-package` ✓
- `MyPackage` ✗ (uppercase)
- `my_package` ✗ (underscore)

### Scoped Names

```yaml
name: "@myorg/my-package"
```

**Format:** `@[scope]/[name]`
- Scope: `[a-z0-9][a-z0-9_-]{0,63}` (allows underscores)
- Name: `[a-z0-9][a-z0-9-]{0,63}` (no underscores)

**Examples:**
- `@myorg/audit-agent` ✓
- `@my-org/skill` ✓
- `@company_name/package` ✓
- `@MyOrg/package` ✗ (uppercase in scope)

**Benefits of scopes:**
- Namespace isolation (avoid name conflicts)
- Organizational identity
- Access control (in HTTP registries)

## Field: `version`

**Type:** `string`
**Required:** Yes
**Validation:** Must be valid semver (MAJOR.MINOR.PATCH)

Semantic version number.

```yaml
version: 1.2.3
```

**Format:** `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

**Examples:**
- `1.0.0` ✓
- `2.3.4` ✓
- `1.0.0-alpha` ✓
- `1.0.0-beta.1` ✓
- `1.0.0+build.123` ✓
- `v1.0.0` ✗ (no 'v' prefix)
- `1.0` ✗ (missing patch)

**Semver rules:**
- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible new features
- **PATCH**: Backwards-compatible bug fixes

## Field: `description`

**Type:** `string`
**Required:** Yes
**Validation:** Non-empty, max 256 characters

Short description of the package.

```yaml
description: "ASVC audit agent with reporting skill and prompts"
```

**Guidelines:**
- Be concise and descriptive
- Describe what the package does, not how
- Used in search results and package listings
- Keep under 100 characters for best display

**Examples:**
- `"Agent for automated code auditing"` ✓
- `"Python linting skills for Cursor"` ✓
- `""` ✗ (empty)
- `"A really amazing package that does lots of cool stuff and you should definitely try it because..."` ✗ (too long)

## Field: `author`

**Type:** `string`
**Required:** No
**Default:** `null`

Author name and/or email.

```yaml
author: "Jane Smith <jane@example.com>"
```

**Formats:**
- `"Jane Smith"`
- `"jane@example.com"`
- `"Jane Smith <jane@example.com>"`

**Auto-populated:** From `~/.aam/config.yaml` when using `aam pkg init`:

```yaml
# In ~/.aam/config.yaml
author:
  name: "Jane Smith"
  email: "jane@example.com"

# Results in aam.yaml:
author: "Jane Smith <jane@example.com>"
```

## Field: `license`

**Type:** `string`
**Required:** No
**Default:** `null`

SPDX license identifier.

```yaml
license: Apache-2.0
```

**Common licenses:**
- `MIT`
- `Apache-2.0`
- `GPL-3.0`
- `BSD-3-Clause`
- `ISC`
- `UNLICENSED` (proprietary)

See [https://spdx.org/licenses/](https://spdx.org/licenses/) for full list.

## Field: `repository`

**Type:** `string`
**Required:** No
**Default:** `null`

Source code repository URL.

```yaml
repository: https://github.com/myorg/my-package
```

**Examples:**
- `https://github.com/user/repo`
- `https://gitlab.com/user/repo`
- `https://bitbucket.org/user/repo`

## Field: `homepage`

**Type:** `string`
**Required:** No
**Default:** `null`

Project homepage or documentation URL.

```yaml
homepage: https://mypackage.dev
```

**Use cases:**
- Documentation site
- Project website
- README hosted elsewhere

## Field: `keywords`

**Type:** `list[string]`
**Required:** No
**Default:** `[]`

Search keywords for registry discovery.

```yaml
keywords:
  - audit
  - asvc
  - compliance
  - reporting
```

**Guidelines:**
- Use 3-10 keywords
- Lowercase preferred
- Include use cases, technologies, domains
- Used by `aam search`

## Section: `artifacts`

**Type:** `ArtifactsDeclaration`
**Required:** Yes
**Validation:** At least one artifact must be declared

Declares all artifacts provided by the package.

### ArtifactsDeclaration Schema

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `agents` | list[ArtifactRef] | `[]` | Agent definitions |
| `skills` | list[ArtifactRef] | `[]` | Skill packages |
| `prompts` | list[ArtifactRef] | `[]` | Prompt templates |
| `instructions` | list[ArtifactRef] | `[]` | Instructions/rules |

**At least one artifact list must be non-empty.**

### ArtifactRef Schema

Each artifact reference has three required fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Artifact identifier |
| `path` | string | Yes | Relative path to artifact |
| `description` | string | Yes | What this artifact does |

### Field: `artifacts.*.name`

**Type:** `string`
**Required:** Yes
**Validation:** `^[a-z0-9][a-z0-9-]{0,63}$`

Artifact identifier (unscoped).

```yaml
artifacts:
  agents:
    - name: audit-agent  # ✓
      path: agents/audit-agent/
      description: "..."
```

**Rules:**
- Lowercase letters, digits, hyphens only
- Must start with letter or digit
- Max 64 characters
- No scope prefix (scope comes from package name)

### Field: `artifacts.*.path`

**Type:** `string`
**Required:** Yes
**Validation:** Relative path, no `..`, no absolute paths

Path to artifact file or directory, relative to package root.

```yaml
artifacts:
  skills:
    - name: my-skill
      path: skills/my-skill/  # ✓ Relative directory
      description: "..."

  prompts:
    - name: my-prompt
      path: prompts/my-prompt.md  # ✓ Relative file
      description: "..."
```

**Invalid paths:**
- `/absolute/path` ✗ (absolute)
- `../outside` ✗ (directory traversal)

### Field: `artifacts.*.description`

**Type:** `string`
**Required:** Yes
**Validation:** Non-empty, max 256 characters

What this artifact does.

```yaml
artifacts:
  agents:
    - name: audit-agent
      path: agents/audit-agent/
      description: "Agent configured for ASVC compliance auditing"  # ✓
```

### Example: Multiple Artifact Types

```yaml
artifacts:
  agents:
    - name: asvc-audit
      path: agents/asvc-audit/
      description: "Agent configured for ASVC compliance auditing"

  skills:
    - name: asvc-report
      path: skills/asvc-report/
      description: "Skill for generating ASVC audit reports"
    - name: code-analyzer
      path: skills/code-analyzer/
      description: "Skill for static code analysis"

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
```

## Section: `dependencies`

**Type:** `dict[string, string]`
**Required:** No
**Default:** `{}`

Declares dependencies on other AAM packages.

```yaml
dependencies:
  "@author/generic-auditor": ">=1.0.0"
  report-templates: "^2.0.0"
```

**Format:** `package-name: version-constraint`

### Package Names

Dependencies can be scoped or unscoped:

```yaml
dependencies:
  # Scoped
  "@myorg/base-agent": "^1.0.0"
  "@another/utility": ">=2.0.0"

  # Unscoped
  common-prompts: "^1.0.0"
  shared-skills: "*"
```

### Version Constraints

| Constraint | Meaning | Example Matches |
|------------|---------|-----------------|
| `1.0.0` | Exact version | `1.0.0` only |
| `>=1.0.0` | Minimum version | `1.0.0`, `1.5.0`, `2.0.0`, etc. |
| `^1.0.0` | Compatible (caret) | `>=1.0.0 <2.0.0` |
| `~1.0.0` | Approximate (tilde) | `>=1.0.0 <1.1.0` |
| `*` | Any version | All versions |

### Caret Ranges (`^`)

**Recommended for most dependencies.**

```yaml
dependencies:
  base-package: "^1.2.3"
```

**Allows:**
- Patch updates: `1.2.4`, `1.2.5`
- Minor updates: `1.3.0`, `1.9.0`

**Blocks:**
- Major updates: `2.0.0` (breaking changes)

**Semver compatibility:** `^1.2.3` = `>=1.2.3 <2.0.0`

### Tilde Ranges (`~`)

```yaml
dependencies:
  strict-package: "~1.2.3"
```

**Allows:**
- Patch updates only: `1.2.4`, `1.2.9`

**Blocks:**
- Minor updates: `1.3.0`
- Major updates: `2.0.0`

**Semver compatibility:** `~1.2.3` = `>=1.2.3 <1.3.0`

### Exact Versions

```yaml
dependencies:
  pinned-package: "1.0.0"
```

Use for critical dependencies where exact versions are required.

### Any Version (`*`)

```yaml
dependencies:
  flexible-package: "*"
```

**Not recommended.** Use specific constraints for reproducibility.

### Example: Complex Dependencies

```yaml
dependencies:
  # Core dependency (caret range)
  "@myorg/base-agent": "^2.0.0"

  # Utilities (minimum version)
  "@tools/utilities": ">=1.5.0"

  # Stable dependency (exact version)
  critical-prompts: "1.2.3"

  # Development dependency (approximate)
  test-helpers: "~3.0.0"
```

## Section: `platforms`

**Type:** `dict[string, PlatformConfig]`
**Required:** No
**Default:** `{}`

Platform-specific deployment configuration.

```yaml
platforms:
  cursor:
    skill_scope: project
    deploy_instructions_as: rules
  copilot:
    merge_instructions: true
  claude:
    merge_instructions: true
```

**Supported platforms:** `cursor`, `copilot`, `claude`, `codex`

### PlatformConfig Schema

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `skill_scope` | string | `"project"` | Skill deployment location: `project` or `user` |
| `deploy_instructions_as` | string | `"rules"` | Instruction format: `rules` or `instructions` |
| `merge_instructions` | bool | `false` | Merge all instructions into one file |

### Field: `platforms.*.skill_scope`

**Type:** `string`
**Default:** `"project"`
**Valid values:** `"project"`, `"user"`
**Applies to:** Cursor, Codex

Where to deploy skills:

- `project`: Deploy to `.cursor/skills/` (project-local)
- `user`: Deploy to `~/.cursor/skills/` (user-global)

```yaml
platforms:
  cursor:
    skill_scope: project  # Deploy to .cursor/skills/
```

### Field: `platforms.*.deploy_instructions_as`

**Type:** `string`
**Default:** `"rules"`
**Valid values:** `"rules"`, `"instructions"`
**Applies to:** Cursor

How to deploy instruction artifacts:

- `rules`: Deploy as `.mdc` rule files in `.cursor/rules/`
- `instructions`: Deploy as `.md` files in `.cursor/instructions/`

```yaml
platforms:
  cursor:
    deploy_instructions_as: rules  # Use .mdc format
```

### Field: `platforms.*.merge_instructions`

**Type:** `bool`
**Default:** `false`
**Applies to:** Claude, Copilot

Whether to merge all instructions into one file:

- Claude: Merge into `CLAUDE.md`
- Copilot: Merge into `.github/copilot-instructions.md`

```yaml
platforms:
  claude:
    merge_instructions: true  # Merge into CLAUDE.md
```

### Example: Multi-Platform Configuration

```yaml
platforms:
  cursor:
    skill_scope: project
    deploy_instructions_as: rules
  copilot:
    merge_instructions: true
  claude:
    merge_instructions: true
  codex:
    skill_scope: user  # Deploy to ~/.codex/skills/
```

## Section: `quality`

**Type:** `QualityConfig`
**Required:** No
**Default:** `null`

Declares tests and evaluations for the package.

```yaml
quality:
  tests:
    - name: unit-tests
      command: pytest tests/
      description: "Run unit tests for all skills"

  evals:
    - name: accuracy-eval
      path: evals/accuracy.yaml
      description: "Measure agent accuracy on test dataset"
      metrics:
        - name: accuracy
          type: percentage
        - name: duration
          type: duration_ms
```

### QualityConfig Schema

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tests` | list[QualityTest] | `[]` | Test definitions |
| `evals` | list[QualityEval] | `[]` | Evaluation definitions |

### QualityTest Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Test name |
| `command` | string | Yes | Shell command to run |
| `description` | string | Yes | What this test verifies |

### Example: Tests

```yaml
quality:
  tests:
    - name: unit-tests
      command: pytest tests/ -v
      description: "Run unit tests for all skills"

    - name: lint
      command: ruff check skills/
      description: "Lint skill code"

    - name: integration-tests
      command: pytest tests/integration/
      description: "Run integration tests"
```

**Run tests:**
```bash
aam test
# Runs all tests defined in quality.tests
```

### QualityEval Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Eval name |
| `path` | string | Yes | Path to eval definition |
| `description` | string | Yes | What this eval measures |
| `metrics` | list[EvalMetric] | No | Metric definitions |

### EvalMetric Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Metric name |
| `type` | string | Yes | Metric type |

**Metric types:**
- `percentage` - 0-100% value
- `score` - Numeric score
- `duration_ms` - Duration in milliseconds
- `boolean` - Pass/fail

### Example: Evaluations

```yaml
quality:
  evals:
    - name: accuracy
      path: evals/accuracy.yaml
      description: "Measure agent accuracy on ASVC test cases"
      metrics:
        - name: accuracy
          type: percentage
        - name: f1_score
          type: score

    - name: performance
      path: evals/performance.yaml
      description: "Measure agent response time"
      metrics:
        - name: avg_duration
          type: duration_ms
        - name: success_rate
          type: percentage
```

**Run evals:**
```bash
aam eval
# Runs all evals defined in quality.evals
```

## Complete Example: Minimal Manifest

```yaml
name: my-package
version: 1.0.0
description: "A simple package with one skill"

artifacts:
  skills:
    - name: my-skill
      path: skills/my-skill/
      description: "My first skill"
```

## Complete Example: Full-Featured Manifest

```yaml
# Package identity
name: "@myorg/asvc-auditor"
version: 2.1.0
description: "ASVC audit agent with reporting skills and compliance prompts"
author: "Jane Smith <jane@myorg.com>"
license: Apache-2.0
repository: https://github.com/myorg/asvc-auditor
homepage: https://myorg.com/packages/asvc-auditor
keywords:
  - audit
  - asvc
  - compliance
  - security
  - reporting

# Artifact declarations
artifacts:
  agents:
    - name: asvc-audit
      path: agents/asvc-audit/
      description: "Agent configured for ASVC compliance auditing"

  skills:
    - name: asvc-report
      path: skills/asvc-report/
      description: "Generate structured ASVC audit reports"
    - name: code-analyzer
      path: skills/code-analyzer/
      description: "Static code analysis for security vulnerabilities"

  prompts:
    - name: audit-finding
      path: prompts/audit-finding.md
      description: "Structured prompt for documenting audit findings"
    - name: audit-summary
      path: prompts/audit-summary.md
      description: "Executive summary generation prompt"
    - name: remediation-plan
      path: prompts/remediation-plan.md
      description: "Generate remediation plans for findings"

  instructions:
    - name: asvc-standards
      path: instructions/asvc-standards.md
      description: "ASVC coding standards and best practices"
    - name: security-guidelines
      path: instructions/security-guidelines.md
      description: "Security audit guidelines"

# Dependencies
dependencies:
  "@myorg/base-auditor": "^3.0.0"
  "@tools/report-generator": ">=2.1.0"
  common-prompts: "~1.5.0"

# Platform configuration
platforms:
  cursor:
    skill_scope: project
    deploy_instructions_as: rules
  copilot:
    merge_instructions: true
  claude:
    merge_instructions: true
  codex:
    skill_scope: user

# Quality: tests and evals
quality:
  tests:
    - name: unit-tests
      command: pytest tests/unit/ -v
      description: "Run unit tests for all skills"
    - name: integration-tests
      command: pytest tests/integration/
      description: "Test agent integration"
    - name: lint
      command: ruff check .
      description: "Lint all Python code"

  evals:
    - name: accuracy
      path: evals/accuracy.yaml
      description: "Measure audit accuracy on test dataset"
      metrics:
        - name: accuracy
          type: percentage
        - name: precision
          type: percentage
        - name: recall
          type: percentage
    - name: performance
      path: evals/performance.yaml
      description: "Measure agent performance"
      metrics:
        - name: avg_duration
          type: duration_ms
        - name: success_rate
          type: percentage
```

## Complete Example: Multi-Platform Package

```yaml
name: "@platform/universal-agent"
version: 1.0.0
description: "Cross-platform agent optimized for all major AI platforms"

artifacts:
  agents:
    - name: universal
      path: agents/universal/
      description: "Universal agent with cross-platform support"

  skills:
    - name: cross-platform-skill
      path: skills/cross-platform/
      description: "Skill that works on all platforms"

  instructions:
    - name: coding-standards
      path: instructions/standards.md
      description: "Universal coding standards"

dependencies:
  common-utilities: "^1.0.0"

# Platform-specific optimizations
platforms:
  cursor:
    skill_scope: project
    deploy_instructions_as: rules
  copilot:
    merge_instructions: false  # Keep separate
  claude:
    merge_instructions: true   # Merge for Claude
  codex:
    skill_scope: project
```

## Validation

AAM validates manifests automatically on:
- `aam pkg init`
- `aam pkg create`
- `aam pkg pack`
- `aam pkg publish`
- `aam install`

### Manual Validation

```bash
aam pkg validate
# Validates aam.yaml in current directory
```

### Common Validation Errors

**Invalid name:**
```
Error: Invalid package name 'My-Package': must be lowercase
```

**Invalid version:**
```
Error: Invalid version 'v1.0': must be valid semver (e.g., 1.0.0)
```

**No artifacts:**
```
Error: At least one artifact must be declared
```

**Invalid dependency:**
```
Error: Invalid dependency name 'Invalid Name': must match pattern
```

**Invalid path:**
```
Error: Artifact path must be relative: '/absolute/path'
```

## Best Practices

### Package Naming

- Use descriptive names: `asvc-auditor` not `aa`
- Include purpose: `python-linter`, `code-reviewer`
- Use scopes for organizations: `@myorg/package`
- Avoid generic names: `utils`, `helpers`

### Versioning

- Start at `1.0.0` for stable releases
- Use `0.x.x` for pre-release development
- Follow semver strictly:
  - Patch: Bug fixes (1.0.0 → 1.0.1)
  - Minor: New features (1.0.0 → 1.1.0)
  - Major: Breaking changes (1.0.0 → 2.0.0)

### Dependencies

- Use caret ranges (`^1.0.0`) for most dependencies
- Pin exact versions only when necessary
- Avoid `*` (unpredictable)
- Keep dependency count low

### Artifacts

- Provide clear, concise descriptions
- Use consistent naming conventions
- Group related artifacts
- Include comprehensive examples

### Platform Config

- Only override when needed
- Document why non-default config is used
- Test on all declared platforms

### Quality

- Include at least basic tests
- Add evals for agent packages
- Keep test commands simple and reproducible

## Migration

### Upgrading from v0.x

The v1 manifest format is backwards-compatible with v0.x for most fields.

**Changed:**
- `artifacts` is now required (was optional)
- `dependencies` supports scoped names
- Added `quality` section

**Removed:**
- None

Run migration tool:
```bash
aam migrate manifest
```

## Next Steps

- [Lock Files](lock-files.md) - Understanding `aam-lock.yaml`
- [Project Configuration](project.md) - Project-level settings
- [CLI Reference: init](../cli/init.md) - Create manifests interactively
- [CLI Reference: create-package](../cli/create-package.md) - Auto-generate manifests
