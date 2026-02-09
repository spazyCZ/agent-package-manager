# aam validate

**Package Authoring**

## Synopsis

```bash
aam validate [PATH]
```

## Description

Validate the package manifest and artifacts. Checks that `aam.yaml` is syntactically correct, all required fields are present, artifact paths exist, and dependencies are properly declared.

Run this before packing or publishing to catch errors early.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PATH | No | Path to package directory or aam.yaml (default: current directory) |

## Options

This command has no command-specific options.

## Examples

### Example 1: Validate Current Directory

```bash
aam validate
```

**Output:**
```
Validating my-package@1.0.0...

Manifest:
  ✓ name: valid format
  ✓ version: valid semver
  ✓ description: present
  ✓ author: present

Artifacts:
  ✓ skill: my-skill
    ✓ skills/my-skill/ exists
  ✓ agent: my-agent
    ✓ agents/my-agent/ exists
  ✓ prompt: welcome
    ✓ prompts/welcome.md exists

Dependencies:
  ✓ utility-package: ^1.0.0
  ✓ shared-prompts: >=2.0.0

✓ Package is valid and ready to publish
```

### Example 2: Validate Specific Directory

```bash
aam validate ./my-package/
```

Validates the package in the specified directory.

### Example 3: Validation Errors

```bash
aam validate
```

**Output:**
```
Validating my-package@1.0.0...

Manifest:
  ✓ name: valid format
  ✓ version: valid semver
  ✗ description: empty

Artifacts:
  ✓ skill: my-skill
    ✓ skills/my-skill/ exists
  ✗ agent: broken-agent
    ✗ agents/broken-agent/: file not found
  ✓ prompt: welcome
    ✓ prompts/welcome.md exists

Dependencies:
  ✓ No dependencies declared

✗ 2 errors found. Fix them before packing.
```

### Example 4: Schema Validation Error

```bash
aam validate
```

**Output:**
```
Validating package...

Manifest:
  ✗ name: field required
  ✗ version: invalid format (expected semver)
  ✗ artifacts.skills.0.path: field required

✗ 3 errors found. Fix them before packing.
```

### Example 5: No Manifest Found

```bash
aam validate ./empty-directory/
```

**Output:**
```
Error: No aam.yaml found. Run 'aam create-package' or 'aam init' first.
```

### Example 6: Valid Package with Warnings

```bash
aam validate
```

**Output:**
```
Validating my-package@1.0.0...

Manifest:
  ✓ name: valid format
  ✓ version: valid semver
  ✓ description: present
  ⚠ author: not set (optional)

Artifacts:
  ✓ skill: my-skill
    ✓ skills/my-skill/ exists

Dependencies:
  ✓ No dependencies declared

✓ Package is valid and ready to publish
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - package is valid |
| 1 | Error - validation failed |

## Validation Checks

### Manifest Schema

- **name** - Must match pattern `^(@[a-z0-9][a-z0-9_-]{0,63}/)?[a-z0-9][a-z0-9-]{0,63}$`
- **version** - Must be valid semver (MAJOR.MINOR.PATCH)
- **description** - Should not be empty
- **artifacts** - Must declare at least one artifact
- **dependencies** - Must use valid version constraints

### Artifact Paths

For each declared artifact:

- File or directory must exist at the specified path
- Skills must contain `SKILL.md`
- Agents must contain `agent.yaml`

### Optional Fields

These fields generate warnings if missing but don't fail validation:

- `author`
- `license`
- `repository`
- `keywords`

## Related Commands

- [`aam pack`](pack.md) - Build archive (runs validation first)
- [`aam publish`](publish.md) - Publish to registry (requires valid package)
- [`aam init`](init.md) - Initialize new package
- [`aam create-package`](create-package.md) - Create package from existing artifacts

## Notes

### Run Before Packing

Always run `aam validate` before `aam pack`. The pack command will fail if validation errors exist, so catching them early saves time.

### Fixing Validation Errors

Common fixes:

**Missing description:**
```yaml
description: "Add a description here"
```

**Invalid version:**
```yaml
version: 1.0.0  # Must be MAJOR.MINOR.PATCH
```

**Missing artifact path:**
```yaml
artifacts:
  skills:
    - name: my-skill
      path: skills/my-skill/  # Ensure this path exists
      description: "My skill"
```

### Schema Errors vs. Path Errors

- **Schema errors** - Problems with `aam.yaml` structure or content
- **Path errors** - Declared artifacts that don't exist on disk

Both must be fixed for the package to be valid.

### Dependency Constraints

Valid constraint formats:

- `1.0.0` - Exact version
- `>=1.0.0` - Minimum version
- `^1.0.0` - Compatible (semver caret)
- `~1.0.0` - Approximate (semver tilde)
- `*` - Any version

Invalid:

- `1.0` - Missing patch version
- `latest` - Not a valid constraint (use `*`)
- `>1.0.0` - Use `>=` instead

### Verbose Mode

For detailed validation output:

```bash
aam validate --verbose
```

Shows debug information about the validation process.

### Validation in CI/CD

Use validation in continuous integration:

```bash
#!/bin/bash
set -e
aam validate
aam pack
```

The script will fail immediately if validation fails.
