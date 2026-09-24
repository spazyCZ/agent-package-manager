# Implementation Plan: UAAPS v0.4.0 Update for aam-cli

**Branch**: `006-uaaps-update` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/006-uaaps-update/spec.md`

## Summary

Update `aam-cli` to implement the Universal Agentic Artifact Package Specification (UAAPS) v0.4.0. The update replaces the `aam.yaml` manifest with `package.agent.json` (YAML secondary), extends the dependency resolver with four typed dependency categories and hoisting, introduces artifact auto-discovery from standard directories, adds six new dependency tree commands, implements client-side governance policy gates, adds system dependency pre-flight checks, and exposes all new capabilities via six new MCP tools. Backward compatibility with existing `aam.yaml`, `aam-lock.yaml`, and `.aam/packages/` installations is preserved throughout.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Click 8.1+, Rich 13.0+, Pydantic v2, FastMCP, PyYAML, GitPython/subprocess
**Storage**: File-based — `package.agent.lock` (JSON, replaces `aam-lock.yaml`), `.agent-packages/` (replaces `.aam/packages/`), `~/.aam/config.yaml`
**Testing**: Pytest — `tests/unit/`, `tests/integration/`
**Target Platform**: Linux, macOS (CLI tool, no UI)
**Project Type**: Single Python project (`apps/aam-cli/`)
**Performance Goals**: Pre-flight checks < 10 seconds for ≤20 system deps; manifest load < 100ms
**Constraints**: Must support `aam.yaml` backward compat; `--allow-sudo` required for elevated system installs; max archive 50 MB (unchanged)
**Scale/Scope**: Single developer to team use; dep trees of ≤50 packages

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Local-First Architecture | ✅ PASS | All new features work without network. Governance is client-side. Lock file is local JSON. System dep checks use subprocess/importlib — no HTTP. |
| II. Platform Adapter Abstraction | ✅ PASS | New artifact types (command, rule, hook, mcp) are added to the `PlatformAdapter` protocol. Platform-specific logic stays exclusively in `adapters/<platform>.py`. |
| III. Strict Code Quality | ✅ PASS | All new modules follow: `logging.getLogger(__name__)`, type hints, Google docstrings, 600-line/100-line limits, 80-char `#` separators. |
| IV. Test-Driven Quality | ✅ PASS | Unit + integration tests written before implementation for all new services and commands. 80%+ coverage target. |
| V. Security by Default (ASVS L2) | ✅ PASS | `env` prompts use `click.prompt(hide_input=True)`. Permissions require explicit confirmation. `--allow-sudo` gate prevents unauthorized elevated installs. `--frozen` re-verifies lock hashes. |
| VI. Monorepo Discipline (Nx) | ✅ PASS | Single project `apps/aam-cli/`. No new projects. |
| VII. No Defensive Fallbacks | ✅ PASS | `aam.yaml` backward compat is explicitly specified (SC-003). Detection is deterministic precedence (JSON > YAML > legacy), not silent fallback. `aam-lock.yaml` migration is explicit user-prompted action, not silent. |
| VIII. Documentation Alignment | ✅ PASS | `docs/DESIGN.md` replaced by UAAPS spec reference; `docs/USER_GUIDE.md` updated for all new commands; `--help` text updated for all new/modified commands. |

**No constitution violations. All gates pass.**

---

## Project Structure

### Documentation (this feature)

