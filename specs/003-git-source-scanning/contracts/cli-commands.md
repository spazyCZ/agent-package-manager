# CLI Command Contracts: Git Source Scanning & Artifact Discovery

**Feature**: 003-git-source-scanning | **Date**: 2026-02-08

## Command Group: `aam source`

All source management commands are grouped under `aam source`.

**Registration** (in `main.py`):
```python
cli.add_command(source.source)  # Click group
```

---

### `aam source add <source>`

Register a remote git repository as an artifact source.

**Signature**:
```
aam source add <source> [--ref REF] [--path PATH] [--name NAME]
```

**Arguments**:

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `source` | str | Yes | Git source: shorthand, HTTPS URL, SSH URL, or tree URL |

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--ref` | str | `main` | Git reference (branch, tag, or commit SHA) |
| `--path` | str | `""` | Subdirectory within repo to scope scanning |
| `--name` | str | auto | Custom display name (default: derived from URL) |

**Exit codes**:

| Code | Condition |
|------|-----------|
| 0 | Source added successfully |
| 1 | Source already exists (suggests `aam source update`) |
| 1 | Git clone failed (network, auth, invalid URL) |
| 1 | URL validation failed (disallowed scheme) |

**Service call**: `source_service.add_source(source, ref, path, name) -> dict`

**Output format** (Rich console):
```
Adding git source 'openai/skills'...
  Repository: https://github.com/openai/skills
  Ref:        main
  Cloning (shallow)...

✓ Source added: openai/skills
  Cached at: ~/.aam/cache/git/github.com/openai/skills/
  Artifacts found:
    Skills:       32
    Agents:        0
    Prompts:       0
    Instructions:  0
  Total: 32 artifacts

Run 'aam source scan openai/skills' to see details.
```

---

### `aam source list`

List all configured remote git sources.

**Signature**:
```
aam source list
```

**Options**: None

**Exit codes**:

| Code | Condition |
|------|-----------|
| 0 | Always (even if no sources configured) |

**Service call**: `source_service.list_sources() -> list[dict]`

**Output format** (Rich table):
```
Configured git sources:
  NAME                      URL                                           REF     ARTIFACTS  LAST UPDATED
  github/awesome-copilot    https://github.com/github/awesome-copilot     main    37         2026-02-08  (default)
  openai/skills:.curated    https://github.com/openai/skills              main    30         2026-02-08  (default)
```

---

### `aam source remove <name>`

Remove a registered source.

**Signature**:
```
aam source remove <name> [--purge-cache]
```

**Arguments**:

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | str | Yes | Source display name |

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--purge-cache` | bool | `False` | Also delete the cached clone |

**Exit codes**:

| Code | Condition |
|------|-----------|
| 0 | Source removed |
| 1 | Source not found |

**Service call**: `source_service.remove_source(name, purge_cache) -> dict`

**Special behavior**: If the removed source has `default: true`, its name is added to `removed_defaults` in config.

---

### `aam source scan <name>`

Scan a cached source and list discovered artifacts.

**Signature**:
```
aam source scan <name> [--type TYPE] [--json]
```

**Arguments**:

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | str | Yes | Source display name |

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type` | str | None | Filter by artifact type (repeatable: skill, agent, prompt, instruction) |
| `--json` | bool | `False` | Output as JSON |

**Exit codes**:

| Code | Condition |
|------|-----------|
| 0 | Scan completed |
| 1 | Source not found or cache missing |

**Service call**: `source_service.scan_source(name, artifact_type) -> dict`

---

### `aam source update [name]`

Fetch upstream changes and report what changed.

**Signature**:
```
aam source update [name] [--all] [--dry-run]
```

**Arguments**:

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | str | No | Source to update (required if `--all` not set) |

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | bool | `False` | Update all registered sources |
| `--dry-run` | bool | `False` | Preview changes without updating cache |

**Exit codes**:

| Code | Condition |
|------|-----------|
| 0 | Update completed (even if some sources failed) |
| 1 | Named source not found |
| 1 | Neither `name` nor `--all` provided |

**Service call**: `source_service.update_source(name, update_all, dry_run) -> dict`

---

### `aam source candidates`

List artifact candidates not yet managed by AAM.

**Signature**:
```
aam source candidates [--source SOURCE] [--type TYPE] [--json]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--source` | str | None | Filter to specific source |
| `--type` | str | None | Filter by artifact type (repeatable) |
| `--json` | bool | `False` | Output as JSON |

**Exit codes**:

| Code | Condition |
|------|-----------|
| 0 | Always |

**Service call**: `source_service.list_candidates(source_name, artifact_type) -> list[dict]`

---

## Standalone Commands

### `aam verify [package]`

Verify installed package integrity via file checksums.

**Signature**:
```
aam verify [package] [--all]
```

**Arguments**:

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `package` | str | No | Package name (required if `--all` not set) |

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | bool | `False` | Verify all installed packages |

**Exit codes**:

| Code | Condition |
|------|-----------|
| 0 | All files verified clean |
| 1 | Modifications detected |
| 1 | Package not found or no checksums available |

**Service call**: `checksum_service.verify_package(package_name, verify_all) -> dict`

---

### `aam diff <package>`

Show local modifications vs installed package version.

**Signature**:
```
aam diff <package>
```

**Arguments**:

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `package` | str | Yes | Package name |

**Exit codes**:

| Code | Condition |
|------|-----------|
| 0 | Diff shown (even if no modifications) |
| 1 | Package not found or no checksums available |

**Service call**: `checksum_service.diff_package(package_name) -> dict`

---

## Extension: `aam create-package`

### New Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--from-source` | str | None | Create package from remote source artifacts |
| `--artifacts` | str | None | Comma-separated artifact names to pre-select |
| `--all` | bool | `False` | Include all candidates without interactive selection (requires `--from-source`) |

**Modified behavior**: When `--from-source` is provided:
1. Read artifacts from the specified source's cache
2. Filter by `--artifacts` if provided, include all if `--all` is set, else present interactive selection
3. Copy selected artifacts from cache to new package directory
4. Generate `aam.yaml` with `provenance:` section
5. Compute file checksums

**Service call**: `source_service.scan_source(source_name) -> dict` (for artifact list)

---

## Extension: `aam install` (upgrade warning)

### Modified Behavior

Before overwriting files during upgrade/reinstall, the install command checks for local modifications:

1. If `file_checksums` exist in lock file, verify all files
2. If modifications detected, display warning and present options:
   - `[b]` Backup and upgrade
   - `[s]` Skip upgrade
   - `[d]` Show diff
   - `[f]` Force upgrade (discard changes)
3. `--force` flag skips the prompt and overwrites

**Service call**: `checksum_service.check_modifications(package_name) -> dict`
