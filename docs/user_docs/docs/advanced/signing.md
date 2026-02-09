# Package Signing

## Overview

Package signing allows package authors to cryptographically sign their packages, and consumers to verify that packages haven't been tampered with and come from the claimed author.

AAM supports two signing methods:

1. **Sigstore** (recommended) - Identity-based signing using OIDC providers
2. **GPG** - Traditional PGP signing with key pairs

## Why Sign Packages?

**Benefits:**

- **Authenticity:** Verify packages come from the claimed author
- **Integrity:** Detect tampering or corruption
- **Trust:** Build confidence in package ecosystem
- **Compliance:** Meet organizational security requirements

## Sigstore Signing (Recommended)

Sigstore provides "keyless" signing using your existing identity providers (GitHub, Google, etc.). No need to manage cryptographic keys.

### How Sigstore Works

```
1. Author publishes package → AAM initiates signing
2. Sigstore authenticates via OIDC (GitHub/Google login)
3. Sigstore issues short-lived certificate tied to your identity
4. Package is signed and certificate is logged in transparency log
5. Signature + certificate stored with package
6. Consumer verifies signature using transparency log
```

### Signing with Sigstore

```bash
# First time: Install Sigstore (cosign)
pip install sigstore

# Publish with Sigstore signing
aam publish --sign

# Interactive OIDC flow:
# 1. Browser opens for GitHub/Google login
# 2. You authenticate
# 3. AAM signs package with issued certificate
# 4. Signature stored in registry
```

**Output:**

```
Signing package with Sigstore...
→ Opening browser for authentication...
→ Authenticated as: alice@github
→ Package signed successfully

Signed with:
  Identity: alice@github
  Issuer: https://github.com/login/oauth
  Transparency log: https://rekor.sigstore.dev/api/v1/log/entries/...

Publishing to registry...
✓ Published @author/my-package@1.0.0
```

### Verifying Sigstore Signatures

```bash
# Install with signature verification
aam install @author/my-package --verify-signature

# Verification checks:
# 1. Signature matches package content (SHA-256)
# 2. Certificate is valid and matches claimed identity
# 3. Entry exists in Sigstore transparency log
```

**Output:**

```
Downloading @author/my-package@1.0.0...
Verifying signature...
  ✓ Signature valid
  ✓ Signed by: alice@github
  ✓ Transparency log verified
  ✓ Package integrity confirmed

Installing...
```

### Sigstore Configuration

```yaml
# ~/.aam/config.yaml

security:
  signing_method: sigstore          # "sigstore" or "gpg"
  require_signature: false          # Require signatures on install
  verify_transparency_log: true    # Check Rekor transparency log
  allowed_issuers:                  # Restrict OIDC issuers
    - https://github.com/login/oauth
    - https://accounts.google.com
```

## GPG Signing

GPG provides traditional PGP signing using public/private key pairs.

### Setting Up GPG

```bash
# Generate GPG key (if you don't have one)
gpg --full-generate-key
# Choose: RSA and RSA, 4096 bits, no expiration
# Enter your name and email

# List your keys
gpg --list-keys
# pub   rsa4096 2026-02-09 [SC]
#       ABCD1234EF567890ABCD1234EF567890ABCD1234
# uid   Alice <alice@example.com>

# Export public key
gpg --armor --export alice@example.com > public.asc

# Configure AAM to use your key
aam config set security.gpg_key alice@example.com
```

### Signing with GPG

```bash
# Publish with GPG signing
aam publish --sign --signing-method gpg

# Enter GPG passphrase when prompted
```

**Output:**

```
Signing package with GPG...
→ Using key: alice@example.com (ABCD1234EF567890)
→ Enter passphrase: ****
→ Package signed successfully

Publishing to registry...
✓ Published @author/my-package@1.0.0
✓ Signature uploaded
```

### Verifying GPG Signatures

```bash
# Import author's public key (first time)
gpg --import public.asc

# Install with verification
aam install @author/my-package --verify-signature

# Verification checks:
# 1. Signature matches package content
# 2. Signature created by claimed key
# 3. Key is trusted (if in your keyring)
```

**Output:**

```
Downloading @author/my-package@1.0.0...
Verifying GPG signature...
  ✓ Signature valid
  ✓ Signed by: Alice <alice@example.com> (ABCD1234EF567890)
  ⚠ Key not in trusted keyring (install anyway? [y/N])
```

### GPG Configuration

```yaml
# ~/.aam/config.yaml

security:
  signing_method: gpg
  gpg_key: alice@example.com        # Your signing key
  gpg_home: ~/.gnupg                # GPG home directory
  require_signature: false
  trusted_keys:                      # Trust specific keys
    - ABCD1234EF567890ABCD1234EF567890ABCD1234
```

## Requiring Signatures

### For Consumers

Force signature verification on all installs:

```bash
# Require signatures globally
aam config set security.require_signature true

# Now all installs will verify signatures
aam install @author/my-package
# Error: Package is not signed
```

### For Organizations

Registry administrators can enforce signing:

```bash
# In registry .env:
REQUIRE_SIGNATURES=true

# Now all published packages must be signed
aam publish
# Error: Package must be signed. Use --sign flag.
```

