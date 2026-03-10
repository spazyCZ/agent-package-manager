# Data Model: UAAPS v0.4.0 Update for aam-cli

**Phase**: 1 — Design
**Date**: 2026-02-20
**Feature**: 006-uaaps-update

---

## Overview

This document defines all new and modified Pydantic models introduced by the UAAPS v0.4.0 update. Models are organized by subsystem. All new models follow Constitution III: type hints on all fields, Google-style docstrings, validation where applicable.

---

## 1. Package Manifest — `core/manifest.py`

### 1.1 New Sub-Models

```python
class EnvVarConfig(BaseModel):
    """Configuration for a required or optional environment variable."""
    description: str
    required: bool = True
    default: str | None = None

class PermissionsConfig(BaseModel):
    """Requested capability permissions for the package."""
    fs: list[str] = []           # ["read", "write"] or ["read"]
    network: list[str] = []      # allowed hostnames/patterns
    shell: bool = False          # allow arbitrary shell execution

class SystemPackages(BaseModel):
    """Package-manager-level system dependencies."""
    pip: list[str] = []
    npm: list[str] = []
    brew: list[str] = []
    apt: list[str] = []
    cargo: list[str] = []

class SystemDependencies(BaseModel):
    """OS-level and runtime system requirements."""
    python: str | None = None          # e.g. ">=3.10"
    node: str | None = None            # e.g. ">=18"
    packages: SystemPackages = SystemPackages()
    binaries: list[str] = []           # must exist on $PATH
    mcp_servers: list[str] = []        # required MCP server names
```

### 1.2 Extended `ArtifactsDeclaration`

```python
class ArtifactsDeclaration(BaseModel):
    """All artifact types declared in or discovered for a package."""
    # Existing types (unchanged)
    agents: list[ArtifactRef] = []
    skills: list[ArtifactRef] = []
    prompts: list[ArtifactRef] = []
    instructions: list[ArtifactRef] = []   # legacy — kept for aam.yaml compat

    # New artifact types (UAAPS v0.4.0)
    commands: list[ArtifactRef] = []       # slash commands
    rules: list[ArtifactRef] = []          # project rules / instructions
    hooks_path: str | None = None          # path to hooks.json (if present)
    mcp_path: str | None = None            # path to servers.json (if present)
```

### 1.3 Extended `PackageManifest`

New fields added (all optional for backward compat with `aam.yaml`):

```python
class PackageManifest(BaseModel):
    """Universal package manifest — supports package.agent.json, package.agent.yaml, aam.yaml."""

    # --- EXISTING REQUIRED FIELDS (unchanged) ---
    name: str
    version: str
    description: str

    # --- EXISTING OPTIONAL FIELDS (unchanged) ---
    author: str | None = None
    license: str | None = None
    repository: str | None = None
    homepage: str | None = None
    keywords: list[str] = []
    quality: QualityConfig | None = None
    provenance: Provenance | None = None
    platforms: dict[str, PlatformConfig] = {}

    # --- EXISTING DEPENDENCY FIELD (unchanged) ---
    dependencies: dict[str, str] = {}

    # --- NEW UAAPS v0.4.0 FIELDS ---
    category: str | None = None
    engines: dict[str, str] = {}          # platform version constraints
    env: dict[str, EnvVarConfig] = {}     # required/optional env vars
    permissions: PermissionsConfig | None = None

    optional_dependencies: dict[str, str] = {}    # graceful degradation
    peer_dependencies: dict[str, str] = {}         # host-must-provide
    system_dependencies: SystemDependencies | None = None
    resolutions: dict[str, str] = {}               # force transitive versions
    dist_tags: dict[str, str] = {}                 # named version aliases

    # Component path overrides (default = convention)
    skills_path: str = "./skills"
    commands_path: str = "./commands"
    agents_path: str = "./agents"
    rules_path: str = "./rules"
    hooks_path: str = "./hooks/hooks.json"
    mcp_path: str = "./mcp/servers.json"

    # Vendor extensions (x-* fields)
    vendor_extensions: dict[str, Any] = {}

    # MANIFEST FORMAT SENTINEL — set by loader, not from file
    manifest_format: Literal["json", "yaml", "legacy"] = "legacy"

    # --- ARTIFACTS (now optional — auto-discovered if absent) ---
    artifacts: ArtifactsDeclaration | None = None
```

**Validation changes**:
- `validate_has_artifacts` model validator is removed (artifacts now optional)
- `validate_dependencies` extended to validate `optional_dependencies` and `peer_dependencies` the same way
- New `validate_system_dependencies` field validator for `SystemDependencies`
- `description` max length updated from 256 → 1024 to match UAAPS spec

