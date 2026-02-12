# Data Model: CLI Local Repository

**Branch**: `001-cli-local-repository` | **Date**: 2026-02-08

## Overview

This document defines the Pydantic models, data structures, and file schemas used by the AAM CLI for the local-first workflow. All models are defined in `core/manifest.py` and `core/config.py`, with registry-specific schemas in `registry/local.py`.

---

## 1. Package Manifest (`aam.yaml`)

### Pydantic Models (`core/manifest.py`)

```python
class ArtifactRef(BaseModel):
    """Reference to a single artifact within a package."""
    name: str                    # ^[a-z0-9][a-z0-9-]{0,63}$
    path: str                    # Relative path within the package
    description: str             # Max 256 chars

class QualityTest(BaseModel):
    """Declared test in quality section."""
    name: str
    command: str
    description: str

class EvalMetric(BaseModel):
    """Metric definition within an eval."""
    name: str
    type: str                    # percentage, score, duration_ms, boolean

class QualityEval(BaseModel):
    """Declared eval in quality section."""
    name: str
    path: str
    description: str
    metrics: list[EvalMetric] = []

class QualityConfig(BaseModel):
    """Quality section of aam.yaml."""
    tests: list[QualityTest] = []
    evals: list[QualityEval] = []

class PlatformConfig(BaseModel):
    """Platform-specific deployment configuration."""
    skill_scope: str = "project"          # "project" or "user"
    deploy_instructions_as: str = "rules" # cursor-specific
    merge_instructions: bool = False       # claude/copilot-specific

class ArtifactsDeclaration(BaseModel):
    """All artifact types declared in a package."""
    agents: list[ArtifactRef] = []
    skills: list[ArtifactRef] = []
    prompts: list[ArtifactRef] = []
    instructions: list[ArtifactRef] = []

class PackageManifest(BaseModel):
    """Complete aam.yaml manifest model."""
    name: str                                 # Full name: "pkg" or "@scope/pkg"
    version: str                              # Semver: MAJOR.MINOR.PATCH
    description: str                          # Max 256 chars
    author: str | None = None
    license: str | None = None
    repository: str | None = None
    homepage: str | None = None
    keywords: list[str] = []
    artifacts: ArtifactsDeclaration
    dependencies: dict[str, str] = {}         # name -> version constraint
    platforms: dict[str, PlatformConfig] = {} # platform -> config
    quality: QualityConfig | None = None

    # Computed properties
    @property
    def scope(self) -> str:
        """Extract scope from name. Empty string for unscoped."""
        ...

    @property
    def base_name(self) -> str:
        """Extract base name without scope."""
        ...

    @property
    def all_artifacts(self) -> list[tuple[str, ArtifactRef]]:
        """Flat list of (type, ref) tuples."""
        ...

    @property
    def artifact_count(self) -> int:
        """Total number of declared artifacts."""
        ...
```

### YAML Schema

```yaml
# Required fields
name: string            # ^(@[a-z0-9][a-z0-9_-]{0,63}/)?[a-z0-9][a-z0-9-]{0,63}$
version: string         # semver: MAJOR.MINOR.PATCH
description: string     # max 256 chars

# Optional metadata
author: string | null
license: string | null   # SPDX identifier
repository: string | null
homepage: string | null
keywords: list[string]

# Artifact declarations (at least one artifact required across all types)
artifacts:
  agents: list[{name, path, description}]
  skills: list[{name, path, description}]
  prompts: list[{name, path, description}]
  instructions: list[{name, path, description}]

# Dependencies (optional)
dependencies:
  "<package-name>": "<version-constraint>"

# Platform configuration (optional)
platforms:
  cursor: {skill_scope, deploy_instructions_as}
  claude: {merge_instructions}
  copilot: {merge_instructions}
  codex: {skill_scope}

# Quality (optional)
quality:
  tests: list[{name, command, description}]
  evals: list[{name, path, description, metrics}]
```

### Validation Rules

| Field | Rule |
|-------|------|
| `name` | Must match `FULL_NAME_REGEX` from `utils/naming.py` |
| `version` | Must be valid semver (parseable by `packaging.version.Version`) |
| `description` | Max 256 characters, non-empty |
| `artifacts` | At least one artifact across all types |
| `artifacts.*.name` | Must match `NAME_REGEX` |
| `artifacts.*.path` | Must be a relative path (no leading `/`), no `..` traversal |
| `dependencies.*` | Keys must match `FULL_NAME_REGEX`, values must be valid version constraints |

---

## 2. Configuration (`config.yaml`)

### Pydantic Models (`core/config.py`)

```python
class RegistrySource(BaseModel):
    """A configured registry source."""
    name: str
    url: str                     # file:///path or https://...
    type: str = "local"          # local, git, http
    default: bool = False

class SecurityConfig(BaseModel):
    """Security settings."""
    require_checksum: bool = True
    require_signature: bool = False
    on_signature_failure: str = "warn"  # warn, error, ignore

class AuthorConfig(BaseModel):
    """Author defaults for aam init."""
    name: str | None = None
    email: str | None = None

class PublishConfig(BaseModel):
    """Publishing defaults."""
    default_scope: str = ""

class AamConfig(BaseModel):
    """Complete AAM configuration (merged global + project)."""
    default_platform: str = "cursor"
    active_platforms: list[str] = ["cursor"]
    registries: list[RegistrySource] = []
    security: SecurityConfig = SecurityConfig()
    author: AuthorConfig = AuthorConfig()
    publish: PublishConfig = PublishConfig()
```

