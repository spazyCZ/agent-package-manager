# Common Issues

This page lists common problems and their solutions.

## Installation Issues

### Package Not Found

**Symptom:** `Error: Package '@author/my-package' not found`

**Causes:**

1. Package doesn't exist
2. Wrong package name (typo)
3. Wrong registry configured
4. Private package without authentication

**Solutions:**

```bash
# Search for package
aam search my-package

# Check registry configuration
aam registry list

# Try with full scope
aam install @author/my-package

# Login if private
aam login
```

### Installation Fails

**Symptom:** `Error: Installation failed`

**Common causes:**

1. Network connectivity
2. Disk space
3. Permission issues
4. Corrupted package

**Solutions:**

```bash
# Check network
ping registry.aam.dev

# Check disk space
df -h

# Check permissions
ls -la .aam/

# Try with debug
aam install @author/my-package --debug

# Force reinstall
aam install @author/my-package --force
```

### Dependency Resolution Failed

**Symptom:** `Error: Could not resolve dependencies`

**Cause:** Conflicting version requirements

**Solution:**

```bash
# Check dependency tree
aam info @author/my-package

# Try with specific version
aam install @author/my-package@1.0.0

# Search for the package
aam search @author/my-package
```

## Deployment Issues

### Artifacts Not Deployed

**Symptom:** Installed but artifacts don't appear in platform

**Causes:**

1. Wrong platform configured
2. Deployment skipped with `--no-deploy`
3. Platform not active

**Solutions:**

```bash
# Check active platforms
aam config get active_platforms

# Manually deploy
aam deploy --platform cursor

# Check installation
aam list
```

### Wrong Deployment Location

**Symptom:** Skills deploy to wrong directory

**Cause:** Incorrect scope configuration

**Solution:**

```bash
# For Cursor, check skill_scope
aam config get platforms.cursor.skill_scope

# Set to project scope
aam config set platforms.cursor.skill_scope project

# Re-deploy
aam deploy --platform cursor
```

### Marker Issues (Claude/Copilot/Codex)

**Symptom:** Content between AAM markers is lost

**Cause:** AAM overwrites content between markers

**Solution:**

Never edit content between `<!-- BEGIN AAM -->` and `<!-- END AAM -->` markers.

Put your custom content outside markers:

```markdown
<!-- Your content here -->

<!-- BEGIN AAM: agent-name agent -->
...AAM content...
<!-- END AAM: agent-name agent -->

<!-- More your content here -->
```

## Configuration Issues

### Invalid Configuration

**Symptom:** `Error: Invalid configuration`

**Cause:** Syntax error in YAML

**Solution:**

```bash
# Check configuration
aam config list

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.aam/config.yaml'))"

# Reset to defaults
rm ~/.aam/config.yaml
```

### Registry Not Configured

**Symptom:** `Error: No registries configured`

**Solution:**

```bash
# Add a registry
aam registry add https://registry.aam.dev --name central --default

# Or add local registry
aam registry init ~/my-packages
aam registry add file:///home/user/my-packages --name local --default
```

## Permission Issues

### Permission Denied (Unix)

**Symptom:** `PermissionError: [Errno 13] Permission denied`

**Causes:**

1. No write permission to target directory
2. Files owned by different user

**Solutions:**

```bash
# Check ownership
ls -la .aam/

# Fix ownership
sudo chown -R $USER:$USER .aam/

# Or use user-level deployment
aam config set platforms.cursor.skill_scope user
```

### Permission Denied (HTTP Registry)

**Symptom:** `HTTP 403: Permission denied`

**Causes:**

1. Not logged in
2. Not package owner
3. Token expired

**Solutions:**

```bash
# Login
aam login

# Check token
aam config get token

# Verify ownership
aam info @author/my-package
```

## Platform-Specific Issues

### Cursor: Skills Not Appearing

**Symptoms:** Skills deployed but not visible in Cursor

**Solutions:**

1. **Reload Cursor:** Command Palette → "Reload Window"

2. **Check SKILL.md:**
   ```bash
   cat .cursor/skills/*/SKILL.md
   ```

3. **Verify scope:**
   ```bash
   aam config get platforms.cursor.skill_scope
   ```

4. **Check Cursor settings:** Ensure skills are enabled

### Claude: CLAUDE.md Not Updated

**Symptom:** `CLAUDE.md` doesn't show AAM content

**Causes:**

1. No agents or instructions in package
2. Markers manually deleted
3. File permission issues

**Solutions:**