## Signature Storage

### Local Registry

Signatures stored alongside packages:

```
registry/
└── packages/
    └── author--my-package/
        ├── 1.0.0.aam
        └── 1.0.0.sig          # Signature file
```

### HTTP Registry

Signatures stored in database and S3:

- Package archive in S3: `s3://aam-packages/@author/my-package/1.0.0.aam`
- Signature in database: `signatures` table
- Sigstore certificate: Stored with signature
- Transparency log URL: Stored with signature

## Trust Models

### Sigstore Trust Model

**Trust chain:**

1. Trust OIDC issuer (GitHub, Google)
2. Verify certificate issued by Sigstore CA
3. Check transparency log entry
4. Verify identity matches package author

**Benefits:**

- No key management
- Identity tied to existing accounts
- Public transparency log
- Automatic key rotation

### GPG Trust Model

**Trust chain:**

1. Obtain author's public key
2. Verify key authenticity (fingerprint, keyserver, web of trust)
3. Add key to trusted keyring
4. Verify signature with trusted key

**Benefits:**

- Established standard
- Full control over keys
- Works offline
- No third-party services

## Best Practices

### For Package Authors

1. **Always sign packages:**
   ```bash
   aam publish --sign
   ```

2. **Use Sigstore for simplicity:**
   - No key management
   - Identity-based
   - Automatic expiration

3. **Use GPG for long-term verification:**
   - Keys under your control
   - Works offline
   - Established tooling

4. **Sign every version:**
   - Don't skip signing
   - Use CI/CD automation

### For Consumers

1. **Verify signatures when possible:**
   ```bash
   aam install @author/my-package --verify-signature
   ```

2. **Enable verification globally:**
   ```bash
   aam config set security.require_signature true
   ```

3. **Check transparency logs (Sigstore):**
   ```bash
   aam info @author/my-package
   # Look for "Transparency log: verified"
   ```

4. **Maintain GPG keyring:**
   - Import and verify author keys
   - Keep keyring up to date
   - Use keyservers for key discovery

### For Organizations

1. **Enforce signing in registry:**
   ```bash
   REQUIRE_SIGNATURES=true
   ```

2. **Maintain list of trusted keys/identities:**
   ```yaml
   security:
     trusted_sigstore_identities:
       - alice@github
       - bob@github
     trusted_gpg_keys:
       - ABCD1234EF567890ABCD1234EF567890ABCD1234
   ```

3. **Audit signing compliance:**
   ```bash
   # Check unsigned packages
   aam search --filter unsigned
   ```

4. **Integrate with CI/CD:**
   - Sign automatically in publish pipelines
   - Verify in install pipelines

## Troubleshooting

### Sigstore Authentication Failed

**Symptom:** Browser doesn't open or authentication fails.

**Solutions:**

1. **Check Sigstore installation:**
   ```bash
   pip install --upgrade sigstore
   ```

2. **Manual OIDC flow:**
   ```bash
   aam publish --sign --oidc-manual
   ```

3. **Use different issuer:**
   ```bash
   aam config set security.oidc_issuer https://accounts.google.com
   ```

### GPG Key Not Found

**Symptom:** `Error: GPG key 'alice@example.com' not found`

**Solution:**

```bash
# List available keys
gpg --list-keys

# Update config with correct key
aam config set security.gpg_key <correct-key-id>
```

### Signature Verification Failed

**Symptom:** `Error: Signature verification failed`

**Causes:**

1. Package tampered with
2. Wrong public key
3. Expired certificate (Sigstore)
4. Network issue (transparency log)

**Solutions:**

```bash
# Check package info
aam info @author/my-package@1.0.0

# Re-download package
aam install @author/my-package --force

# Skip verification (not recommended)
aam install @author/my-package --no-verify
```

### Transparency Log Unreachable

**Symptom:** Can't verify Sigstore transparency log.

**Solution:**

```bash
# Temporary: Skip transparency log check
aam config set security.verify_transparency_log false

# Or use cached verification
aam install @author/my-package --use-cached-verification
```

## Advanced Topics

### Custom Sigstore Instance

Use your own Sigstore deployment:

```yaml
security:
  sigstore_endpoint: https://sigstore.myorg.com
  sigstore_oidc_issuer: https://auth.myorg.com
```

### Multiple Signing Keys (GPG)

Sign with multiple keys for redundancy:

```bash
# Sign with multiple keys
aam publish --sign --gpg-keys alice@example.com,backup@example.com
```

### Signature Delegation

Authorize others to sign on your behalf:

```yaml
security:
  signing_delegates:
    - user: bob@github
      packages:
        - "@author/package1"
        - "@author/package2"
```

### Offline Verification

Pre-fetch keys for offline verification:

```bash
# Download all signatures and certificates
aam verify --offline-prepare @author/my-package

# Verify offline
aam verify --offline @author/my-package
```

## Next Steps

- [HTTP Registry](http-registry.md) - Registry with signature storage
- [Security Concept](../concepts/security.md) - Security fundamentals
- [Hosting a Registry](hosting-registry.md) - Production deployment
- [Configuration: Security](../configuration/security.md) - Detailed security config