```text
specs/006-uaaps-update/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cli-commands.md
│   └── mcp-tools.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
apps/aam-cli/
├── src/aam_cli/
│   ├── core/
│   │   ├── manifest.py          # EXTEND — new fields, universal format, JSON support
│   │   ├── resolver.py          # EXTEND — 4 dep types, hoisting, cycle detection, strategies
│   │   ├── installer.py         # UPDATE — new install dir, new artifact types, governance gate
│   │   ├── workspace.py         # UPDATE — new lock file format (JSON), migration helper
│   │   ├── config.py            # EXTEND — GovernanceConfig, GovernanceInstallPolicy
│   │   ├── autodiscovery.py     # NEW — auto-discover artifacts from standard directories
│   │   └── version.py           # unchanged
│   ├── services/
│   │   ├── validate_service.py  # UPDATE — validate package.agent.json + new fields
│   │   ├── system_deps_service.py  # NEW — pre-flight checks + auto-install
│   │   ├── governance_service.py   # NEW — client-side policy gate enforcement
│   │   ├── dependency_tree_service.py  # NEW — tree, why, check, audit, dedupe, prune
│   │   ├── init_service.py      # UPDATE — generate package.agent.json by default
│   │   ├── install_service.py   # UPDATE — governance gate, system deps, new flow
│   │   ├── publish_service.py   # UPDATE — governance publish gate (check_publish_policy)
│   │   ├── package_service.py   # UPDATE — read package.agent.json
│   │   └── [existing services]  # unchanged
│   ├── adapters/
│   │   ├── base.py              # EXTEND — deploy_command, deploy_rule, deploy_hook, deploy_mcp
│   │   ├── claude.py            # EXTEND — implement new artifact deploy methods
│   │   ├── cursor.py            # EXTEND — implement new artifact deploy methods
│   │   ├── copilot.py           # EXTEND — implement new artifact deploy methods
│   │   └── codex.py             # EXTEND — implement new artifact deploy methods
│   ├── commands/
│   │   ├── tree.py              # NEW — aam tree
│   │   ├── why.py               # NEW — aam why <package>
│   │   ├── check.py             # NEW — aam check [--system]
│   │   ├── audit.py             # NEW — aam audit [--severity]
│   │   ├── dedupe.py            # NEW — aam dedupe
│   │   ├── prune.py             # NEW — aam prune
│   │   ├── install.py           # UPDATE — new flags (--frozen, --minimal, --latest, --dry-run, --install-system-deps, --allow-sudo, --skip-checks)
│   │   ├── convert.py           # UPDATE — new conversion rules (instructions.md→RULE.md, hook events)
│   │   └── pkg/
│   │       ├── init.py          # UPDATE — generate package.agent.json
│   │       ├── create.py        # UPDATE — generate package.agent.json
│   │       └── validate.py      # UPDATE — validate new schema
│   ├── mcp/
│   │   ├── tools_read.py        # EXTEND — 6 new tools (tree, why, check, audit, dedupe, prune)
│   │   ├── tools_write.py       # UPDATE — install tool handles new flags
│   │   ├── resources.py         # UPDATE — manifest resource serves package.agent.json
│   │   └── server.py            # UPDATE — tool count, instructions
│   └── utils/
│       ├── paths.py             # UPDATE — new path constants for .agent-packages/
│       └── [existing utils]     # unchanged
└── tests/
    ├── unit/
    │   ├── test_unit_manifest_v2.py          # NEW
    │   ├── test_unit_autodiscovery.py        # NEW
    │   ├── test_unit_resolver_v2.py          # NEW
    │   ├── test_unit_system_deps.py          # NEW
    │   ├── test_unit_governance.py           # NEW
    │   ├── test_unit_dependency_tree.py      # NEW
    │   ├── test_unit_adapter_commands.py     # NEW (new artifact types)
    │   └── test_unit_mcp_tools_v2.py         # NEW
    └── integration/
        ├── test_integration_uaaps_install.py  # NEW — full install with new manifest
        └── test_integration_system_deps.py    # NEW — pre-flight check flow

docs/
├── USER_GUIDE.md   # UPDATE — new commands, new manifest format
└── DESIGN.md       # REPLACE — reference UAAPS spec instead
```

**Structure Decision**: Single project (Option 1). All changes are within `apps/aam-cli/`. No new Nx projects. New files follow existing module layout (core, services, commands, adapters, mcp, utils).

---

## Complexity Tracking

No constitution violations requiring justification.

---

