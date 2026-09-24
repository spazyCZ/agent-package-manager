# aam cache ls

**Cache**

## Synopsis

```bash
aam cache ls
```

## Description

List cached package archives in the local download cache, along with
their size and total cache usage.

## Examples

### Example 1: List cached packages

```bash
aam cache ls
```

**Output:**
```
Cached packages (2):

  my-pkg@1.2.0  128.4 KB
  other-pkg@2.0.0  56.1 KB

  Total: 184.5 KB
```

**Output (empty cache):**
```
Cache is empty.
```

## Related commands

- [`aam cache clean`](cache-clean.md) — Remove cached package archives
