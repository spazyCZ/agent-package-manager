# Developer Quickstart: UAAPS v0.4.0 Update

**Feature**: 006-uaaps-update
**Date**: 2026-02-20
**Audience**: Engineers implementing this feature

---

## Pre-requisites

- Python 3.11+
- Existing `apps/aam-cli/` codebase (spec 004)
- Nx monorepo setup (all tests via `npx nx test aam-cli`)

---

## Implementation Order

Implement phases in this order to maintain a working codebase at each step. Each phase has testable deliverables.

### Phase A — Manifest & File Format (~2 days)

**Goal**: `package.agent.json` readable; `aam.yaml` still works; `aam pkg init` generates JSON.

1. **`core/manifest.py`** — Add new sub-models (`EnvVarConfig`, `PermissionsConfig`, `SystemDependencies`, `SystemPackages`) and new optional fields to `PackageManifest`. Update `MAX_DESCRIPTION_LENGTH = 1024`. Remove `validate_has_artifacts` validator. Update `ArtifactsDeclaration` with `commands`, `rules`, `hooks_path`, `mcp_path`.

2. **`utils/paths.py`** — Add constants:
   ```python
   MANIFEST_JSON = "package.agent.json"
   MANIFEST_YAML = "package.agent.yaml"
   MANIFEST_LEGACY = "aam.yaml"
   PACKAGES_DIR_NAME = ".agent-packages"   # changed from "packages"
   LOCK_FILE_JSON = "package.agent.lock"
   ```

3. **`core/manifest.py`** — Implement `load_manifest_universal(path)`:
   ```python
   def load_manifest_universal(path: Path) -> PackageManifest:
       """Try package.agent.json → package.agent.yaml → aam.yaml."""
   ```

4. **`services/init_service.py`** — Update `init_package()` to write `package.agent.json` by default. Keep `aam.yaml` mode available via `format="legacy"` param.

5. **Tests** (write first):
   - `tests/unit/test_unit_manifest_v2.py` — test all new fields, JSON loading, YAML loading, precedence order, backward compat with `aam.yaml`
   - Update existing validate service tests for new format

**Milestone**: `aam pkg init` creates `package.agent.json`; `aam pkg validate` validates it; existing `aam.yaml` tests still pass.

---

### Phase B — Artifact Auto-Discovery (~1 day)

**Goal**: Packages without explicit `artifacts` section work.

1. **`core/autodiscovery.py`** — Implement `discover_artifacts(package_dir, manifest)`:
   ```python
   def discover_artifacts(package_dir: Path, manifest: PackageManifest) -> ArtifactsDeclaration:
       """Scan standard directories; merge with any explicit artifact declarations."""
   ```
   - If `manifest.artifacts` is not `None`, return it (explicit overrides)
   - Otherwise scan: `skills/*/SKILL.md`, `agents/*/agent.yaml`, `agents/*.md`, `commands/*.md`, `rules/*/RULE.md`
   - Register `hooks_path` if `hooks/hooks.json` exists
   - Register `mcp_path` if `mcp/servers.json` exists
   - Use `manifest.skills_path`, `manifest.commands_path` etc. for custom paths

2. **Update `installer.py`** — Replace `manifest.all_artifacts` iteration with `discover_artifacts(package_dir, manifest).all_artifacts`

3. **Tests**:
   - `tests/unit/test_unit_autodiscovery.py` — scan fixtures with/without explicit artifacts, custom paths, hooks, MCP

**Milestone**: Install a package with no `artifacts` section in its `package.agent.json` — artifacts are auto-discovered and deployed.

---

### Phase C — Resolver v2 + Lock File (~3 days)

**Goal**: Four dependency types, new lock file format, cycle detection, resolution strategies.

1. **`core/workspace.py`** — Add `LockedPackageV2`, `UniversalLockFile`. Add `read_universal_lock_file()`, `write_universal_lock_file()`. Add `migrate_lock_file()` with user prompt. Keep existing `LockFile` + `read_lock_file()` for backward compat during transition.

