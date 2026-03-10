# Research: UAAPS v0.4.0 Update for aam-cli

**Phase**: 0 — Unknowns resolved
**Date**: 2026-02-20
**Feature**: 006-uaaps-update

---

## R-001: Manifest Format — JSON vs YAML

**Question**: How do we load both `package.agent.json` and `package.agent.yaml` while keeping `aam.yaml` backward compatibility?

**Decision**: Single `PackageManifest` Pydantic model; new `load_manifest_universal(path)` entry point with deterministic precedence.

**Rationale**: A unified model avoids duplicating validation logic. The loader implements explicit precedence (`package.agent.json` > `package.agent.yaml` > `aam.yaml`) — not a fallback, a defined lookup order. JSON is parsed with stdlib `json`; YAML with existing `PyYAML`. No new dependencies needed.

**Alternatives considered**:
- Two separate models (`PackageManifestV2` + `PackageManifest`) — rejected: doubles validation surface, complicates downstream consumers
- Always convert YAML to JSON on load — rejected: unnecessary overhead, adds complexity with no benefit

---

## R-002: Dependency Graph — Cycle Detection Algorithm

**Question**: Which cycle detection algorithm to use for the dependency graph?

**Decision**: DFS with an explicit recursion stack (`ancestors: set[str]`), run as a pre-check before BFS resolution.

**Rationale**: O(V+E) complexity. Simple implementation (~30 lines). Returns the exact cycle path for a useful error message. The existing BFS resolver is unchanged — cycles are detected before it runs, not inside it.

**Alternatives considered**:
- Tarjan's SCC — overkill for a DAG validator; cycle path reporting is simpler with DFS
- Detect during BFS — more complex state tracking; error message quality worse

---

## R-003: Dependency Hoisting Strategy

**Question**: How should hoisting (npm-style flat install) be implemented?

**Decision**: Post-BFS flattening pass. After full resolution, build `{name: version}` map across all resolved packages. Since v1 resolver already fails on version conflicts, all resolved packages have exactly one version → all are hoisted to the install root (`.agent-packages/<pkg>/`). Namespaced skills use `<pkg>:<skill-name>` at activation time, not filesystem nesting.

**Rationale**: Since the v1 resolver raises on conflicts, every successfully resolved dependency graph is already conflict-free and trivially hoist-able. The "hoisting" in v1 is effectively: flat installation (no nesting), which is already how `.aam/packages/` worked. No structural change needed beyond the directory rename.

**Alternatives considered**:
- npm-style nested nesting with selective hoisting — unnecessary complexity for v1; agent packages have much shallower dependency trees than npm packages
- Symlink hoisting — platform portability concerns; not all target systems support symlinks reliably

---

## R-004: System Dependency Verification Methods

**Question**: How do we check each system dependency type efficiently without new dependencies?

**Decision**: All stdlib + existing subprocess.