## Key Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Manifest model unification | Extend `PackageManifest` with new optional fields + new JSON loader | Single model handles both old and new; Pydantic `default=None` for new fields preserves backward compat without duplication |
| 2 | Manifest file detection order | `package.agent.json` → `package.agent.yaml` → `aam.yaml` (deterministic, not fallback) | Exactly as UAAPS spec requires; explicit precedence enforced at `load_manifest_universal()` entry point |
| 3 | Lock file format | New `UniversalLockFile` (Pydantic, JSON via stdlib `json`) for `package.agent.lock`; old `aam-lock.yaml` triggers explicit migration prompt | Spec requires JSON. Stdlib avoids new dependency. Migration is user-prompted (No Defensive Fallbacks principle) |
| 4 | Install directory | `PACKAGES_DIR_NAME` constant updated to `.agent-packages/`; `migrate_install_dir()` helper detects old `.aam/packages/` | Single constant change minimizes blast radius; explicit migration keeps user informed |
| 5 | Dependency hoisting | Post-BFS flattening pass: packages with single compatible version across all dependents are placed at install root | Simplest correct hoisting; aligns with npm flat model; avoids need for a full SAT solver in v1 |
| 6 | Circular dependency detection | DFS with visitation stack before BFS resolution, returns full cycle path | O(V+E), runs fast; provides actionable error with the exact cycle path |
| 7 | System dep checks | Subprocess for binaries/runtimes, `importlib.metadata` for pip packages, `shutil.which()` for PATH binaries, `json` for MCP server config | All stdlib; no extra dependencies; fast; composable |
| 8 | `aam audit` v1 scope | Check installed package integrity (re-verify lock file hashes) + optional HTTP advisory lookup if registry configured | Local-first: always works offline; HTTP advisory is opt-in only when registry is configured |
| 9 | Governance enforcement point | `governance_service.check_install_policy()` called at the top of `install_service` before resolver runs | Fails fast before any network or FS operations; clean separation |
| 10 | Auto-discovery result | `autodiscovery.py` returns `ArtifactsDeclaration` with discovered artifacts; merged with explicit manifest declarations | Explicit declarations in manifest take precedence; auto-discovered fill gaps |
| 11 | New adapter methods | Extend `PlatformAdapter` protocol with `deploy_command`, `deploy_rule`, `deploy_hook`, `deploy_mcp`; existing adapters get `NotImplemented` stub with logged warning | New artifact types gracefully unsupported on platforms that lack native support; no silent drops |

---

## Implementation Phases

### Phase A — Manifest & File Format (FR-001 to FR-005)

**Goal**: Support `package.agent.json` / `package.agent.yaml` + backward compat with `aam.yaml`

**Files changed**:
- `core/manifest.py` — extend `PackageManifest` with new fields; new `load_manifest_universal()`
- `utils/paths.py` — add `MANIFEST_JSON`, `MANIFEST_YAML`, `MANIFEST_LEGACY` constants
- `services/init_service.py` — generate `package.agent.json` by default
- `commands/pkg/init.py` — pass `format="json"` to init service
- `commands/pkg/create.py` — generate `package.agent.json`
- `services/validate_service.py` — call `load_manifest_universal()`
- `commands/pkg/validate.py` — update manifest file path reporting

**New Pydantic fields on `PackageManifest`**:
```python
# New optional fields (all default to None or [])
category: str | None = None
engines: dict[str, str] = {}          # {"claude-code": ">=1.0"}
env: dict[str, EnvVarConfig] = {}     # required + optional env vars
permissions: PermissionsConfig | None = None
optional_dependencies: dict[str, str] = {}
peer_dependencies: dict[str, str] = {}
system_dependencies: SystemDependencies | None = None
resolutions: dict[str, str] = {}      # force specific transitive versions
dist_tags: dict[str, str] = {}
# Component path overrides (default to convention paths)
skills_path: str = "./skills"
commands_path: str = "./commands"
agents_path: str = "./agents"
rules_path: str = "./rules"
hooks_path: str = "./hooks/hooks.json"
mcp_path: str = "./mcp/servers.json"
# Vendor extensions
vendor_extensions: dict[str, Any] = {}  # x-* fields
```

