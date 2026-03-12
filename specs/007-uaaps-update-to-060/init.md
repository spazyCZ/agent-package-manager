# Implementation Plan: UAAPS v0.5.0 → v0.6.0-draft Update for aam-cli

**Branch**: `007-uaaps-update-to-060` | **Date**: 2026-02-23 | **Spec**: UAAPS v0.6.0-draft
**Upstream**: `uaaps` repo commit `dd1cb8e` (diff from `3f55175`)
**Depends on**: `006-uaaps-update` (merged, implements v0.4.0 → v0.5.0)

## Summary

Update `aam-cli` from UAAPS v0.5.0-draft to v0.6.0-draft. The new spec introduces:

1. **Conformance levels** (Level 1 Reader, Level 2 Installer, Level 3 Publisher)
2. **Forward-compatibility parsing rules** (unknown fields MUST be silently ignored)
3. **ABNF syntax definitions** for all identifiers
4. **Formalized 5-phase resolution algorithm** with resolver versioning
5. **Pre-release version handling** (npm semantics)
6. **Workspace / monorepo support** (`workspace.agent.json`, shared lock file)
7. **Platform capability negotiation** (`.platform-capabilities.json`)
8. **SLSA provenance attestation** (L0–L3, in-toto format)
9. **Permission composition engine** (root-governs model, `permissionGrants`)
10. **Package lifecycle states** (Published → Deprecated / Yanked, immutability guarantee)
11. **Registry protocol expansion** (structured error codes, content negotiation, pagination, audit-log)
12. **Expanded validation rules** and YAML round-trip guarantees

The implementation is organized into 10 phases. Phase 1 (Manifest & Schema) unblocks all others. Phases 3–6 are parallelizable after Phase 1. Phase 10 is finalization.

---

## Implementation Status (audited 2026-03-12)

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Manifest & Schema Finalization | **NOT STARTED** |
| 2 | Validation Rules | **NOT STARTED** (only `--permissions` flag pre-exists from 006) |
| 3 | Resolution Algorithm | **NOT STARTED** |
| 4 | Package Lifecycle Commands | **NOT STARTED** |
| 5 | Platform Capability Negotiation | **NOT STARTED** |
| 6 | Workspace / Monorepo Support | **NOT STARTED** |
| 7 | SLSA Provenance Attestation | **NOT STARTED** |
| 8 | Permission Composition Engine | **NOT STARTED** |
| 9 | Registry Protocol Updates | **NOT STARTED** |
| 10 | Finalization | **NOT STARTED** |

**Notes**:
- Current `__version__` is `"0.1.0"` — the 006 spec's bump to `"0.5.0"` was never applied.
- The `aam validate --permissions` flag and `_audit_permissions()` function exist from a prior implementation, but the new `permissionGrants`-specific audit logic from this spec is not yet implemented.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Click 8.1+, Rich 13.0+, Pydantic v2, FastMCP, PyYAML, GitPython/subprocess
**Storage**: File-based — `package.agent.lock` (JSON), `.agent-packages/`, `~/.aam/config.yaml`
**Testing**: Pytest — `tests/unit/`, `tests/integration/`
**Target Platform**: Linux, macOS (CLI tool, no UI)
**Constraints**: Must preserve backward compat with v0.5.0 manifests; v0.4.0 `aam.yaml` compat already handled by 006
**Scale/Scope**: Dep trees of ≤50 packages; workspace monorepos up to ≤20 members

---

## Constitution Check

*GATE: Must pass before implementation begins.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Local-First Architecture | ✅ PASS | Workspace resolution is local. Platform capabilities are written to local file. Provenance verification is offline for L0/L1. Permission composition is computed locally. |
| II. Platform Adapter Abstraction | ✅ PASS | Platform capabilities per §10 are an adapter concern. New artifact deployment unchanged. |
| III. Strict Code Quality | ✅ PASS | All new modules follow logging, type hints, Google docstrings, 600-line/100-line limits. |
| IV. Test-Driven Quality | ✅ PASS | Unit + integration tests for all new features. 80%+ coverage target. |
| V. Security by Default (ASVS L2) | ✅ PASS | Permission composition uses least-privilege intersection. Provenance verification prevents supply-chain attacks. Structured error codes prevent error message injection. |
| VI. Monorepo Discipline (Nx) | ✅ PASS | All changes within `apps/aam-cli/`. No new Nx projects. |
| VII. No Defensive Fallbacks | ✅ PASS | Unknown `resolverVersion` = fatal error (not fallback). Forward-compat is explicit spec requirement, not silent fallback. |
| VIII. Documentation Alignment | ✅ PASS | All new commands, flags, and behaviors documented in user docs. |

**No constitution violations. All gates pass.**

---

## Project Structure

### Documentation (this feature)

```text
specs/007-uaaps-update-to-060/
├── plan.md              # This file
└── (future outputs)
```

### Source Code Changes

