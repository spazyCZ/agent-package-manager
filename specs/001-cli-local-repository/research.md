# Research: CLI Local Repository

**Branch**: `001-cli-local-repository` | **Date**: 2026-02-08

## Overview

This document resolves all technical unknowns identified during the Technical Context phase of the implementation plan. Each section documents the decision, rationale, and alternatives considered.

---

## R-001: YAML Library Choice

**Decision**: Use **PyYAML 6.0+** with `yaml.safe_load()` / `yaml.safe_dump()`.

**Rationale**: PyYAML is the de facto standard for YAML in Python. It is well-maintained, widely used (pytest, Ansible, Docker Compose all depend on it), and has a safe loading API that prevents arbitrary code execution. The `safe_load` / `safe_dump` functions handle all YAML types needed by AAM manifests (strings, lists, dicts, numbers, booleans, timestamps).

**Alternatives Considered**:
- **ruamel.yaml**: Preserves YAML comments and formatting. More complex API. Overkill for AAM where we control the YAML format and don't need round-trip comment preservation.
- **strictyaml**: Type-safe YAML that rejects implicit typing. Interesting but adds a non-standard dependency and the validation already happens in Pydantic.

**Integration**: Wrapped in `utils/yaml_utils.py` with helpers `load_yaml(path)` and `dump_yaml(data, path)` that handle `FileNotFoundError`, `yaml.YAMLError`, and ensure `safe_load`/`safe_dump` are always used.

---

## R-002: Archive Format and Checksum

**Decision**: Use Python's built-in `tarfile` module with gzip compression. Calculate SHA-256 using `hashlib`.

**Rationale**: Both `tarfile` and `hashlib` are part of the Python standard library — zero additional dependencies. The `.aam` format is defined as a gzipped tar archive in DESIGN.md Section 3.4. SHA-256 is the industry standard for package integrity verification (used by pip, npm, cargo).

**Alternatives Considered**:
- **zipfile**: Simpler API but doesn't preserve Unix file permissions. Tar+gz is the convention for most package managers (pip, cargo).
- **External tools (gzip CLI)**: Would add a system dependency. Pure Python is more portable.

**Implementation**:
- `utils/archive.py`: `create_archive(source_dir, output_path)` and `extract_archive(archive_path, dest_dir)`
- `utils/checksum.py`: `calculate_sha256(file_path)` and `verify_sha256(file_path, expected)`
- Archive creation validates: no symlinks outside package dir, no absolute paths, total size < 50 MB.

---

## R-003: Semver Constraint Matching

**Decision**: Use the **`packaging`** library (already a dependency) for version parsing and comparison.

**Rationale**: The `packaging` library is the Python standard for PEP 440 version handling and is already declared in `pyproject.toml`. While PEP 440 and semver have minor differences, `packaging.version.Version` handles all the version formats AAM uses (e.g., `1.0.0`, `1.0.0-beta.1`).

**Implementation**: `core/version.py` wraps `packaging.version.Version` and implements custom constraint matching for AAM's version constraint syntax:
- `1.0.0` → exact match
- `>=1.0.0` → minimum version
- `^1.0.0` → compatible (>=1.0.0, <2.0.0)
- `~1.0.0` → approximate (>=1.0.0, <1.1.0)
- `*` → any version
- `>=1.0.0,<2.0.0` → range (comma-separated)

The `^` (caret) and `~` (tilde) operators are not native to PEP 440, so we implement them as range conversions:
- `^1.2.3` → `>=1.2.3, <2.0.0` (bump major)
- `^0.2.3` → `>=0.2.3, <0.3.0` (bump minor when major is 0)
- `~1.2.3` → `>=1.2.3, <1.3.0` (bump minor)

**Alternatives Considered**:
- **semver** (pypi package): Pure semver implementation. Would add a dependency for something `packaging` already handles with minor custom logic.
- **node-semver** (python port): More complete npm-style semver, but an unnecessary dependency.

---

## R-004: Fuzzy Search Strategy for Local Registry

**Decision**: Simple case-insensitive substring matching on name, description, and keywords.

**Rationale**: For a local registry with up to ~100 packages, fuzzy matching algorithms (Levenshtein distance, TF-IDF) are overkill. Substring matching is fast, predictable, and sufficient for the scale. Users type `aam search "audit"` and expect packages with "audit" in the name, description, or keywords.

**Implementation**:
```python
def search(query: str, index: list[PackageIndexEntry]) -> list[PackageIndexEntry]:
    query_lower = query.lower()
    return [
        entry for entry in index
        if query_lower in entry.name.lower()
        or query_lower in entry.description.lower()
        or any(query_lower in kw.lower() for kw in entry.keywords)
    ]
```

**Alternatives Considered**:
- **fuzzywuzzy / rapidfuzz**: Levenshtein-based fuzzy matching. Good for typo tolerance but adds a dependency and is unnecessary at this scale.
- **whoosh**: Full-text search engine. Way too heavy for a local YAML index.

---

## R-005: Interactive Terminal UI for `create-package`

**Decision**: Use **Rich** prompts and manual keyboard handling for interactive selection.

**Rationale**: Rich is already a dependency and provides `Prompt`, `Confirm`, `Table`, and `Console` APIs. For the checkbox-style artifact selection in `create-package`, we use `rich.prompt.Prompt` with numbered selection rather than implementing a full TUI with cursor movement, since Rich doesn't have native checkbox widgets.

