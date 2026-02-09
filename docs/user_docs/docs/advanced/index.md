# Advanced Topics

This section covers advanced features and use cases for AAM power users and organizations.

## Topics

### [HTTP Registry](http-registry.md)
Learn how to set up and run your own HTTP registry server for centralized package management with authentication, package signing verification, and download statistics.

### [Package Signing](signing.md)
Understand AAM's package signing system using Sigstore for identity-based signing and GPG for traditional cryptographic signatures.

### [Dist-Tags](dist-tags.md)
Use distribution tags to create named aliases for package versions (`latest`, `stable`, `bank-approved`, etc.) for controlled deployments and organizational gates.

### [Scoped Packages](scoped-packages.md)
Organize your packages with namespaces using scoped package names (`@author/package-name`) for better organization and ownership management.

### [Quality & Evals](quality-evals.md)
Add automated tests and evaluations to your packages to measure and publish quality metrics for consumers.

### [Hosting a Registry](hosting-registry.md)
Deploy and operate an AAM HTTP registry in production, including infrastructure recommendations, scaling considerations, and maintenance procedures.

## Who Should Read This?

**You should explore advanced topics if you:**

- Run a team or organization using AAM
- Want to host a private registry
- Need package signing and verification
- Require governance controls (approvals, gates)
- Want to publish quality metrics with your packages
- Need to understand AAM's security model in depth

## Prerequisites

Before diving into advanced topics, you should be comfortable with:

- Basic AAM commands (`install`, `publish`, `search`)
- Creating and publishing packages
- Understanding manifests (`aam.yaml`)
- Platform deployment concepts

## Quick Links

### For Teams

- [HTTP Registry](http-registry.md) - Centralized package sharing
- [Scoped Packages](scoped-packages.md) - Namespace management
- [Dist-Tags](dist-tags.md) - Release gates and channels

### For Security-Focused Users

- [Package Signing](signing.md) - Identity verification
- [Hosting a Registry](hosting-registry.md) - Production deployment

### For Package Authors

- [Quality & Evals](quality-evals.md) - Quality metrics
- [Dist-Tags](dist-tags.md) - Version aliasing

## Additional Resources

- [Security Concept](../concepts/security.md) - Security fundamentals
- [Configuration Reference](../configuration/index.md) - Advanced configuration options
- [Troubleshooting](../troubleshooting/index.md) - Common issues and solutions
