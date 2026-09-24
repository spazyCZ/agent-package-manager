# aam logout

**Authentication**

## Synopsis

```bash
aam logout [OPTIONS]
```

## Description

Remove the saved authentication token for a registry.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--registry` | `https://registry.aam.dev` | Registry URL to log out of |

## Examples

### Example 1: Log out of the default registry

```bash
aam logout
```

### Example 2: Log out of a custom registry

```bash
aam logout --registry https://registry.example.com
```

## Related commands

- [`aam login`](login.md) — Authenticate with a package registry
- [`aam whoami`](whoami.md) — Show current authentication status
