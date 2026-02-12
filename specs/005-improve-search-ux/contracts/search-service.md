# Contract: Search Service

**Branch**: `005-improve-search-ux` | **Date**: 2026-02-10

## Service: `search_service.py`

**Location**: `apps/aam-cli/src/aam_cli/services/search_service.py`
**Consumers**: CLI command (`commands/search.py`), MCP tool (`mcp/tools_read.py`)

---

### `search_packages()`

Main entry point for all search operations.

**Signature**:

```python
def search_packages(
    query: str,
    config: AamConfig,
    limit: int = DEFAULT_SEARCH_LIMIT,
    package_types: list[str] | None = None,
    source_filter: str | None = None,
    registry_filter: str | None = None,
    sort_by: str = "relevance",
) -> SearchResponse:
```

**Parameters**:

| Parameter | Type | Default | Validation |
|-----------|------|---------|------------|
| `query` | `str` | (required) | Any string including empty. Treated as literal (no regex). |
| `config` | `AamConfig` | (required) | Must have at least one registry or source configured. |
| `limit` | `int` | 10 | 1 ≤ limit ≤ 50. Raises `ValueError` outside range. |
| `package_types` | `list[str] \| None` | None | If provided, each entry validated against `VALID_ARTIFACT_TYPES`. Unknown types generate a warning in response but do not raise. |
| `source_filter` | `str \| None` | None | If provided, must match a `config.sources[].name`. Non-match generates a warning. |
| `registry_filter` | `str \| None` | None | If provided, must match a `config.registries[].name`. Non-match generates a warning. |
| `sort_by` | `str` | "relevance" | Must be one of: "relevance", "name", "recent". Raises `ValueError` for invalid value. |

**Returns**: `SearchResponse` (see data-model.md)

**Raises**:
- `ValueError`: If `limit` is outside [1, 50] or `sort_by` is invalid.

**Behavior**:

1. Validate `limit` and `sort_by`
2. Validate `package_types` — add warning for unknown types, keep valid ones
3. Validate `source_filter` / `registry_filter` — add warning if name not found
4. If no registries AND no sources configured → raise `ValueError` with guidance message
5. Search registries (unless `source_filter` excludes them):
   - For each registry (or filtered registry), call `reg.search(query)`
   - Convert each `PackageIndexEntry` to `SearchResult` with relevance score
   - On failure: catch `(ValueError, OSError, KeyError)`, add warning, continue
6. Search sources (unless `registry_filter` excludes them):
   - Call `build_source_index(config)`
   - Iterate `index.by_qualified_name.values()`
   - Match and score each `VirtualPackage`
   - On failure: catch `(ValueError, OSError)`, add warning, continue
7. Apply `package_types` filter (OR logic across types)
8. Sort by `sort_by`: relevance (score desc, name asc), name (asc), recent (updated_at desc)
9. Compute `total_count` before limiting
10. Apply `limit`
11. If `results` is empty, populate `all_names` with full name index
12. Return `SearchResponse`

**Backward compatibility**:
- The old `search_packages()` returned `list[dict[str, Any]]`. The new version returns `SearchResponse`. The MCP tool must serialize the response appropriately. This is a breaking internal change (not a public API).

---

### `compute_relevance_score()`

Compute the relevance score for a single candidate against a query.

**Signature**:

```python
def compute_relevance_score(
    query_lower: str,
    name_lower: str,
    description_lower: str,
    keywords_lower: list[str],
) -> int:
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `query_lower` | `str` | Lowercased query string |
| `name_lower` | `str` | Lowercased package/artifact name |
| `description_lower` | `str` | Lowercased description |
| `keywords_lower` | `list[str]` | Lowercased keywords |

**Returns**: `int` — score (0-100). Returns 0 if no match.

**Behavior**:

1. If `query_lower` is empty → return `SCORE_EXACT_NAME` (browse mode: everything matches at top score)
2. If `query_lower == name_lower` → return `SCORE_EXACT_NAME` (100)
3. If `name_lower.startswith(query_lower)` → return `SCORE_NAME_PREFIX` (80)
4. If `query_lower in name_lower` → return `SCORE_NAME_CONTAINS` (60)
5. If any keyword equals `query_lower` → return `SCORE_KEYWORD_MATCH` (50)
6. If `query_lower in description_lower` → return `SCORE_DESCRIPTION_CONTAINS` (30)
7. Otherwise → return 0 (no match)

---

## Utility: `text_match.py`

**Location**: `apps/aam-cli/src/aam_cli/utils/text_match.py`

### `find_similar_names()`

Find names similar to a query for "Did you mean?" suggestions.

**Signature**:

```python
def find_similar_names(
    query: str,
    names: list[str],
    threshold: float = SUGGESTION_THRESHOLD,
    max_suggestions: int = MAX_SUGGESTIONS,
) -> list[str]:
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | (required) | The user's original query |
| `names` | `list[str]` | (required) | All known package/artifact names |
| `threshold` | `float` | 0.6 | Minimum similarity ratio |
| `max_suggestions` | `int` | 3 | Maximum suggestions to return |

**Returns**: `list[str]` — Similar names sorted by descending similarity. Empty list if none exceed threshold.

**Behavior**:

1. Lowercase the query
2. For each name in `names`, compute `difflib.SequenceMatcher(None, query_lower, name_lower).ratio()`
3. Filter to those above `threshold`
4. Sort by ratio descending
5. Return top `max_suggestions`

---

## CLI Command: `commands/search.py`

**Responsibilities** (presentation-only):

1. Define Click options: `query` (argument), `--limit`, `--type` (multiple), `--source`, `--registry`, `--sort`, `--json`
2. Call `search_packages()` with parsed arguments
3. If no results and `response.all_names` is populated, call `find_similar_names()` and display suggestions
4. Display warnings from `response.warnings`
5. Display results as Rich Table (or JSON)
6. Show "Showing X of Y" when `total_count > len(results)`

**Click option changes from current**:

| Option | Current | New |
|--------|---------|-----|
| `--type` / `-t` | `str` (single) | `multiple=True` (tuple of strings) |
| `--source` / `-s` | N/A | New option (string) |
| `--registry` / `-r` | N/A | New option (string) |
| `--sort` | N/A | New option (`click.Choice(["relevance", "name", "recent"])`, default "relevance") |

---

## MCP Tool: `mcp/tools_read.py`

**Changes**:

1. Update `aam_search()` to accept new parameters: `package_types` (list), `source_filter`, `registry_filter`, `sort_by`
2. Call `search_packages()` with new signature
3. Serialize `SearchResponse` to dict: `{"results": [...], "total_count": N, "warnings": [...]}`
4. Return the serialized dict (not a raw list)

**MCP tool signature change**:

```python
@mcp.tool(tags={"read"})
def aam_search(
    query: str,
    limit: int = 10,
    package_types: list[str] | None = None,
    source_filter: str | None = None,
    registry_filter: str | None = None,
    sort_by: str = "relevance",
) -> dict[str, Any]:
```