```text
apps/aam-cli/
├── src/aam_cli/
│   ├── core/
│   │   ├── manifest.py          # EXTEND — permissionGrants, resolverVersion, deprecated, forward-compat
│   │   ├── resolver.py          # REWRITE — formal 5-phase algorithm, pre-release handling, resolver versioning
│   │   ├── installer.py         # EXTEND — lifecycle state handling, capability writes, permission composition
│   │   ├── workspace.py         # EXTEND — workspaceMembers in lock file
│   │   ├── config.py            # EXTEND — require_provenance, on_provenance_failure
│   │   ├── version.py           # UPDATE — bump to 0.6.0
│   │   └── workspace_manager.py # NEW — workspace.agent.json parsing, multi-member resolution
│   ├── services/
│   │   ├── validate_service.py  # EXTEND — 8 new validation rules, YAML round-trip checks
│   │   ├── install_service.py   # EXTEND — deprecated/yanked handling, permission grant display
│   │   ├── lifecycle_service.py # NEW — deprecate, yank, yank --undo
│   │   ├── platform_service.py  # NEW — aam platform info, capability file writer
│   │   ├── provenance_service.py # NEW — attestation generation, verification (L0-L2)
│   │   ├── permission_service.py # NEW — permission composition engine
│   │   └── audit_log_service.py  # NEW — query/display audit logs
│   ├── commands/
│   │   ├── deprecate.py         # NEW — aam deprecate
│   │   ├── yank.py              # NEW — aam yank / yank --undo
│   │   ├── platform.py          # NEW — aam platform info [--json]
│   │   ├── workspace_cmd.py     # NEW — aam workspace list
│   │   ├── audit_log.py         # NEW — aam audit-log
│   │   ├── inspect_cmd.py       # NEW — aam inspect provenance
│   │   ├── install.py           # UPDATE — lifecycle warnings, --workspace flag
│   │   └── audit.py             # UPDATE — --provenance, --reproducible flags
│   ├── registry/
│   │   ├── http.py              # EXTEND — error codes, content negotiation, pagination, lifecycle endpoints
│   │   └── base.py              # EXTEND — new abstract methods for lifecycle + audit
│   ├── mcp/
│   │   ├── tools_read.py        # EXTEND — platform info, workspace list tools
│   │   └── tools_write.py       # EXTEND — deprecate, yank tools
│   └── utils/
│       └── paths.py             # UPDATE — workspace.agent.json, .platform-capabilities.json paths
└── tests/
    ├── unit/
    │   ├── test_unit_resolver_v3.py        # NEW — 5-phase algorithm, pre-release
    │   ├── test_unit_permission_composition.py # NEW
    │   ├── test_unit_lifecycle.py          # NEW — deprecate/yank state machine
    │   ├── test_unit_workspace_manager.py  # NEW
    │   ├── test_unit_platform_service.py   # NEW
    │   ├── test_unit_provenance.py         # NEW
    │   ├── test_unit_forward_compat.py     # NEW — unknown fields parsing
    │   └── test_unit_validate_v3.py        # NEW — new validation rules
    └── integration/
        ├── test_integration_workspace.py   # NEW — multi-member install
        └── test_integration_lifecycle.py   # NEW — deprecate/yank flow
```

---

## Key Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Resolver rewrite vs extend | Rewrite `resolve_dependencies_v2` to match named 5-phase algorithm | Current BFS is close but lacks named phases, formal pre-release handling, and resolver version dispatch. Clean rewrite of the resolution function (not the module) is safer than patching. |
| 2 | Workspace implementation | New `workspace_manager.py` module | Workspace logic is substantial (glob resolution, cross-member resolution, shared lock file). Doesn't fit cleanly into existing `workspace.py` (which is lock file I/O). |
| 3 | Permission composition | New `permission_service.py` | Composition formula `effective(dep) = declared(dep) ∩ (declared(root) ∪ permissionGrants(dep))` is complex enough to warrant its own service with dedicated tests. |
| 4 | Provenance scope | Implement L0–L2 now; defer L3 (reproducible builds) | L3 requires heavy infrastructure (deterministic builds, source rebuild). L0–L2 are achievable with in-toto attestation + Sigstore. |
| 5 | HTTP registry error handling | Typed error enum + response parser | Current `http.py` uses raw status codes. Structured error codes from spec require a mapping layer. |
| 6 | Forward-compat implementation | Pydantic `model_config = ConfigDict(extra="ignore")` + explicit tests | Pydantic v2's `extra="ignore"` already ignores unknown fields. Need to verify all model classes have this and add test coverage. |
| 7 | Lifecycle state in lock file | Add `deprecated` and `yanked` optional fields to `LockedPackageV2` | Lock file needs to record package state for `--frozen` installs that must honor yanked packages. |
| 8 | Platform capabilities | Adapter method `get_capabilities() -> dict` | Each adapter knows its platform's capabilities. The service assembles the full object. |
| 9 | Workspace lock file | Add `workspaceMembers` field to `UniversalLockFile` | Spec requires single lock file with member listing. Adding a field to the existing model is cleanest. |
| 10 | YAML round-trip validation | PyYAML safe_load + custom validator | Use `yaml.safe_load` (rejects custom tags) and add explicit checks for anchors/aliases via regex pre-scan of raw YAML. |

---

## Implementation Phases

### Phase 1 — Manifest & Schema Finalization (unblocks all others)

**Goal**: Add new manifest fields, ensure forward-compatibility, align with v0.6.0 schema changes.

**Files changed**:
- `core/manifest.py` — add new fields, enforce forward-compat
- `utils/paths.py` — add `WORKSPACE_MANIFEST`, `PLATFORM_CAPABILITIES_FILE` constants

**New Pydantic fields on `PackageManifest`**:
```python
# New fields for v0.6.0
permission_grants: dict[str, PermissionsConfig] = Field(
    default_factory=dict, alias="permissionGrants"
)
resolver_version: int = Field(default=1, alias="resolverVersion")
deprecated: DeprecatedInfo | None = None
```