**Implementation approach**:
1. Display detected artifacts in a numbered table using `rich.table.Table`
2. Use `rich.prompt.Prompt` to ask the user to enter numbers to toggle selection (e.g., "Toggle selection (space-separated numbers, 'a' for all, enter to confirm): ")
3. Use `rich.prompt.Confirm` for yes/no prompts
4. Non-interactive mode (`--all --yes`) bypasses all prompts

**Alternatives Considered**:
- **questionary**: Full interactive prompt library with checkboxes. Would add a dependency for a single use case.
- **InquirerPy**: Rich-compatible prompt library. Adds a dependency.
- **textual**: Full TUI framework from the Rich team. Far too heavy for this use case.

---

## R-006: Configuration File Format and Library

**Decision**: Use YAML for config files with PyYAML (same as registry/manifest files).

**Rationale**: Consistency — all AAM data files (manifests, registry metadata, lock files, config) use YAML. A single serialization format reduces cognitive load and dependency count.

**Config locations**:
- Global: `~/.aam/config.yaml`
- Project: `.aam/config.yaml`
- Credentials: `~/.aam/credentials.yaml` (chmod 600, out of scope for this feature)

**Implementation**: `core/config.py` loads both files, merges with project taking precedence, and provides a typed `AamConfig` Pydantic model with sensible defaults.

**Alternatives Considered**:
- **TOML**: More structured, used by `pyproject.toml`. But YAML is already the AAM ecosystem format.
- **JSON**: No comments support, less readable for human-edited config.
- **INI**: Too limited for nested structures (registries list, platform config).

---

## R-007: Lock File Format

**Decision**: YAML format following the schema defined in DESIGN.md Section 7.3.

**Rationale**: Consistency with all other AAM data files. The lock file is human-readable (for debugging) but machine-managed (users don't edit it). YAML handles the nested structure (packages → versions → checksums → dependencies) cleanly.

**Location**: `.aam/aam-lock.yaml`

**Implementation**: `core/workspace.py` manages reading/writing the lock file. The lock file is written after every successful `install` operation and read during `install` to check for already-resolved versions.

---

## R-008: Cursor Adapter — Agent to .mdc Conversion

**Decision**: Generate `.mdc` files with YAML frontmatter following Cursor's rule format.

**Rationale**: Cursor rules use `.mdc` files with YAML frontmatter (`description`, `globs`, `alwaysApply`). The DESIGN.md Section 8.1 specifies the conversion format. Agent system prompts are wrapped in an `.mdc` rule with `alwaysApply: true`.

**Conversion templates**:

Agent → Rule:
```markdown
---
description: "{agent.description}"
alwaysApply: true
---

# Agent: {agent.name}

{system-prompt.md contents}

## Available Skills
{list of skills from agent.yaml}

## Available Prompts
{list of prompts from agent.yaml}
```

Instruction → Rule:
```markdown
---
description: "{instruction.description}"
globs: {instruction.globs if defined}
alwaysApply: {true if no globs, false if globs defined}
---

{instruction body}
```

---

## R-009: Artifact Detection Patterns

**Decision**: Implement the detection patterns exactly as specified in DESIGN.md Section 5.2 and USER_GUIDE.md Section 2.3.

**Detection rules (in order of specificity)**:

| Artifact Type | Pattern | Source |
|---------------|---------|--------|
| Skill | `**/SKILL.md` (parent dir is the skill) | Any project |
| Skill | `.cursor/skills/*/SKILL.md` | Cursor convention |
| Skill | `.codex/skills/*/SKILL.md` | Codex convention |
| Agent | `**/agent.yaml` | AAM convention |
| Agent | `.cursor/rules/agent-*.mdc` | Cursor convention |
| Prompt | `prompts/*.md` | AAM convention |
| Prompt | `.cursor/prompts/*.md` | Cursor convention |
| Prompt | `.github/prompts/*.md` | Copilot convention |
| Instruction | `instructions/*.md` | AAM convention |
| Instruction | `.cursor/rules/*.mdc` (non-agent) | Cursor convention |
| Instruction | `CLAUDE.md` | Claude convention |
| Instruction | `AGENTS.md` | Codex convention |
| Instruction | `.github/copilot-instructions.md` | Copilot convention |

**Exclusion directories**: `.aam/packages/`, `node_modules/`, `.venv/`, `__pycache__/`, `.git/`

**Implementation**: `detection/scanner.py` with a `scan_project(root: Path) -> list[DetectedArtifact]` function that returns typed results.

---

## R-010: Dependency on Existing Naming Utilities

**Decision**: Reuse `utils/naming.py` as-is. It is complete and tested.

**Rationale**: The naming module already implements all required functions: `parse_package_name`, `validate_package_name`, `format_package_name`, `to_filesystem_name`, `parse_package_spec`. The regex patterns match both CLI and backend conventions. No changes needed.

---

## Summary of Resolved Unknowns

| ID | Unknown | Resolution |
|----|---------|-----------|
| R-001 | YAML library | PyYAML 6.0+ with safe_load/safe_dump |
| R-002 | Archive + checksum | stdlib tarfile + hashlib (SHA-256) |
| R-003 | Semver constraints | `packaging` library + custom ^/~ operators |
| R-004 | Search strategy | Case-insensitive substring matching |
| R-005 | Interactive UI | Rich prompts with numbered selection |
| R-006 | Config format | YAML (consistent with ecosystem) |
| R-007 | Lock file format | YAML per DESIGN.md schema |
| R-008 | Cursor .mdc conversion | YAML frontmatter + markdown body |
| R-009 | Detection patterns | Per DESIGN.md + USER_GUIDE.md |
| R-010 | Naming utilities | Reuse existing utils/naming.py |

All NEEDS CLARIFICATION items resolved. No outstanding unknowns.
