# aam init

**Package Authoring**

## Synopsis

```bash
aam init [NAME]
```

## Description

Scaffold a new AAM package interactively. Creates an `aam.yaml` manifest and directory structure for artifacts. This command guides you through selecting artifact types and target platforms.

Use this when starting a brand-new package from scratch. If you have existing artifacts, use [`aam create-package`](create-package.md) instead.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| NAME | No | Package name (prompted if not provided) |

## Options

This command has no command-specific options.

## Examples

### Example 1: Interactive Initialization

```bash
aam init
```

**Interactive prompts:**
```
Package name [current-directory]: my-package
Version [1.0.0]: 1.0.0
Description []: A sample package for demonstrations
Author []: John Doe
License [MIT]: MIT

What artifacts will this package contain?
  Skills [Y/n]: y
  Agents [Y/n]: y
  Prompts [Y/n]: y
  Instructions [Y/n]: n

Which platforms should this package support?
  Cursor [Y/n]: y
  Claude [Y/n]: n
  Copilot [Y/n]: n
  Codex [Y/n]: n

Created my-package/
  ├── aam.yaml
  ├── skills/
  ├── agents/
  └── prompts/

✓ Package initialized: my-package
```

### Example 2: Initialize with Name

```bash
aam init my-custom-agent
```

Starts interactive prompts with `my-custom-agent` as the default package name.

### Example 3: Initialize Scoped Package

```bash
aam init @author/my-package
```

**Interactive prompts:**
```
Package name [@author/my-package]: @author/my-package
Version [1.0.0]:
Description []: Scoped package example
...
```

### Example 4: Minimal Package

```bash
aam init minimal-skill
```

**Prompts (selecting only skills):**
```
Package name [minimal-skill]: minimal-skill
Version [1.0.0]:
Description []: A minimal skill package
Author []:
License [MIT]:

What artifacts will this package contain?
  Skills [Y/n]: y
  Agents [Y/n]: n
  Prompts [Y/n]: n
  Instructions [Y/n]: n

Which platforms should this package support?
  Cursor [Y/n]: y
  Claude [Y/n]: n
  Copilot [Y/n]: n
  Codex [Y/n]: n

Created minimal-skill/
  ├── aam.yaml
  └── skills/

✓ Package initialized: minimal-skill
```

### Example 5: Initialize in Current Directory

```bash
mkdir my-package && cd my-package
aam init
```

Creates package files in the current directory instead of creating a subdirectory.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - package initialized |
| 1 | Error - invalid name or file already exists |

## Package Structure Created

After initialization, your package contains:

```
my-package/
├── aam.yaml              # Package manifest
├── skills/               # Directory for skills (if selected)
├── agents/               # Directory for agents (if selected)
├── prompts/              # Directory for prompts (if selected)
└── instructions/         # Directory for instructions (if selected)
```

### Generated aam.yaml

```yaml
name: my-package
version: 1.0.0
description: A sample package for demonstrations
author: John Doe
license: MIT

artifacts:
  agents: []
  skills: []
  prompts: []
  instructions: []

dependencies: {}

platforms:
  cursor:
    skill_scope: project
    deploy_instructions_as: rules
```

## Related Commands

- [`aam create-package`](create-package.md) - Create package from existing artifacts
- [`aam validate`](validate.md) - Validate the package
- [`aam pack`](pack.md) - Build distributable archive

## Notes

### Package Name Validation

Package names must follow these rules:

- Lowercase letters, numbers, hyphens
- Optional scope: `@scope/name`
- Scope format: `@lowercase-scope/package-name`
- No spaces or special characters
- Maximum 64 characters for name, 64 for scope

Valid names:

- `my-package`
- `@author/my-package`
- `chatbot-agent`
- `@company/internal-tool`

Invalid names:

- `My-Package` (uppercase)
- `my_package` (underscore)
- `package name` (space)
- `@Scope/package` (uppercase scope)

### Default Values

When you press Enter without typing a value, AAM uses:

- **Version**: `1.0.0`
- **License**: `MIT`
- **Artifact types**: All enabled by default
- **Platforms**: Cursor enabled, others disabled

### Next Steps

After initialization:

1. Add artifact files to the appropriate directories
2. Update `aam.yaml` to declare your artifacts
3. Run `aam validate` to check correctness
4. Run `aam pack` to build distributable archive

### Existing Files

If `aam.yaml` already exists in the target directory, the command will fail:

```
Error: aam.yaml already exists. Use --force to overwrite (planned feature).
```

### Scoped Packages

Scoped packages use the format `@scope/name`:

- The `@scope/` prefix is organizational namespacing
- Useful for company or personal packages
- Registries can enforce scope ownership

Example: `@mycompany/internal-agent`