**New model class**:
```python
class DeprecatedInfo(BaseModel):
    """Deprecation metadata per §12.7."""
    message: str                    # REQUIRED
    successor: str | None = None    # optional replacement package specifier
```

**Forward-compatibility enforcement**:
- Verify all Pydantic models use `model_config = ConfigDict(extra="ignore")`
- `PackageManifest`, `ArtifactsDeclaration`, `PermissionsConfig`, `SystemDependencies` — all must silently ignore unknown fields
- Skill/command/rule frontmatter parsers must ignore unknown keys
- `hooks.json` parser must ignore unknown event names

**`permissionGrants` validation** (model validator):
- Keys MUST exist in `dependencies` dict
- Values MUST be valid `PermissionsConfig` objects

**`resolverVersion` validation**:
- Must be positive integer (≥1)
- Currently only version `1` is recognized

**Path constants**:
```python
WORKSPACE_MANIFEST = "workspace.agent.json"
PLATFORM_CAPABILITIES_FILE = ".agent-packages/.platform-capabilities.json"
```

**Tests**: `test_unit_forward_compat.py`
- Parse manifest with unknown top-level field → no error
- Parse manifest with unknown frontmatter key → no error
- Parse `hooks.json` with unknown event → no error
- Parse manifest with `permissionGrants` → correct model
- Parse manifest with `resolverVersion: 1` → accepted
- Parse manifest with `resolverVersion: 99` → depends on context (model accepts, validation rejects)
- Parse manifest with `deprecated` → requires `message`

**Verification**:
- `PackageManifest.model_validate({"name": "x", "version": "1.0.0", "description": "d", "futureField": 123})` succeeds without error
- `PackageManifest.model_validate({..., "permissionGrants": {"dep-a": {"shell": {"allow": true}}}})` populates correctly

---

### Phase 2 — Validation Rules (depends on Phase 1)

**Goal**: Implement §16 validation rules and YAML round-trip checks.

**Files changed**:
- `services/validate_service.py` — add 7 new validation rules, extend existing `--permissions` audit

**New validation rules in `validate_package()`**:

| Rule | Implementation | Severity |
|------|---------------|----------|
| `resolverVersion` must be positive integer | Check `manifest.resolver_version >= 1`; if unknown (>1 currently), emit fatal error | ERROR |
| Unknown `resolverVersion` | Only version `1` supported; any other = `"Unsupported resolverVersion: {v}. Update aam-cli."` | ERROR |
| YAML round-trip | Pre-scan raw YAML for anchors (`&`), aliases (`*`), merge keys (`<<`), custom tags (`!!`); check YAML 1.2 compat | ERROR |
| Workspace globs | If `workspace.agent.json` exists, each `packages[]` glob must resolve to dirs with `package.agent.json` | ERROR |
| `permissionGrants` keys | Every key in `permissionGrants` must exist in `dependencies` | ERROR |
| `deprecated.message` required | If `deprecated` is present but `message` is missing or empty | ERROR |
| Forward-compat | No-op for validation (already handled by Pydantic `extra="ignore"`) — but add explicit test | INFO |
| `aam validate --permissions` (**flag already exists** — extend `_audit_permissions()`) | Extend existing audit to also warn when `permissionGrants` grants `shell.allow: true` without a `binaries` list | WARN |

**YAML round-trip validator** (new helper function):
```python
def validate_yaml_roundtrip(raw_content: str, file_path: str) -> list[str]:
    """Check YAML 1.2 round-trip conformance per §3 YAML round-trip guarantee."""
    errors = []
    # Check for anchors: & followed by identifier
    # Check for aliases: * followed by identifier (not inside strings)
    # Check for merge keys: <<:
    # Check for custom tags: !!
    # Check for duplicate keys (PyYAML safe_load handles this)
    return errors
```

**Tests**: `test_unit_validate_v3.py`
- Manifest with `resolverVersion: 0` → error
- Manifest with `resolverVersion: 99` → error (unsupported)
- YAML with anchor → error
- YAML with alias → error
- YAML with `!!python/object` tag → error
- `permissionGrants` key not in `dependencies` → error
- `deprecated` without `message` → error (Pydantic validation)
- `permissionGrants` with `shell.allow: true` and no `binaries` → warning
- `permissionGrants` with `shell.allow: true` and `binaries: ["prettier"]` → no warning

**Verification**:
- `aam validate` on manifest with unknown fields → no error (forward-compat)
- `aam validate` on manifest with `resolverVersion: 99` → fatal error
- `aam validate --permissions` on `permissionGrants` with shell.allow=true, no binaries → WARN

---

### Phase 3 — Resolution Algorithm (depends on Phase 1)

**Goal**: Implement the formal 5-phase resolution algorithm per §13.4 with pre-release handling and resolver versioning.

**Files changed**:
- `core/resolver.py` — rewrite `resolve_dependencies_v2` as 5-phase algorithm

**New `resolve_v3()` function** implementing named phases:

```python
def resolve_v3(
    root_manifest: PackageManifest,
    registries: list[Registry],
    strategy: ResolutionStrategy,
    lock_file: UniversalLockFile | None = None,
) -> ResolvedGraph:
    """
    UAAPS §13.4 five-phase resolution algorithm (resolver version 1).

    Phase 1: Parse — read root manifest; if --frozen, skip to Phase 5.
    Phase 2: Build requirement graph — collect deps into DAG with constraint edges.
    Phase 3: Resolve — topological traversal with 4-tier version selection.
    Phase 4: Validate — cycle detection, conflict checks, peer checks, system checks.
    Phase 5: Commit — write lock file, install, hoist.
    """
```

