# Tasks: UAAPS v0.4.0 Update for aam-cli

**Input**: Design documents from `/specs/006-uaaps-update/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Test tasks (T076–T083) are in Phase 2.5 and must be written before the corresponding implementation tasks per Constitution IV (Test-Driven Quality).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete-task dependencies)
- **[Story]**: Which user story this task belongs to (US1–US7)
- Paths are relative to `apps/aam-cli/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish new path constants and shared sub-models that all phases depend on

- [x] T001 Update `PACKAGES_DIR_NAME = ".agent-packages"`, add `MANIFEST_JSON`, `MANIFEST_YAML`, `MANIFEST_LEGACY`, `LOCK_FILE_JSON = "package.agent.lock"` constants in `src/aam_cli/utils/paths.py`
- [x] T002 Add `get_universal_lock_file_path()` and `get_legacy_packages_dir()` helpers in `src/aam_cli/utils/paths.py` (depends on T001)
- [x] T003 [P] Add `EnvVarConfig`, `PermissionsConfig`, `SystemPackages`, `SystemDependencies` Pydantic sub-models to `src/aam_cli/core/manifest.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core manifest infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Extend `ArtifactsDeclaration` in `src/aam_cli/core/manifest.py` with `commands: list[ArtifactRef] = []`, `rules: list[ArtifactRef] = []`, `hooks_path: str | None = None`, `mcp_path: str | None = None` (depends on T003)
- [x] T005 Add new optional fields to `PackageManifest` in `src/aam_cli/core/manifest.py`: `category`, `engines`, `env`, `permissions`, `optional_dependencies`, `peer_dependencies`, `system_dependencies`, `resolutions`, `dist_tags`, component path overrides (`skills_path` … `mcp_path`), `vendor_extensions`, `manifest_format` sentinel; update `MAX_DESCRIPTION_LENGTH = 1024`; remove `validate_has_artifacts` validator; make `artifacts` field optional. **Pydantic aliases required (UAAPS §3)**: configure `model_config = ConfigDict(populate_by_name=True)` and add JSON aliases for each field whose Python name differs from the UAAPS JSON key: `optional_dependencies` → `Field(alias="optionalDependencies")`, `peer_dependencies` → `Field(alias="peerDependencies")`, `system_dependencies` → `Field(alias="systemDependencies")`, `dist_tags` → `Field(alias="dist-tags")`, `skills_path` → `Field(alias="skills")`, `commands_path` → `Field(alias="commands")`, `agents_path` → `Field(alias="agents")`, `rules_path` → `Field(alias="rules")`, `hooks_path` → `Field(alias="hooks")`, `mcp_path` → `Field(alias="mcp")`. Add a `model_validator(mode="before")` that collects all `x-*` prefixed keys from the raw dict into `vendor_extensions`. Serialize all JSON output with `model.model_dump(by_alias=True)`. Also add `Field(alias="mcp-servers")` to `SystemDependencies.mcp_servers`. (depends on T004)
- [x] T006 Implement `load_manifest_universal(path: Path) -> PackageManifest` in `src/aam_cli/core/manifest.py` — deterministic lookup: `package.agent.json` → `package.agent.yaml` → `aam.yaml`, JSON via stdlib `json`, YAML via PyYAML, sets `manifest_format` sentinel (depends on T005)
- [x] T007 [P] Update all existing callers of `load_manifest()` in `src/aam_cli/core/installer.py`, `src/aam_cli/services/validate_service.py`, `src/aam_cli/services/package_service.py`, and `src/aam_cli/mcp/resources.py` to call `load_manifest_universal()` instead (depends on T006)
- [x] T008 [P] Add `DependencyType`, `ResolutionStrategy` enums to `src/aam_cli/core/resolver.py` (depends on T001)
- [x] T009 [P] Add `LockedPackageV2` and `UniversalLockFile` Pydantic models to `src/aam_cli/core/workspace.py`. **Pydantic aliases required (UAAPS §13.3)**: `UniversalLockFile` fields must serialize to camelCase JSON to match the spec: `lock_version` → `Field(1, alias="lockVersion")`, `packages` → `Field(alias="resolved")`, `system_checks` → `Field(alias="systemChecks")`; add `model_config = ConfigDict(populate_by_name=True)`. Load with `UniversalLockFile.model_validate(data)` (resolves aliases). Serialize with `model.model_dump(by_alias=True)`. (depends on T001)
- [x] T010 Implement `read_universal_lock_file()` and `write_universal_lock_file()` in `src/aam_cli/core/workspace.py` — reads `package.agent.lock` (JSON), atomic write via `.tmp` + rename (depends on T009)

**Checkpoint**: Foundation ready — manifest loads from `package.agent.json` or `aam.yaml`; new lock file model available; all user story phases can now start

---

## Phase 2.5: Test Infrastructure (Constitution IV — MUST write before critical-path implementation)

**⚠️ Constitution IV requires test-first for all critical paths. Write the test files below before implementing the corresponding phases. Each test file uses mocks/fakes only — no real filesystem or subprocess calls in unit tests.**

- [x] T084 Update `tests/conftest.py` with new shared fixtures: `tmp_agent_packages(tmp_path)` → creates `.agent-packages/` dir in tmp_path and returns its path; `sample_manifest_json(tmp_path)` → writes a minimal valid `package.agent.json` to tmp_path and returns the path; `sample_lock_file_v2(tmp_path)` → writes a minimal `package.agent.lock` (JSON, using camelCase keys per UAAPS §13.3) and returns the path; `sample_system_dependencies()` → returns a `SystemDependencies` instance with one entry per dep type (python, node, pip, npm, cargo, binary, MCP). All new test files (T076–T083) should use these fixtures instead of duplicating setup. (depends on T005, T009)
- [x] T076 [P] Write `tests/unit/test_unit_manifest_v2.py` — test `load_manifest_universal()`: JSON-only dir, YAML-only dir, legacy-only dir, JSON+YAML precedence (JSON wins), JSON+YAML+legacy (JSON wins), file path directly, missing all three raises `FileNotFoundError`; test all new `PackageManifest` fields default correctly; test `validate_has_artifacts` is removed; test `MAX_DESCRIPTION_LENGTH = 1024`; test `EnvVarConfig`, `PermissionsConfig`, `SystemDependencies` model validation (depends on T006)
- [x] T077 [P] Write `tests/unit/test_unit_resolver_v2.py` — test `detect_cycles()`: no cycle returns None, direct cycle A→B→A returns path, multi-hop cycle; test `resolve_dependencies_v2()`: direct deps BFS, optional dep `PackageNotFound` swallowed, peer dep verify-only warning, frozen strategy uses lock file exact version, minimal selects lowest satisfying, dry_run returns graph without side effects; test `resolutions` override applied post-BFS (depends on T026)
- [x] T078 [P] Write `tests/unit/test_unit_system_deps.py` — mock `subprocess.run` and `importlib.metadata.version`; test each dep type (python binary check, node check, `shutil.which` for binaries, pip via importlib, npm via subprocess, MCP via JSON parse); test `auto_install_system_deps`: pip auto-installs, brew blocked without `allow_sudo`, binaries always rejected; test `SystemCheckResults.all_required_passed` property (depends on T019)
- [x] T079 [P] Write `tests/unit/test_unit_governance.py` — test `check_install_policy()`: empty `allowed_scopes` allows all, scoped package matches scope, unscoped package blocked when scopes configured, `blocked_packages` glob `@sketchy/*` blocks `@sketchy/pkg`, `require_tag` blocks untagged package, `require_signature` blocks `signed=False`; test `PolicyViolationError` carries `rule` and `message`; test each violation raises with correct exit code 3 (depends on T051)
- [x] T080 [P] Write `tests/unit/test_unit_autodiscovery.py` — test `discover_artifacts()`: explicit `artifacts` in manifest returns manifest value (no scan); no artifacts section triggers scan; finds skills, agents (structured dir format), agents (legacy .md), commands, rules; custom path overrides used; hooks_path set when `hooks/hooks.json` exists; mcp_path set when `mcp/servers.json` exists; `instructions` entries passed through with deprecation log (depends on T044)
- [x] T081 [P] Write `tests/unit/test_unit_dependency_tree.py` — mock `UniversalLockFile`; test all 6 service functions: `get_tree()` returns correct `DependencyTreeNode` structure, `get_why()` returns correct parent list and `is_direct`, `check_deps()` detects missing dirs, `check_deps(system_only=True)` aggregates across installed manifests, `audit_deps()` detects directory hash mismatch as CRITICAL, `dedupe_deps(dry_run=True)` returns plan without changes, `prune_deps(dry_run=True)` returns removal list without changes (depends on T036)
- [x] T082 [P] Write `tests/unit/test_unit_adapter_commands.py` — mock filesystem; test `deploy_command`, `deploy_rule`, `deploy_hook`, `deploy_mcp` for Claude and Cursor adapters: correct target paths, correct file content transformations (RULE.md frontmatter → .mdc for Cursor, hook event name translation), MCP key namespacing; test Copilot adapter logs warning for unsupported hook events (depends on T057, T058)
- [x] T083 [P] Write `tests/unit/test_unit_mcp_tools_v2.py` — mock `dependency_tree_service` functions; test all 6 new MCP tools return dicts matching contracts/mcp-tools.md schemas: `aam_tree` returns correct tree structure, `aam_why` returns `required_by` list, `aam_check` returns `check_type` and `results`, `aam_audit` returns `findings` with severity, `aam_dedupe` returns `would_dedupe`, `aam_prune` returns `would_remove`; test `aam_validate` includes `manifest_format` and `artifacts_discovered` fields; test `aam_install` accepts all new parameters (depends on T064, T065, T067)

---

## Phase 3: User Story 1 — Author Universal Package with New Manifest (Priority: P1) 🎯 MVP

**Goal**: `aam pkg init` generates `package.agent.json`; `aam pkg validate` validates it; `aam.yaml` still works; env var prompting and permissions confirmation wired into install

**Independent Test**: Run `aam pkg init`, confirm `package.agent.json` created → run `aam pkg validate`, confirm passes → run `aam pkg validate` on an existing `aam.yaml` package, confirm still passes

### Implementation for User Story 1

- [x] T011 [US1] Update `services/init_service.py` `init_package()` to write `package.agent.json` (JSON) by default; add `format: Literal["json", "yaml", "legacy"] = "json"` param; existing `format="legacy"` path writes `aam.yaml` (depends on T006)
- [x] T012 [US1] Update `commands/pkg/init.py` to pass `format="json"` default to init service; add `--migrate` flag that calls `load_manifest_universal()` on existing `aam.yaml` and re-writes as `package.agent.json` (depends on T011)
- [x] T013 [US1] Update `commands/pkg/create.py` to generate `package.agent.json` instead of `aam.yaml` — change manifest template file name in `src/aam_cli/services/package_service.py` (depends on T006)
- [x] T014 [US1] Update `services/validate_service.py` `validate_package()` to call `load_manifest_universal()`, report `manifest_format` in result dict, validate new UAAPS fields (`env`, `permissions`, `systemDependencies`, component overrides), report `artifacts_discovered: true` when auto-discovery used (depends on T007)
- [x] T015 [US1] Update `commands/pkg/validate.py` help text and output rendering to display `manifest_format` and `artifacts_discovered` fields from validation report (depends on T014)
- [x] T016 [US1] Implement env var prompting in `core/installer.py` `install_packages()`: after manifest load, iterate `manifest.env`; for each `required=True` var not in `os.environ`, call `click.prompt(hide_input=True)`; store in process env only (depends on T007)
- [x] T017 [US1] Implement permissions confirmation in `core/installer.py` `install_packages()`: if `manifest.permissions` is not None and any permission is declared, display Rich panel listing all permissions and call `click.confirm("Proceed with these permissions?", abort=True)` (depends on T016)

**Checkpoint**: US1 complete — `aam pkg init` creates `package.agent.json`; `aam pkg validate` handles both formats; env vars prompted; permissions confirmed

---

## Phase 4: User Story 2 — Install with System Dependency Pre-flight (Priority: P1)

**Goal**: Before installing a package, the CLI checks system requirements (`python`, `node`, binaries, pip/npm packages, MCP servers) and guides the user through resolving gaps

**Independent Test**: Create a `package.agent.json` declaring `systemDependencies.binaries: ["nonexistent-tool"]` → run `aam install` → confirm pre-flight check reports failure with install hint → confirm install is blocked or user-prompted

### Implementation for User Story 2

- [x] T018 [US2] Create `services/system_deps_service.py` with `SystemCheckResult` and `SystemCheckResults` models (per data-model.md) and `check_system_deps(system_deps: SystemDependencies) -> SystemCheckResults` implementing: python via `subprocess.run(["python3", "--version"])` to check the system `python3` binary (NOT `sys.version_info`, which reflects the CLI's own venv and would give a false positive in virtualenv environments); node via `subprocess.run(["node", "--version"])`; binaries via `shutil.which()`; pip packages via `importlib.metadata.version()` (fast, no subprocess); npm packages via `subprocess.run(["npm", "list", "-g", "--json"])`; cargo packages via `subprocess.run(["cargo", "install", "--list"])` and parse output for package names (UAAPS §13.7); MCP servers by parsing `~/.claude/.mcp.json` (Claude Code's MCP config — document that this path is Claude Code-specific and other platforms may use different locations) (depends on T003)
- [x] T019 [US2] Add `auto_install_system_deps(missing: list[SystemCheckResult], allow_sudo: bool) -> dict[str, bool]` to `services/system_deps_service.py`: pip via `sys.executable -m pip install`, npm via `subprocess npm install -g`, brew/apt gated behind `allow_sudo`, binaries always rejected with instructions, MCP servers via `mcp install` if on PATH (depends on T018)
- [x] T020 [US2] Integrate pre-flight check into `core/installer.py` `install_packages()`: as the first step before the resolver — call `check_system_deps(manifest.system_dependencies)`; display Rich table of results; if failures: prompt user `[continue/abort/auto-install]`. Call chain for context: `install_service.install()` (outer) → calls governance check (added by T053 in US5, at `install_service` level) → then calls `installer.install_packages()` (inner, this task) → which calls `check_system_deps()`. These are two separate call frames; T020 modifies the inner function only. (depends on T018, T007)
- [x] T021 [US2] Add `--install-system-deps`, `--allow-sudo`, and `--skip-checks` Click options to `commands/install.py`; pass through to installer. `--install-system-deps`: if failures exist, call `auto_install_system_deps()` then re-check. `--skip-checks`: pass `skip_checks=True` to `install_packages()`, which skips calling `check_system_deps()` entirely — intended for CI environments where system deps are pre-provisioned (UAAPS §16). Update `install_packages()` signature to accept `skip_checks: bool = False`. (depends on T019, T020)
- [x] T022 [US2] Create `commands/check.py` as a **stub** implementing only the `--system` branch: `aam check --system` calls `check_system_deps()` using system deps collected from all installed packages' manifests (see T033 for the aggregation mechanism); display Rich status table. The command is not registered in `main.py` yet (that happens in T043). The default no-flag behavior (`aam check` checking installed dirs against lock file) is intentionally left unimplemented here — T039 (US3) adds that behavior once `dependency_tree_service.check_deps()` exists. (depends on T018)
- [x] T023 [US2] Persist system check results to `UniversalLockFile.system_checks` in `core/installer.py` after successful install. Also compute and store the installed package directory hash in `LockedPackageV2.integrity` as `sha256-<hex>` (deterministic: sorted file list → per-file SHA-256 → SHA-256 of concatenated results) — this is the hash that `aam audit` (T034) verifies later. (depends on T010, T020)

**Checkpoint**: US2 complete — `aam install` on a package with `systemDependencies` shows pre-flight check table; missing required deps prompt user; `--install-system-deps` auto-installs pip/npm packages

---

## Phase 5: User Story 3 — Resolve and Inspect Dependency Trees (Priority: P2)

**Goal**: Enhanced resolver with 4 dep types, cycle detection, hoisting, and resolution strategies; six new tree-inspection commands (`tree`, `why`, `check`, `audit`, `dedupe`, `prune`); install dir migration

**Independent Test**: Install a package with transitive dependencies → `aam tree` shows nested graph → `aam why <transitive-pkg>` names the parent → `aam check` confirms all present → `aam audit` passes with matching hashes → install a package with `optionalDependencies` pointing to nonexistent pkg → confirm install succeeds

### Implementation for User Story 3

- [x] T024 [US3] Implement `detect_cycles(root_specs: list[tuple[str, str]], registries: list[Registry]) -> list[str] | None` in `src/aam_cli/core/resolver.py` — DFS with `visiting: set[str]` and `ancestors: list[str]` stack; returns cycle path or None (depends on T008)
- [x] T025 [US3] Add `SystemCheckResults` model to `src/aam_cli/core/resolver.py` (import from `services/system_deps_service.py`); add `ResolvedGraph` model per data-model.md (depends on T008)
- [x] T026 [US3] Implement `resolve_dependencies_v2(root_manifest: PackageManifest, registries: list[Registry], strategy: ResolutionStrategy, lock_file: UniversalLockFile | None) -> ResolvedGraph` in `src/aam_cli/core/resolver.py` — BFS for `dependencies` (fail on conflict), optional BFS with swallowed `PackageNotFound` for `optionalDependencies`, verify-only pass for `peerDependencies`; hoisting (flat install since v1 resolver already fails on conflicts); `frozen` strategy uses lock file exact versions; `minimal`/`latest` select version accordingly; `dry_run` resolves without triggering install. **`resolutions` enforcement (FR-012)**: after BFS completes but before returning `ResolvedGraph`, apply `manifest.resolutions` in two steps: (1) **validate tree membership** — for each key in `manifest.resolutions`, assert it is present in the resolved package set; raise `ValueError(f"resolutions entry '{name}' does not reference any package in the dependency tree")` for unknown names (UAAPS §16: "resolutions entries must reference packages in the tree"); (2) **apply overrides** — replace the resolved version of each validated entry with the forced version regardless of constraints; log a warning if the forced version violates a dependent's semver constraint (never silently drop). (depends on T025, T024, T010)
- [x] T027 [US3] Implement `migrate_lock_file(project_dir: Path | None = None) -> bool` in `src/aam_cli/core/workspace.py` — detect `.aam/aam-lock.yaml`, prompt user, if accepted: convert `LockFile` → `UniversalLockFile`, write `package.agent.lock`, rename old file to `aam-lock.yaml.bak` (depends on T010)
- [x] T028 [US3] Implement install directory migration helper `migrate_install_dir(project_dir: Path | None = None) -> bool` in `src/aam_cli/core/installer.py` — detect `.aam/packages/` with contents, prompt user, `shutil.move()` to `.agent-packages/`, update lock file path (depends on T027)
- [x] T029 [US3] Update `core/installer.py` `install_packages()` to use `resolve_dependencies_v2()`, pass strategy from flags, run `detect_cycles()` before resolution, use `get_packages_dir()` (now returns `.agent-packages/`) (depends on T026, T028)
- [x] T030 [US3] Add `--frozen`, `--minimal`, `--latest`, `--dry-run` Click options to `commands/install.py`; pass `ResolutionStrategy` enum to installer (depends on T026)
- [x] T031 [US3] Create `services/dependency_tree_service.py` with `DependencyTreeNode` model (per data-model.md) and `get_tree(project_dir: Path | None, depth: int) -> DependencyTreeNode` — build tree from `UniversalLockFile.packages` (depends on T010)
- [x] T032 [US3] Add `get_why(package_name: str, project_dir: Path | None) -> dict[str, Any]` to `services/dependency_tree_service.py` — traverse lock file to find all packages that list target in their `dependencies` dict (depends on T031)
- [x] T033 [US3] Add `check_deps(project_dir: Path | None, system_only: bool) -> dict[str, Any]` to `services/dependency_tree_service.py` — for each package in lock file verify `.agent-packages/<fs-name>/` exists and report status. For `system_only=True`: aggregate system deps across all installed packages by iterating every package dir in `.agent-packages/`, calling `load_manifest_universal(package_dir)` for each, collecting all `manifest.system_dependencies` into a merged `SystemDependencies` object (union of all pip/npm/binary/MCP requirements), then calling `system_deps_service.check_system_deps(merged_deps)` and returning the results. (depends on T031, T018)
- [x] T034 [US3] Add `AuditFinding` model and `audit_deps(project_dir: Path | None, severity: str) -> dict[str, Any]` to `services/dependency_tree_service.py` — integrity verification strategy: hash the **installed package directory** using a deterministic directory hash (sorted file list → per-file SHA-256 → combined SHA-256 of all hashes) and compare against the `integrity` field in the lock file. The `.aam` archive is NOT retained post-install; the directory tree is the canonical artifact. The installer must store a directory hash (not archive hash) in `LockedPackageV2.integrity` at install time for this to work — add a note to T010/T023 that `write_universal_lock_file()` must store `sha256-<dir-hash>`. Report mismatches as CRITICAL findings. If HTTP registry configured, call `/packages/{name}/advisories` and merge advisory results. (depends on T031)
- [x] T035 [US3] Add `dedupe_deps(project_dir: Path | None, dry_run: bool) -> dict[str, Any]` to `services/dependency_tree_service.py` — v1 scope: scan `.agent-packages/` for any packages that appear in more than one sub-namespace directory (a layout produced by pre-update installs or migration from `.aam/packages/`). If compatible versions exist in multiple locations, hoist to root and remove sub-namespace copies. Note: post-v1-install packages are always flat (resolver fails on conflicts), so `dedupe` is most useful for migrated or legacy installs. If no nested packages found, return `packages_changed: 0` and report success (not an error). (depends on T031)
- [x] T036 [US3] Add `prune_deps(project_dir: Path | None, dry_run: bool) -> dict[str, Any]` to `services/dependency_tree_service.py` — compare `.agent-packages/` directory listing against lock file; remove unlisted dirs if not dry_run; update lock file (depends on T031)
- [x] T037 [P] [US3] Create `commands/tree.py` — Click command `aam tree [--depth N] [--project PATH]` delegating to `get_tree()`; render with `rich.tree.Tree` (depends on T031)
- [x] T038 [P] [US3] Create `commands/why.py` — Click command `aam why PACKAGE [--project PATH]` delegating to `get_why()`; render with Rich panel (depends on T032)
- [x] T039 [P] [US3] Complete `commands/check.py` (extends the T022 stub): add the default no-flag behavior — `aam check` (without `--system`) calls `check_deps(system_only=False)` and renders a Rich table of package-presence results (each lock-file entry vs its `.agent-packages/<name>/` directory). The `--system` branch written in T022 is preserved unchanged. Exit code 1 if any check fails. (depends on T033)
- [x] T040 [P] [US3] Create `commands/audit.py` — Click command `aam audit [--severity critical|high|medium|low|all] [--project PATH]` delegating to `audit_deps()`; render Rich findings table; exit code 1 on findings at or above severity (depends on T034)
- [x] T041 [P] [US3] Create `commands/dedupe.py` — Click command `aam dedupe [--dry-run] [--project PATH]` delegating to `dedupe_deps()`; render before/after summary (depends on T035)
- [x] T042 [P] [US3] Create `commands/prune.py` — Click command `aam prune [--dry-run] [--project PATH]` delegating to `prune_deps()`; render removed packages list (depends on T036)
- [x] T043 [US3] Register all 6 new commands (`tree`, `why`, `check`, `audit`, `dedupe`, `prune`) in `src/aam_cli/main.py` root Click group (depends on T037–T042)

**Checkpoint**: US3 complete — `aam tree` displays graph; `aam why` names parents; `aam check` detects missing dirs; `aam audit` catches hash mismatches; `aam dedupe` and `aam prune` report correctly; optional deps don't block install

---

## Phase 6: User Story 4 — Artifact Auto-Discovery (Priority: P2)

**Goal**: Packages without an `artifacts` section in their manifest have all artifacts discovered from standard directories automatically

**Independent Test**: Create `package.agent.json` with no `artifacts` section; add `skills/my-skill/SKILL.md`, `commands/review.md`, `rules/ts-standards/RULE.md`; run `aam pkg validate` → confirm artifacts discovered; run `aam install` (local registry) → confirm all three artifact types deployed

### Implementation for User Story 4

- [x] T044 [US4] Create `src/aam_cli/core/autodiscovery.py` — implement `discover_artifacts(package_dir: Path, manifest: PackageManifest) -> ArtifactsDeclaration`: if `manifest.artifacts` is not None return it; else scan: `manifest.skills_path` for `*/SKILL.md`; `manifest.agents_path` for structured agents (`*/agent.yaml` present) — for each such directory also read `system-prompt.md` and combine into a single `ArtifactRef` with `path=<dir>/agent.yaml` and `description` sourced from the YAML `description` field; `manifest.agents_path` for legacy single-file agents (`*.md` at top level); `manifest.commands_path` for `*.md`; `manifest.rules_path` for `*/RULE.md`; register `hooks_path` field if a file exists at `package_dir / manifest.hooks_path`; register `mcp_path` field if a file exists at `package_dir / manifest.mcp_path`. (depends on T005)
- [x] T045 [US4] Update `core/installer.py` `_deploy_package()` to call `discover_artifacts(package_dir, manifest)` and iterate the returned `ArtifactsDeclaration` instead of `manifest.all_artifacts` (depends on T044, T007)
- [x] T046 [US4] Update `services/validate_service.py` to call `discover_artifacts()` and set `artifacts_discovered: true` in validation report when artifacts were auto-discovered (vs explicitly declared) (depends on T044, T014)
- [x] T047 [US4] Update `services/package_service.py` `get_package_info()` to call `discover_artifacts()` and include `artifacts_discovered` flag in info dict (depends on T044)
- [x] T048 [P] [US4] Add backward compatibility for legacy `instructions` artifact type: in `discover_artifacts()`, if `manifest.artifacts` contains `instructions` entries, pass them through as-is and log deprecation warning via `utils/deprecation.py` (depends on T044)

**Checkpoint**: US4 complete — packages without `artifacts` section are fully installable; all four auto-discoverable artifact types (skill, agent, command, rule) plus hooks/MCP configs are found and deployed

---

## Phase 7: User Story 5 — Governance Policy Gates (Priority: P2)

**Goal**: Client-side policies from `config.yaml` block disallowed installs and publishes before any resolution or file operations occur

**Independent Test**: Add `governance.install_policy.allowed_scopes: ["@myorg"]` to `~/.aam/config.yaml`; attempt `aam install unscoped-pkg`; confirm error code 3 and message naming the policy; attempt `aam install @myorg/allowed-pkg`; confirm no policy error

### Implementation for User Story 5

- [x] T049 [US5] Add `GovernanceInstallPolicy`, `GovernancePublishPolicy`, `GovernanceConfig` Pydantic models to `src/aam_cli/core/config.py`; add `governance: GovernanceConfig = GovernanceConfig()` field to `AamConfig` (depends on T001)
- [x] T050 [US5] Create `src/aam_cli/services/governance_service.py` with `PolicyViolation`, `PolicyResult` models and `PolicyViolationError` exception class (depends on T049)
- [x] T051 [US5] Implement `check_install_policy(package_name: str, version: str, tags: list[str], signed: bool, config: AamConfig) -> PolicyResult` in `services/governance_service.py`: evaluate `allowed_scopes` (empty = allow all), `require_signature`, `require_tag`, `blocked_packages` (via `fnmatch.fnmatchcase()`) — raise `PolicyViolationError` on first violation with `rule`, `package_name`, `message`. **Transitive enforcement (C2)**: `check_install_policy()` is called once per package in the full resolved graph, including all transitive and optional dependencies — not just the direct CLI argument. The call site in T053 loops over `resolved_graph.all_packages`. **`signed` determination (C3)**: the `signed` bool is derived by checking whether the package's registry metadata includes a `signature` field (e.g., a Sigstore bundle or GPG detached signature) in the package manifest fetched from the registry; if registry does not return signature metadata, `signed=False`. Document in the function docstring that v1 only supports registry-provided signatures, not local file `.sig` verification. (depends on T050)
- [x] T052 [US5] Implement `check_publish_policy(signed: bool, config: AamConfig) -> PolicyResult` in `services/governance_service.py` (depends on T050)
- [x] T053 [US5] Integrate `check_install_policy()` into `services/install_service.py` `install()`. Call chain: `install_service.install()` (this file) → runs governance → then calls `installer.install_packages()` (T020's file) → which runs system dep check → then resolver. Governance runs in the outer service layer BEFORE any call to the inner installer, so no modification to `installer.py` is needed here. Implementation: (1) after resolving the dependency graph (via a dry-run resolve call), loop over `resolved_graph.all_packages` and call `check_install_policy()` for each package (direct + transitive); (2) catch `PolicyViolationError`, render a Rich error panel with `violation.rule`, `violation.package_name`, and `violation.message`; (3) exit with code 3. (depends on T051, T020)
- [x] T054 [US5] Integrate `check_publish_policy()` at the top of `services/publish_service.py` `publish()` — catch `PolicyViolationError`, render rich error panel, exit code 3 (depends on T052)

**Checkpoint**: US5 complete — `allowed_scopes`, `require_signature`, `require_tag`, `blocked_packages` and publish `require_signature` all block correctly with policy-specific error messages

---

## Phase 8: User Story 6 — Deploy All Artifact Types Across Platforms (Priority: P3)

**Goal**: Commands, Rules, Hooks, and MCP configs are deployed to correct platform-native locations by all four platform adapters; `aam convert` handles new format conversions

**Independent Test**: Create a package with `commands/review.md`, `rules/ts-standards/RULE.md`, `hooks/hooks.json`, `mcp/servers.json`; run `aam install --platform claude` → verify each artifact in correct Claude Code location; run `aam install --platform cursor` → verify each artifact in correct Cursor location

### Implementation for User Story 6

- [x] T055 [US6] Extend `PlatformAdapter` Protocol in `src/aam_cli/adapters/base.py` with four new abstract methods: `deploy_command(cmd_path, ref, config) -> Path`, `deploy_rule(rule_path, ref, config) -> Path`, `deploy_hook(hooks_json_path, config) -> Path`, `deploy_mcp(servers_json_path, config) -> Path` (depends on T007)
- [x] T056 [P] [US6] Implement `deploy_command`, `deploy_rule`, `deploy_hook`, `deploy_mcp` in `src/aam_cli/adapters/claude.py`: commands → `.claude/commands/<pkg>:<name>.md`; rules → append to `CLAUDE.md`; hooks → merge into `.claude/hooks.json` with package-namespaced keys; MCP → merge into `.mcp.json` with namespaced server keys (depends on T055)
- [x] T057 [P] [US6] Implement `deploy_command`, `deploy_rule`, `deploy_hook`, `deploy_mcp` in `src/aam_cli/adapters/cursor.py`: commands → convert to skill with `disable-model-invocation: true` in `.cursor/skills/`; rules → convert frontmatter and write `.mdc` to `.cursor/rules/`; hooks → translate event names and write `.cursor/hooks.json`; MCP → write `.cursor/mcp.json` (depends on T055)
- [x] T058 [P] [US6] Implement `deploy_command`, `deploy_rule`, `deploy_hook`, `deploy_mcp` in `src/aam_cli/adapters/copilot.py`: commands → `.github/prompts/<pkg>:<name>.prompt.md`; rules → convert to `.github/instructions/<name>.instructions.md` (`globs` → `applyTo`); hooks → partial (4 events only, log warning for unsupported); MCP → VS Code MCP config location (depends on T055)
- [x] T059 [P] [US6] Implement `deploy_command`, `deploy_rule`, `deploy_hook`, `deploy_mcp` in `src/aam_cli/adapters/codex.py`: commands → convert to skill with `disable-model-invocation`; rules → append to `AGENTS.md`; hooks → log warning (not supported); MCP → log warning (limited support) (depends on T055)
- [x] T060 [US6] Update `core/installer.py` `_deploy_package()` to call new adapter methods for `commands`, `rules`, `hooks_path`, `mcp_path` entries from the discovered `ArtifactsDeclaration` (depends on T055, T045)
- [x] T061 [US6] Add hook event name translation table in `src/aam_cli/converters/mappings.py` — bidirectional mapping: `PreToolUse` ↔ `beforeShellCommand` (Cursor) ↔ `preToolUse` (Copilot) etc. per UAAPS spec cross-platform hook table (depends on T001)
- [x] T062 [US6] Update `services/convert_service.py` to add new conversion rules: `.instructions.md` → `RULE.md` (map `applyTo` → `globs`; add `description` placeholder); hook event name translation using T061 mappings; MCP config restructure between `servers.json`, `.mcp.json`, `mcp.json` formats (depends on T061)
- [x] T063 [US6] Update `commands/convert.py` help text and conversion logic to invoke new conversion rules from T062 (depends on T062)

**Checkpoint**: US6 complete — all four new artifact types deploy correctly to Claude Code and Cursor; `aam convert` handles `.instructions.md` → `RULE.md` and hook event name translation

---

## Phase 9: User Story 7 — New and Updated MCP Server Tools (Priority: P3)

**Goal**: Six new MCP read tools expose tree inspection capabilities; updated tools handle new manifest format; manifest resource serves `package.agent.json`

**Independent Test**: Start `aam mcp-serve`; call `aam_tree` tool → confirm structured dependency tree response; call `aam_check` → confirm package status table; call `aam_audit` → confirm finding format; call `aam_validate` → confirm `manifest_format` field present in response

### Implementation for User Story 7

- [x] T064 [US7] Add six new read tools to `src/aam_cli/mcp/tools_read.py`: `aam_tree(depth: int = 0, project: str = ".")`, `aam_why(package_name: str, project: str = ".")`, `aam_check(system_only: bool = False, project: str = ".")`, `aam_audit(severity: str = "all", project: str = ".")`, `aam_dedupe(dry_run: bool = True, project: str = ".")`, `aam_prune(dry_run: bool = True, project: str = ".")` — each tagged `read`, each delegating to corresponding `dependency_tree_service` function and returning structured dict per `contracts/mcp-tools.md` (depends on T031–T036)
- [x] T065 [US7] Update `aam_validate` tool in `src/aam_cli/mcp/tools_read.py` to include `manifest_format` and `artifacts_discovered` fields in returned dict (depends on T014, T046)
- [x] T066 [US7] Update `aam_info` tool in `src/aam_cli/mcp/tools_read.py` to include new manifest fields: `manifest_format`, `category`, `engines`, `env`, `permissions`, `optional_dependencies`, `peer_dependencies`, `system_dependencies` (depends on T007)
- [x] T067 [US7] Update `aam_install` tool in `src/aam_cli/mcp/tools_write.py` with new parameters: `frozen: bool = False`, `minimal: bool = False`, `latest: bool = False`, `dry_run: bool = False`, `install_system_deps: bool = False`, `skip_checks: bool = False`, `no_deploy: bool = False`, `force: bool = False` (full signature per `contracts/mcp-tools.md`); update returned dict to include `strategy`, `system_checks`, `env_vars_prompted`, `lock_file` fields per `contracts/mcp-tools.md` (depends on T030)
- [x] T068 [US7] Update manifest resource in `src/aam_cli/mcp/resources.py` to call `load_manifest_universal()` and set `mime_type = "application/json"` when `manifest_format == "json"`, `text/yaml` otherwise (depends on T006)
- [x] T069 [US7] Update `src/aam_cli/mcp/server.py` `SERVER_INSTRUCTIONS` to document 6 new tools; update tool count constants: read-only 17 → 23, full 29 → 35 (depends on T064)

**Checkpoint**: US7 complete — all 23 read tools available (17 existing + 6 new); `aam_install` accepts new flags; `aam://manifest` serves JSON; tool count matches

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, integration quality, and final validation