---

## 2. Lock File — `core/workspace.py`

### 2.1 `LockedPackageV2`

```python
class LockedPackageV2(BaseModel):
    """A single package entry in the universal lock file."""
    version: str
    source: str                          # registry name, "local", or "git"
    integrity: str                       # "sha256-<hex>" format
    dependencies: dict[str, str] = {}   # name -> resolved version
    optional: bool = False              # True if from optionalDependencies
    peer: bool = False                  # True if peer dep (verified, not installed)
    # Legacy fields (preserved for aam-lock.yaml compat)
    source_name: str | None = None
    source_commit: str | None = None
```

### 2.2 `UniversalLockFile`

```python
class UniversalLockFile(BaseModel):
    """package.agent.lock — universal JSON lock file."""
    lock_version: int = 1
    resolved_at: str = ""               # ISO 8601 timestamp
    packages: dict[str, LockedPackageV2] = {}
    system_checks: dict[str, Any] = {} # last system dep verification snapshot
```

**Lock file path**: `<project_dir>/package.agent.lock`
**Legacy lock file path**: `<project_dir>/.aam/aam-lock.yaml` (detected for migration)

---

## 3. Configuration — `core/config.py`

### 3.1 `GovernanceInstallPolicy`

```python
class GovernanceInstallPolicy(BaseModel):
    """Client-side install governance rules."""
    allowed_scopes: list[str] = []       # empty = allow all; e.g. ["@myorg", "@trusted"]
    require_signature: bool = False      # block unsigned packages
    require_tag: str | None = None       # only allow packages with this dist-tag
    blocked_packages: list[str] = []     # fnmatch glob patterns; e.g. "@sketchy/*"
```

### 3.2 `GovernancePublishPolicy`

```python
class GovernancePublishPolicy(BaseModel):
    """Client-side publish governance rules."""
    require_signature: bool = False      # must sign before publishing
```

### 3.3 `GovernanceConfig`

```python
class GovernanceConfig(BaseModel):
    """Complete governance configuration."""
    install_policy: GovernanceInstallPolicy = GovernanceInstallPolicy()
    publish_policy: GovernancePublishPolicy = GovernancePublishPolicy()
```

### 3.4 Updated `AamConfig`

New field added:
```python
class AamConfig(BaseModel):
    ...
    governance: GovernanceConfig = GovernanceConfig()  # NEW
```

---

## 4. Dependency Resolution — `core/resolver.py`

### 4.1 `DependencyType`

```python
from enum import StrEnum

class DependencyType(StrEnum):
    DIRECT = "direct"
    OPTIONAL = "optional"
    PEER = "peer"
    SYSTEM = "system"
```

### 4.2 `ResolutionStrategy`

```python
class ResolutionStrategy(StrEnum):
    DEFAULT = "default"    # highest compatible version
    FROZEN = "frozen"      # use lock file exactly
    MINIMAL = "minimal"    # lowest satisfying version
    LATEST = "latest"      # newest available (ignores constraints)
    DRY_RUN = "dry_run"   # resolve without installing
```

### 4.3 `SystemCheckResults`

```python
class SystemCheckResult(BaseModel):
    """Result of checking a single system dependency."""
    name: str
    dep_type: str                    # "python", "node", "binary", "pip", "npm", "mcp"
    required: bool
    found: bool
    found_version: str | None = None
    found_path: str | None = None
    install_hint: str | None = None  # shown if not found

class SystemCheckResults(BaseModel):
    """Aggregate results of all system dependency pre-flight checks."""
    passed: list[SystemCheckResult] = []
    failed: list[SystemCheckResult] = []
    optional_failed: list[SystemCheckResult] = []

    @property
    def all_required_passed(self) -> bool:
        return len(self.failed) == 0
```

### 4.4 `ResolvedGraph`

```python
class ResolvedGraph(BaseModel):
    """Complete dependency resolution result."""
    direct: list[ResolvedPackage] = []
    optional_resolved: list[ResolvedPackage] = []
    optional_failed: list[str] = []           # names that were not found
    peer_satisfied: list[str] = []
    peer_unsatisfied: list[str] = []          # names missing from environment
    system_check_results: SystemCheckResults = SystemCheckResults()
    all_packages: list[ResolvedPackage] = []  # hoisted, deduped, install order

    model_config = ConfigDict(arbitrary_types_allowed=True)
```

---

## 5. Auto-Discovery — `core/autodiscovery.py`