2. **`core/resolver.py`** — Add:
   - `DependencyType` enum
   - `ResolutionStrategy` enum
   - `SystemCheckResults` model
   - `ResolvedGraph` model
   - `detect_cycles(root_specs, registries)` — DFS cycle detector
   - `resolve_dependencies_v2(root_manifest, registries, strategy, lock_file)` — handles all 4 dep types

3. **Install strategy flags** in `commands/install.py` and `services/install_service.py`

4. **`utils/paths.py`** — Migrate `get_packages_dir()` to use `.agent-packages/`; add `get_legacy_packages_dir()`

5. **Tests**:
   - `tests/unit/test_unit_resolver_v2.py` — cycle detection, optional deps, peer dep warnings, frozen strategy, dry run
   - Update `tests/unit/test_unit_workspace.py` for new lock file format

**Milestone**: `aam install --dry-run` resolves and displays tree without installing; `aam install --frozen` fails with stale lock; optional deps don't block install.

---

### Phase D — System Dependencies (~2 days)

**Goal**: Pre-flight checks before install; auto-install with flag.

1. **`services/system_deps_service.py`** — Implement `check_system_deps()` and `auto_install_system_deps()` for all dep types.

2. **`services/install_service.py`** — Integrate pre-flight before resolver. Add env var prompting. Add permissions confirmation.

3. **`commands/install.py`** — Add `--install-system-deps` and `--allow-sudo` flags.

4. **Tests**:
   - `tests/unit/test_unit_system_deps.py` — mock subprocess; test each dep type check; test auto-install with/without allow_sudo

**Milestone**: `aam install` a package declaring `systemDependencies`; pre-flight results displayed; missing deps block or prompt; `--install-system-deps` auto-installs pip packages.

---

### Phase E — New CLI Commands (~2 days)

**Goal**: `aam tree`, `aam why`, `aam check`, `aam audit`, `aam dedupe`, `aam prune` all functional.

1. **`services/dependency_tree_service.py`** — Implement `get_tree()`, `get_why()`, `check_deps()`, `audit_deps()`, `dedupe_deps()`, `prune_deps()`.

2. **Command files** — Create `commands/tree.py`, `why.py`, `check.py`, `audit.py`, `dedupe.py`, `prune.py` each as thin Click wrappers.

3. **`main.py`** — Register all 6 new commands in the root Click group.

4. **Tests**:
   - `tests/unit/test_unit_dependency_tree.py` — all 6 service functions with mock lock files

**Milestone**: All 6 commands available in `aam --help`; `aam tree` shows dependency tree; `aam check` detects missing package dirs; `aam audit` detects hash mismatches.

---

### Phase F — Platform Adapters (~2 days)

**Goal**: New artifact types deployed correctly by all adapters.

1. **`adapters/base.py`** — Add `deploy_command`, `deploy_rule`, `deploy_hook`, `deploy_mcp` to `PlatformAdapter` protocol.

2. **`adapters/claude.py`** — Implement all 4 new methods.

3. **`adapters/cursor.py`** — Implement all 4 new methods.

4. **`adapters/copilot.py`** — Implement all 4 new methods (with documented gaps for unsupported hooks).

5. **`adapters/codex.py`** — Implement all 4 new methods (with documented gaps).

6. **`installer.py`** — Update `_deploy_package()` to call new artifact type methods.

7. **`services/convert_service.py`** + **`converters/`** — Add new conversion rules.

8. **Tests**:
   - `tests/unit/test_unit_adapter_commands.py` — test deploy_command, deploy_rule for Claude and Cursor adapters
   - `tests/unit/test_convert.py` — update with new conversion rules

**Milestone**: Install a package with `commands/` and `rules/` dirs; verify correct platform-native deployment locations.

---

### Phase G — Governance (~1 day)

**Goal**: Client-side policy gates block disallowed installs and publishes.

