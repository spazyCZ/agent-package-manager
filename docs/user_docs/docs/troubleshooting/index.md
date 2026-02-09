# Troubleshooting

Having issues with AAM? This section provides solutions to common problems and guidance for getting help.

## Quick Diagnostic

Run the built-in diagnostic tool:

```bash
aam doctor
```

This checks:

- AAM installation and version
- Python environment
- Registry configuration
- Platform detection
- Installed packages
- Configuration validity

## Common Issues

### [Common Issues](common-issues.md)

Solutions to frequently encountered problems:

- Installation failures
- Package not found errors
- Deployment issues
- Permission denied errors
- Network connectivity problems
- Platform-specific issues

### [FAQ](faq.md)

Frequently asked questions about AAM:

- General concepts
- Package management
- Platform support
- Registry usage
- Security and signing
- Performance and optimization

### [Migration Guide](migration.md)

Guidance for migrating:

- From manual skill management to AAM
- Between AAM versions
- Between registry types
- From unscoped to scoped packages
- Between platforms

## Getting Help

### Check Documentation

1. Search this documentation
2. Review relevant concept pages
3. Check platform-specific guides
4. Read CLI command reference

### Run Diagnostics

```bash
# Environment check
aam doctor

# Verify configuration
aam config list

# Check installed packages
aam list

# Test registry connectivity
aam search test
```

### Enable Debug Logging

```bash
# Run commands with debug output
aam --debug install @author/my-package

# Or enable globally
aam config set debug true
```

### Community Support

- GitHub Issues: https://github.com/spazyCZ/agent-package-manager/issues
- Discussions: https://github.com/spazyCZ/agent-package-manager/discussions
- Discord: [Coming soon]

### Reporting Bugs

When reporting bugs, include:

1. **AAM version:** `aam --version`
2. **Platform:** `uname -a` (Linux/macOS) or OS version (Windows)
3. **Python version:** `python --version`
4. **Full command:** The command you ran
5. **Error output:** Complete error message with `--debug` flag
6. **Doctor output:** Output of `aam doctor`

Example bug report:

```
### Environment
- AAM version: 0.1.0
- Platform: Ubuntu 22.04
- Python: 3.11.5

### Command
aam install @author/my-package --debug

### Error
[Full error output here]

### Doctor Output
[Output of aam doctor]

### Expected Behavior
Package should install successfully

### Actual Behavior
Installation fails with...
```

## Debug Checklist

Before asking for help, try:

- [ ] Run `aam doctor`
- [ ] Check AAM version is latest: `pip install --upgrade aam`
- [ ] Verify registry configuration: `aam registry list`
- [ ] Test with `--debug` flag
- [ ] Check for similar issues on GitHub
- [ ] Review relevant documentation
- [ ] Try with a minimal example

## Emergency Fixes

### Complete Reset

If nothing works, reset AAM:

```bash
# Backup your packages first!
cp -r .aam .aam.backup

# Remove all AAM data
rm -rf ~/.aam
rm -rf .aam

# Reinstall AAM
pip uninstall aam
pip install aam

# Reconfigure
aam config set default_platform cursor
aam registry add <your-registry> --default
```

### Package Corruption

```bash
# Verify package integrity
aam verify @author/my-package

# Force reinstall
aam install @author/my-package --force

# If that fails, remove and reinstall
aam uninstall @author/my-package
aam install @author/my-package
```

### Configuration Issues

```bash
# Check current configuration
aam config list

# Reset configuration to defaults
rm ~/.aam/config.yaml
aam config set default_platform cursor

# Or manually edit
nano ~/.aam/config.yaml
```

## Platform-Specific Issues

### Cursor Issues

See [Cursor Troubleshooting](../platforms/cursor.md#troubleshooting)

### Claude Desktop Issues

See [Claude Troubleshooting](../platforms/claude.md#troubleshooting)

### GitHub Copilot Issues

See [Copilot Troubleshooting](../platforms/copilot.md#troubleshooting)

### Codex Issues

See [Codex Troubleshooting](../platforms/codex.md#troubleshooting)

## Advanced Topics

### Registry Issues

See [HTTP Registry Troubleshooting](../advanced/http-registry.md#troubleshooting)

### Signing Issues

See [Package Signing Troubleshooting](../advanced/signing.md#troubleshooting)

### Performance Issues

- Check available disk space
- Verify network connectivity
- Clear package cache: `rm -rf ~/.aam/cache`
- Use local registry for faster installs

## Still Need Help?

If you've tried everything and still have issues:

1. Search GitHub issues: https://github.com/spazyCZ/agent-package-manager/issues
2. Ask in Discussions: https://github.com/spazyCZ/agent-package-manager/discussions
3. File a bug report with full details

We're here to help!

## Next Steps

- [Common Issues](common-issues.md) - Specific problem solutions
- [FAQ](faq.md) - Frequently asked questions
- [Migration Guide](migration.md) - Version and platform migration
