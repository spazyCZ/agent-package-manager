# Data Model: Git Repository Source Scanning & Artifact Discovery

**Feature**: 003-git-source-scanning | **Date**: 2026-02-08

## Entity Overview

| # | Entity | Location | New/Modified | Purpose |
|---|--------|----------|-------------|---------|
| 1 | `GitSourceURL` | `utils/git_url.py` | NEW | Parsed components from a git source URL |
| 2 | `SourceEntry` | `core/config.py` | NEW | Persisted source configuration in `config.yaml` |
| 3 | `AamConfig.sources` | `core/config.py` | MODIFIED | Add sources list and removed_defaults to global config |
| 4 | `DiscoveredArtifact` | `services/source_service.py` | NEW | Artifact found during source scanning |
| 5 | `ScanResult` | `services/source_service.py` | NEW | Complete scan output for a source |
| 6 | `SourceChangeReport` | `services/source_service.py` | NEW | Diff between old and new commit scans |
| 7 | `FileChecksums` | `core/workspace.py` | NEW | Per-file checksum map in lock file |
| 8 | `LockedPackage.file_checksums` | `core/workspace.py` | MODIFIED | Add file_checksums to locked package |
| 9 | `VerifyResult` | `services/checksum_service.py` | NEW | Checksum verification report |
| 10 | `Provenance` | `core/manifest.py` | NEW | Source provenance metadata in aam.yaml |
| 11 | `PackageManifest.provenance` | `core/manifest.py` | MODIFIED | Add optional provenance to manifest |
| 12 | `BackupRecord` | `services/checksum_service.py` | NEW | Backup metadata for upgrade safety |

---

## Entity Definitions

### 1. GitSourceURL

**Location**: `apps/aam-cli/src/aam_cli/utils/git_url.py`  
**Purpose**: Decomposed URL components from any supported git source format.

```python
@dataclass(frozen=True)
class GitSourceURL:
    """Parsed components of a git source URL."""
    host: str               # "github.com", "gitlab.com", etc.
    owner: str              # Repository owner/org
    repo: str               # Repository name
    ref: str                # Branch, tag, or commit SHA (default: "main")
    path: str               # Subdirectory scan scope (default: "")
    clone_url: str          # Full clone URL (HTTPS or SSH)
    display_name: str       # Display name: "{owner}/{repo}" or "{owner}/{repo}:{suffix}"
    source_format: str      # "https", "ssh", "shorthand", "tree_url", "git_https"
```

**Validation rules**:
- `host` must not be empty
- `owner` and `repo` must match `[a-zA-Z0-9._-]+`
- `clone_url` must use an allowed scheme (`https://`, `git@`, `git+https://`)
- `ref` defaults to `"main"` if not specified
- `display_name` follows naming convention: `{owner}/{repo}` or `{owner}/{repo}:{path_suffix}`

**Factory methods**:
- `parse(source: str, ref: str | None, path: str | None, name: str | None) -> GitSourceURL`
- Handles all formats: HTTPS, SSH, `git+https://`, tree URL, shorthand

---

### 2. SourceEntry

**Location**: `apps/aam-cli/src/aam_cli/core/config.py`  
**Purpose**: Persisted source configuration entry in `~/.aam/config.yaml`.

```python
class SourceEntry(BaseModel):
    """A registered remote git artifact source."""
    name: str                                    # Display name
    type: Literal["git"] = "git"                 # Source type (always "git" for now)
    url: str                                     # Clone URL (HTTPS or SSH)
    ref: str = "main"                            # Git reference
    path: str = ""                               # Subdirectory scan scope
    last_commit: str | None = None               # SHA of last fetched commit
    last_fetched: str | None = None              # ISO 8601 timestamp
    artifact_count: int | None = None            # Artifacts found in last scan
    default: bool = False                        # True if AAM-shipped default
```

**Serialization** (YAML):
```yaml
sources:
  - name: "openai/skills:.curated"
    type: git
    url: https://github.com/openai/skills
    ref: main
    path: skills/.curated
    last_commit: abc123def456
    last_fetched: "2026-02-08T10:30:00Z"
    artifact_count: 30
    default: false
```

---

### 3. AamConfig Extension

**Location**: `apps/aam-cli/src/aam_cli/core/config.py`  
**Purpose**: Add `sources` list and `removed_defaults` to global config model.

```python
class AamConfig(BaseModel):
    # ... existing fields ...
    default_platform: str = "cursor"
    active_platforms: list[str] = ["cursor"]
    registries: list[RegistrySource] = []
    security: SecurityConfig = SecurityConfig()
    author: AuthorConfig = AuthorConfig()
    publish: PublishConfig = PublishConfig()

    # NEW fields
    sources: list[SourceEntry] = []              # Registered remote git sources
    removed_defaults: list[str] = []             # Names of removed default sources
```

---

### 4. DiscoveredArtifact

**Location**: `apps/aam-cli/src/aam_cli/services/source_service.py`  
**Purpose**: Represents a single artifact found during source scanning.

```python
@dataclass
class DiscoveredArtifact:
    """An artifact discovered during source scanning."""
    name: str                    # Artifact name (e.g., "gh-fix-ci")
    type: str                    # "skill", "agent", "prompt", "instruction"
    path: str                    # Relative path from source root
    file_path: str               # Path to the primary file (e.g., SKILL.md)
    source_name: str             # Name of the source this was found in
    has_vendor_agent: bool       # True if companion agents/*.yaml exists
    vendor_agent_file: str | None  # Path to vendor agent file (if any)
    description: str | None      # Extracted from first line of SKILL.md, if available
```

---

### 5. ScanResult

