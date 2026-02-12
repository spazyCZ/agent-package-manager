# aam registry init

**Registry Management**

## Synopsis

```bash
aam registry init PATH [OPTIONS]
```

## Description

Create a new local file-based registry. Initializes the directory structure with `registry.yaml`, `index.yaml`, and `packages/` directory. Local registries are simple, require no server infrastructure, and can be shared via file systems, NFS, or git.

After initialization, use `aam registry add` to register it for use.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PATH | Yes | Directory path for the new registry |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--default` | | false | Also register and set as default |
| `--force` | | false | Reinitialize even if registry exists |

## Examples

### Example 1: Initialize Local Registry

```bash
aam registry init ~/my-packages
```

**Output:**
```
✓ Created local registry at /home/user/my-packages
  registry.yaml
  index.yaml
  packages/
```

### Example 2: Initialize and Set as Default

```bash
aam registry init ~/my-packages --default
```

**Output:**
```
✓ Created local registry at /home/user/my-packages
  registry.yaml
  index.yaml
  packages/

✓ Registered as default: 'my-packages' (file:///home/user/my-packages)
```

Now you can publish and install without additional configuration.

### Example 3: Reinitialize Existing Registry

```bash
aam registry init ~/my-packages --force
```

**Output:**
```
✓ Created local registry at /home/user/my-packages
  registry.yaml
  index.yaml
  packages/
```

Recreates the directory structure. Existing packages are preserved.

### Example 4: Initialize in Shared Location

```bash
aam registry init /mnt/shared/team-packages
```

Creates a registry on a shared file system (NFS, SMB, etc.) that multiple team members can use.

### Example 5: Initialize for Git Sharing

```bash
mkdir my-registry-repo && cd my-registry-repo
git init
aam registry init . --default
git add .
git commit -m "Initialize AAM registry"
git push origin main
```

Creates a git-based registry that can be shared by cloning.

### Example 6: Permission Error

```bash
aam registry init /root/packages
```

**Output:**
```
Error: Cannot write to /root/packages: Permission denied.
Suggestion: Check directory permissions or choose a different location with write access.
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - registry created |
| 1 | Error - path exists (without --force) or permission denied |

## Registry Structure

After initialization:

```
my-packages/
├── registry.yaml       # Registry metadata
├── index.yaml          # Package index (searchable)
└── packages/           # Archive storage
```

### registry.yaml

```yaml
name: my-packages
type: local
created_at: '2026-02-09T14:30:00Z'
version: 1.0
```

### index.yaml

```yaml
packages: {}
last_updated: '2026-02-09T14:30:00Z'
```

Initially empty, populated when you publish packages.

## Related Commands

- [`aam registry add`](registry-add.md) - Register the initialized registry
- [`aam registry list`](registry-list.md) - List all registries
- [`aam pkg publish`](publish.md) - Publish packages to the registry

## Notes

### Path Expansion

Paths are expanded:

- `~/my-packages` → `/home/user/my-packages`
- `./local-registry` → `/current/directory/local-registry`
- `/absolute/path` → `/absolute/path`

### Default Flag Convenience

Using `--default` combines initialization and registration:

```bash
# Without --default (two steps):
aam registry init ~/packages
aam registry add local file:///home/user/packages --default

# With --default (one step):
aam registry init ~/packages --default
```

### Force Reinitialization

`--force` recreates the structure but:

- Preserves existing packages in `packages/`
- Resets `registry.yaml` to defaults
- Clears `index.yaml` (requires rebuild)

To rebuild the index after force init:

```bash
aam registry rebuild-index ~/packages  # Planned feature
```

### Shared Registries

**Network file systems:**

```bash
# Mount shared drive
mount -t nfs server:/share /mnt/registry

# Initialize
aam registry init /mnt/registry --default

# Other team members:
aam registry add team file:///mnt/registry --default
```

**Git-based sharing:**

```bash
# Initialize and push
aam registry init my-registry --default
cd my-registry
git init && git add . && git commit -m "Init"
git remote add origin git@github.com:team/registry.git
git push -u origin main

# Other team members:
git clone git@github.com:team/registry.git
aam registry add team file:///path/to/registry --default
```

### Permissions

Ensure the directory is writable:

```bash
mkdir ~/my-packages
chmod 755 ~/my-packages
aam registry init ~/my-packages
```

For shared registries, set group permissions:

```bash
sudo mkdir /opt/aam-registry
sudo chgrp developers /opt/aam-registry
sudo chmod 775 /opt/aam-registry
aam registry init /opt/aam-registry
```

### Registry Naming

The registry name is derived from the directory name:

- `~/my-packages` → registry name: `my-packages`
- `/opt/team-registry` → registry name: `team-registry`

### Multiple Registries

You can initialize multiple registries:

```bash
aam registry init ~/public-packages
aam registry init ~/private-packages
aam registry init ~/experimental-packages

aam registry add public file:///home/user/public-packages --default
aam registry add private file:///home/user/private-packages
aam registry add experimental file:///home/user/experimental-packages
```

### HTTP Registries

To set up an HTTP registry instead of a local one, see the HTTP registry deployment guide. HTTP registries support:

- Authentication and access control
- Download analytics
- Package signing verification
- Web UI for discovery

Local registries are simpler but lack these features.