> **⚠️ UAAPS JSON Serialization Alignment (§3)**: The Pydantic Python field names use `snake_case` but the UAAPS spec and `package.agent.json` on disk use different casing. The model MUST be configured with `model_config = ConfigDict(populate_by_name=True)` and each field must declare a JSON alias matching the spec:
>
> | Python field | JSON key (UAAPS spec) | Alias required? |
> |---|---|---|
> | `optional_dependencies` | `optionalDependencies` | ✅ Yes |
> | `peer_dependencies` | `peerDependencies` | ✅ Yes |
> | `system_dependencies` | `systemDependencies` | ✅ Yes |
> | `dist_tags` | `dist-tags` (hyphen) | ✅ Yes |
> | `skills_path` | `skills` (no suffix) | ✅ Yes |
> | `commands_path` | `commands` | ✅ Yes |
> | `agents_path` | `agents` | ✅ Yes |
> | `rules_path` | `rules` | ✅ Yes |
> | `hooks_path` | `hooks` | ✅ Yes |
> | `mcp_path` | `mcp` | ✅ Yes |
> | `vendor_extensions` | `x-*` (dynamic) | Via `model_validator` |
>
> Use `Field(alias="optionalDependencies")` etc. The `vendor_extensions` dict is populated by a pre-validator that collects all `x-` prefixed keys from the raw dict. When writing JSON output, use `model.model_dump(by_alias=True)`.
>
> **`SystemDependencies` sub-field**: The `mcp_servers` field maps to JSON key `"mcp-servers"` (hyphen): `Field(alias="mcp-servers")`.
>
> **`dist-tags` in `PackageManifest`**: JSON key is `"dist-tags"` (hyphen). Python attribute is `dist_tags`. Pydantic v2 allows hyphens only via alias.

**New model classes**:
- `EnvVarConfig` (description, required, default)
- `PermissionsConfig` (fs, network, shell)
- `SystemDependencies` (python, node, packages, binaries, mcp_servers)
- `SystemPackages` (pip, npm, brew, apt, cargo)

**`load_manifest_universal(path)` algorithm**:
1. If path is a file, use it directly
2. If path is a directory: try `package.agent.json`, then `package.agent.yaml`, then `aam.yaml`
3. Raise `FileNotFoundError` if none found (no silent fallback)
4. Parse JSON with stdlib `json`, YAML with PyYAML — single `PackageManifest` model handles both

### Phase B — Artifact Auto-Discovery (FR-023 to FR-025)

**Goal**: Discover artifacts from standard directories when `artifacts` section is omitted

**New file**: `core/autodiscovery.py`

**`ArtifactsDeclaration` extended** with:
```python
commands: list[ArtifactRef] = []
rules: list[ArtifactRef] = []      # ⚠️ UAAPS extension (rules absent from spec §3 artifacts)
hooks_path: str | None = None      # relative path to hooks.json if present
mcp_path: str | None = None        # relative path to servers.json if present
```
> **Notes**:
> - `hooks_path` and `mcp_path` are simple string paths, not model objects. `HooksConfig`/`McpConfig` wrapper types are not used.
> - **`rules` is a UAAPS extension**: UAAPS §3 `artifacts` object lists `skills`, `agents`, `prompts`, `commands` — but **not** `rules`. Adding `rules: list[ArtifactRef]` extends the spec to allow explicit rule declarations, consistent with other artifact types. This does not conflict with the spec since the `artifacts` section is entirely optional.

**`discover_artifacts(package_dir, manifest)` algorithm**:
1. If manifest has explicit `artifacts`, return them (explicit overrides convention)
2. Scan `skills/<name>/SKILL.md` → skill artifacts (name = dir name)
3. Scan `agents/<name>/agent.yaml` → agent artifacts (directory-based)
4. Scan `agents/<name>.md` → agent artifacts (legacy single-file)
5. Scan `commands/<name>.md` → command artifacts
6. Scan `rules/<name>/RULE.md` → rule artifacts
7. If `hooks/hooks.json` exists → register hooks config
8. If `mcp/servers.json` exists → register MCP config
9. Use manifest component path overrides if declared
10. Return merged `ArtifactsDeclaration`

### Phase C — Dependency Resolver v2 (FR-006 to FR-012)

**Goal**: Four dep types, hoisting, cycle detection, resolution strategies, new lock format

**Files changed**:
- `core/resolver.py` — major extension
- `core/workspace.py` — new lock file model
- `utils/paths.py` — new path constants

**New `ResolvedGraph` model**:
```python
class ResolvedGraph(BaseModel):
    direct: list[ResolvedPackage]         # from 'dependencies'
    optional: list[ResolvedPackage]       # from 'optionalDependencies' (successful)
    optional_failed: list[str]            # from 'optionalDependencies' (missing)
    peer_satisfied: list[str]             # peerDeps found in environment
    peer_unsatisfied: list[str]           # peerDeps missing (warn only in lenient mode)
    system_checks: SystemCheckResults     # from 'systemDependencies' pre-flight
    all_packages: list[ResolvedPackage]   # hoisted, deduplicated, ordered
```

