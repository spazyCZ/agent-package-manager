# Data Model: CLI Interface Scaffolding & npm-Style Source Workflow

**Feature Branch**: `004-npm-style-source-workflow`
**Date**: 2026-02-09
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

---

## Entity Overview

```
┌─────────────────────┐     ┌─────────────────────────┐
│   AamConfig         │────>│   SourceEntry            │
│   (config.yaml)     │     │   (per-source metadata)  │
└─────────────────────┘     └────────────┬────────────┘
                                         │ scans into
                                         ▼
┌─────────────────────┐     ┌─────────────────────────┐
│   LockedPackage     │<────│   VirtualPackage         │
│   (aam-lock.yaml)   │     │   (in-memory index)      │
└─────────────────────┘     └─────────────────────────┘
         │
         │ installed as
         ▼
┌─────────────────────┐     ┌─────────────────────────┐
│   PackageManifest   │     │   ArtifactIndex          │
│   (aam.yaml)        │     │   (in-memory resolution) │
└─────────────────────┘     └─────────────────────────┘
```

---

## Entity 1: LockedPackage (Extended)

**File**: `apps/aam-cli/src/aam_cli/core/workspace.py`
**Change**: Add two optional fields for source tracking

```python
class LockedPackage(BaseModel):
    """A single resolved package in the lock file."""

    # Existing fields (unchanged)
    version: str
    source: str                          # Registry name or "local"
    checksum: str                        # "sha256:<hex>"
    dependencies: dict[str, str] = {}
    file_checksums: FileChecksums | None = None

    # NEW: Source provenance fields (spec 004)
    # Optional for backward compatibility — None for registry installs
    source_name: str | None = None       # e.g., "openai/skills"
    source_commit: str | None = None     # Full 40-char SHA at install time
```

**Validation Rules**:
- `source_name`: Must match an existing source in config, or be None
- `source_commit`: Must be a valid 40-character hex SHA, or None
- Both must be set together (both None or both present)

**State Transitions**:
- `None → set`: When installing from a source (`install_from_source()`)
- `set → updated`: When upgrading (`aam upgrade`)
- `set → None`: Never — source provenance is preserved permanently

**Backward Compatibility**:
- Existing lock files without these fields parse correctly (Pydantic defaults to None)
- Lock file version remains `1` (additive change)

---

## Entity 2: VirtualPackage

**File**: `apps/aam-cli/src/aam_cli/services/source_service.py` (new dataclass)
**Purpose**: In-memory representation of a source artifact available for installation

```python
@dataclass
class VirtualPackage:
    """A source artifact available for installation as a package.

    Created during source index building. Represents an artifact
    discovered in a git source that can be installed via
    ``aam install <name>``.
    """

    name: str                    # Artifact name (e.g., "code-review")
    qualified_name: str          # "source_name/artifact_name" (e.g., "openai/skills/code-review")
    source_name: str             # Source display name (e.g., "openai/skills")
    type: str                    # "skill" | "agent" | "prompt" | "instruction"
    path: str                    # Relative path from source root (e.g., "skills/.curated/code-review")
    commit_sha: str              # Current HEAD commit SHA of the source
    cache_dir: Path              # Absolute path to source cache directory
    description: str = ""        # Extracted from artifact (e.g., first line of SKILL.md)
    has_vendor_agent: bool = False  # True if companion agents/*.yaml exists
    vendor_agent_file: str | None = None  # Path to vendor agent file
```

**Relationships**:
- Derived from `DiscoveredArtifact` (existing) + `SourceEntry` metadata
- Resolves to a `PackageManifest` during installation (auto-generated)
- Recorded as a `LockedPackage` after installation

---

## Entity 3: ArtifactIndex

**File**: `apps/aam-cli/src/aam_cli/services/source_service.py` (new dataclass)
**Purpose**: In-memory index of all installable source artifacts across all configured sources

```python
@dataclass
class ArtifactIndex:
    """In-memory index of source artifacts for package resolution.

    Built on-demand by ``build_source_index()``. Two lookup structures:

    - ``by_name``: Unqualified name → list of matching VirtualPackages
      (for ``aam install code-review``)
    - ``by_qualified_name``: Qualified name → single VirtualPackage
      (for ``aam install openai/skills/code-review``)
    """

    by_name: dict[str, list[VirtualPackage]]         # "code-review" → [pkg1, pkg2, ...]
    by_qualified_name: dict[str, VirtualPackage]      # "openai/skills/code-review" → pkg
    total_count: int                                  # Total artifacts indexed
    sources_indexed: int                              # Number of sources successfully indexed
    build_timestamp: str                              # ISO 8601 when index was built
```

**Lifecycle**:
- Built by `build_source_index(config)` — scans all source caches
- Consumed by `resolve_artifact(name, index)` — resolves package names
- Rebuilt on `aam source update` (cache changes)
- Not persisted — fast enough to rebuild on every `install` (~50ms for 1000 artifacts)

---

## Entity 4: OutdatedPackage

**File**: `apps/aam-cli/src/aam_cli/services/upgrade_service.py` (new)
**Purpose**: Result of comparing an installed package against its source

```python
@dataclass
class OutdatedPackage:
    """A package that has updates available from its source."""

    name: str                             # Package name
    current_commit: str                   # Short SHA (7 chars) — installed version
    latest_commit: str                    # Short SHA (7 chars) — source HEAD
    source_name: str                      # Source display name
    has_local_modifications: bool         # True if files differ from checksums
    last_source_update: str | None = None # ISO 8601 of last source fetch
```

