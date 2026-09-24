# aam login

**Authentication**

## Synopsis

```bash
aam login [OPTIONS]
```

## Description

Authenticate with a package registry and save the token locally for
future publish and install operations against that registry.

You will be prompted for the auth token interactively (input is
hidden); it is not accepted via a visible command-line flag.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--registry` | `https://registry.aam.dev` | Registry URL to authenticate with |

## Examples

### Example 1: Log in to the default registry

```bash
aam login
```

### Example 2: Log in to a custom registry

```bash
aam login --registry https://registry.example.com
```

## Related commands

- [`aam logout`](logout.md) — Remove saved registry authentication
- [`aam whoami`](whoami.md) — Show current authentication status
