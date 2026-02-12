# Security Configuration Reference

AAM provides comprehensive security policies to protect against malicious packages, ensure package integrity, and enforce organizational security requirements.

## Security Model

AAM's security model is based on three pillars:

1. **Checksum verification** - Always verify package integrity
2. **Signature verification** - Optional cryptographic signatures
3. **Policy enforcement** - Configurable security policies

## Configuration Location

Security policies are configured in the `security` section of:

- **Global config** (`~/.aam/config.yaml`) - User-level policies
- **Project config** (`.aam/config.yaml`) - Project-level policies

Project config overrides global config.

## Security Schema

### SecurityConfig Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `require_checksum` | bool | `true` | Enforce SHA-256 checksum verification |
| `require_signature` | bool | `false` | Require package signatures |
| `on_signature_failure` | string | `"warn"` | Action on signature failure: `warn`, `error`, `ignore` |
| `trusted_identities` | list[string] | `[]` | Sigstore OIDC identities to trust |
| `trusted_keys` | list[string] | `[]` | GPG key fingerprints to trust |

### Example: Basic Security

```yaml
security:
  require_checksum: true
  require_signature: false
  on_signature_failure: warn
```

## Checksum Verification

### Field: `require_checksum`

**Type:** `bool`
**Default:** `true`
**Non-configurable:** Always enforced (cannot be disabled)

Every package includes a SHA-256 checksum that is verified on installation.

```yaml
security:
  require_checksum: true  # Always true
```

### How Checksums Work

1. **Package creation:** `aam pkg pack` calculates SHA-256 of `.aam` archive
2. **Publishing:** Checksum stored in registry metadata
3. **Installation:** AAM downloads package and verifies checksum
4. **Lock file:** Checksum recorded in `.aam/aam-lock.yaml`

### Checksum Format

```yaml
checksum: "sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
```

**Format:** `sha256:<64-character-hex>`

### Checksum Verification Failure

```
Error: Checksum mismatch for package my-package@1.0.0
Expected: sha256:abc123...
Got:      sha256:def456...
```

**Causes:**
- Package was modified after publishing
- Download corruption
- Man-in-the-middle attack

**Action:** Installation fails immediately (non-configurable).

## Signature Verification

### Field: `require_signature`

**Type:** `bool`
**Default:** `false`

When `true`, AAM rejects unsigned packages.

```yaml
security:
  require_signature: true
```

**Use cases:**
- High-security environments
- Regulated industries
- Enterprise deployments

### Signature Methods

AAM supports two signature methods:

1. **Sigstore** (recommended) - Keyless signing via OIDC
2. **GPG** - Traditional GPG key-based signing

### Sigstore Signatures

Sigstore uses OIDC identities (e.g., email addresses) instead of managing keys.

**Publishing with Sigstore:**
```bash
aam pkg publish --sign
# Opens browser for OIDC authentication
# Signs package with your identity
```

**Verification:**
```yaml
security:
  require_signature: true
  trusted_identities:
    - "developer@mycompany.com"
```

AAM verifies:
1. Package signature is valid
2. Signer identity matches trusted list

### GPG Signatures

Traditional GPG key-based signing.

**Publishing with GPG:**
```bash
aam pkg publish --sign --gpg-key KEY_ID
```

**Verification:**
```yaml
security:
  require_signature: true
  trusted_keys:
    - "ABCD1234EFGH5678IJKL9012MNOP3456QRST7890"
```

## Signature Verification Policies

### Field: `on_signature_failure`

**Type:** `string`
**Default:** `"warn"`
**Valid values:** `"warn"`, `"error"`, `"ignore"`

Controls behavior when signature verification fails.

### Mode: `warn`

Log warning but continue installation.

```yaml
security:
  on_signature_failure: warn
```

**Output:**
```
Warning: Signature verification failed for package my-package@1.0.0
Continuing installation...
```

**Use case:** Transitioning to mandatory signatures.

### Mode: `error`

Fail installation immediately.

```yaml
security:
  on_signature_failure: error
```

**Output:**
```
Error: Signature verification failed for package my-package@1.0.0
Installation aborted.
```

**Use case:** Production environments with strict security.

### Mode: `ignore`

Skip signature verification entirely.

```yaml
security:
  on_signature_failure: ignore
```

**Use case:** Development environments (not recommended for production).

## Trusted Identities

### Field: `trusted_identities`

**Type:** `list[string]`
**Default:** `[]`

List of Sigstore OIDC identities (email patterns) to trust.

### Exact Identity Match

```yaml
security:
  trusted_identities:
    - "developer@mycompany.com"
```

Only packages signed by `developer@mycompany.com` are trusted.

### Wildcard Patterns

Trust all users from a domain:

```yaml
security:
  trusted_identities:
    - "*@mycompany.com"
```

Trust multiple domains:

```yaml
security:
  trusted_identities:
    - "*@mycompany.com"
    - "*@partner.com"
    - "contractor@external.com"
```

