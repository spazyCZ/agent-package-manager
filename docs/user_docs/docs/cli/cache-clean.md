# aam cache clean

**Cache**

## Synopsis

```bash
aam cache clean [PACKAGE_SPEC]
```

## Description

Remove cached package archives from the local download cache. With no
argument, clears the entire cache. With `name@version`, removes only
the cached entries for that specific package version.

## Arguments

| Argument | Description |
|----------|-------------|
| `PACKAGE_SPEC` | Optional — a specific `name@version` to remove. Clears the whole cache if omitted. |

## Examples

### Example 1: Clean the entire cache

```bash
aam cache clean
```

### Example 2: Clean a specific package version

```bash
aam cache clean my-pkg@1.2.0
```

## Related commands

- [`aam cache ls`](cache-ls.md) — List cached package archives