### 5.1 `DiscoveredArtifact`

```python
class DiscoveredArtifact(BaseModel):
    """An artifact found during convention-based directory scan."""
    name: str
    artifact_type: str    # skill, agent, command, rule
    path: str             # relative path from package root
    source: Literal["manifest", "discovered"] = "discovered"
```

---

## 6. Governance — `services/governance_service.py`

### 6.1 `PolicyResult`

```python
class PolicyResult(BaseModel):
    """Result of evaluating governance policies."""
    allowed: bool
    violations: list[PolicyViolation] = []

class PolicyViolation(BaseModel):
    """A single governance policy violation."""
    rule: str            # e.g. "allowed_scopes", "blocked_packages"
    package_name: str
    message: str         # human-readable reason
```

### 6.2 `PolicyViolationError`

```python
class PolicyViolationError(Exception):
    """Raised when a governance policy blocks an operation."""
    def __init__(self, violation: PolicyViolation) -> None:
        self.violation = violation
        super().__init__(violation.message)
```

---

## 7. Dependency Tree — `services/dependency_tree_service.py`

### 7.1 `DependencyTreeNode`

```python
class DependencyTreeNode(BaseModel):
    """A node in the resolved dependency tree."""
    name: str
    version: str
    source: str
    dep_type: DependencyType
    children: list["DependencyTreeNode"] = []
    optional: bool = False
```

### 7.2 `AuditFinding`

```python
class AuditFinding(BaseModel):
    """A security finding from aam audit."""
    package_name: str
    version: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    title: str
    description: str
    finding_type: Literal["integrity", "advisory"] = "integrity"
    advisory_url: str | None = None
```

---

## 8. Entity Relationships

```
PackageManifest
  ├── ArtifactsDeclaration (optional — auto-discovered if absent)
  │   ├── list[ArtifactRef] skills/agents/commands/rules/prompts/instructions
  │   └── hooks_path / mcp_path (strings)
  ├── SystemDependencies
  │   └── SystemPackages
  ├── dict[str, EnvVarConfig]
  ├── PermissionsConfig
  └── dict[str, str] dependencies / optional_dependencies / peer_dependencies

UniversalLockFile
  ├── dict[str, LockedPackageV2]
  └── dict[str, Any] system_checks

AamConfig
  ├── list[RegistrySource]
  ├── SecurityConfig
  ├── GovernanceConfig
  │   ├── GovernanceInstallPolicy
  │   └── GovernancePublishPolicy
  └── list[SourceEntry]

ResolvedGraph
  ├── list[ResolvedPackage] (direct, optional, all_packages)
  ├── SystemCheckResults
  │   └── list[SystemCheckResult]
  └── list[str] (peer_satisfied, peer_unsatisfied, optional_failed)
```

---

## 9. State Transitions

### Package Install Flow (updated)

```
user: aam install <pkg>
  │
  ├── 1. load_config() → AamConfig (including GovernanceConfig)
  ├── 2. check_install_policy(pkg, config) → PolicyResult
  │       └── FAIL: PolicyViolationError → rich error, exit
  ├── 3. load_manifest_universal() → PackageManifest (new format)
  ├── 4. detect_cycles(root_specs, registry)
  │       └── FAIL: cycle path error → exit
  ├── 5. check_system_deps(manifest.system_dependencies)
  │       ├── PASS: continue
  │       └── FAIL: prompt user → continue / abort / auto-install
  ├── 6. resolve_dependencies(specs, strategy, lock_file)
  │       ├── direct deps: BFS, conflict detection
  │       ├── optional deps: BFS, swallow PackageNotFound
  │       └── peer deps: verify in environment, warn if missing
  ├── 7. install_packages(resolved_graph, adapter, config)
  │       ├── download + verify integrity
  │       ├── extract to .agent-packages/<fs-name>/
  │       ├── discover_artifacts(package_dir, manifest)
  │       ├── check env vars → prompt if needed
  │       ├── display permissions → confirm if declared
  │       └── deploy via PlatformAdapter (all artifact types)
  └── 8. write_universal_lock_file(graph, system_checks)
```

### Manifest Detection Flow

```
load_manifest_universal(path: Path) -> PackageManifest
  │
  ├── if path.is_file(): load that file directly
  ├── elif (path / "package.agent.json").exists(): load JSON → manifest_format="json"
  ├── elif (path / "package.agent.yaml").exists(): load YAML → manifest_format="yaml"
  ├── elif (path / "aam.yaml").exists(): load YAML → manifest_format="legacy"
  └── else: raise FileNotFoundError (no silent fallback)
```