### Verification Process

When installing a package:

1. AAM extracts signer identity from Sigstore bundle
2. Checks if identity matches any pattern in `trusted_identities`
3. If no match: Action depends on `on_signature_failure`

## Trusted Keys

### Field: `trusted_keys`

**Type:** `list[string]`
**Default:** `[]`

List of GPG key fingerprints to trust.

### Example

```yaml
security:
  trusted_keys:
    - "ABCD1234EFGH5678IJKL9012MNOP3456QRST7890"
    - "1234567890ABCDEF1234567890ABCDEF12345678"
```

### Getting Key Fingerprints

```bash
# List your GPG keys
gpg --list-keys --fingerprint

# Output:
# pub   rsa4096 2024-01-01 [SC]
#       ABCD 1234 EFGH 5678 IJKL  9012 MNOP 3456 QRST 7890
# uid           [ultimate] Your Name <you@example.com>
```

**Use the 40-character fingerprint** (spaces optional).

## Security Policy Examples

### Policy: Permissive (Default)

Verify checksums, warn on signature failures.

```yaml
security:
  require_checksum: true       # Always enforced
  require_signature: false     # Don't require signatures
  on_signature_failure: warn   # Warn but continue
```

**Use case:** Individual developers, open-source projects.

### Policy: Moderate

Require signatures, warn on failures.

```yaml
security:
  require_checksum: true
  require_signature: true      # Reject unsigned packages
  on_signature_failure: warn   # Warn on bad signatures
  trusted_identities:
    - "*@mycompany.com"
```

**Use case:** Teams transitioning to mandatory signatures.

### Policy: Strict

Require signatures, fail on bad signatures.

```yaml
security:
  require_checksum: true
  require_signature: true
  on_signature_failure: error  # Fail immediately
  trusted_identities:
    - "*@mycompany.com"
```

**Use case:** Production environments, regulated industries.

### Policy: High-Security Enterprise

Strict verification with GPG keys.

```yaml
security:
  require_checksum: true
  require_signature: true
  on_signature_failure: error
  trusted_keys:
    - "ABCD1234EFGH5678IJKL9012MNOP3456QRST7890"
    - "1234567890ABCDEF1234567890ABCDEF12345678"
```

**Use case:** Financial services, healthcare, government.

### Policy: Air-Gapped Environment

Checksums only (no signature verification).

```yaml
security:
  require_checksum: true
  require_signature: false
  on_signature_failure: ignore
```

**Use case:** Offline/air-gapped networks with pre-vetted packages.

## Advanced Security Configuration

### Registry Allowlists

Restrict package installation to specific registries.

```yaml
security:
  allowed_registries:
    - "aam-central"
    - "company-registry"
```

**Effect:** Packages from other registries are rejected.

**Error message:**
```
Error: Registry "untrusted" is not in allowed list
```

### Package Blocklists

Block specific packages from installation.

```yaml
security:
  blocked_packages:
    - "malicious-package"
    - "@attacker/evil-agent"
```

**Effect:** Blocked packages cannot be installed.

**Error message:**
```
Error: Package "malicious-package" is blocked by security policy
```

### Install Policy

Control what can be installed based on scope, tags, etc.

```yaml
security:
  install_policy:
    allowed_scopes:
      - "myorg"
      - "trusted-vendor"
    require_tag: true  # Only allow tagged releases
```

**`allowed_scopes`**: Only install packages from these scopes.
**`require_tag`**: Reject packages without dist-tags.

### Publish Policy

Control package publishing.

```yaml
security:
  publish_policy:
    require_approval: true
    approvers:
      - "manager@mycompany.com"
      - "security@mycompany.com"
```

**`require_approval`**: Require manual approval before publishing.
**`approvers`**: List of email addresses that can approve.

**Workflow:**
```bash
aam pkg publish
# Package uploaded but marked "pending approval"
# Approver runs: aam approve @myorg/my-package@1.0.0
# Package becomes available
```

## Team Security Policies

### Global vs. Project Config

**Global config** (`~/.aam/config.yaml`):
- Personal security preferences
- Less strict for development

**Project config** (`.aam/config.yaml`):
- Team-wide security requirements
- Committed to git
- More strict for production

### Example: Team Policy