1. **`core/config.py`** — Add `GovernanceInstallPolicy`, `GovernancePublishPolicy`, `GovernanceConfig`. Add to `AamConfig`.

2. **`services/governance_service.py`** — Implement `check_install_policy()`, `check_publish_policy()`, `PolicyViolationError`.

3. **`services/install_service.py`** — Call `check_install_policy()` at the top, before resolver.

4. **`services/publish_service.py`** — Call `check_publish_policy()` at the top.

5. **Tests**:
   - `tests/unit/test_unit_governance.py` — each policy type; glob patterns; empty policy = allow all

**Milestone**: Configure `allowed_scopes: ["@myorg"]` in `config.yaml`; attempt `aam install unscoped-pkg`; receive policy violation error.

---

### Phase H — MCP Server (~1 day)

**Goal**: 6 new MCP tools; updated existing tools; correct tool count.

1. **`mcp/tools_read.py`** — Add 6 new tools delegating to `dependency_tree_service`. Update `aam_validate`, `aam_info` for new manifest fields. Update tool count log.

2. **`mcp/tools_write.py`** — Add new flags to `aam_install`.

3. **`mcp/resources.py`** — Update manifest resource to call `load_manifest_universal()`.

4. **`mcp/server.py`** — Update tool count (17 → 23 read-only; 29 → 35 full).

5. **Tests**:
   - `tests/unit/test_unit_mcp_tools_v2.py` — all 6 new tools with mock data

**Milestone**: Start MCP server; call `aam_tree` tool via MCP; receive structured dependency tree response.

---

### Final — Documentation

1. **`docs/USER_GUIDE.md`** — Add sections for all new commands; update install command docs; add governance config reference; add migration guide.

2. **`docs/DESIGN.md`** — Replace with reference to `specs/006-uaaps-update/universal_package_specification.md`.

3. **`--help` text** — Verify all new commands have descriptive help text. Update existing commands for new flags.

---

## Running Tests

```bash
# Unit tests only (fast)
npx nx test aam-cli --testPathPattern=unit

# All tests
npx nx test aam-cli

# With coverage
npx nx test aam-cli -- --cov=src/aam_cli --cov-report=term-missing

# Specific new test files
npx nx test aam-cli --testPathPattern=test_unit_manifest_v2
```

## Linting and Type Checking

```bash
# Lint + format check
npx nx lint aam-cli

# Type check
npx nx run aam-cli:mypy
```

---

## Migration Reference

| Old | New | Tool |
|-----|-----|------|
| `aam.yaml` | `package.agent.json` | `aam pkg init --migrate` |
| `aam-lock.yaml` | `package.agent.lock` | prompted on `aam install` |
| `.aam/packages/` | `.agent-packages/` | prompted on `aam install` |
| `artifacts.instructions` | `artifacts.rules` | manual: move files to `rules/*/RULE.md` |
| `"dependencies"` only | `dependencies` + `optionalDependencies` + `peerDependencies` | update `package.agent.json` |

---

## Key Files Summary

| File | Action | Phase |
|------|--------|-------|
| `core/manifest.py` | EXTEND | A |
| `utils/paths.py` | UPDATE | A |
| `core/autodiscovery.py` | NEW | B |
| `core/workspace.py` | UPDATE | C |
| `core/resolver.py` | EXTEND | C |
| `services/system_deps_service.py` | NEW | D |
| `services/dependency_tree_service.py` | NEW | E |
| `commands/tree.py` … `prune.py` | NEW (6 files) | E |
| `adapters/base.py` | EXTEND | F |
| `adapters/claude.py … codex.py` | EXTEND (4 files) | F |
| `services/governance_service.py` | NEW | G |
| `core/config.py` | EXTEND | G |
| `mcp/tools_read.py` | EXTEND | H |
| `mcp/server.py` | UPDATE | H |
| `docs/USER_GUIDE.md` | UPDATE | Final |
