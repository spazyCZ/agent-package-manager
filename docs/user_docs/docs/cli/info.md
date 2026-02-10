# aam info

**Package Management**

## Synopsis

```bash
aam info PACKAGE
```

## Description

Show detailed information about a package, including metadata,
artifacts, dependencies, and source information. This command works
for both **installed** and **uninstalled** packages:

- **Installed packages** display the full manifest from
  `.aam/packages/`, including artifacts, dependencies, and checksums.
- **Uninstalled packages** are looked up in the source artifact index.
  The output includes the artifact type, description, source origin,
  and a direct GitHub link to the original artifact directory so you
  can inspect the files in your browser.

Each result clearly shows its install status so you know at a glance
whether the package is already in your project.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PACKAGE | Yes | Name of the package (installed or from sources) |

## Options

This command has no command-specific options.

## Examples

### Example 1: Installed package

```bash
aam info my-package
```

**Output:**

```
my-package@1.0.0
  Status:      Installed
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

### Example 2: Uninstalled source package

When the package isn't installed but exists in a configured git
source, you get a summary with a link to the original artifact on
GitHub. If the artifact file contains YAML frontmatter (between
`---` delimiters), the header metadata is displayed in a panel.

```bash
aam info openai-docs
```

**Output:**

```
openai-docs  source@4ab6e0f
  Status:      Not installed
  Type:        skill
  Description: OpenAI documentation reference
  Source:      openai/skills:.curated
  Commit:      4ab6e0f3c8d1

  ╭──── Artifact header ────╮
  │ name: openai-docs       │
  │ description: Use when   │
  │ the user asks how to    │
  │ build with OpenAI ...   │
  ╰─────────────────────────╯

  View on GitHub:
  https://github.com/openai/skills/tree/4ab6e0f/.curated/openai-docs

  To install, run:  aam install openai/skills:.curated/openai-docs
```

The **Artifact header** panel shows the YAML frontmatter exactly as
it appears in the original SKILL.md file. This lets you read the
full trigger description and other metadata without leaving the
terminal.

### Example 3: Uninstalled source package without frontmatter

When the artifact file has no YAML frontmatter, the header panel is
omitted and only the basic metadata and GitHub link are shown.

```bash
aam info docs-changelog
```

**Output:**

```
docs-changelog  source@da66c7c
  Status:      Not installed
  Type:        skill
  Description: Generate changelog files from release information
  Source:      google-gemini/gemini-cli:skills
  Commit:      da66c7c4b1f2

  View on GitHub:
  https://github.com/google-gemini/gemini-cli/tree/da66c7c/.../docs-changelog

  To install, run:  aam install google-gemini/gemini-cli:skills/docs-changelog
```

The GitHub link points at the exact commit that was indexed, so you
see the same version of the artifact files that AAM discovered.

### Example 4: Uninstalled source package (qualified name)

You can use the fully qualified name to be explicit about which source
the package comes from.

```bash
aam info google-gemini/gemini-cli:skills/docs-changelog
```

### Example 5: Scoped installed package

```bash
aam info @author/advanced-agent
```

**Output:**

```
@author/advanced-agent@2.5.0
  Status:      Installed
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

### Example 6: Package not found

```bash
aam info non-existent-package
```

**Output:**

```
Error: 'non-existent-package' is not installed and was not found in
any configured source.

  Try:  aam search non-existent-package
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (package found, installed or from sources) |
| 1 | Error (package not found anywhere) |

## Information displayed

### Installed packages

For installed packages you see the full manifest:

- **Name and version** — Package identifier and version
- **Status** — "Installed" (green)
- **Description** — What the package does
- **Author** — Package author (if specified)
- **License** — License identifier (SPDX format)
- **Repository** — Source code repository URL
- **Artifacts** — Each artifact's type, name, and description
- **Dependencies** — Dependency names, version constraints, and
  installed versions
- **Source** — Where the package came from (`registry` or `local`)
- **Checksum** — SHA-256 hash (registry installs only)

### Uninstalled source packages

For packages discovered in git sources but not yet installed:

- **Name and version** — Name with `source@<commit>` version
- **Status** — "Not installed" (yellow)
- **Type** — Artifact type (skill, agent, prompt, instruction)
- **Description** — Extracted from the artifact metadata
- **Source** — Which git source provides this artifact
- **Commit** — Git commit SHA the artifact was indexed from
- **Vendor agent** — Companion vendor agent file, if present
- **Artifact header** — If the artifact file (for example,
  SKILL.md) contains YAML frontmatter between `---` delimiters,
  the full header is displayed in a bordered panel. This includes
  fields like `name`, `description`, and any custom metadata the
  artifact author defined.
- **GitHub link** — Direct link to the artifact directory on
  GitHub at the indexed commit
- **Install command** — Ready-to-copy command to install

## Related commands

- [`aam list`](list.md) — List all installed packages
- [`aam install`](install.md) — Install a package
- [`aam search`](search.md) — Search for packages in registries
  and sources

## Notes

### GitHub links

The GitHub link uses the exact commit SHA that was indexed, not a
branch name. This means the link always points to the same version
of the artifact files that AAM discovered during the last
`aam source update`.

For non-GitHub hosts (GitLab, Bitbucket), the URL format uses the
same `tree/<commit>/<path>` pattern, which works on most major git
hosting platforms.

### Missing metadata

Optional fields (author, license, repository) are omitted from the
output if not specified in the package manifest.

### Dependency installation status

The command shows whether each dependency is actually installed. If
a dependency is listed but not installed, it indicates a corrupted
environment. Run:

```bash
aam install package-name --force
```

to reinstall and resolve dependencies.

### Checksum verification

Checksums are only available for packages installed from archives.
Packages installed from local directories don't have checksums.

### Querying registry packages

To see information about packages in a registry (not installed), use:

```bash
aam search package-name
```

Registry search results show similar metadata but for all available
versions.
