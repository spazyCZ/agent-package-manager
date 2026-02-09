# aam create-package

**Package Authoring**

## Synopsis

```bash
aam create-package [PATH] [OPTIONS]
```

## Description

Create an AAM package from an existing project by auto-detecting artifacts. Scans the project for skills, agents, prompts, and instructions, allows interactive selection, and generates `aam.yaml` with proper artifact references.

Use this when you have existing artifacts in your project that aren't yet managed by AAM. For new packages, use [`aam init`](init.md) instead.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PATH | No | Project directory to scan (default: current directory) |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--all` | | false | Include all detected artifacts (skip selection) |
| `--type` | `-t` | all | Filter detection to specific types (repeatable) |
| `--organize` | | copy | File organization mode (copy, reference, move) |
| `--include` | | | Manually include file or directory (repeatable) |
| `--include-as` | | skill | Artifact type for manually included files |
| `--name` | | | Package name (prompted if not provided) |
| `--scope` | | | Scope prefix for package name |
| `--version` | | 1.0.0 | Package version |
| `--description` | | | Package description |
| `--author` | | | Package author |
| `--dry-run` | | false | Preview without creating files |
| `--output-dir` | | PATH | Output directory for package files |
| `-y, --yes` | | false | Skip confirmation prompts |

## Examples

### Example 1: Interactive Creation

```bash
aam create-package
```

**Output:**
```
Scanning for artifacts not managed by AAM...

Found artifacts:

  Skills (2):
    [x]  1. my-skill              .cursor/skills/my-skill/
    [x]  2. data-processor        skills/data-processor/

  Agents (1):
    [x]  3. automation-agent      agents/automation-agent/

  Prompts (2):
    [x]  4. welcome               prompts/welcome.md
    [x]  5. farewell              prompts/farewell.md

Toggle items by entering their number (space-separated).
Press enter to confirm, a to select all, n to select none.

Toggle / confirm []:

Selected 5 artifacts. Continue? [Y/n]: y

Package name [current-directory]: my-package
Version [1.0.0]: 1.0.0
Description []: Package with existing artifacts
Author []: John Doe
License [MIT]: MIT

Creating package...
  ✓ Created aam.yaml
  ✓ Copied .cursor/skills/my-skill/ → skills/my-skill/
  ✓ Copied skills/data-processor/ → skills/data-processor/
  ✓ Copied agents/automation-agent/ → agents/automation-agent/
  ✓ Copied prompts/welcome.md → prompts/welcome.md
  ✓ Copied prompts/farewell.md → prompts/farewell.md

✓ Package created: my-package@1.0.0
  5 artifacts (2 skills, 1 agents, 2 prompts)

Next steps:
  aam validate    — verify the package is well-formed
  aam pack        — build distributable .aam archive
  aam publish     — publish to registry
```

### Example 2: Include All Artifacts

```bash
aam create-package --all --name my-package --yes
```

Non-interactive mode: detects and includes all artifacts without prompting.

### Example 3: Filter by Type

```bash
aam create-package --type skill --type agent
```

Only detects skills and agents, ignoring prompts and instructions.

### Example 4: Reference Mode (No Copying)

```bash
aam create-package --organize reference
```

Creates `aam.yaml` with artifact paths pointing to existing locations. Files are not copied or moved.

**Generated manifest:**
```yaml
artifacts:
  skills:
    - name: my-skill
      path: .cursor/skills/my-skill/
      description: Skill my-skill
```

### Example 5: Move Files

```bash
aam create-package --organize move
```

Moves artifact files into the AAM package structure instead of copying (destructive).

### Example 6: Manual Includes

```bash
aam create-package --include ./custom-skill/ --include-as skill
```

Manually includes `./custom-skill/` as a skill, even if auto-detection doesn't find it.

### Example 7: Dry Run Preview

```bash
aam create-package --dry-run
```

**Output:**
```
Scanning for artifacts not managed by AAM...

Found artifacts:
  ...

Would create:
  aam.yaml
  Would copy: .cursor/skills/my-skill/ → skills/my-skill/
  Would copy: prompts/welcome.md → prompts/welcome.md

[Dry run — no files written]

┌─ aam.yaml ──────────────────────────────┐
│ name: my-package                         │
│ version: 1.0.0                           │
│ description: ''                          │
│ artifacts:                               │
│   skills:                                │
│     - name: my-skill                     │
│       path: skills/my-skill/             │
│       description: Skill my-skill        │
│   ...                                    │
└──────────────────────────────────────────┘
```

### Example 8: Scoped Package

```bash
aam create-package --scope mycompany --name internal-tools
```

Creates `@mycompany/internal-tools`.

### Example 9: Custom Output Directory

```bash
aam create-package --output-dir ./packages/my-new-package
```

Creates package files in the specified output directory instead of the scanned directory.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - package created |
| 1 | Error - no artifacts found or invalid input |

## Detection Patterns

The scanner looks for these artifact patterns:

### Skills

- `**/SKILL.md` - Any SKILL.md file (parent directory is the skill)
- `.cursor/skills/*/SKILL.md` - Cursor skills
- `.codex/skills/*/SKILL.md` - Codex skills
- `skills/*/SKILL.md` - AAM convention

### Agents

- `**/agent.yaml` - Agent definition files
- `agents/*/agent.yaml` - AAM convention
- `.cursor/rules/agent-*.mdc` - Cursor agent rules

### Prompts

- `prompts/*.md` - AAM convention
- `.cursor/prompts/*.md` - Cursor prompts

### Instructions

- `instructions/*.md` - AAM convention
- `.cursor/rules/*.mdc` - Cursor rules/instructions

## File Organization Modes

### copy (default)

Copies artifact files into the AAM package structure:

- Skills: `skills/<skill-name>/`
- Agents: `agents/<agent-name>/`
- Prompts: `prompts/<prompt-name>.md`
- Instructions: `instructions/<instruction-name>.md`

Original files remain untouched.

### reference

Creates manifest entries pointing to existing file locations. No files are copied.

Use when:

- You want to keep files in their current locations
- Working with large artifacts
- Files are managed elsewhere (git submodules, etc.)

### move

Moves artifact files into the AAM structure. Original files are deleted.

**Warning:** This is destructive. Use with caution.

## Related Commands

- [`aam init`](init.md) - Initialize a new package from scratch
- [`aam validate`](validate.md) - Validate the created package
- [`aam pack`](pack.md) - Build distributable archive

## Notes

### Interactive Selection

The interactive selection UI shows:

- Artifact type groupings
- Checkbox indicators `[x]` (selected) or `[ ]` (not selected)
- Numbered list for toggling

Commands:

- Enter numbers to toggle (e.g., `1 3 5`)
- `a` to select all
- `n` to deselect all
- Enter to confirm

### Already Managed Artifacts

The scanner excludes artifacts already declared in any `aam.yaml` in the project. This prevents duplicates.

### No Artifacts Found

If no artifacts are detected:

```
No unmanaged artifacts found in this project.
Use 'aam init' to create a new package from scratch.
```

### Large Projects

For large projects with many artifacts, filtering by type can speed up scanning:

```bash
aam create-package --type skill
```

### Post-Creation Steps

After creating the package:

1. Review `aam.yaml` and edit descriptions
2. Add any missing metadata (repository, keywords)
3. Run `aam validate` to check correctness
4. Test locally with `aam install ./`
5. Pack and publish when ready