- [x] T070 [P] Update `docs/USER_GUIDE.md` — add sections for all 6 new commands (`tree`, `why`, `check`, `audit`, `dedupe`, `prune`) with usage examples; update install command section with new flags (`--frozen`, `--minimal`, `--latest`, `--dry-run`, `--install-system-deps`, `--allow-sudo`, `--skip-checks`); add governance configuration reference; add manifest migration guide; add system dependencies reference. Also update root `README.md` if it references `aam.yaml`, `.aam/packages/`, `aam-lock.yaml`, or the old command set — update to mention `package.agent.json`, `.agent-packages/`, `package.agent.lock`, and the 6 new commands
- [x] T071 [P] Replace `docs/DESIGN.md` content with a reference to `specs/006-uaaps-update/universal_package_specification.md` as the authoritative design document; preserve link to UAAPS spec in repo
- [x] T072 [P] Audit all `--help` text for new and modified commands: `aam install`, `aam tree`, `aam why`, `aam check`, `aam audit`, `aam dedupe`, `aam prune`, `aam pkg init`, `aam pkg validate`, `aam convert` — ensure each has a clear docstring and all new options are documented
- [x] T073 Run `npx nx lint aam-cli` and `npx nx run aam-cli:mypy` — fix all Ruff and MyPy errors introduced by new code
- [x] T074 Run full test suite `npx nx test aam-cli` — confirm all existing tests still pass (no regressions from manifest format changes, path constant changes, or resolver changes). Also manually verify `aam outdated` (existing command, referenced in US3 AC-5) correctly handles packages from `package.agent.lock` and reads both `optionalDependencies` and `peerDependencies` when checking for newer versions. If the existing `aam outdated` command reads only `dependencies`, file a follow-up task.
- [x] T075 Validate quickstart.md end-to-end scenario

