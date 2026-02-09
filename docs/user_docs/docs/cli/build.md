# aam build

**Package Authoring**

## Synopsis

```bash
aam build --target PLATFORM [OPTIONS]
```

## Description

Build a portable, platform-specific bundle archive. Bundles contain all artifacts pre-compiled and ready to deploy for the target platform, with no dependency resolution needed. This enables manual sharing via Slack, email, git, or any file transfer mechanism without requiring access to a registry.

Recipients install from bundles using `aam install ./bundle-file.bundle.aam`.

**Note:** This command is currently under development and not yet fully implemented.

## Arguments

This command takes no arguments.

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--target` | `-t` | required | Target platform (cursor, copilot, claude, codex, all) |
| `--output` | `-o` | dist | Output directory for bundle archives |

## Examples

### Example 1: Build for Cursor

```bash
aam build --target cursor
```

**Planned Output:**
```
Building bundle for target: cursor

Resolving dependencies...
  + my-package@1.0.0
  + dependency-package@2.0.1

Compiling artifacts for cursor...
  → skill: my-skill        → .cursor/skills/
  → agent: my-agent        → .cursor/rules/
  → prompt: welcome        → .cursor/prompts/

✓ Built dist/my-package-1.0.0-cursor.bundle.aam (250 KB)
```

### Example 2: Build for All Platforms

```bash
aam build --target all
```

**Planned Output:**
```
Building bundle for target: all

✓ Built dist/my-package-1.0.0-cursor.bundle.aam
✓ Built dist/my-package-1.0.0-copilot.bundle.aam
✓ Built dist/my-package-1.0.0-claude.bundle.aam
✓ Built dist/my-package-1.0.0-codex.bundle.aam

Built 4 platform bundles
```

### Example 3: Custom Output Directory

```bash
aam build --target cursor --output ./releases/
```

Creates bundle in `./releases/` instead of `./dist/`.

### Example 4: Install from Bundle

After building:

```bash
aam build --target cursor
aam install ./dist/my-package-1.0.0-cursor.bundle.aam
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - bundle(s) created |
| 1 | Error - build failed or invalid target |

## Bundle Structure

Bundles contain:

```
my-package-1.0.0-cursor.bundle.aam
├── bundle.json          # Bundle manifest
├── .cursor/             # Pre-compiled artifacts
│   ├── skills/
│   ├── rules/
│   └── prompts/
└── aam.yaml             # Original manifest (reference)
```

### bundle.json Format

```json
{
  "format": "aam-bundle",
  "version": "1.0",
  "package": "my-package",
  "package_version": "1.0.0",
  "target": "cursor",
  "built_at": "2026-02-09T14:30:00Z",
  "checksum": "sha256:...",
  "artifacts": [
    {
      "type": "skill",
      "name": "my-skill",
      "path": ".cursor/skills/my-skill/"
    }
  ]
}
```

## Supported Targets

| Target | Description |
|--------|-------------|
| `cursor` | Cursor IDE format (.cursor/ directory structure) |
| `copilot` | GitHub Copilot format |
| `claude` | Claude Code format |
| `codex` | OpenAI Codex format (.codex/ directory structure) |
| `all` | Build for all configured platforms |

## Related Commands

- [`aam pack`](pack.md) - Create registry-publishable archive
- [`aam install`](install.md) - Install from bundle
- [`aam validate`](validate.md) - Validate before building

## Notes

### Implementation Status

This command is **under development**. Current status:

- Command structure defined
- Options and arguments specified
- Bundle format designed
- Implementation in progress

Expected in version 0.2.0.

### Use Cases

**Manual distribution:**

```bash
# Build and share via Slack
aam build --target cursor
# Send dist/my-package-1.0.0-cursor.bundle.aam to team
```

**Offline installation:**

```bash
# Build bundles on machine with registry access
aam build --target all

# Transfer to offline machine
scp dist/*.bundle.aam offline-machine:~/

# Install on offline machine
aam install ~/my-package-1.0.0-cursor.bundle.aam
```

**Platform-specific releases:**

```bash
# Build and tag for GitHub release
aam build --target all
gh release create v1.0.0 dist/*.bundle.aam
```

### Bundle vs. Pack

**`aam pack`** creates registry archives:

- Contains raw artifacts
- Requires deployment during install
- Dependencies resolved at install time
- Smaller file size

**`aam build`** creates platform bundles:

- Contains pre-compiled artifacts
- Ready to deploy immediately
- Dependencies bundled (no resolution needed)
- Larger file size

### Bundle Size

Bundles are typically 2-3x larger than packed archives because they include:

- Pre-compiled artifacts for the specific platform
- All resolved dependencies
- Platform-specific transformations

### When to Use Bundles

Use bundles when:

- Recipients don't have registry access
- You need offline installation
- You want to avoid dependency resolution
- Distributing via manual channels (email, Slack, file shares)

Use `aam pack` + publish when:

- Publishing to a registry
- Dependency resolution is acceptable
- Minimizing distribution size
- Supporting multiple platforms from one package

### Future Enhancements

Planned features:

- Bundle signing for verification
- Compression optimization
- Incremental bundle updates
- Bundle dependency analysis