**Global config** (developer's machine):
```yaml
security:
  require_checksum: true
  require_signature: false
  on_signature_failure: warn
```

**Project config** (committed to git):
```yaml
security:
  require_checksum: true
  require_signature: true      # Team requires signatures
  on_signature_failure: error  # Fail on bad signatures
  trusted_identities:
    - "*@mycompany.com"
```

**Result:** Project config overrides global, enforcing team policy.

## Auditing and Compliance

### Audit Installed Packages

```bash
aam list --audit
# Shows all packages with signature status
```

**Output:**
```
@myorg/package-a@1.0.0
  Signature: Valid (developer@mycompany.com)
  Checksum: sha256:abc123...

@vendor/package-b@2.0.0
  Signature: Missing
  Checksum: sha256:def456...
```

### Verify Signatures

```bash
aam verify
# Verifies all installed packages against security policy
```

**Output:**
```
Checking 5 packages...
✓ @myorg/package-a@1.0.0 (signed by developer@mycompany.com)
✓ @myorg/package-b@1.2.0 (signed by admin@mycompany.com)
✗ @vendor/package-c@3.0.0 (unsigned)

2/3 packages passed verification
```

### Export Audit Report

```bash
aam list --audit --format json > audit.json
# Generate audit report for compliance
```

## Signature Workflow

### For Package Publishers

1. **Setup signing:**

Sigstore (recommended):
```bash
aam login sigstore
# Authenticates via OIDC
```

GPG:
```bash
gpg --gen-key
# Generate GPG key
```

2. **Sign and publish:**

```bash
aam pkg publish --sign
# Signs package and publishes
```

3. **Verify signature:**

```bash
aam verify @myorg/my-package@1.0.0
```

### For Package Consumers

1. **Configure trust:**

```yaml
# ~/.aam/config.yaml
security:
  require_signature: true
  trusted_identities:
    - "*@trusted-org.com"
```

2. **Install packages:**

```bash
aam install @trusted-org/package
# Verifies signature automatically
```

3. **Audit periodically:**

```bash
aam verify
# Re-verify all installed packages
```

## Troubleshooting

### Signature Verification Failed

**Problem:**
```
Error: Signature verification failed for package my-package@1.0.0
```

**Solutions:**

1. **Check trusted identities:**
```bash
aam config get security.trusted_identities
```

2. **Verify package signature:**
```bash
aam verify my-package
# Shows detailed signature information
```

3. **Override for testing:**
```bash
aam install my-package --no-verify
# Bypasses signature check (use with caution)
```

### Package Not Signed

**Problem:**
```
Warning: Package my-package@1.0.0 is not signed
```

**Solutions:**

1. **Contact package author** to sign and republish

2. **Override security policy** (if acceptable):
```yaml
security:
  require_signature: false
```

3. **Use different package** from trusted source

### Checksum Mismatch

**Problem:**
```
Error: Checksum mismatch for package my-package@1.0.0
```

**Solutions:**

1. **Re-download package:**
```bash
aam install my-package --force
```

2. **Check registry integrity:**
```bash
aam search my-package --registry aam-central
```

3. **Report to registry maintainer** if persistent

## Best Practices

### Always Verify Checksums

Never disable checksum verification (it's enforced anyway).

### Sign Your Packages

If publishing packages, always sign them:

```bash
aam pkg publish --sign
```

### Use Sigstore for Simplicity

Sigstore is easier than GPG (no key management).

```bash
aam login sigstore
aam pkg publish --sign
```

### Configure Trust Lists

Define who you trust:

```yaml
security:
  trusted_identities:
    - "*@mycompany.com"      # Trust company developers
    - "*@trusted-vendor.com" # Trust vendor packages
```

### Enable Strict Mode for Production

```yaml
security:
  require_signature: true
  on_signature_failure: error
```

### Audit Regularly

```bash
# Weekly or monthly
aam verify
aam list --audit
```

### Document Security Policies

Add security policy to project README:

```markdown
## Security Policy

This project requires all packages to be signed by @mycompany.com developers.

See `.aam/config.yaml` for security configuration.
```

## Migration

### Enabling Signatures Gradually

**Step 1:** Warn on unsigned packages
```yaml
security:
  require_signature: false
  on_signature_failure: warn
```

**Step 2:** Require signatures, but warn on failures
```yaml
security:
  require_signature: true
  on_signature_failure: warn
```

**Step 3:** Strict enforcement
```yaml
security:
  require_signature: true
  on_signature_failure: error
```

### From GPG to Sigstore

1. **Add Sigstore identities:**
```yaml
security:
  trusted_identities:
    - "*@mycompany.com"
  trusted_keys:  # Keep GPG keys temporarily
    - "ABCD1234..."
```

2. **Transition packages:**
- Republish with Sigstore signatures
- Verify both GPG and Sigstore work

3. **Remove GPG keys:**
```yaml
security:
  trusted_identities:
    - "*@mycompany.com"
  # trusted_keys removed
```

## Compliance Considerations

### GDPR

- Signing metadata may include personal information (email)
- Document in privacy policy

### SOC 2

- Enable signature verification
- Audit installed packages regularly
- Document security policies

### HIPAA

- Use strict security policies
- Enable signature verification
- Restrict to approved registries

### ISO 27001

- Document security configuration
- Regular security audits
- Access control via scopes

## Next Steps

- [Global Configuration](global.md) - Configure security globally
- [Project Configuration](project.md) - Project-level security policies
- [CLI Reference: publish](../cli/publish.md) - Signing packages
- [CLI Reference: verify](../cli/verify.md) - Verifying signatures
- [Advanced: Package Signing](../advanced/signing.md) - In-depth signing guide