**Resolution strategies** implemented as `strategy` enum param:
- `default` — highest compatible version (current behavior)
- `frozen` — exact lock file versions, fail if stale
- `minimal` — lowest satisfying version
- `latest` — newest available (ignores constraints)
- `dry_run` — resolve + return `ResolvedGraph` without installing

**Cycle detection**: `detect_cycles(root_specs, registry) -> list[str] | None`
- DFS traversal with `visiting` set and `ancestors` path
- Returns cycle path list if found, `None` if graph is acyclic

**Hoisting algorithm**:
- After full BFS resolution, build `version_map: {name: {version: set[dependents]}}`
- If a package has exactly one version across all dependents → hoist to install root
- If multiple incompatible versions → keep separate per-dependent namespace
- V1 simplification: always hoist (fail on conflicts per existing behavior)

**New `UniversalLockFile` model** (`package.agent.lock`):
```python
class UniversalLockFile(BaseModel):
    lock_version: int = Field(1, alias="lockVersion")     # UAAPS §13.3: "lockVersion"
    resolved_at: str = ""
    packages: dict[str, LockedPackageV2] = Field(         # UAAPS §13.3: "resolved"
        default_factory=dict, alias="resolved"
    )
    system_checks: dict[str, Any] = Field(                # UAAPS §13.3: "systemChecks"
        default_factory=dict, alias="systemChecks"
    )
    model_config = ConfigDict(populate_by_name=True)

class LockedPackageV2(BaseModel):
    version: str
    source: str
    integrity: str      # sha256-<hex> of installed directory tree (not archive)
    dependencies: dict[str, str] = {}
    optional: bool = False
```

> **⚠️ UAAPS JSON Alignment (§13.3)**: Lock file fields use camelCase in the spec. `lock_version` → `"lockVersion"`, `packages` → `"resolved"`, `system_checks` → `"systemChecks"`. Always serialize with `model.model_dump(by_alias=True)` and load with `UniversalLockFile.model_validate(data)` (respects aliases).

**Lock file paths** (two locations per UAAPS §13.11):
- **Primary**: `<project_dir>/package.agent.lock` — at the project root alongside `package.agent.json`, referenced via `LOCK_FILE_JSON = "package.agent.lock"` constant in `utils/paths.py` (added in T001).
- **Secondary**: `.agent-packages/.lock` — a symlink or copy of the primary file inside the install directory, per UAAPS §13.11. Created by the installer after writing the primary file. Allows tooling inside `.agent-packages/` to locate the lock file without traversing up.

**Migration helper** `migrate_lock_file(project_dir)`:
1. Detect `aam-lock.yaml` in `.aam/`
2. Prompt user: "Found legacy lock file. Migrate to package.agent.lock? [y/N]"
3. If yes: convert model, write `package.agent.lock`, keep old file as `.aam/aam-lock.yaml.bak`

### Phase D — System Dependencies (FR-013 to FR-016)

**New file**: `services/system_deps_service.py`

**`check_system_deps(system_deps, config) -> SystemCheckResults`**:
- `python`: `subprocess.check_output(["python3", "--version"])` + semver compare
- `node`: `subprocess.check_output(["node", "--version"])` + semver compare
- `binaries`: `shutil.which(binary)` for each
- `pip` packages: `importlib.metadata.version(pkg)` (fast, no subprocess)
- `npm` packages: `subprocess.check_output(["npm", "list", "-g", "--json"])`
- `mcp-servers`: check `~/.claude/.mcp.json` for server names
- Returns `SystemCheckResults(passed, failed, optional_failed)`

**`auto_install_system_deps(missing, config, allow_sudo) -> InstallResult`**:
- pip: `subprocess.run(["pip", "install", pkg])` — always supported with `--install-system-deps`
- npm: `subprocess.run(["npm", "install", "-g", pkg])` — always supported
- brew/apt: require `allow_sudo=True`; prompt if False
- binaries: never auto-install, provide instructions only
- mcp-servers: `subprocess.run(["mcp", "install", server])` if MCP CLI available