---

## Phase 11: Remediation (Issues Found During Review)

**Purpose**: Fix bugs and inconsistencies found during implementation review

- [x] T085 Fix hash mismatch bug: align `_compute_dir_integrity()` in `src/aam_cli/core/installer.py` with `_compute_dir_hash()` in `src/aam_cli/services/dependency_tree_service.py` — both must skip `.lock` files and `__pycache__` directories for deterministic hashing (depends on T023, T034): create a fresh `package.agent.json` with `systemDependencies`, `commands/`, `rules/`, `hooks/hooks.json`; `aam pkg validate`; `aam install --dry-run`; `aam tree`; `aam check --system` — all pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) — BLOCKS all user stories
- **Test Infrastructure (Phase 2.5)**: T084 (conftest fixtures) depends on T005/T009 and MUST complete before any T076–T083 test file. T076 depends on T006 (load_manifest_universal), T077 on T026, T078 on T019, T079 on T051, T080 on T044, T081 on T036, T082 on T057/T058, T083 on T064/T065/T067. Write each test file immediately before the corresponding implementation tasks. All T076–T083 can be parallelized since they write different test files.
- **US1 (Phase 3)**: Depends on Foundational — T076 must be written before T011
- **US2 (Phase 4)**: Depends on Foundational — T078 must be written before T018; can parallelize with US1
- **US3 (Phase 5)**: Depends on Foundational — T077 and T081 must be written before T024 and T031; can parallelize with US1, US2
- **US4 (Phase 6)**: Depends on Foundational — T080 must be written before T044; can parallelize with US1–US3
- **US5 (Phase 7)**: Depends on Foundational — T079 must be written before T050; integrates with US2's install service (T053 inserts call before T020's check in install_service.py outer layer)
- **US6 (Phase 8)**: Depends on US4 (adapters need `discover_artifacts()` to know what to deploy) — T082 must be written before T056/T057
- **US7 (Phase 9)**: Depends on US3 (new tools delegate to `dependency_tree_service`) — T083 must be written before T064
- **Polish (Phase 10)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — independent
- **US2 (P1)**: After Foundational — independent (can parallel with US1)
- **US3 (P2)**: After Foundational — independent (can parallel with US1, US2)
- **US4 (P2)**: After Foundational — independent (can parallel with US1–US3)
- **US5 (P2)**: After Foundational — integrates with US2's install service call site (T053 inserts before T020 in install flow)
- **US6 (P3)**: After US4 (needs auto-discovery for deploy pipeline)
- **US7 (P3)**: After US3 (new MCP tools delegate to dependency_tree_service)

