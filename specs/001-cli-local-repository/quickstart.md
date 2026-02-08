# Quickstart: CLI Local Repository Development

**Branch**: `001-cli-local-repository` | **Date**: 2026-02-08

## Prerequisites

- Python 3.11+
- Node.js 20+ (for Nx)
- Git

## Setup

### 1. Clone and switch to the feature branch

```bash
git clone <repo-url>
cd agent-package-manager
git checkout 001-cli-local-repository
```

### 2. Install Node dependencies (Nx workspace)

```bash
npm install
```

### 3. Set up the CLI project

```bash
cd apps/aam-cli

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify the CLI works
aam --version
# aam 0.1.0
```

### 4. Verify the development environment

```bash
# Run existing tests
pytest

# Run linter
ruff check src/ tests/

# Run type checker
mypy src/aam_cli/

# Run formatter check
ruff format --check src/ tests/
```

## Development Workflow

### Running the CLI during development

```bash
# The `aam` command is available after `pip install -e .`
aam --help
aam registry init ~/test-registry
aam config set default_platform cursor
```

### Running tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_unit_manifest.py

# With coverage report
pytest --cov=src/aam_cli --cov-report=term-missing

# Via Nx
npx nx test aam-cli
```

### Linting and formatting

```bash
# Check lint
ruff check src/ tests/

# Auto-fix lint issues
ruff check --fix src/ tests/

# Check formatting
ruff format --check src/ tests/

# Auto-format
ruff format src/ tests/

# Type checking
mypy src/aam_cli/
```

## Testing a Full Local Workflow

Once the implementation is complete, verify the end-to-end workflow:

```bash
# 1. Create a local registry
aam registry init /tmp/test-registry
aam registry add local file:///tmp/test-registry --default

# 2. Set up a test package
mkdir /tmp/test-pkg && cd /tmp/test-pkg
mkdir -p skills/my-skill
echo "---
name: my-skill
description: A test skill
---
# My Skill
Hello world" > skills/my-skill/SKILL.md

# 3. Initialize package
aam init my-test-package
# (follow prompts or use: aam init my-test-package --non-interactive flags)

# 4. Validate
aam validate

# 5. Pack
aam pack

# 6. Publish
aam publish --registry local

# 7. Search
aam search "test"

# 8. Install in a different project
mkdir /tmp/consumer && cd /tmp/consumer
aam install my-test-package

# 9. Verify deployment
ls -la .cursor/skills/
ls -la .aam/packages/

# 10. List installed
aam list

# 11. Uninstall
aam uninstall my-test-package
```

## Key Files to Understand

| File | Purpose |
|------|---------|
| `src/aam_cli/main.py` | CLI entry point, Click group, command registration |
| `src/aam_cli/utils/naming.py` | Package name parsing and validation (complete) |
| `src/aam_cli/core/manifest.py` | Pydantic models for `aam.yaml` |
| `src/aam_cli/core/config.py` | Configuration loading with precedence |
| `src/aam_cli/registry/local.py` | Local filesystem registry implementation |
| `src/aam_cli/adapters/cursor.py` | Cursor platform deployment |
| `src/aam_cli/core/resolver.py` | Dependency resolution algorithm |
| `src/aam_cli/core/installer.py` | Install orchestration |

## New Dependency

Add to `pyproject.toml` dependencies:

```toml
"pyyaml>=6.0.0",
```

This is the only new runtime dependency needed. All other required libraries (Click, Rich, Pydantic, packaging) are already declared.

## Module Implementation Order

Follow this order to minimize blocking dependencies:

1. **Layer 0** (utilities): `utils/yaml_utils.py`, `utils/checksum.py`, `utils/paths.py`, `utils/archive.py`
2. **Layer 1** (core models): `core/version.py`, `core/manifest.py`, `core/config.py`, `core/workspace.py`
3. **Layer 2** (interfaces): `registry/base.py`, `adapters/base.py`, `detection/scanner.py`
4. **Layer 3** (implementations): `registry/local.py`, `registry/factory.py`, `adapters/cursor.py`
5. **Layer 4** (orchestration): `core/resolver.py`, `core/installer.py`
6. **Layer 5** (commands): All command modules under `commands/`

Write unit tests alongside each module (red-green-refactor for critical paths).