**Pre-flight integration in `installer.py`**:
1. Before resolver: call `check_system_deps()` — unless `--skip-checks` flag is set (UAAPS §16: "pre-flight check must pass or explicit `--skip-checks`"); if skipped, log a warning and proceed
2. If failures: display table via Rich, prompt user: continue / abort / auto-install
3. If `--install-system-deps`: call `auto_install_system_deps()` and re-check
4. Write system check results to `UniversalLockFile.system_checks`

### Phase E — New CLI Commands (FR-017 to FR-022)

**Pattern**: thin Click command → delegates to `dependency_tree_service.py`

**New file**: `services/dependency_tree_service.py`

| Command file | Function | Output |
|---|---|---|
| `commands/tree.py` | `get_tree(project_dir, depth)` | Rich `Tree` panel |
| `commands/why.py` | `get_why(pkg_name, project_dir)` | Rich explanation panel |
| `commands/check.py` | `check_deps(project_dir, system_only)` | Rich status table |
| `commands/audit.py` | `audit_deps(project_dir, severity)` | Rich findings table |
| `commands/dedupe.py` | `dedupe_deps(project_dir)` | Before/after tree diff |
| `commands/prune.py` | `prune_deps(project_dir)` | List of removed packages |

**`aam tree`**: reads `UniversalLockFile`, builds a tree structure from `dependencies` fields, renders with `rich.tree.Tree`

**`aam why <package>`**: traverses lock file to find which packages list the target in their `dependencies` dict; prints the dependency chain

**`aam check`**: verifies each package in lock file has a corresponding directory in `.agent-packages/`; `--system` flag delegates to `check_system_deps()`

**`aam audit`**: v1 — re-verifies SHA-256 hashes of installed archives against lock file; optionally calls registry `/packages/{name}/advisories` if HTTP registry configured

**`aam dedupe`**: v1 scope — identifies packages installed in the old nested namespace directories (pre-migration layout) that can be hoisted to the root `.agent-packages/` level; also detects packages duplicated across sub-directories of the same install tree. Note: since v1 resolver already fails on version conflicts (always flat), post-v1 installs will never produce nested duplicates. `aam dedupe` is primarily useful for packages installed before this update or migrated from the old `.aam/packages/` structure with nested layouts.

**`aam prune`**: compares `.agent-packages/` directory listing against lock file; removes unlisted directories; updates lock file

**`main.py` registration**: add all 6 new commands to the root Click group

### Phase F — Platform Adapters (FR-026 to FR-027)

**Extended `PlatformAdapter` protocol** in `adapters/base.py`:
```python
def deploy_command(self, cmd_path: Path, ref: ArtifactRef, config: dict[str, str]) -> Path: ...
def deploy_rule(self, rule_path: Path, ref: ArtifactRef, config: dict[str, str]) -> Path: ...
def deploy_hook(self, hooks_json_path: Path, config: dict[str, str]) -> Path: ...
def deploy_mcp(self, servers_json_path: Path, config: dict[str, str]) -> Path: ...
```

**Claude adapter** (`adapters/claude.py`):
- `deploy_command` → copy to `.claude/commands/<pkg>:<name>.md`
- `deploy_rule` → copy to `CLAUDE.md` section append (or `.claude/rules/<pkg>/<name>.md` if per-rule supported)
- `deploy_hook` → merge into `.claude/hooks.json`
- `deploy_mcp` → merge into `.mcp.json`

**Cursor adapter** (`adapters/cursor.py`):
- `deploy_command` → convert to skill with `disable-model-invocation: true` in `.cursor/skills/`
- `deploy_rule` → convert `RULE.md` frontmatter → `.mdc` in `.cursor/rules/`
- `deploy_hook` → convert event names, write `.cursor/hooks.json`
- `deploy_mcp` → write `.cursor/mcp.json`

**Copilot adapter** (`adapters/copilot.py`):
- `deploy_command` → convert to `.github/prompts/<pkg>:<name>.prompt.md`
- `deploy_rule` → convert to `.github/instructions/<name>.instructions.md` (globs → applyTo)
- `deploy_hook` → partial (only 4 events supported)
- `deploy_mcp` → write to VS Code MCP config location