### Within Each User Story

- Models/sub-models before services
- Services before commands/adapters
- Commands before MCP tools (MCP tools delegate to same services)
- Core implementation before integration points

---

## Parallel Opportunities

```
# Phase 1 — run together:
T001 paths.py constants
T003 [P] manifest sub-models

# Phase 2 — sequential T004→T005→T006, then branch:
T007 [P] update callers       ← parallel with →    T008 [P] resolver enums
T009 [P] lock file models     ← parallel with →    T010 workspace functions

# Phase 2.5 — T084 (conftest fixtures) first, then write all test files in parallel:
T084     conftest.py shared fixtures    (write before T076–T083)
T076 [P] test_unit_manifest_v2.py      (write before T011)
T077 [P] test_unit_resolver_v2.py      (write before T024)
T078 [P] test_unit_system_deps.py      (write before T018)
T079 [P] test_unit_governance.py       (write before T050)
T080 [P] test_unit_autodiscovery.py    (write before T044)
T081 [P] test_unit_dependency_tree.py  (write before T031)
T082 [P] test_unit_adapter_commands.py (write before T056)
T083 [P] test_unit_mcp_tools_v2.py     (write before T064)

# After Foundational — start all in parallel:
US1 (T011–T017)  ← can parallelize with →  US2 (T018–T023)
US3 (T024–T043)  ← can parallelize with →  US4 (T044–T048)
US5 (T049–T054)  ← independent →           (after US2's T020 exists in install_service outer layer)

# Within US3 — once dependency_tree_service complete (T031–T036):
T037 [P] commands/tree.py
T038 [P] commands/why.py
T039 [P] commands/check.py     ← all six can be written in parallel
T040 [P] commands/audit.py
T041 [P] commands/dedupe.py
T042 [P] commands/prune.py

# Within US6 — once base.py extended (T055):
T056 [P] adapters/claude.py
T057 [P] adapters/cursor.py    ← all four adapters in parallel
T058 [P] adapters/copilot.py
T059 [P] adapters/codex.py

# Polish — all three docs tasks in parallel:
T070 [P] USER_GUIDE.md
T071 [P] DESIGN.md
T072 [P] --help text audit
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T010)
3. Write T084 (conftest fixtures), then T076 (manifest tests) and T078 (system dep tests) from Phase 2.5
4. Complete Phase 3: US1 — New Manifest Format (T011–T017) — run T076 tests after each task
5. Complete Phase 4: US2 — System Dependency Pre-flight (T018–T023) — run T078 tests after each task
6. **STOP and VALIDATE**: Both P1 stories work; `package.agent.json` generated; pre-flight checks run; `aam.yaml` backward compat confirmed; unit tests green
7. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → `package.agent.json` authoring works → Demo
3. Add US2 → System dep pre-flight → Demo
4. Add US3 → Full dependency tree commands → Demo
5. Add US4 → Auto-discovery → Demo
6. Add US5 → Governance gates → Demo
7. Add US6 → Cross-platform artifact deployment → Demo
8. Add US7 → MCP tools complete → Demo
9. Polish → Documentation + cleanup → Release

### Parallel Team Strategy (2–3 developers)

After Foundational completes:
- **Developer A**: US1 (T011–T017) then US6 (T055–T063)
- **Developer B**: US2 (T018–T023) then US5 (T049–T054)
- **Developer C**: US3 (T024–T043) then US7 (T064–T069)
- US4 (T044–T048) can be taken by whichever developer finishes first

---

## Notes

- [P] tasks write different files — safe to parallelize
- Each [Story] label maps to spec.md user story for full traceability
- `aam.yaml` backward compat is non-negotiable — all existing tests must pass throughout
- Constitution VII: No silent migration — all format migrations require explicit user confirmation
- Constitution IV: Test tasks T076–T083 (Phase 2.5) MUST be written before the corresponding implementation tasks
- Commit after each logical group (e.g., after all Phase 2 tasks, after each user story phase)
- Stop at any Checkpoint to independently validate the completed story
- Install dir change (`.aam/packages/` → `.agent-packages/`) is in T028 — test migration prompt explicitly
- Lock file lives at `<project_dir>/package.agent.lock` (project root), constant `LOCK_FILE_JSON = "package.agent.lock"` in `utils/paths.py` — never inside `.agent-packages/`
- `aam audit` integrity check (T034) hashes the installed directory tree, not the archive — T023 stores the dir hash at install time
- Governance check (T053) runs in `install_service.install()` outer layer; system dep check (T020) runs in `installer.install_packages()` inner layer — two separate call frames
- `aam dedupe` v1 targets migrated/legacy nested layouts; post-v1 fresh installs are always flat
- `aam outdated` (existing command) — verify handles new dep types in T074
