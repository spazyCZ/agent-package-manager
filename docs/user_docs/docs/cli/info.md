# aam info

**Package Management**

## Synopsis

```bash
aam info PACKAGE
```

## Description

Show detailed information about an installed package, including metadata, artifacts, dependencies, and source information. This command reads the package manifest from `.aam/packages/` and displays comprehensive details.

Use this to inspect what a package contains before using it, or to verify installation details.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PACKAGE | Yes | Name of the installed package |

## Options

This command has no command-specific options.

## Examples

### Example 1: Show Package Information

```bash
aam info my-package
```

**Output:**
```
my-package@1.0.0
  Description: A sample package with skills and agents
  Author:      John Doe
  License:     MIT
  Repository:  https://github.com/johndoe/my-package

  Artifacts:
    skill: my-skill           — Core skill for data processing
    agent: my-agent           — Agent configured for automation
    prompt: welcome-prompt    — Welcome message template
    instruction: code-style   — Coding standards and conventions

  Dependencies:
    utility-package  ^1.0.0 (installed: 1.2.0)
    shared-prompts   >=2.0.0 (installed: 2.1.0)

  Source: registry
  Checksum: sha256:a1b2c3d4e5f6...
```

### Example 2: Scoped Package

```bash
aam info @author/advanced-agent
```

**Output:**
```
@author/advanced-agent@2.5.0
  Description: Advanced AI agent with multiple skills
  Author:      Author Name
  License:     Apache-2.0
  Repository:  https://github.com/author/advanced-agent

  Artifacts:
    skill: data-analysis      — Analyze and visualize data
    skill: code-review        — Review code for best practices
    agent: advanced-agent     — Multi-skilled automation agent
    prompt: analysis-prompt   — Data analysis prompt template

  Dependencies:
    None

  Source: local
```

### Example 3: Package Not Installed

```bash
aam info non-existent-package
```

**Output:**
```
Error: 'non-existent-package' is not installed.
```

### Example 4: Package with Many Dependencies

```bash
aam info complex-package
```

**Output:**
```
complex-package@3.0.0
  Description: Complex package with multiple dependencies
  Author:      Package Team
  License:     MIT
  Repository:  https://github.com/team/complex-package

  Artifacts:
    skill: main-skill         — Main functionality
    agent: orchestrator       — Orchestrates multiple skills

  Dependencies:
    @author/skill-library  ^2.0.0 (installed: 2.3.1)
    prompt-templates       ~1.5.0 (installed: 1.5.2)
    utility-functions      >=1.0.0 (installed: 1.8.0)
    shared-instructions    * (installed: 0.9.0)

  Source: registry
  Checksum: sha256:9f8e7d6c5b4a...
```

### Example 5: Local Package Installation

```bash
aam info my-local-package
```

**Output:**
```
my-local-package@0.1.0
  Description: Package installed from local directory

  Artifacts:
    skill: test-skill         — Test skill for development

  Dependencies:
    None

  Source: local
  Checksum:
```

Note: Local installations don't have checksums.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - package found and displayed |
| 1 | Error - package not installed |

## Information Displayed

### Metadata

- **Name and Version** - Package identifier and version
- **Description** - What the package does
- **Author** - Package author (if specified)
- **License** - License identifier (SPDX format)
- **Repository** - Source code repository URL

### Artifacts

For each artifact:

- **Type** - skill, agent, prompt, or instruction
- **Name** - Artifact identifier
- **Description** - What the artifact does

### Dependencies

For each dependency:

- **Name** - Dependency package name
- **Constraint** - Version constraint from manifest
- **Installed** - Actual installed version (if present)

### Source Information

- **Source** - Where the package came from:
  - `registry` - Downloaded from a registry
  - `local` - Installed from local directory or archive

- **Checksum** - SHA-256 hash of the archive (registry installs only)

## Related Commands

- [`aam list`](list.md) - List all installed packages
- [`aam install`](install.md) - Install a package
- [`aam search`](search.md) - Search for packages in registries

## Notes

### Missing Metadata

Optional fields (author, license, repository) may not be present. They will be omitted from the output if not specified in the package manifest.

### Dependency Installation Status

The command shows whether each dependency is actually installed. If a dependency is listed but not installed, it indicates a corrupted environment. Run:

```bash
aam install package-name --force
```

to reinstall and resolve dependencies.

### Checksum Verification

Checksums are only available for packages installed from archives. Packages installed from local directories do not have checksums.

### Artifact Paths

This command does not show artifact file paths. The paths are internal to the package structure. To explore package files directly:

```bash
ls -la .aam/packages/package-name/
```

### Querying Registry Packages

To see information about packages in a registry (not installed), use:

```bash
aam search package-name
```

Registry search results show similar metadata but for all available versions.
