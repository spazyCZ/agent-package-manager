# Frequently Asked Questions

## General

### What is AAM?

AAM (Agent Artifact Manager) is a package manager for AI agent artifacts like skills, agents, prompts, and instructions. It's like npm for agent configurations.

### Why do I need AAM?

AAM solves:

- **Distribution:** Share skills and agents easily
- **Dependencies:** Manage artifact dependencies automatically
- **Multi-platform:** Deploy to Cursor, Claude, Copilot, Codex
- **Versioning:** Track and update artifacts over time

### Is AAM free?

Yes, AAM is open-source and free to use. The HTTP registry is also free for public packages.

### Does AAM work offline?

Yes! AAM's core features work without a network. Use local or Git registries for fully offline operation.

## Installation & Setup

### How do I install AAM?

```bash
pip install aam
```

See [Installation Guide](../getting-started/installation.md) for details.

### What are the requirements?

- Python 3.11+
- Supported platform (Cursor, Claude, Copilot, or Codex)
- Git (for Git-based registries)

### Do I need to set up a server?

No! AAM works with local registries. HTTP registry is optional for teams.

## Packages

### What's the difference between scoped and unscoped packages?

- **Unscoped:** `my-package` (no namespace)
- **Scoped:** `@author/my-package` (with namespace)

Scoped packages clarify ownership and prevent naming conflicts.

### Can I create private packages?

Yes! Use:

1. Local registry (file-based)
2. Private Git repository
3. HTTP registry with authentication

### How do I share packages with my team?

Three options:

1. **Git registry:** Share via Git repository
2. **Local registry:** Share via network filesystem
3. **HTTP registry:** Host your own registry server

### What's the maximum package size?

50 MB per package (compressed). If larger, consider:

- Removing unnecessary files
- Using `.aamignore`
- Hosting large files separately

## Platforms

### Which platforms does AAM support?

- Cursor
- Claude Desktop
- GitHub Copilot
- OpenAI Codex

### Can I deploy to multiple platforms?

Yes! Set active platforms:

```bash
aam config set active_platforms cursor,claude,copilot
```

### Do I need all platforms installed?

No. AAM only deploys to platforms you have configured and installed.

### Can I create platform-specific packages?

Yes. Configure in `aam.yaml`:

```yaml
platforms:
  cursor:
    skill_scope: project
  claude:
    merge_instructions: true
```

## Publishing

### How do I publish a package?

```bash
aam init my-package        # Create package
aam validate               # Validate
aam pack                   # Build archive
aam publish                # Publish to registry
```

### Do I need to sign packages?

No, but it's recommended for security:

```bash
aam publish --sign
```

### Can I unpublish a package?

You can yank (hide) versions:

```bash
aam yank @author/my-package@1.0.0
```

Yanked versions can't be installed but remain for existing users.

### How do I update a published package?

1. Increment version in `aam.yaml`
2. Run `aam publish`

## Dependencies

### How do dependency versions work?

AAM uses semantic versioning:

- `1.0.0` - Exact version
- `^1.0.0` - Compatible (>=1.0.0 <2.0.0)
- `~1.0.0` - Approximate (>=1.0.0 <1.1.0)
- `>=1.0.0` - Minimum version

### What if dependencies conflict?

AAM resolves to the highest compatible version. If no resolution exists, installation fails.

### Can I see the dependency tree?

```bash
aam info @author/my-package
```

## Registries

### What types of registries exist?

1. **Local:** File-based, no server needed
2. **Git:** Git repository structure
3. **HTTP:** Server with API (like npm)

### Do I need an HTTP registry?

No. Local and Git registries work great for solo/small teams.

### Can I use multiple registries?

Yes:

```bash
aam registry add https://registry1.com --name reg1
aam registry add https://registry2.com --name reg2
```

AAM searches all configured registries.

### How do I switch registries?

```bash
aam registry add <new-registry> --default
```

## Security

### Are packages signed?

Optionally. Authors can sign with Sigstore or GPG:

```bash
aam publish --sign
```

### How do I verify signatures?

```bash
aam install @author/my-package --verify-signature
```

### Can I require signatures?

Yes:

```bash
aam config set security.require_signature true
```

### Is my token secure?

Tokens are stored in `~/.aam/credentials.json` with restricted permissions (0600). Keep this file secure.

## Troubleshooting

### Package not found?

```bash
# Search for it
aam search package-name

# Check registry
aam registry list

# Try full name
aam install @author/package-name
```

### Installation failed?

```bash
# Run diagnostics
aam doctor

# Try with debug
aam --debug install @author/my-package

# Force reinstall
aam install @author/my-package --force
```

### Skills not appearing?

1. Reload your IDE/editor
2. Check deployment: `aam list`
3. Verify file location: `ls .cursor/skills/`
4. Check configuration: `aam config list`

### Getting rate limited?

HTTP registries may rate limit. Solutions:

1. Use local/Git registry
2. Authenticate: `aam login`
3. Wait and retry

## Advanced

### Can I use AAM in CI/CD?

Yes:

```bash
# Install in CI
pip install aam

# Use token for authentication
export AAM_TOKEN=$SECRET_TOKEN
aam publish
```

### How do I migrate from manual skills to AAM?

```bash
# Auto-detect existing artifacts
aam create-package

# Creates package from current project
```

See [Migration Guide](migration.md) for details.

### Can I build platform-specific bundles?

Yes:

```bash
aam build --target cursor
```

Creates a pre-built bundle for Cursor only.

### Does AAM support MCP?

Yes! AAM can run as an MCP server:

```bash
aam mcp serve
```

See [MCP Integration](../tutorials/mcp-integration.md) for details.

## Performance

### Is AAM fast?

Yes. Most operations are local and instant. Network operations (publish/install) depend on registry speed.

### Can I cache packages?

Yes, AAM caches downloads in `~/.aam/cache/`.

### How much disk space does AAM use?

Varies by packages installed. Typically 10-100 MB. Clean cache with:

```bash
rm -rf ~/.aam/cache
```

## Contributing

### Can I contribute to AAM?

Yes! AAM is open-source:

- GitHub: https://github.com/spazyCZ/agent-package-manager
- Issues: Report bugs or suggest features
- PRs: Submit improvements

### How do I report bugs?

File an issue on GitHub with:

- AAM version: `aam --version`
- Platform and Python version
- Full error message with `--debug`
- Output of `aam doctor`

### Can I create custom platforms?

Yes, platform adapters are pluggable. See developer documentation.

## Still Have Questions?

- Check [Common Issues](common-issues.md) for specific problems
- Review [Concepts](../concepts/index.md) for deeper understanding
- Visit [GitHub Discussions](https://github.com/spazyCZ/agent-package-manager/discussions)
- File an [issue](https://github.com/spazyCZ/agent-package-manager/issues) if you found a bug

## Next Steps

- [Troubleshooting Index](index.md) - More help resources
- [Common Issues](common-issues.md) - Specific problem solutions
- [Migration Guide](migration.md) - Version and platform migration
