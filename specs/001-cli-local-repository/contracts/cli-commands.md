# CLI Command Contracts: CLI Local Repository

**Branch**: `001-cli-local-repository` | **Date**: 2026-02-08

This document specifies the exact command signatures, options, arguments, and expected outputs for all AAM CLI commands in scope.

---

## 1. Registry Commands (`aam registry`)

### `aam registry init <path> [--default]`

**Purpose**: Create a new local file-based registry at the given path.

**Arguments**:
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `path` | PATH | Yes | Directory path for the new registry |

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--default` | flag | false | Also register and set as default |
| `--force` | flag | false | Reinitialize even if registry exists |

**Success Output**:
```
✓ Created local registry at /home/user/my-packages
  registry.yaml
  index.yaml
  packages/
```

**Error Cases**:
- Path already contains a registry → `Error: Registry already exists at /path. Use --force to reinitialize.`
- Path is not writable → `Error: Cannot write to /path: Permission denied`

---

### `aam registry add <name> <url> [--default]`

**Purpose**: Register a new registry source in user configuration.

**Arguments**:
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `name` | STRING | Yes | User-defined registry name |
| `url` | STRING | Yes | Registry URL (e.g., `file:///path`) |

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--default` | flag | false | Set as the default registry |

**Success Output**:
```
✓ Added registry 'local' (file:///home/user/my-packages)
  Set as default: yes
```

**Error Cases**:
- Name already exists → `Error: Registry 'local' already configured. Use 'aam registry remove local' first.`
- URL not a valid local path → `Error: Registry path does not exist: /invalid/path`

---

### `aam registry list`

**Purpose**: Display all configured registries.

**Success Output**:
```
Configured registries:

  Name      URL                                  Type    Default
  local     file:///home/user/my-packages        local   ✓
  central   https://registry.aam.dev             http
```

**Empty State**: `No registries configured. Run 'aam registry init' to create one.`

---

### `aam registry remove <name>`

**Purpose**: Remove a configured registry.

**Success Output**: `✓ Removed registry 'local'`

**Error Cases**:
- Name not found → `Error: Registry 'unknown' not found. Run 'aam registry list' to see configured registries.`

---

## 2. Package Authoring Commands

### `aam create-package [path] [options]`

**Purpose**: Create an AAM package from an existing project by detecting artifacts.

**Arguments**:
| Arg | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `path` | PATH | No | `.` | Project directory to scan |

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | flag | false | Include all detected artifacts |
| `--type` | STRING (multi) | all | Filter to specific types: skill, agent, prompt, instruction |
| `--organize` | CHOICE | copy | File org mode: copy, reference, move |
| `--include` | PATH (multi) | — | Manually include file/dir |
| `--include-as` | CHOICE | — | Artifact type for --include |
| `--name` | STRING | — | Package name (skip prompt) |
| `--scope` | STRING | — | Package scope (skip prompt) |
| `--version` | STRING | 1.0.0 | Package version |
| `--description` | STRING | — | Package description |
| `--author` | STRING | — | Author name |
| `--dry-run` | flag | false | Preview without writing |
| `--output-dir` | PATH | `.` | Output directory |
| `-y, --yes` | flag | false | Skip confirmation prompts |

**Interactive Output** (without `--all --yes`):
```
Scanning for artifacts not managed by AAM...

Found 5 artifacts:

  Skills (2):
    [x] 1. code-reviewer       .cursor/skills/code-reviewer/SKILL.md
    [x] 2. deploy-helper       .cursor/skills/deploy-helper/SKILL.md

  Agents (1):
    [x] 3. security-auditor    .cursor/rules/agent-security-auditor.mdc

  Instructions (2):
    [x] 4. python-standards    .cursor/rules/python-standards.mdc
    [x] 5. coding-guide        CLAUDE.md

Toggle selection (space-separated numbers, 'a' for all, enter to confirm):

Selected 5 artifacts. Continue? [Y/n]

Package name [my-project]:
Version [1.0.0]:
Description:
Author [spazy]:

Creating package...
  ✓ Created aam.yaml
  ✓ Copied ...

✓ Package created: my-project@1.0.0
  5 artifacts (2 skills, 1 agent, 2 instructions)

Next steps:
  aam validate    — verify the package is well-formed
  aam pack        — build distributable .aam archive
  aam publish     — publish to registry
```

**Dry-Run Output**: Same detection output, followed by `[Dry run — no files written]`

---

### `aam init [name]`

**Purpose**: Scaffold a new package interactively.

**Arguments**:
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `name` | STRING | No | Package name (prompted if omitted) |

**Interactive Output**:
```
Package name [dirname]: @author/my-package
Version [1.0.0]:
Description: My agent package
Author [spazy]:
License [MIT]:

What artifacts will this package contain?
  [x] Skills
  [x] Agents
  [x] Prompts
  [ ] Instructions

Which platforms should this package support?
  [x] Cursor
  [ ] Claude
  [ ] GitHub Copilot
  [ ] Codex

Created my-package/
  ├── aam.yaml
  ├── agents/
  ├── skills/
  └── prompts/
```

---

### `aam validate [path]`

**Purpose**: Validate the package manifest and artifacts.

**Arguments**:
| Arg | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `path` | PATH | No | `.` | Package directory |

**Success Output**:
```
Validating my-package@1.0.0...

Manifest:
  ✓ name: valid format
  ✓ version: valid semver
  ✓ description: present
  ✓ author: present

Artifacts:
  ✓ skill: python-reviewer
    ✓ SKILL.md exists and valid
  ✓ prompt: refactor-function
    ✓ prompts/refactor-function.md exists and valid

Dependencies:
  ✓ No dependencies declared

✓ Package is valid and ready to publish
```

**Error Output**:
```
Validating my-package@1.0.0...

Manifest:
  ✓ name: valid format
  ✗ version: '1.0' is not valid semver (expected MAJOR.MINOR.PATCH)

Artifacts:
  ✗ skill: python-reviewer
    ✗ skills/python-reviewer/SKILL.md: file not found

✗ 2 errors found. Fix them before packing.
```

---

### `aam pack [path]`

**Purpose**: Build a distributable `.aam` archive.

**Arguments**:
| Arg | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `path` | PATH | No | `.` | Package directory |

**Success Output**:
```
Building my-package@1.0.0...
  Adding aam.yaml
  Adding skills/python-reviewer/SKILL.md
  Adding skills/python-reviewer/scripts/analyze.py
  Adding prompts/refactor-function.md

✓ Built my-package-1.0.0.aam (4.2 KB)
  Checksum: sha256:a1b2c3d4e5f6...
```

**Error Cases**:
- Validation fails → `Error: Package validation failed. Run 'aam validate' for details.`
- Archive exceeds 50 MB → `Error: Archive size (52.3 MB) exceeds maximum of 50 MB.`

---

## 3. Publishing

### `aam publish [--registry <name>] [--tag <tag>]`

**Purpose**: Publish the packed archive to a registry.

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--registry` | STRING | default | Target registry name |
| `--tag` | STRING | latest | Dist-tag to apply |
| `--dry-run` | flag | false | Preview without publishing |

**Success Output**:
```
Publishing my-package@1.0.0 to local...

  ✓ Archive verified: sha256:a1b2c3d4e5f6...
  ✓ Copied to registry
  ✓ Updated metadata.yaml
  ✓ Rebuilt index.yaml
  ✓ Tagged as 'latest'

✓ Published my-package@1.0.0
```

**Error Cases**:
- No `.aam` file found → `Error: No archive found. Run 'aam pack' first.`
- Version exists → `Error: my-package@1.0.0 already published. Bump the version in aam.yaml.`
- Registry not configured → `Error: Registry 'local' not found. Run 'aam registry list'.`

---

## 4. Discovery

### `aam search <query> [--limit N] [--type TYPE] [--json]`

**Purpose**: Search configured registries for packages.

**Arguments**:
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `query` | STRING | Yes | Search terms |

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit` | INT | 10 | Max results |
| `--type` | STRING | — | Filter by artifact type |
| `--json` | flag | false | JSON output |

**Success Output**:
```
Search results for "audit" (2 packages):

  @author/asvc-auditor  1.0.0
    ASVC audit agent with reporting capabilities
    [agent, skill, prompt]

  code-review-toolkit   1.2.0
    Comprehensive code review toolkit
    [skill, prompt, instruction]
```

**Empty Output**: `No packages found matching "nonexistent".`

---

## 5. Installation

### `aam install <package> [--platform P] [--no-deploy] [--force] [--dry-run]`

**Purpose**: Install a package and deploy artifacts.

**Arguments**:
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `package` | STRING | Yes | Package spec: `name`, `name@ver`, `@scope/name`, `@scope/name@ver`, `./path/`, `file.aam` |

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--platform` | STRING | config default | Deploy to specific platform |
| `--no-deploy` | flag | false | Download only, skip deployment |
| `--force` | flag | false | Reinstall even if present |
| `--dry-run` | flag | false | Preview without installing |

**Success Output**:
```
Resolving @author/asvc-auditor@1.0.0...
  + @author/asvc-auditor@1.0.0
  + @author/generic-auditor@1.2.3 (dependency)

Downloading 2 packages...
  ✓ @author/asvc-auditor@1.0.0 (4.2 KB)
  ✓ @author/generic-auditor@1.2.3 (2.1 KB)

Verification:
  ✓ @author/asvc-auditor: sha256:abc123... matches
  ✓ @author/generic-auditor: sha256:def456... matches

Deploying to cursor...
  → skill: asvc-report        → .cursor/skills/author--asvc-report/
  → agent: asvc-audit         → .cursor/rules/agent-author--asvc-audit.mdc
  → prompt: audit-finding     → .cursor/prompts/audit-finding.md

✓ Installed 2 packages (1 agent, 1 skill, 1 prompt)
```

**Error Cases**:
- Package not found → `Error: Package 'unknown-pkg' not found in any configured registry.`
- No registries → `Error: No registries configured. Run 'aam registry init' to create one.`
- Version conflict → detailed conflict message with both constraints
- Already installed → `@author/asvc-auditor@1.0.0 is already installed. Use --force to reinstall.`

---

## 6. Package Management

### `aam list [--tree]`

**Purpose**: List installed packages.

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--tree` | flag | false | Show dependency tree |

**Success Output (flat)**:
```
Installed packages:

  Name                     Version  Artifacts
  @author/asvc-auditor     1.0.0    3 (1 agent, 1 skill, 1 prompt)
  @author/generic-auditor  1.2.3    1 (1 skill)
```

**Success Output (tree)**:
```
@author/asvc-auditor@1.0.0
└── @author/generic-auditor@1.2.3
```

**Empty State**: `No packages installed.`

---

### `aam info <package>`

**Purpose**: Show detailed package metadata.

**Success Output**:
```
@author/asvc-auditor@1.0.0
  Description: ASVC audit agent with reporting capabilities
  Author:      author
  License:     MIT
  Repository:  https://github.com/author/asvc-auditor

  Artifacts:
    agent: asvc-audit           — Agent configured for ASVC compliance auditing
    skill: asvc-report          — Skill for generating ASVC audit reports
    prompt: audit-finding       — Structured prompt for documenting audit findings

  Dependencies:
    @author/generic-auditor  >=1.0.0  (installed: 1.2.3)

  Deployed to:
    cursor: .cursor/skills/, .cursor/rules/, .cursor/prompts/
```

---

### `aam uninstall <package>`

**Purpose**: Remove an installed package and its deployed artifacts.

**Success Output**:
```
Uninstalling @author/asvc-auditor@1.0.0...

Removing deployed artifacts from cursor...
  ✓ Removed .cursor/rules/agent-author--asvc-audit.mdc
  ✓ Removed .cursor/skills/author--asvc-report/
  ✓ Removed .cursor/prompts/audit-finding.md

✓ Uninstalled @author/asvc-auditor
```

**Error Cases**:
- Not installed → `Error: '@author/asvc-auditor' is not installed.`
- Has dependents → `Warning: 'generic-auditor' is required by: asvc-auditor. Uninstall anyway? [y/N]`

---

## 7. Configuration

### `aam config set <key> <value>`

**Success Output**: `✓ Set default_platform = cursor`

### `aam config get <key>`

**Success Output**: `default_platform = cursor`

### `aam config list`

**Success Output**:
```
AAM Configuration:

  Key                 Value              Source
  default_platform    cursor             global (~/.aam/config.yaml)
  registries.0.name   local              global
  registries.0.url    file:///home/...   global
  security.require_checksum  true        default
```

---

## 8. Core Protocol: Registry Interface

All registry implementations conform to this interface:

```python
class Registry(Protocol):
    name: str

    def search(self, query: str) -> list[PackageIndexEntry]: ...
    def get_metadata(self, name: str) -> PackageMetadata: ...
    def get_versions(self, name: str) -> list[str]: ...
    def download(self, name: str, version: str, dest: Path) -> Path: ...
    def publish(self, archive_path: Path) -> None: ...
```

## 9. Core Protocol: Platform Adapter

```python
class PlatformAdapter(Protocol):
    name: str

    def deploy_skill(self, skill_path: Path, skill_ref: ArtifactRef, config: dict) -> Path: ...
    def deploy_agent(self, agent_path: Path, agent_ref: ArtifactRef, config: dict) -> Path: ...
    def deploy_prompt(self, prompt_path: Path, prompt_ref: ArtifactRef, config: dict) -> Path: ...
    def deploy_instruction(self, instr_path: Path, instr_ref: ArtifactRef, config: dict) -> Path: ...
    def undeploy(self, artifact_name: str, artifact_type: str) -> None: ...
    def list_deployed(self) -> list[tuple[str, str, Path]]: ...
```