**Phase 1: Parse**:
- Read `root_manifest.resolver_version`; if unknown → fatal error
- If `strategy == FROZEN` and lock_file exists → skip to Phase 5 (locked install)

**Phase 2: Build requirement graph**:
- Collect `dependencies`, `peerDependencies`, `optionalDependencies` into a DAG
- Each edge carries: package name, version constraint, dependency type

**Phase 3: Resolve** (per-requirement, topological order):
- `fetch_versions(name, registries)` — query registry, exclude yanked versions
- `filter_by_constraint(versions, constraint)` — SemVer range matching
- `select_version(filtered, lock_file, root_manifest.resolutions, constraint)`:
  1. Locked version (from lock file, unless `--latest`)
  2. `resolutions` override (from root manifest)
  3. Highest stable version satisfying constraint
  4. Highest pre-release version (only if constraint includes pre-release tag)
- `resolve_transitive(selected)` — recursively resolve the selected version's deps

**Pre-release handling** (npm semantics):
```python
def includes_prerelease(constraint: str) -> bool:
    """Return True if the constraint explicitly opts into pre-releases.

    ^1.0.0       → False (exclude pre-releases)
    ^1.0.0-beta.0 → True (constraint has pre-release tag)
    >=1.0.0-beta.1 → True
    *             → True (wildcard matches everything)
    """
```

| Constraint | Matches `1.0.0-beta.1`? | Matches `1.0.0`? |
|------------|--------------------------|-------------------|
| `^1.0.0` | No | Yes |
| `^1.0.0-beta.0` | Yes | Yes |
| `>=1.0.0-beta.1` | Yes | Yes |
| `*` | Yes | Yes |

**Phase 4: Validate**:
- `detect_cycles()` — existing DFS, now called as named step; cycles = fatal
- `check_conflicts()` — incompatible version requirements for same dependency → apply §13.9 strategy
- `check_peers()` — each `peerDependency` must be satisfied by root or ancestor; unmet = WARN (or ERROR with `--strict-peers`)
- `check_system()` — delegate to `system_deps_service.check_system_deps()`

**Phase 5: Commit**:
- Write `package.agent.lock` (unless `--frozen` → verify lock matches)
- Install to `.agent-packages/`
- Hoist shared dependencies where version-compatible

**Resolver version dispatch**:
```python
RESOLVER_IMPLEMENTATIONS = {
    1: resolve_v3,
}

def dispatch_resolver(version: int) -> Callable:
    if version not in RESOLVER_IMPLEMENTATIONS:
        raise ResolverVersionError(
            f"Unknown resolverVersion: {version}. "
            f"Supported: {sorted(RESOLVER_IMPLEMENTATIONS.keys())}. "
            f"Update aam-cli to support this version."
        )
    return RESOLVER_IMPLEMENTATIONS[version]
```

**Tests**: `test_unit_resolver_v3.py`
- 5-phase happy path with direct + optional + peer deps
- Pre-release exclusion: `^1.0.0` does not match `1.0.0-beta.1`
- Pre-release inclusion: `^1.0.0-beta.0` matches `1.0.0-beta.1`
- `resolutions` override applied in select_version
- Frozen strategy with existing lock file → skip to Phase 5
- Unknown `resolverVersion` → fatal error
- Cycle detection → fatal error with cycle path
- Peer dependency unsatisfied → WARN
- Yanked version excluded from `fetch_versions`
- Deprecated version included with warning metadata

**Verification**:
- `aam install` with pre-release constraint → correct version selected
- `aam install --frozen` with existing lock → succeeds without network
- Manifest with `resolverVersion: 99` → `aam install` refuses to resolve

---

### Phase 4 — Package Lifecycle Commands (parallel with Phase 3)

**Goal**: Implement deprecate, yank, yank --undo commands and lifecycle state handling in install.

**New files**:
- `services/lifecycle_service.py`
- `commands/deprecate.py`
- `commands/yank.py`

**`lifecycle_service.py`**:
```python
def deprecate_version(
    package_name: str,
    version: str,
    message: str,
    replacement: str | None,
    registry: HttpRegistry,
) -> dict:
    """POST /packages/:name/:version/deprecate"""

def undeprecate_version(
    package_name: str,
    version: str,
    registry: HttpRegistry,
) -> dict:
    """DELETE /packages/:name/:version/deprecate"""

def yank_version(
    package_name: str,
    version: str,
    registry: HttpRegistry,
) -> dict:
    """POST /packages/:name/:version/yank"""

def undo_yank_version(
    package_name: str,
    version: str,
    registry: HttpRegistry,
) -> dict:
    """DELETE /packages/:name/:version/yank"""
```

**CLI commands**:

```bash
aam deprecate @myorg/agent@1.0.0 "Use @myorg/agent@2.0.0 instead"
aam deprecate @myorg/agent@1.0.0 "Use v2" --replacement "@myorg/agent@^2.0.0"
aam yank @myorg/agent@1.0.0
aam yank --undo @myorg/agent@1.0.0
```

**Install behavior changes** (`install_service.py`):
- When resolver returns a deprecated package: display Rich warning panel with deprecation message and replacement suggestion. Installation proceeds.
- When resolver encounters a yanked package:
  - Normal install → refuse with `PACKAGE_YANKED` error
  - `--frozen` install → honor the lock file entry (yanked packages remain downloadable for lock integrity)

