# aam pkg init

**Package Authoring**

## Synopsis

```bash
aam pkg init [NAME]
```

## Description

Scaffold a new AAM package interactively. Creates an `aam.yaml` manifest and directory structure for artifacts. This command guides you through selecting artifact types and target platforms.

Use this when starting a brand-new package from scratch. If you have existing artifacts, use [`aam pkg create`](create-package.md) instead.

!!! note "Moved from `aam init`"
    This command was previously available as `aam init <name>`. The root `aam init` command now handles [client setup](init.md). Package scaffolding has moved to `aam pkg init`.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| NAME | No | Package name (prompted if not provided) |

## Examples

### Example 1: Interactive Initialization

```bash
aam pkg init
```

**Interactive prompts:**
```
Package name [current-directory]: my-package
Version [1.0.0]: 1.0.0
Description []: A sample package for demonstrations
Author []: John Doe
License [Apache-2.0]: Apache-2.0

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
aam pkg init my-custom-agent
```

Starts interactive prompts with `my-custom-agent` as the default package name.

### Example 3: Initialize Scoped Package

```bash
aam pkg init @author/my-package
```

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
├── prompts/               # Directory for prompts (if selected)
└── instructions/         # Directory for instructions (if selected)
```

## Related Commands

- [`aam init`](init.md) - Set up AAM client (platform & sources)
- [`aam pkg create`](create-package.md) - Create package from existing artifacts
- [`aam pkg validate`](validate.md) - Validate the package
- [`aam pkg pack`](pack.md) - Build distributable archive

## Notes

### Next Steps

After initialization:

1. Add artifact files to the appropriate directories
2. Update `aam.yaml` to declare your artifacts
3. Run `aam pkg validate` to check correctness
4. Run `aam pkg pack` to build distributable archive
