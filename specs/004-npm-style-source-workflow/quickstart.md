# Quickstart: npm-Style Source Workflow

**Feature Branch**: `004-npm-style-source-workflow`
**Prerequisites**: Spec 001 (CLI), Spec 002 (MCP), Spec 003 (Source Scanning) completed

---

## Consumer Quickstart — Install from Sources

### 1. Initialize AAM (first time only)

```bash
aam init
```

Follow the interactive prompts:
- Select your AI platform (Cursor, Copilot, Claude, Codex)
- Optionally create a local registry
- Add community artifact sources

Or use defaults non-interactively:

```bash
aam init --yes
```

### 2. Add a source and refresh

```bash
aam source add openai/skills
aam source update
```

### 3. Browse available packages

```bash
aam list --available
aam search code-review
```

### 4. Install directly from source

```bash
aam install code-review
```

That's it — the artifact is installed and deployed to your AI platform.

### 5. Check for updates

```bash
aam outdated
```

### 6. Upgrade packages

```bash
aam upgrade                    # upgrade all
aam upgrade code-review        # upgrade specific
aam upgrade --dry-run          # preview changes
```

---

## Creator Quickstart — Package Authoring

All authoring commands now use the `aam pkg` prefix:

```bash
aam pkg init my-skill          # scaffold a new package
aam pkg create                 # create from existing artifacts
aam pkg validate               # validate manifest
aam pkg pack                   # build .aam archive
aam pkg publish                # publish to registry
```

Old root-level commands (`aam create-package`, `aam validate`, etc.) still work but print deprecation warnings.

---

## Key Differences from Spec 003

| Before (5 steps) | After (2 steps) |
|-------------------|------------------|
| `aam source add openai/skills` | `aam source add openai/skills` |
| `aam source scan openai/skills` | `aam install code-review` |
| `aam source candidates` | |
| `aam create-package --from-source` | |
| `aam install ./my-package` | |

---

## Development Setup

### Run tests

```bash
cd apps/aam-cli
npx nx test aam-cli
```

### Run specific test files

```bash
cd apps/aam-cli
python -m pytest tests/unit/test_unit_outdated.py -v
python -m pytest tests/unit/test_unit_upgrade.py -v
python -m pytest tests/unit/test_unit_install_from_source.py -v
python -m pytest tests/unit/test_unit_client_init.py -v
python -m pytest tests/unit/test_unit_pkg_group.py -v
python -m pytest tests/unit/test_unit_help_grouping.py -v
```

### Run linting

```bash
cd apps/aam-cli
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/
```

---

## Architecture Notes

### Resolution Order

When you run `aam install <name>`:
1. Registry lookup (all configured registries, in order)
2. Source index lookup (all sources, in order)
3. Qualified name override: `aam install openai/skills/code-review`

### Lock File

Source-installed packages record provenance:

```yaml
packages:
  code-review:
    version: "0.0.0"
    source: "openai/skills"
    checksum: "sha256:abc..."
    source_name: "openai/skills"        # NEW
    source_commit: "abc123def456..."     # NEW
    file_checksums:
      algorithm: sha256
      files:
        skills/code-review/SKILL.md: "def456..."
```

### MCP Tools

Three new MCP tools:
- `aam_outdated` (read) — check for updates
- `aam_available` (read) — list installable artifacts
- `aam_upgrade` (write, gated by `--allow-write`) — upgrade packages