**Lock file changes** (`LockedPackageV2`):
```python
deprecated: str | None = None     # deprecation message if package is deprecated
yanked: bool = False              # True if version was yanked at resolution time
```

**`HttpRegistry` new methods**:
```python
def deprecate(self, name: str, version: str, message: str, replacement: str | None = None) -> dict:
    """POST /packages/{name}/{version}/deprecate"""

def undeprecate(self, name: str, version: str) -> dict:
    """DELETE /packages/{name}/{version}/deprecate"""

def yank(self, name: str, version: str) -> dict:
    """POST /packages/{name}/{version}/yank"""

def undo_yank(self, name: str, version: str) -> dict:
    """DELETE /packages/{name}/{version}/yank"""
```

**`main.py`**: Register `deprecate` and `yank` commands.

**Tests**: `test_unit_lifecycle.py`
- Deprecate → returns success, message stored
- Undeprecate → returns success
- Yank → returns success
- Undo yank → returns success
- Install deprecated package → installs with warning
- Install yanked package → refused
- Install `--frozen` with yanked package in lock → succeeds

**Verification**:
- `aam install` on deprecated package → installs with warning and replacement message
- `aam install` on yanked package → refused
- `aam install --frozen` with yanked in lock → succeeds

---

### Phase 5 — Platform Capability Negotiation (parallel with Phase 3)

**Goal**: Implement `aam platform info` and `.platform-capabilities.json`.

**New files**:
- `services/platform_service.py`
- `commands/platform.py`

**Capabilities object schema** (per §10):
```python
class PlatformCapabilities(BaseModel):
    """Platform capabilities object per §10."""
    platform: str
    platform_version: str
    uaaps_conformance_level: int = Field(alias="uaaps_conformance_level")
    spec_version: str
    supported_artifacts: list[str]
    hook_events: list[str]
    permissions_enforcement: dict[str, bool]
    eval_headless: bool
    resolver_version: int = 1
```

**`platform_service.py`**:
```python
def get_platform_capabilities(platform_name: str, config: AamConfig) -> PlatformCapabilities:
    """Build capabilities object from adapter + config."""

def write_capabilities_file(capabilities: PlatformCapabilities, project_dir: Path) -> Path:
    """Write to .agent-packages/.platform-capabilities.json"""

def check_package_compatibility(
    manifest: PackageManifest,
    capabilities: PlatformCapabilities,
) -> list[str]:
    """Return list of warnings for unsupported features."""
```

**Adapter extension** (`adapters/base.py`):
```python
@abstractmethod
def get_supported_artifacts(self) -> list[str]: ...

@abstractmethod
def get_supported_hook_events(self) -> list[str]: ...

@abstractmethod
def get_permissions_enforcement(self) -> dict[str, bool]: ...

@abstractmethod
def supports_eval_headless(self) -> bool: ...
```

Each adapter implements these based on platform capabilities per the §10 compatibility matrix.

**CLI commands**:
```bash
aam platform info               # Human-readable Rich output
aam platform info --json        # JSON capabilities object to stdout
```

Output format (human-readable):
```
Platform:        cursor
Version:         0.6.0 (aam-cli)
Conformance:     Level 3 (Publisher)
Spec Version:    0.6.0-draft
Artifacts:       skills, commands, agents, rules, hooks, mcp
Hook Events:     pre-tool-use, post-tool-use, stop, session-start, session-end, ...
Permissions:     fs ✓  network ✓  shell ✓
Eval Headless:   No
Resolver:        v1
```

**Install integration**:
- At the start of `install_packages()`, call `write_capabilities_file()` to ensure `.platform-capabilities.json` exists
- After resolving packages, call `check_package_compatibility()` for each — emit WARNs for unsupported artifacts, hooks, or missing permission enforcement
- Installation MUST NOT fail due to capability mismatches (per spec)

**Tests**: `test_unit_platform_service.py`
- Build capabilities for each adapter → correct fields
- Package with unsupported artifact type → WARN emitted, no error
- Package with unsupported hook event → no error
- `--json` output is valid JSON matching schema

**Verification**:
- `aam platform info --json` → valid capabilities JSON
- `aam install` on package with hooks on a platform that doesn't support them → WARN, installs anyway

---

### Phase 6 — Workspace / Monorepo Support (parallel with Phase 3)

**Goal**: Parse `workspace.agent.json`, resolve all members into a shared lock file.

**New files**:
- `core/workspace_manager.py`
- `commands/workspace_cmd.py`

**`workspace.agent.json` schema**:
```json
{
  "workspace": {
    "packages": ["packages/*", "internal/*"]
  }
}
```

**`workspace_manager.py`**:
```python
class WorkspaceConfig(BaseModel):
    """Parsed workspace.agent.json."""
    packages: list[str]   # glob patterns

class WorkspaceMember(BaseModel):
    """A resolved workspace member."""
    name: str
    path: Path
    manifest: PackageManifest

def load_workspace(root_dir: Path) -> WorkspaceConfig | None:
    """Load workspace.agent.json if it exists at root_dir. Return None if not a workspace."""

def resolve_workspace_members(config: WorkspaceConfig, root_dir: Path) -> list[WorkspaceMember]:
    """Resolve glob patterns to workspace members. Each must have package.agent.json."""

def resolve_workspace_dependencies(
    members: list[WorkspaceMember],
    registries: list[Registry],
    strategy: ResolutionStrategy,
) -> ResolvedGraph:
    """Resolve all members' dependencies into a single graph.
    Inter-workspace dependencies resolved locally (no registry fetch).
    """
```