**Codex adapter** (`adapters/codex.py`):
- `deploy_command` → convert to skill with `disable-model-invocation`
- `deploy_rule` → append to `AGENTS.md`
- `deploy_hook` → log warning (not supported)
- `deploy_mcp` → log warning (limited support)

**`aam convert` updates** (`services/convert_service.py`, `converters/`):
- `.instructions.md` → `RULE.md`: map `applyTo` → `globs`, add `description` field
- Hook event names: build bidirectional platform translation table
- MCP config: restructure between `servers.json`, `.mcp.json`, `mcp.json` formats

**`_deploy_package()` in `installer.py`** updated to call new artifact type methods.

### Phase G — Governance Gates (FR-028 to FR-029)

**Extended `AamConfig`** in `core/config.py`:
```python
class GovernanceInstallPolicy(BaseModel):
    allowed_scopes: list[str] = []        # empty = allow all
    require_signature: bool = False
    require_tag: str | None = None
    blocked_packages: list[str] = []       # supports glob patterns

class GovernancePublishPolicy(BaseModel):
    require_signature: bool = False

class GovernanceConfig(BaseModel):
    install_policy: GovernanceInstallPolicy = GovernanceInstallPolicy()
    publish_policy: GovernancePublishPolicy = GovernancePublishPolicy()

class AamConfig(BaseModel):
    ...
    governance: GovernanceConfig = GovernanceConfig()
```

**New file**: `services/governance_service.py`

```python
def check_install_policy(package_name: str, version: str, tags: list[str],
                          signed: bool, config: AamConfig) -> PolicyResult:
    """Evaluate all install governance rules. Raises PolicyViolationError if blocked."""

def check_publish_policy(signed: bool, config: AamConfig) -> PolicyResult:
    """Evaluate publish governance rules. Raises PolicyViolationError if blocked."""
```

**`PolicyViolationError`** includes: `rule_name`, `package_name`, `message` — rendered by Click as a clear error.

**Integration**: called at the top of `install_service.install()` and `publish_service.publish()` before any resolution.

### Phase H — MCP Server Updates (FR-030 to FR-032)

**`mcp/tools_read.py`** — 6 new read tools:
- `aam_tree(depth: int = 0)` → delegates to `dependency_tree_service.get_tree()`
- `aam_check(system_only: bool = False)` → delegates to `dependency_tree_service.check_deps()`
- `aam_audit(severity: str = "all")` → delegates to `dependency_tree_service.audit_deps()`
- `aam_why(package_name: str)` → delegates to `dependency_tree_service.get_why()`
- `aam_dedupe(dry_run: bool = True)` → delegates to `dependency_tree_service.dedupe_deps()`
- `aam_prune(dry_run: bool = True)` → delegates to `dependency_tree_service.prune_deps()`

**`mcp/resources.py`** — updated manifest resource:
- Resource `aam://manifest` reads `package.agent.json` first, then falls back to `aam.yaml`

**`mcp/tools_write.py`** — `aam_install` updated:
- New parameters: `frozen`, `minimal`, `latest`, `dry_run`, `install_system_deps`

**`mcp/server.py`** — updated tool count and instructions.

---

## Migration Guide (referenced from `quickstart.md`)

| Old | New | Action |
|-----|-----|--------|
| `aam.yaml` | `package.agent.json` | Run `aam pkg init --migrate` (auto-converts) |
| `aam-lock.yaml` | `package.agent.lock` | Prompted on next `aam install` |
| `.aam/packages/` | `.agent-packages/` | Prompted on next `aam install` |
| `artifacts.instructions` | `artifacts.rules` | Update manifest + move files to `rules/*/RULE.md` |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Breaking `aam.yaml` users on first update | High | Strict backwards compat: `load_manifest_universal()` tries `aam.yaml` last; no forced migration |
| System dep auto-install fails mid-way | Medium | Atomic check before install; partial installs reported as warnings not failures |
| Lock file hash mismatch on CI with `--frozen` | High | Clear error message with exact file and hash mismatch details; `aam check` pre-diagnosis |
| Governance blocklist pattern matching edge cases | Low | Use `fnmatch` for glob patterns; document pattern syntax in help text |
| Adapter `deploy_mcp` merging conflicts | Medium | Merge strategy: package-namespaced server keys prevent collisions |
