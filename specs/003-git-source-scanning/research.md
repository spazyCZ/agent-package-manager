# Research: Git Repository Source Scanning & Artifact Discovery

**Feature**: 003-git-source-scanning | **Date**: 2026-02-08

## R-001: Git Operations via Subprocess

**Decision**: Use `subprocess.run()` to invoke system `git` rather than a Python git library (GitPython, dulwich, pygit2).

**Rationale**:
- The AAM CLI already assumes `git` on PATH (stated in spec assumptions).
- Subprocess approach is simpler, has zero additional dependencies, and supports all needed operations: `clone --depth 1`, `fetch`, `rev-parse`, `diff --name-only`, `log --oneline`.
- GitPython has known security concerns and complexity overhead for simple operations.
- dulwich/pygit2 are large dependencies for a CLI tool that only needs 5-6 git commands.

**Alternatives considered**:
- **GitPython**: Large dependency, GIL issues, security advisory history. Rejected.
- **dulwich**: Pure Python, no system git dependency. Adds ~2MB. Rejected because AAM already requires system git.
- **pygit2**: C library bindings, complex installation. Rejected for installation friction.

**Implementation pattern**:
```python
def _run_git(args: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a git command via subprocess with validation."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise GitOperationError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result
```

---

## R-002: URL Parsing Strategy

**Decision**: Use regex-based URL parsing with a dedicated `GitSourceURL` dataclass to decompose URLs into components.

**Rationale**:
- The reference document (`docs/work/git_repo_skills.md` Section 4.1.1) provides explicit regex patterns and decomposition rules.
- URL formats are well-defined: HTTPS, SSH, `git+https://`, tree URLs, shorthand.
- A dataclass provides type-safe access to parsed components (host, owner, repo, ref, path).
- `urllib.parse` is insufficient for git-specific formats (SSH, shorthand).

**Alternatives considered**:
- **urllib.parse only**: Cannot handle `git@host:owner/repo.git` or shorthand. Rejected.
- **Third-party URL parser**: No git-specific library exists. Rejected.
- **String splitting**: Fragile, hard to maintain. Rejected.

**Key patterns from reference doc**:
```
# GitHub tree URL regex
^https?://(github\.com|gitlab\.com)/(?P<owner>[^/]+)/(?P<repo>[^/]+)(/tree/(?P<ref>[^/]+)(/(?P<path>.+))?)?$

# Shorthand patterns
{owner}/{repo}           → https://github.com/{owner}/{repo}, ref=main
{owner}/{repo}@{branch}  → https://github.com/{owner}/{repo}, ref={branch}
{owner}/{repo}#{sha}     → https://github.com/{owner}/{repo}, ref={sha}
```

---

## R-003: Artifact Scanner Extension Strategy

**Decision**: Extend the existing `detection/scanner.py` with a new `scan_directory()` function that reuses detection patterns but adds remote-specific handling (dot-prefixed directories, vendor agent files).

**Rationale**:
- The existing scanner in `detection/scanner.py` handles local project scanning with `os.walk()` and pattern matching.
- Remote repositories use different conventions (dot-prefixed category dirs, vendor agent files in `agents/openai.yaml`).
- Extending rather than replacing preserves backward compatibility with `aam create-package`.
- The key difference: remote scanning must NOT skip dot-prefixed directories (unlike typical glob behavior).

**Alternatives considered**:
- **Separate scanner class**: More isolation but code duplication. Rejected — patterns overlap significantly.
- **Pluggable strategy pattern**: Over-engineered for 2 scan modes (local vs remote). Rejected.
- **Configuration-driven exclusions**: Pass exclusion lists as parameters instead of hardcoding. **Adopted** — the scanner will accept an `exclude_dirs` parameter.

**Critical implementation note** (from reference doc Section 5.2.2):
> Use `os.walk()` — do NOT use `pathlib.Path.glob()` on Python < 3.12 which skips dot-dirs unless paired with explicit dot patterns.

---

## R-004: Cache Directory Strategy

**Decision**: Cache cloned repositories under `~/.aam/cache/git/{host}/{owner}/{repo}/` with shared clones across multiple sources.

**Rationale**:
- The reference document specifies this exact structure (Section 5.1).
- Multiple sources can point to the same repository with different `path` scopes (e.g., `openai/skills:.curated` and `openai/skills:.experimental`).
- Sharing one clone saves disk space and clone time.
- The `{host}` prefix prevents collisions between github.com, gitlab.com, and self-hosted instances.

**Alternatives considered**:
- **Hash-based cache keys**: Deterministic but opaque, hard to inspect/debug. Rejected.
- **Flat cache directory**: Name collisions with `owner/repo` across hosts. Rejected.
- **Per-source clones**: Wastes disk when multiple sources target same repo. Rejected.

**Cache lifecycle**:
1. `source add` → shallow clone to cache if not exists
2. `source update` → `git fetch` in existing cache
3. `source remove --purge-cache` → delete cache only if no other sources use it
4. Corrupt cache → detect via `git status`, delete and re-clone

---

## R-005: Change Detection Between Commits

**Decision**: Use `git diff --name-status <old-sha>..<new-sha>` within the path scope to detect new, modified, and deleted files, then re-run artifact detection on affected paths.