**Location**: `apps/aam-cli/src/aam_cli/services/source_service.py`  
**Purpose**: Complete scan output for a single source.

```python
@dataclass
class ScanResult:
    """Result of scanning a cached source for artifacts."""
    source_name: str
    commit_sha: str
    scan_path: str                                # Scoped path (or "" for full repo)
    artifacts: list[DiscoveredArtifact]
    skills_count: int
    agents_count: int
    prompts_count: int
    instructions_count: int
    total_count: int
```

---

### 6. SourceChangeReport

**Location**: `apps/aam-cli/src/aam_cli/services/source_service.py`  
**Purpose**: Diff report between two commits showing artifact changes.

```python
@dataclass
class SourceChangeReport:
    """Report of changes between old and new commits for a source."""
    source_name: str
    old_commit: str
    new_commit: str
    new_artifacts: list[DiscoveredArtifact]        # Artifacts added
    modified_artifacts: list[DiscoveredArtifact]    # Artifacts with content changes
    removed_artifacts: list[DiscoveredArtifact]     # Artifacts deleted
    unchanged_count: int
    has_changes: bool
```

---

### 7. FileChecksums

**Location**: `apps/aam-cli/src/aam_cli/core/workspace.py`  
**Purpose**: Per-file checksum map stored in the lock file.

```python
class FileChecksums(BaseModel):
    """Per-file integrity checksums for an installed package."""
    algorithm: str = "sha256"                     # Hash algorithm
    files: dict[str, str] = {}                    # {relative_path: hex_digest}
```

**Serialization** (in `aam-lock.yaml`):
```yaml
file_checksums:
  algorithm: sha256
  files:
    skills/my-skill/SKILL.md: "e3b0c44298fc1c149afbf4c8..."
    agents/my-agent/agent.yaml: "f6e5d4c3b2a1..."
```

---

### 8. LockedPackage Extension

**Location**: `apps/aam-cli/src/aam_cli/core/workspace.py`  
**Purpose**: Add file checksums to locked package entry.

```python
class LockedPackage(BaseModel):
    version: str
    source: str
    checksum: str
    dependencies: dict[str, str] = {}

    # NEW field
    file_checksums: FileChecksums | None = None   # Per-file integrity data
```

**Backward compatibility**: Lock files without `file_checksums` continue to work. Verification simply reports "no checksums available" for those packages.

---

### 9. VerifyResult

**Location**: `apps/aam-cli/src/aam_cli/services/checksum_service.py`  
**Purpose**: Result of verifying installed package file integrity.

```python
@dataclass
class VerifyResult:
    """Result of verifying installed package integrity."""
    package_name: str
    version: str
    ok_files: list[str]                          # Files matching checksums
    modified_files: list[str]                    # Files with changed checksums
    missing_files: list[str]                     # Files in checksums but not on disk
    untracked_files: list[str]                   # Files on disk but not in checksums
    has_checksums: bool                          # False if lock file lacks checksums
    is_clean: bool                               # True if no modifications
```

---

### 10. Provenance

**Location**: `apps/aam-cli/src/aam_cli/core/manifest.py`  
**Purpose**: Source provenance metadata added to `aam.yaml` when created from a remote source.

```python
class Provenance(BaseModel):
    """Tracks where a package's artifacts originated."""
    source_type: Literal["git", "local"] = "local"
    source_url: str | None = None                 # Clone URL
    source_ref: str | None = None                 # Branch/tag/commit
    source_path: str | None = None                # Scan scope
    source_commit: str | None = None              # Commit SHA at time of creation
    fetched_at: str | None = None                 # ISO 8601 timestamp
```

**Serialization** (in `aam.yaml`):
```yaml
provenance:
  source_type: git
  source_url: https://github.com/openai/skills
  source_ref: main
  source_path: skills/.curated
  source_commit: abc123def456
  fetched_at: "2026-02-08T10:30:00Z"
```

---

### 11. PackageManifest Extension

**Location**: `apps/aam-cli/src/aam_cli/core/manifest.py`  
**Purpose**: Add optional provenance to package manifest.

```python
class PackageManifest(BaseModel):
    # ... existing fields ...
    name: str
    version: str
    description: str
    # ...

    # NEW field
    provenance: Provenance | None = None          # Source provenance (if from remote)
```

---

### 12. BackupRecord

**Location**: `apps/aam-cli/src/aam_cli/services/checksum_service.py`  
**Purpose**: Metadata about a backup created before an upgrade.

```python
@dataclass
class BackupRecord:
    """Record of a backup created before upgrading a package."""
    package_name: str
    backup_dir: str                               # ~/.aam/backups/<name>--<date>/
    backed_up_files: list[str]                    # Relative paths of backed-up files
    created_at: str                               # ISO 8601 timestamp
```

---

## Entity Relationship Summary

```
AamConfig
  ├── sources: list[SourceEntry]        (config.yaml)
  ├── removed_defaults: list[str]       (config.yaml)
  └── registries: list[RegistrySource]  (existing)

SourceEntry ──uses──▶ GitSourceURL      (for parsing input)

ScanResult
  └── artifacts: list[DiscoveredArtifact]

SourceChangeReport
  ├── new_artifacts: list[DiscoveredArtifact]
  ├── modified_artifacts: list[DiscoveredArtifact]
  └── removed_artifacts: list[DiscoveredArtifact]

LockFile
  └── packages: dict[str, LockedPackage]
       └── file_checksums: FileChecksums (NEW)

PackageManifest
  └── provenance: Provenance (NEW, optional)

VerifyResult ──reads──▶ FileChecksums
BackupRecord ──creates──▶ ~/.aam/backups/
```
