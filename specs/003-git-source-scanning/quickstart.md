# Developer Quickstart: Git Source Scanning Implementation

**Feature**: 003-git-source-scanning | **Date**: 2026-02-08

## Prerequisites

- Python 3.11+
- `git` on PATH
- Node.js 20+ (for Nx)
- Working `apps/aam-cli/` development environment

## Setup

```bash
# Clone and enter the repo
cd /data/projects/code_workspace/agent-package-manager

# Install workspace dependencies
npm install

# Set up CLI virtual environment
cd apps/aam-cli
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Verify tests pass
npx nx test aam-cli
```

## Key Files to Understand First

Read these files in order to build context:

1. **Reference document** (implementation details): `docs/work/git_repo_skills.md`
2. **Spec**: `specs/003-git-source-scanning/spec.md`
3. **Existing scanner**: `apps/aam-cli/src/aam_cli/detection/scanner.py`
4. **Config model**: `apps/aam-cli/src/aam_cli/core/config.py`
5. **Lock file model**: `apps/aam-cli/src/aam_cli/core/workspace.py`
6. **Manifest model**: `apps/aam-cli/src/aam_cli/core/manifest.py`
7. **Checksum utility**: `apps/aam-cli/src/aam_cli/utils/checksum.py`
8. **CLI entry point**: `apps/aam-cli/src/aam_cli/main.py`

## Implementation Order

### Phase 1: Foundation (no git operations)

Start with the models and utilities that don't require network:

1. **`utils/git_url.py`** — URL parsing and validation
   - Test first: `tests/unit/test_unit_git_url.py`
   - Parse shorthand, HTTPS, SSH, tree URLs
   - Validate URL schemes

2. **Extend `core/config.py`** — Add `SourceEntry` model and `sources` to `AamConfig`
   - Test: verify YAML serialization roundtrip

3. **Extend `core/workspace.py`** — Add `FileChecksums` to `LockedPackage`
   - Test: verify backward compatibility (old lock files without checksums)

4. **Extend `core/manifest.py`** — Add `Provenance` model
   - Test: verify YAML serialization

### Phase 2: Scanner Extension

5. **Extend `detection/scanner.py`** — Add remote scanning support
   - Key change: dot-prefixed directory handling
   - Key change: vendor agent file detection
   - Test: mock directory structures matching `openai/skills` layout

### Phase 3: Services

6. **`services/git_service.py`** — Git subprocess wrapper
   - `clone_shallow()`, `fetch()`, `get_head_sha()`, `diff_names()`
   - Test with mocked subprocess

7. **`services/source_service.py`** — Source management logic
   - `add_source()`, `list_sources()`, `remove_source()`, `scan_source()`, `update_source()`, `list_candidates()`
   - Test with mocked git_service

8. **`services/checksum_service.py`** — Verification and diff logic
   - `verify_package()`, `diff_package()`, `check_modifications()`, `backup_files()`
   - Test with temp directories

### Phase 4: CLI Commands

9. **`commands/source.py`** — Source command group
   - Wire up Click commands to services
   - Rich output formatting

10. **`commands/verify.py`** — Verify command
11. **`commands/diff.py`** — Diff command
12. **Extend `commands/create_package.py`** — Add `--from-source` flag
13. **Extend `commands/install.py`** — Add upgrade warning

### Phase 5: MCP Tools (depends on spec 002)

14. **Extend `mcp/tools_read.py`** — Add source tools
15. **Extend `mcp/tools_write.py`** — Add source write tools
16. **Extend `mcp/resources.py`** — Add `aam://sources/*` resources

### Phase 6: Documentation

17. **Update `docs/USER_GUIDE.md`** — New commands
18. **Update `docs/DESIGN.md`** — New `aam source` group, checksum extension
19. **CLI `--help` text** — All new commands

## Running Tests

```bash
# All tests
npx nx test aam-cli

# Unit tests only
cd apps/aam-cli
pytest tests/unit/ -v

# Specific test file
pytest tests/unit/test_unit_git_url.py -v

# With coverage
pytest tests/ --cov=src/aam_cli --cov-report=term-missing
```

## Testing a Source Locally

For integration testing without hitting real GitHub:

```bash
# Create a local bare repo mimicking openai/skills layout
mkdir -p /tmp/test-source/skills/.curated/gh-fix-ci
echo "# GH Fix CI" > /tmp/test-source/skills/.curated/gh-fix-ci/SKILL.md
mkdir -p /tmp/test-source/skills/.curated/playwright
echo "# Playwright" > /tmp/test-source/skills/.curated/playwright/SKILL.md

cd /tmp/test-source
git init && git add . && git commit -m "init"

# Use local path as source in tests
# The git_service should accept file:// URLs for local bare repos
```

## Architecture Decisions

See `research.md` for detailed rationale on:
- R-001: Why subprocess over GitPython
- R-002: Regex-based URL parsing
- R-003: Scanner extension vs replacement
- R-004: Cache directory structure
- R-005: Git diff for change detection
- R-006: Per-file checksums in lock file
- R-007: Backup strategy for upgrades
- R-008: Service layer architecture
- R-009: Vendor agent file handling
- R-010: Default source registration