| Dependency type | Check method | Auto-install method |
|----------------|-------------|---------------------|
| Python version | `sys.version_info` | N/A (can't self-upgrade) |
| Node version | `subprocess.check_output(["node", "--version"])` | N/A |
| Binaries | `shutil.which(binary)` | N/A (print instructions) |
| pip packages | `importlib.metadata.version(pkg)` (fast, no subprocess) | `subprocess.run([sys.executable, "-m", "pip", "install", pkg])` |
| npm packages | `subprocess.check_output(["npm", "list", "-g", "--json"])` | `subprocess.run(["npm", "install", "-g", pkg])` |
| brew packages | `subprocess.check_output(["brew", "list", "--formula"])` | `subprocess.run(["brew", "install", pkg])` — requires `--allow-sudo` consent |
| apt packages | `subprocess.check_output(["dpkg", "-l", pkg])` | `subprocess.run(["sudo", "apt-get", "install", "-y", pkg])` — requires `--allow-sudo` |
| MCP servers | Parse `~/.claude/.mcp.json` or `~/.claude/mcp.json` | `subprocess.run(["mcp", "install", server])` if `mcp` CLI on PATH |

**Rationale**: `importlib.metadata` is significantly faster than subprocess for pip packages (already in-process). Using `sys.executable` for pip auto-install ensures we install to the active Python environment, not a system Python. All methods are idempotent and safe to re-run.

**Alternatives considered**:
- `pip show <pkg>` via subprocess — slower than importlib.metadata
- Third-party system package detection libraries — avoid new dependencies (Constitution I)

---

## R-005: Lock File JSON Format

**Question**: How should `package.agent.lock` be structured and serialized?

**Decision**: `UniversalLockFile` Pydantic model serialized to JSON via stdlib `json.dump()`. File written atomically (write to `.tmp`, rename).

**Schema**:
```json
{
  "lockVersion": 1,
  "resolvedAt": "2026-02-20T10:00:00Z",
  "packages": {
    "code-review": {
      "version": "1.3.2",
      "source": "local",
      "integrity": "sha256-abc123...",
      "dependencies": {"git-utils": "1.0.1"},
      "optional": false
    }
  },
  "systemChecks": {
    "python": "3.12.1",
    "node": "20.11.0",
    "binaries": {"git": "/usr/bin/git"},
    "pip": {"pypdf": "4.1.0"}
  }
}
```

**Rationale**: `lockVersion` enables future format migrations. `resolvedAt` enables stale-lock detection. `integrity` uses UAAPS `sha256-<hex>` format (matches spec). Atomic write prevents partial lock files on crash. `systemChecks` records last verified state for `--frozen` installs.

**Alternatives considered**:
- Keep YAML format — spec requires JSON for lock files; also faster to parse
- Use `orjson` for speed — stdlib `json` is sufficient for the size of lock files expected; no new dependency

---

## R-006: `aam audit` v1 Scope

**Question**: What does `aam audit` check and how does it work offline?

**Decision**: Two-tier approach:
1. **Always (local)**: Re-verify SHA-256 hashes of installed archives against `package.agent.lock` integrity hashes. Reports any hash mismatches as `CRITICAL` findings.
2. **Optional (network)**: If an HTTP registry is configured, call `GET /packages/{name}/advisories` to fetch known vulnerability reports. Gracefully skips if no network or no HTTP registry.

**Rationale**: Local integrity check always works offline (Constitution I — Local-First). It catches tampered packages. The network advisory lookup extends coverage but is strictly optional. No third-party advisory DB dependency needed for v1.

**Alternatives considered**:
- Ship an embedded advisory JSON file with the CLI — maintenance burden; becomes stale immediately
- Require network for audit — violates Local-First principle; `--frozen` CI environments would break

---

## R-007: Governance Glob Pattern Matching for `blocked_packages`

**Question**: How should `blocked_packages` glob patterns be matched against package names?

**Decision**: `fnmatch.fnmatchcase()` for exact pattern matching. Case-sensitive to match package name rules. Document the pattern syntax in `--help`.

**Examples**:
- `"@sketchy/*"` blocks all packages in `@sketchy` scope
- `"malicious-*"` blocks all packages starting with `malicious-`
- `"@org/bad-pkg"` blocks an exact package name

**Rationale**: `fnmatch` is stdlib, well-understood (same as shell globbing), and is already used throughout the codebase. Case-sensitive is correct for package names (UAAPS names are lowercase only).

**Alternatives considered**:
- Regex matching — too powerful/confusing for configuration; security risk if patterns are user-controlled
- Exact string matching only — too rigid; `@sketchy/*` is a natural and necessary pattern

---

## R-008: `env` Variable Prompting Security

**Question**: How do we securely prompt for environment variables during install?

**Decision**: Use `click.prompt(hide_input=True)` for required env vars. Store the value in the process environment (`os.environ`) for the duration of the install only. Do not write to disk. Display a summary table of all required vars before prompting.

**Rationale**: `click.prompt(hide_input=True)` masks terminal input (like password fields). Storing only in process env avoids writing secrets to config files. The user controls persistence via their own shell profile if needed.

**Alternatives considered**:
- Write to `.aam/env.yaml` — unacceptable: plaintext secrets on disk; security violation
- Use `keyring` library — adds a dependency; varies by OS; overengineered for v1

---

## R-009: MCP Config Merge Strategy for `deploy_mcp`

**Question**: How do we merge MCP server configs from multiple packages without collisions?

**Decision**: Namespace server keys by package name: `<scope>--<pkg-name>/<server-name>` in the merged config. Example: `my-org--code-review/my-service`. During uninstall, remove all keys matching the package prefix.

**Rationale**: Server key namespacing mirrors the UAAPS skill namespacing convention. Prevents package A's `my-service` from overwriting package B's `my-service`. Reversal on uninstall is clean and deterministic.

**Alternatives considered**:
- Last-write-wins — silently drops servers from previously installed packages
- Per-package MCP config files sourced by the host config — requires host platform support, not universally available

---

## R-010: Install Directory Migration Strategy

**Question**: How do we migrate from `.aam/packages/` to `.agent-packages/`?

**Decision**: On first `aam install` or `aam check` after upgrade, detect `.aam/packages/` with contents. Prompt: "Found legacy install directory `.aam/packages/` with N packages. Migrate to `.agent-packages/`? [y/N]". If yes: `shutil.move()`, update lock file path, success message. If no: continue using old directory for this session but warn again next time.

**Rationale**: Explicit user consent required (Constitution VII — No Defensive Fallbacks). The migration is reversible (user can move files back). No data is lost in either path.

**Alternatives considered**:
- Auto-migrate silently — violates No Defensive Fallbacks; surprises users
- Support both directories simultaneously — complex state management; confusing