```bash
# Check what was deployed
aam list

# Re-deploy
aam deploy --platform claude

# Check file
cat CLAUDE.md
```

### Copilot: Instructions Not Followed

**Symptom:** Copilot ignores deployed instructions

**Causes:**

1. Instructions not clear enough
2. Copilot cache
3. Wrong file location

**Solutions:**

1. **Reload IDE:** Restart VS Code

2. **Check file:**
   ```bash
   cat .github/copilot-instructions.md
   ```

3. **Clarify instructions:** Make them more specific

### Codex: Skills Not Found

**Symptom:** Codex can't find skills

**Causes:**

1. Wrong scope (project vs user)
2. SKILL.md missing
3. Path mismatch

**Solutions:**

```bash
# Check skill location
ls .codex/skills/
ls ~/.codex/skills/

# Verify SKILL.md
cat .codex/skills/*/SKILL.md

# Check scope
aam config get platforms.codex.skill_scope
```

## Network Issues

### Connection Timeout

**Symptom:** `Error: Connection timeout`

**Solutions:**

```bash
# Check network
ping registry.aam.dev

# Check DNS
nslookup registry.aam.dev

# Try with proxy
export HTTP_PROXY=http://proxy.company.com:8080
aam install @author/my-package

# Use local registry if offline
aam registry add file:///path/to/local/registry --default
```

### SSL Certificate Error

**Symptom:** `SSLError: certificate verify failed`

**Causes:**

1. Corporate proxy/firewall
2. Self-signed certificate
3. Outdated CA bundle

**Solutions:**

```bash
# Update CA certificates (Ubuntu/Debian)
sudo apt-get install ca-certificates

# Or disable verification (not recommended)
aam config set security.verify_ssl false
```

## Package Issues

### Corrupted Package

**Symptom:** Checksum mismatch or extraction fails

**Solutions:**

```bash
# Remove corrupted cache
rm -rf ~/.aam/cache

# Force fresh download
aam install @author/my-package --force

# Verify integrity
aam verify @author/my-package
```

### Package Too Large

**Symptom:** `Error: Package exceeds maximum size (50 MB)`

**Cause:** Package archive is too large

**Solutions:**

1. **Remove unnecessary files:**
   - Large datasets
   - Binary files
   - Generated files

2. **Use `.aamignore`:**
   ```
   # .aamignore
   *.pyc
   __pycache__/
   .git/
   tests/
   docs/
   ```

3. **Optimize assets:**
   - Compress images
   - Minify scripts

4. **Use Git LFS** for large files

### Signature Verification Failed

**Symptom:** `Error: Signature verification failed`

**Causes:**

1. Package was tampered with
2. Wrong public key
3. Network issue (Sigstore)

**Solutions:**

```bash
# Check package info
aam info @author/my-package

# Skip verification (not recommended)
aam install @author/my-package --no-verify

# Update public keys (GPG)
gpg --refresh-keys
```

## Performance Issues

### Slow Installation

**Causes:**

1. Slow network
2. Large package
3. Many dependencies
4. Slow registry

**Solutions:**

```bash
# Use local registry
aam registry init ~/local-cache
aam registry add file:///home/user/local-cache --default

# Parallel downloads (if supported)
aam config set parallel_downloads 5

# Use CDN registry if available
aam registry add https://cdn.aam.dev --default
```

### High Disk Usage

**Symptom:** `.aam/` directory is very large

**Solutions:**

```bash
# Check size
du -sh .aam/

# Clean cache
rm -rf ~/.aam/cache

# Remove old packages
aam uninstall @author/old-package
```

## Debugging Tips

### Enable Debug Logging

```bash
# Per-command
aam --debug install @author/my-package

# Globally
aam config set debug true

# View logs
tail -f ~/.aam/logs/aam.log
```

### Check Package Contents

```bash
# Extract .aam file
tar -tzf package-1.0.0.aam

# Or extract
tar -xzf package-1.0.0.aam

# Check manifest
cat aam.yaml
```

### Verify File Checksums

```bash
# Verify installed package
aam verify @author/my-package

# Show differences
aam diff @author/my-package
```

## Still Having Issues?

If none of these solutions work:

1. Run `aam doctor` for full diagnostics
2. Check [FAQ](faq.md) for more questions
3. Visit [main troubleshooting page](index.md) for getting help
4. File a bug report on GitHub

## Next Steps

- [FAQ](faq.md) - Frequently asked questions
- [Migration Guide](migration.md) - Version and platform migration
- [Troubleshooting Index](index.md) - Overview and getting help