### YAML Schema (Global: `~/.aam/config.yaml`)

```yaml
default_platform: string       # cursor (default), claude, copilot, codex
active_platforms: list[string]  # [cursor]

registries:
  - name: string               # user-defined name
    url: string                 # file:///path or https://...
    type: string                # local, git, http
    default: boolean            # true/false

security:
  require_checksum: true
  require_signature: false
  on_signature_failure: warn

author:
  name: string | null
  email: string | null

publish:
  default_scope: string         # "" or "myorg"
```

### YAML Schema (Project: `.aam/config.yaml`)

```yaml
# Subset — only fields that override global
default_platform: string
platforms:
  cursor:
    skill_scope: project
```

---

## 3. Local Registry Files

### Registry Metadata (`registry.yaml`)

```yaml
name: string                   # registry identifier
type: local                    # always "local" for local registries
description: string
api_version: 1
created_at: string             # ISO 8601 timestamp
```

### Package Index (`index.yaml`)

```yaml
packages:
  - name: string               # Full package name (scoped or unscoped)
    description: string
    latest: string              # Latest version number
    keywords: list[string]
    artifact_types: list[string] # [agent, skill, prompt, instruction]
    updated_at: string          # ISO 8601 timestamp
```

### Per-Package Metadata (`packages/<name>/metadata.yaml`)

```yaml
name: string                   # Full package name
description: string
author: string | null
license: string | null
repository: string | null
keywords: list[string]

dist_tags:
  latest: string               # Version that "latest" points to
  # Additional tags: stable, beta, etc.

versions:
  - version: string            # Semver
    published: string           # ISO 8601 timestamp
    checksum: string            # "sha256:<hex>"
    size: integer               # Bytes
    dependencies:
      "<package-name>": "<constraint>"
```

---

## 4. Lock File (`.aam/aam-lock.yaml`)

### Pydantic Model

```python
class LockedPackage(BaseModel):
    """A single resolved package in the lock file."""
    version: str
    source: str                  # Registry name or "local"
    checksum: str                # "sha256:<hex>"
    dependencies: dict[str, str] # name -> resolved version

class LockFile(BaseModel):
    """Complete lock file model."""
    lockfile_version: int = 1
    resolved_at: str             # ISO 8601 timestamp
    packages: dict[str, LockedPackage]  # package name -> locked info
```

### YAML Schema

```yaml
lockfile_version: 1
resolved_at: string            # ISO 8601 timestamp

packages:
  "<package-name>":
    version: string
    source: string              # registry name
    checksum: string            # "sha256:<hex>"
    dependencies:
      "<dep-name>": "<resolved-version>"
```

---

## 5. Agent Definition (`agent.yaml`)

### Pydantic Model

```python
class AgentDefinition(BaseModel):
    """Agent definition file model."""
    name: str
    description: str
    version: str | None = None
    system_prompt: str           # Relative path to system-prompt.md
    skills: list[str] = []       # Skill names used by this agent
    prompts: list[str] = []      # Prompt names used by this agent
    tools: list[str] = []        # Tool names (file_read, shell, etc.)
    parameters: dict[str, str | int | float | bool] = {}
```

---

## 6. Detected Artifact (`detection/scanner.py`)

```python
class DetectedArtifact(BaseModel):
    """An artifact found during project scanning."""
    name: str                    # Derived artifact name
    type: str                    # skill, agent, prompt, instruction
    source_path: Path            # Absolute path to the source file/dir
    platform: str | None = None  # cursor, codex, copilot, claude, or None (generic)
    description: str = ""        # Extracted from frontmatter if available
```

---

## 7. Resolved Package (Dependency Resolution)

```python
class ResolvedPackage(BaseModel):
    """A package resolved during dependency resolution."""
    name: str                    # Full package name
    version: str                 # Resolved version
    source: str                  # Registry name
    checksum: str                # "sha256:<hex>"
    archive_path: Path | None = None  # Local path to .aam file
    manifest: PackageManifest | None = None
```

---

## Entity Relationship Diagram

```
PackageManifest (aam.yaml)
├── has many ArtifactRef (agents, skills, prompts, instructions)
├── has many dependencies → references other PackageManifest by name+constraint
├── has optional PlatformConfig per platform
└── has optional QualityConfig (tests, evals)

AamConfig (~/.aam/config.yaml)
├── has many RegistrySource
├── has one SecurityConfig
├── has one AuthorConfig
└── has one PublishConfig

RegistrySource → points to a local registry directory
  └── Registry directory contains:
      ├── registry.yaml (metadata)
      ├── index.yaml (search index)
      └── packages/<name>/
          ├── metadata.yaml (version index + dist-tags)
          └── versions/<ver>.aam (archives)

LockFile (.aam/aam-lock.yaml)
├── has many LockedPackage
└── LockedPackage.dependencies → references other LockedPackage by name

ResolvedPackage (in-memory during install)
├── points to a PackageManifest
└── references a registry source
```

---

## State Transitions

### Package Lifecycle (Local)

```
[nonexistent] → aam init / aam create-package → [created: aam.yaml exists]
[created] → aam validate → [validated]
[validated] → aam pack → [packed: .aam archive exists]
[packed] → aam publish → [published: in registry]
[published] → aam install (consumer) → [installed: in .aam/packages/]
[installed] → deploy → [deployed: in .cursor/]
[deployed] → aam uninstall → [removed]
```

### Registry Version States

```
[nonexistent] → publish → [available]
[available] → (future: yank) → [yanked] (not in scope)
```
