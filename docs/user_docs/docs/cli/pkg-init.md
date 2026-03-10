# aam pkg init

**Package Authoring**

## Synopsis

```bash
aam pkg init [NAME]
```

## Description

Scaffold a new AAM package interactively. Creates a `package.agent.json` manifest and directory structure for artifacts. This command guides you through selecting which artifact types to include.

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
  Instructions [Y/n]: y
  Commands [Y/n]: y
  Rules [Y/n]: n

Created my-package/
  ├── package.agent.json
  ├── skills/
  ├── agents/
  ├── instructions/
  └── commands/

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

The package directory is created as `author_my-package` (the `@` is stripped and `/` is replaced with `_`).

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - package initialized |
| 1 | Error - invalid name or file already exists |

## Package Structure Created

After initialization, your package contains:

```
my-package/
├── package.agent.json    # Package manifest
├── skills/               # Directory for skills (if selected)
├── agents/               # Directory for agents (if selected)
├── instructions/         # Directory for instructions (if selected)
├── commands/             # Directory for commands (if selected)
└── rules/                # Directory for rules (if selected)
```

For scoped packages (e.g. `@author/my-package`), the directory name uses an underscore instead of `/` and strips the `@`: `author_my-package/`.

## Related Commands

- [`aam init`](init.md) - Set up AAM client (platform & sources)
- [`aam pkg create`](create-package.md) - Create package from existing artifacts
- [`aam pkg validate`](validate.md) - Validate the package
- [`aam pkg pack`](pack.md) - Build distributable archive

## Notes

### Next Steps

After initialization:

1. Add artifact files to the appropriate directories
2. Update `package.agent.json` to declare your artifacts
3. Run `aam pkg validate` to check correctness
4. Run `aam pkg pack` to build distributable archive