**Rationale**:
- Git's built-in diff is the most efficient way to detect changes between two commits.
- The `--name-status` flag gives A (added), M (modified), D (deleted) status per file.
- Filtering by path scope (the source's `path` field) ensures only relevant changes are reported.
- Re-running the scanner on the new commit and comparing artifact lists gives the final new/modified/removed artifact report.

**Alternatives considered**:
- **Full re-scan on every update**: Simple but slow for large repos. Rejected for performance.
- **File hash comparison**: Would require storing hashes for every scanned file. Over-engineered. Rejected.
- **Git log parsing**: Less reliable than diff. Rejected.

**Implementation sketch**:
```python
# Get changed files between old and new commit
result = _run_git(["diff", "--name-status", f"{old_sha}..{new_sha}", "--", path_scope], cwd=cache_dir)

# Parse output: "A\tpath/to/file.md" → added, "M\tpath" → modified, etc.
# Re-scan to get current artifacts
# Compare with stored artifacts from last scan
```

---

## R-006: Checksum Storage and Verification

**Decision**: Extend `LockedPackage` in `core/workspace.py` with a `file_checksums` field containing per-file SHA-256 hashes. The existing `utils/checksum.py` is extended to support file-map operations.

**Rationale**:
- The lock file (`aam-lock.yaml`) is the natural location for integrity metadata — it already stores package-level checksums.
- Per-file checksums enable targeted verification (identify exactly which files changed).
- SHA-256 is already used for package-level checksums in the existing codebase.
- The existing `checksum.py` utility handles single-file checksums — needs extension for directory-level operations.

**Alternatives considered**:
- **Separate checksum manifest file**: Additional file to manage. Rejected — lock file is simpler.
- **Store checksums in aam.yaml**: Manifest is the author's file, not installation metadata. Rejected.
- **Use git hashes**: Ties integrity to git internals. Rejected — packages may not come from git.

**Lock file extension (from reference doc Section 4.4.2)**:
```yaml
packages:
  "@myorg/my-agent":
    version: 1.0.0
    source: local
    checksum: sha256:abc123...
    dependencies:
      generic-auditor: 1.2.3
    file_checksums:               # NEW
      algorithm: sha256
      files:
        skills/my-skill/SKILL.md: "e3b0c44..."
        agents/my-agent/agent.yaml: "f6e5d4..."
```

---

## R-007: Backup Strategy for Upgrade Safety

**Decision**: Before overwriting modified files during upgrade, copy them to `~/.aam/backups/<package-fs-name>--<iso-date>/` preserving directory structure.

**Rationale**:
- Users expect package managers to protect their customizations (npm, pip, etc. all warn or preserve).
- A timestamped backup directory allows users to recover changes after upgrade.
- Using the filesystem-safe package name (`scope--name`) avoids path issues.
- The backup is opt-in during interactive upgrades and skipped with `--force`.

**Alternatives considered**:
- **Git stash-like approach**: Requires git in the project directory, which may not exist. Rejected.
- **Side-by-side `.bak` files**: Pollutes the working directory. Rejected.
- **Diff patch files**: Harder for users to apply manually. Rejected.

---

## R-008: Service Layer Architecture

**Decision**: Create 3 new service modules following the pattern established by spec 002: `source_service.py`, `checksum_service.py`, and `git_service.py`. Services are pure functions returning dicts, with no CLI or Rich dependencies.

**Rationale**:
- Spec 002 establishes the service layer pattern: extract business logic from Click handlers into reusable services.
- Services are consumed by both CLI commands and MCP tools.
- Pure functions returning dicts are easy to test and serialize to JSON.
- Three services provide clean separation: git operations, source management, checksum verification.

**Alternatives considered**:
- **Single monolithic service**: Too large, violates 600-line limit. Rejected.
- **Class-based services**: Unnecessary statefulness for functional operations. Rejected.
- **Direct CLI-to-core**: Skips service layer, duplicates logic for MCP. Rejected.

---

## R-009: Vendor Agent File Handling

**Decision**: Detect `agents/*.yaml` inside skill directories as companion metadata, not standalone agents. Report as "skill: {name} (with {vendor} agent interface)". During `create-package --from-source`, optionally map vendor fields to AAM `agent.yaml`.

**Rationale**:
- The `openai/skills` repository uses `agents/openai.yaml` inside skill directories — these are vendor-specific agent interface definitions, not AAM agents.
- Treating them as standalone agents would pollute the artifact list with non-portable definitions.
- The heuristic is simple: if `SKILL.md` AND `agents/*.yaml` exist in the same directory → companion metadata.

**Implementation heuristic** (from reference doc Section 5.2.3):
```
IF dir has SKILL.md AND agents/*.yaml → companion metadata (reported with skill)
IF dir has agents/*.yaml WITHOUT SKILL.md → standalone agent
```

---

## R-010: Default Source Registration

**Decision**: Default sources are registered during `aam init` by checking if `sources:` key exists in config. Removed defaults are tracked in `removed_defaults:` list to prevent re-addition.

**Rationale**:
- Default sources provide a polished out-of-box experience.
- The `removed_defaults` tracking prevents the annoying pattern where a removed default reappears on upgrade.
- Checking for the existence of the `sources:` key (not just an empty list) ensures we don't add defaults to a user who explicitly has an empty list.

**Default sources** (from reference doc Section 4.1.5):
1. `github/awesome-copilot` — `https://github.com/github/awesome-copilot`, path: `skills`
2. `openai/skills:.curated` — `https://github.com/openai/skills`, path: `skills/.curated`

---

## R-011: Exponential Backoff for Network Operations

**Decision**: Use a simple retry loop with 3 attempts and delays of 1s, 2s, 4s for git network operations.

**Rationale**:
- The reference doc specifies 3 attempts with 1s/2s/4s delays (Section 6.1).
- A simple loop is sufficient — no need for a retry library.
- After all retries fail, fall back to cached version if available (for `update`), or fail with clear error (for `add`).

**Implementation**:
```python
RETRY_DELAYS = [1, 2, 4]  # seconds

for attempt, delay in enumerate(RETRY_DELAYS):
    try:
        return _run_git(args, cwd=cache_dir)
    except GitOperationError:
        if attempt == len(RETRY_DELAYS) - 1:
            raise
        time.sleep(delay)
```