**Lock file extension** (`UniversalLockFile`):
```python
workspace_members: dict[str, list[str]] | None = Field(
    default=None, alias="workspaceMembers"
)
# Maps member name → list of dependency names resolved for that member
```

**CLI commands**:
```bash
aam install                            # At workspace root: install all members
aam install --workspace packages/my-pkg  # Install one specific member
aam workspace list                     # List all workspace members
aam test --workspace                   # Run tests across all members
aam publish --workspace                # Publish all changed members
```

**Install integration** (`install_service.py`):
- At start: check for `workspace.agent.json` in `project_dir`
- If workspace root and no `--workspace` flag: resolve all members
- If `--workspace <path>`: resolve only that member
- Write single `package.agent.lock` at workspace root with `workspaceMembers` field

**Inter-workspace resolution**:
- When member A depends on member B (both in workspace), resolve B from local filesystem
- B's directory is used directly — no registry fetch, no archive download
- Version constraint still checked against B's `package.agent.json` version

**Tests**: `test_unit_workspace_manager.py`
- Parse valid `workspace.agent.json` → correct members
- Glob resolution → finds correct directories
- Missing `package.agent.json` in member dir → error
- Inter-workspace dependency resolution → local path used
- Shared lock file has `workspaceMembers` field

**Integration test**: `test_integration_workspace.py`
- Create temp workspace with 2 members, one depending on the other
- `aam install` at root → single lock file with both members
- Lock file contains `workspaceMembers` field

**Verification**:
- Workspace root `aam install` → single shared lock file with all members resolved
- `aam workspace list` → lists all members with paths and versions

---

### Phase 7 — SLSA Provenance Attestation (depends on Phase 2)

**Goal**: Support provenance generation and verification (L0–L2). Defer L3.

**New file**: `services/provenance_service.py`

**Provenance levels implemented**:

| Level | Implementation | Scope |
|-------|---------------|-------|
| L0 | SHA-256 checksum (already exists) | Always applied |
| L1 | Sigstore/GPG signature verification (already exists) | Per security config |
| L2 | in-toto attestation generation and verification | New in v0.6.0 |
| L3 | Reproducible build (source rebuild + hash compare) | **DEFERRED** |

**`provenance_service.py`**:
```python
def generate_attestation(
    archive_path: Path,
    source_uri: str,
    source_commit: str,
    builder_id: str,
) -> dict:
    """Generate in-toto provenance attestation (L2)."""

def verify_attestation(
    attestation: dict,
    archive_path: Path,
) -> ProvenanceResult:
    """Verify an attestation chain against an archive."""

def fetch_attestation(
    package_name: str,
    version: str,
    registry: HttpRegistry,
) -> dict | None:
    """Fetch attestation from registry."""

def check_provenance_policy(
    result: ProvenanceResult,
    config: AamConfig,
) -> None:
    """Apply require_provenance and on_provenance_failure policy."""
```

**Config extensions** (`config.py`):
```python
class SecurityConfig(BaseModel):
    require_checksum: bool = True
    require_signature: bool = False
    on_signature_failure: str = "warn"
    require_provenance: str = "L0"           # L0 | L1 | L2 | L3
    on_provenance_failure: str = "warn"      # warn | error | ignore
```

**CLI commands**:
```bash
aam pkg publish --provenance         # Generate attestation during publish
aam audit --provenance @myorg/pkg    # Verify attestation chain (L2)
aam audit --reproducible @myorg/pkg  # DEFERRED (L3) — prints "Not yet supported"
aam inspect provenance @myorg/pkg@1.0.0  # Display raw attestation JSON
```

**Tests**: `test_unit_provenance.py`
- Generate attestation → valid in-toto format
- Verify valid attestation → pass
- Verify tampered attestation → fail
- Policy `require_provenance: L2` with L0 package → warn/error per config
- `aam inspect provenance` → pretty-printed JSON

**Verification**:
- `aam pkg publish --provenance` → attestation attached to archive
- `aam audit --provenance pkg` → verification result displayed

---

### Phase 8 — Permission Composition Engine (depends on Phase 2)

**Goal**: Implement root-governs permission model with `permissionGrants`.

**New file**: `services/permission_service.py`

**Composition formula**:
```
effective(dep) = declared(dep) ∩ (declared(root) ∪ permissionGrants(dep))
```

**`permission_service.py`**:
```python
def compute_effective_permissions(
    dep_name: str,
    dep_permissions: PermissionsConfig | None,
    root_permissions: PermissionsConfig | None,
    permission_grants: dict[str, PermissionsConfig],
) -> PermissionsConfig:
    """Compute effective permissions for a dependency using root-governs model."""

def intersect_permissions(a: PermissionsConfig, b: PermissionsConfig) -> PermissionsConfig:
    """Compute intersection (least-privilege) of two permission sets."""

def union_permissions(a: PermissionsConfig, b: PermissionsConfig) -> PermissionsConfig:
    """Compute union of two permission sets."""

def format_permission_grants_for_review(
    grants: dict[str, PermissionsConfig],
) -> str:
    """Format grants as Rich-renderable string for user review during install."""

def audit_permission_grants(
    grants: dict[str, PermissionsConfig],
) -> list[str]:
    """Return warnings for over-privileged grants (shell without binaries, etc.)."""
```

