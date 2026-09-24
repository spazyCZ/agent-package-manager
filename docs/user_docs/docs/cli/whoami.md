# aam whoami

**Authentication**

## Synopsis

```bash
aam whoami [OPTIONS]
```

## Description

Show the current authentication status for a registry, including a
masked view of the saved token if logged in.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--registry` | `https://registry.aam.dev` | Registry URL to check |

## Examples

### Example 1: Check default registry status

```bash
aam whoami
```

**Output (logged in):**
```
Logged in to https://registry.aam.dev (token: abcd...wxyz)
```

**Output (not logged in):**
```
Not logged in to https://registry.aam.dev
```

### Example 2: Check a custom registry

```bash
aam whoami --registry https://registry.example.com
```

## Related commands

- [`aam login`](login.md) — Authenticate with a package registry
- [`aam logout`](logout.md) — Remove saved registry authentication