---

## Entity 5: OutdatedResult

**File**: `apps/aam-cli/src/aam_cli/services/upgrade_service.py` (new)
**Purpose**: Aggregated result of an outdated check across all installed packages

```python
@dataclass
class OutdatedResult:
    """Complete result of an outdated detection scan."""

    outdated: list[OutdatedPackage]       # Packages with updates available
    up_to_date: list[str]                 # Package names that are current
    no_source: list[str]                  # Packages not installed from sources
    total_outdated: int                   # len(outdated)
    stale_sources: list[str]              # Sources not updated in 7+ days
```

**JSON Serialization** (for `--json` output):
```json
{
  "outdated": [
    {
      "name": "code-review",
      "current_commit": "abc123f",
      "latest_commit": "def456a",
      "source_name": "openai/skills",
      "has_local_modifications": false
    }
  ],
  "up_to_date": ["architect"],
  "no_source": ["@registry/some-package"],
  "total_outdated": 1,
  "stale_sources": ["github/awesome-copilot"]
}
```

---

## Entity 6: UpgradeResult

**File**: `apps/aam-cli/src/aam_cli/services/upgrade_service.py` (new)
**Purpose**: Result of an upgrade operation

```python
@dataclass
class UpgradeResult:
    """Result of upgrading packages from sources."""

    upgraded: list[dict[str, str]]        # [{"name", "from_commit", "to_commit"}]
    skipped: list[dict[str, str]]         # [{"name", "reason"}]
    failed: list[dict[str, str]]          # [{"name", "error"}]
    total_upgraded: int
```

---

## Entity 7: ClientInitResult

**File**: `apps/aam-cli/src/aam_cli/services/client_init_service.py` (new)
**Purpose**: Result of the interactive client initialization

```python
@dataclass
class ClientInitResult:
    """Result of ``aam init`` client setup."""

    platform: str                         # Selected platform (e.g., "cursor")
    registry_created: bool                # True if a local registry was created
    registry_name: str | None             # Name of created/added registry
    sources_added: list[str]              # Names of added community sources
    config_path: Path                     # Path to written config file
    is_reconfigure: bool                  # True if config already existed
```

---

## Modified Entities (Existing)

### AamConfig — No Schema Change

The `AamConfig` model in `core/config.py` is **not modified**. The `aam init` command writes config using the existing `save_global_config()` function. All fields (`default_platform`, `active_platforms`, `registries`, `sources`, `removed_defaults`) are already sufficient.

### PackageManifest — No Schema Change

The `PackageManifest` model in `core/manifest.py` is **not modified**. Auto-generated manifests for source installs use the existing `Provenance` model to track source origin. The `version` field uses `"0.0.0"` as a synthetic semver (valid per existing validator).

### SourceEntry — No Schema Change

The `SourceEntry` model in `core/config.py` is **not modified**. All fields needed for source indexing and outdated detection (`name`, `url`, `ref`, `path`, `last_commit`, `last_fetched`, `artifact_count`) already exist.

---

## Data Flow: Install from Source

```
User: aam install code-review

1. Parse package spec → name="code-review", version=None

2. Check registries (existing flow)
   └── Not found in registries

3. Build source index
   ├── For each SourceEntry in config:
   │   ├── Get cache_dir from git URL
   │   ├── Scan cached source → list[DiscoveredArtifact]
   │   └── Create VirtualPackage for each artifact
   └── Return ArtifactIndex

4. Resolve artifact
   ├── Look up "code-review" in index.by_name
   ├── Found in "openai/skills" (first match)
   └── Return VirtualPackage

5. Install from source (atomic)
   ├── Stage: .aam/.tmp/code-review/
   ├── Copy files from cache → staging
   ├── Generate aam.yaml with Provenance
   ├── Compute file checksums
   ├── Move staging → .aam/packages/code-review/
   ├── Deploy to platform via adapter
   └── Update aam-lock.yaml:
       └── LockedPackage(
             version="0.0.0",
             source="openai/skills",
             source_name="openai/skills",
             source_commit="abc123def456..."
           )
```

## Data Flow: Outdated Check

```
User: aam outdated

1. Read aam-lock.yaml → dict[name, LockedPackage]

2. Group packages by source_name:
   ├── "openai/skills" → [code-review, architect]
   ├── None → [@registry/pkg]  (no_source)

3. For each source group:
   ├── Find SourceEntry in config
   ├── Get cache HEAD SHA
   └── Compare each package's source_commit vs HEAD SHA

4. Return OutdatedResult:
   ├── outdated: [code-review (abc→def)]
   ├── up_to_date: [architect]
   ├── no_source: [@registry/pkg]
   └── stale_sources: [sources not fetched in 7+ days]
```

## Data Flow: Upgrade

```
User: aam upgrade code-review

1. Run outdated check → OutdatedResult

2. Filter to requested package

3. For each outdated package:
   ├── Check local modifications (checksum_service)
   │   ├── Modified + not --force → prompt backup/skip/diff/force
   │   └── Not modified → proceed
   ├── Copy new files from source cache
   ├── Recompute checksums
   ├── Update lock file (new source_commit)
   └── Re-deploy to platform

4. Return UpgradeResult
```