**Install integration** (`installer.py`):
- After resolving, for each dependency with declared permissions:
  - Compute effective permissions via `compute_effective_permissions()`
  - If `permissionGrants` contains entries: display Rich panel showing what's being granted
  - Prompt user to confirm escalated permissions

**Validation integration** (`validate_service.py`):
- `aam validate` calls `audit_permission_grants()` → WARN for shell.allow without binaries
- `aam validate --permissions` includes grant audit in output

**Tests**: `test_unit_permission_composition.py`
- Root `fs.read=["src/**"]`, dep `fs.read=["**"]` → effective `fs.read=["src/**"]`
- Root `shell.allow=false`, dep `shell.allow=true`, grant `shell={allow: true, binaries: ["prettier"]}` → effective `shell={allow: true, binaries: ["prettier"]}`
- No root permissions → dep permissions are advisory only
- No dep permissions → inherits root boundary
- Grant key not in dependencies → rejected by manifest validation

**Verification**:
- `aam install` with `permissionGrants` → displays grants for review
- `aam validate` warns on `shell.allow: true` without `binaries` in grant

---

### Phase 9 — Registry Protocol Updates (depends on Phase 4)

**Goal**: Structured error codes, content negotiation, pagination, audit-log.

**Files changed**:
- `registry/http.py` — comprehensive update
- `registry/base.py` — new abstract methods

**Structured error codes** (new enum):
```python
class RegistryErrorCode(StrEnum):
    PACKAGE_NOT_FOUND = "PACKAGE_NOT_FOUND"
    VERSION_NOT_FOUND = "VERSION_NOT_FOUND"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    MANIFEST_INVALID = "MANIFEST_INVALID"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    TAG_NOT_FOUND = "TAG_NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    REGISTRY_UNAVAILABLE = "REGISTRY_UNAVAILABLE"
    PACKAGE_YANKED = "PACKAGE_YANKED"
    PACKAGE_DEPRECATED = "PACKAGE_DEPRECATED"
```

**Error response parsing**:
```python
class RegistryError(Exception):
    """Structured registry error with machine-readable code."""
    def __init__(self, code: RegistryErrorCode, message: str, status: int): ...
```

All `HttpRegistry` methods updated to parse error responses and raise `RegistryError` with the appropriate code.

**Content negotiation**:
- All requests send `Accept: application/vnd.uaaps.v1+json`
- Handle `406 Not Acceptable` gracefully (fall back to `application/json`)

**Pagination** (new helper):
```python
def paginate(
    self,
    path: str,
    params: dict | None = None,
    limit: int = 50,
) -> Iterator[dict]:
    """Cursor-based pagination. Follows Link: rel="next" headers."""
```

**New methods on `HttpRegistry`**:
```python
def get_audit_log(self, package_name: str, event: str | None = None, limit: int = 50) -> Iterator[dict]:
    """GET /packages/{name}/audit-log with pagination."""
```

**New CLI command** (`commands/audit_log.py`):
```bash
aam audit-log @myorg/code-review                   # All events
aam audit-log @myorg/code-review --event publish    # Filter by event type
aam audit-log --actor user@myorg.com --since 2026-01-01
```

**Registry ABC extension** (`registry/base.py`):
```python
@abstractmethod
def deprecate(self, name: str, version: str, message: str, replacement: str | None = None) -> dict: ...

@abstractmethod
def undeprecate(self, name: str, version: str) -> dict: ...

@abstractmethod
def yank(self, name: str, version: str) -> dict: ...

@abstractmethod
def undo_yank(self, name: str, version: str) -> dict: ...

@abstractmethod
def get_audit_log(self, name: str, **filters) -> Iterator[dict]: ...
```

**Tests**: (in existing `test_unit_mcp_tools_v2.py` and new HTTP registry tests)
- Error response with `PACKAGE_YANKED` code → raises `RegistryError(code=PACKAGE_YANKED)`
- Pagination: mock 3 pages → iterator yields all items
- Content negotiation header present on all requests
- `406 Not Acceptable` → fallback to `application/json`

**Verification**:
- All registry errors display machine-readable code + human message
- `aam audit-log @pkg` → paginated output

---

### Phase 10 — Finalization (depends on all)

**Goal**: Version bump, full.md regeneration, cross-cutting verification.

**Tasks**:

1. **Version bump** (`core/version.py` / `aam_cli/__init__.py`):
   - Update `__version__` from `"0.1.0"` to `"0.6.0"` (current version is `0.1.0`; the 006 spec's bump to `0.5.0` was never applied)
   - Requires human review per AGENTS.md

2. **`aam platform info` conformance**:
   - Verify output declares correct conformance level (Level 3 for aam-cli)
   - Verify `spec_version` is `"0.6.0-draft"`

3. **Documentation updates** (`docs/user_docs/`):
   - New pages: `docs/cli/deprecate.md`, `docs/cli/yank.md`, `docs/cli/platform.md`, `docs/cli/workspace.md`, `docs/cli/audit-log.md`, `docs/cli/inspect.md`
   - Updated pages: `docs/cli/install.md` (lifecycle warnings, --workspace), `docs/cli/audit.md` (--provenance), `docs/cli/validate.md` (new rules)
   - Updated: `docs/concepts/dependencies.md` (5-phase algorithm, pre-release), `docs/concepts/packages.md` (lifecycle states)
   - Updated: `docs/configuration/manifest.md` (permissionGrants, resolverVersion, deprecated, installMode)
   - Updated: `docs/mcp/index.md` (new MCP tools)
   - Updated: `mkdocs.yml` nav structure

4. **Upstream spec file copy**:
   - Copy updated schemas from `uaaps/docs/schemas/` to `specs/007-uaaps-update-to-060/schemas/` for reference
   - Ensure CLI's internal schema validation (if any) uses 2020-12 draft

5. **Integration test suite** run:
   - All existing tests pass
   - All new tests pass
   - Manual testing per verification checklist below

**Verification checklist** (all must pass):

| # | Test | Expected |
|---|------|----------|
| 1 | `aam validate` on manifest with unknown fields | No error (forward-compat) |
| 2 | `aam validate` on manifest with `resolverVersion: 99` | Fatal error |
| 3 | `aam install` on deprecated package | Installs with warning + replacement message |
| 4 | `aam install` on yanked package | Refused |
| 5 | `aam install --frozen` with yanked in lock | Succeeds |
| 6 | `aam platform info --json` | Valid capabilities JSON |
| 7 | Workspace root `aam install` | Single shared lock file with all members |
| 8 | `aam deprecate @pkg@1.0.0 "msg"` | Calls registry, success message |
| 9 | `aam yank @pkg@1.0.0` | Calls registry, success message |
| 10 | `aam audit --provenance @pkg` | Displays provenance attestation result |
| 11 | `aam validate --permissions` on overprivileged grants | WARN emitted |
| 12 | Install with `permissionGrants` | Grants displayed for user review |
| 13 | Pre-release `^1.0.0` does not resolve `1.0.0-beta.1` | Correct |
| 14 | Pre-release `^1.0.0-beta.0` resolves `1.0.0-beta.1` | Correct |
| 15 | `aam workspace list` at workspace root | Lists all members |

---

## Dependency Graph

```
Phase 1 (Manifest & Schema)
    ├──► Phase 2 (Validation Rules)
    │        └──► Phase 7 (SLSA Provenance)
    │        └──► Phase 8 (Permission Composition)
    ├──► Phase 3 (Resolution Algorithm) ──────────────┐
    ├──► Phase 4 (Package Lifecycle) ──► Phase 9 (Registry Protocol)
    ├──► Phase 5 (Platform Capabilities)              │
    └──► Phase 6 (Workspace Support)                  │
                                                      ▼
                                              Phase 10 (Finalization)
```

Phases 3, 4, 5, 6 are parallelizable after Phase 1 completes.
Phase 7 and 8 are parallelizable after Phase 2 completes.
Phase 9 depends on Phase 4 (lifecycle endpoints).
Phase 10 depends on all.

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Resolver rewrite introduces regressions | High | Keep `resolve_dependencies_v2` as fallback; new `resolve_v3` gated behind `resolverVersion` dispatch. Full test suite on both paths. |
| Workspace resolution conflicts with per-project installs | Medium | Clear error when running `aam install <pkg>` at workspace root (must use `--workspace`). Workspace detection is explicit (`workspace.agent.json` must exist). |
| Pre-release semver edge cases | Medium | Port npm's well-tested semver comparison logic. Comprehensive test matrix per §13.4 table. |
| Provenance attestation format compatibility | Low | Follow in-toto spec exactly. Use existing `in-toto` Python library if available, else implement minimal subset. |
| Registry API not yet implementing lifecycle endpoints | Medium | CLI commands gracefully handle 404/501 from registries that don't support deprecate/yank yet. Display "Registry does not support this operation." |
| Permission composition edge cases (absent permissions, partial grants) | Medium | Extensive unit tests for all combinations in spec §17.3. Default to most restrictive when ambiguous. |
| Breaking forward-compat by rejecting unknown fields somewhere | High | Audit all Pydantic models for `extra="ignore"`. Add integration test that installs a manifest with 5 unknown fields. |
| Workspace glob patterns matching unexpected directories | Low | Validate each resolved directory contains `package.agent.json` before treating it as a member. Log skipped directories at debug level. |

---

## Decisions Requiring Human Review

Per AGENTS.md, the following changes require human review before commit:

1. **Schema changes** — New fields in `PackageManifest` (`permissionGrants`, `resolverVersion`, `deprecated`)
2. **VERSION bump** — `0.5.0` → `0.6.0` in `core/version.py`
3. **Resolver rewrite** — Replacing resolution algorithm core logic
4. **Phase 7 scope** — Confirming L3 (reproducible builds) is deferred to post-0.6.0

---

## Effort Estimates

| Phase | Effort | New Files | Changed Files | New Tests |
|-------|--------|-----------|---------------|-----------|
| 1 — Manifest & Schema | Small (1 day) | 0 | 2 | 1 |
| 2 — Validation Rules | Small (1 day) | 0 | 1 | 1 |
| 3 — Resolution Algorithm | Large (3 days) | 0 | 1 | 1 |
| 4 — Package Lifecycle | Medium (2 days) | 3 | 3 | 1 |
| 5 — Platform Capabilities | Small (1 day) | 2 | 2 | 1 |
| 6 — Workspace Support | Large (3 days) | 2 | 2 | 2 |
| 7 — SLSA Provenance | Medium (2 days) | 1 | 2 | 1 |
| 8 — Permission Composition | Medium (2 days) | 1 | 2 | 1 |
| 9 — Registry Protocol | Medium (2 days) | 1 | 2 | 1 |
| 10 — Finalization | Small (1 day) | 0 | 3+ | 0 |
| **Total** | **~18 days** | **10** | **~20** | **10** |

With Phases 3–6 parallelized, critical path is approximately 10 days.
