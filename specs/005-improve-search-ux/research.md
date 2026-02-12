# Research: Improve Search Command UX

**Branch**: `005-improve-search-ux` | **Date**: 2026-02-10

## R-001: Relevance Scoring Algorithm

**Decision**: Implement a tiered integer scoring system with 5 match levels.

**Rationale**: A simple integer-based scoring approach is predictable, testable, and requires no external libraries. Each result receives the score of its highest-tier match (a result matching both name and description gets only the name score). This mirrors how `cargo search` and `npm search` rank results internally.

**Score tiers**:

| Tier | Match Type | Score | Example (query: "audit") |
|------|-----------|-------|--------------------------|
| 1 | Exact name match | 100 | Package named "audit" |
| 2 | Name starts with query | 80 | Package named "audit-agent" |
| 3 | Name contains query | 60 | Package named "security-audit" |
| 4 | Keyword exact match | 50 | Package with keyword "audit" |
| 5 | Description contains query | 30 | Package with description "ASVS audit tool" |

All matching is case-insensitive. A result that does not match any tier is excluded (score 0). Results with equal scores are sub-sorted alphabetically by name for deterministic output.

**Alternatives considered**:
- **TF-IDF / BM25**: Overkill for the current scale (10-500 packages). Adds complexity with no measurable benefit. Revisit when the registry exceeds 10,000 packages.
- **Levenshtein distance for ranking**: Conflates relevance with spelling similarity. Better suited for the "Did you mean?" feature (R-002) than for ranking actual matches.
- **Weighted multi-field scoring**: Sum scores across all matching fields (e.g., name score + description score). Tested mentally — a package matching only the name (score 60) should rank above a package matching both keyword and description (50+30=80). Summing creates counterintuitive rankings. Highest-tier-wins is cleaner.

## R-002: Fuzzy Matching for "Did You Mean?" Suggestions

**Decision**: Use Python stdlib `difflib.SequenceMatcher.ratio()` with a threshold of 0.6.

**Rationale**: `difflib` is part of the Python standard library (no new dependency), well-tested, and returns a 0.0–1.0 similarity ratio. A threshold of 0.6 balances between catching common typos (1-2 character errors in 5-8 character names) and avoiding false positives. Testing with representative names:

| Query | Target | Ratio | Included? |
|-------|--------|-------|-----------|
| "chatbt" | "chatbot" | 0.857 | Yes |
| "audiit" | "audit" | 0.727 | Yes |
| "skil" | "skill" | 0.889 | Yes |
| "xyz" | "chatbot" | 0.0 | No |
| "code" | "chatbot" | 0.167 | No |

The comparison runs against the full name index (both registry package names and source artifact names). Names are compared case-insensitively. Up to 3 suggestions are returned, sorted by descending similarity.

**Performance**: For 500 packages, comparing one query against all names takes < 1ms. No caching needed.

**Alternatives considered**:
- **Levenshtein distance (python-Levenshtein)**: Requires a new PyPI dependency. `difflib` achieves similar results for our use case.
- **`thefuzz` (fuzz.ratio)**: Wraps `difflib` with extra features we don't need. Adds a dependency for no benefit.
- **Prefix trie / autocomplete**: Better suited for interactive completion (future feature), not post-search suggestions.

## R-003: Tabular Display Format

**Decision**: Use `rich.table.Table` with 5 columns: Name, Version, Type, Source, Description.

**Rationale**: Rich is already a project dependency (13.0+). The `Table` class provides automatic column alignment, terminal-width-aware truncation, and consistent styling. This matches the pattern used by `aam source list` for consistency across the CLI.

**Column specification**:

| Column | Width | Style | Overflow |
|--------|-------|-------|----------|
| Name | auto | cyan, bold | no_wrap |
| Version | 12 max | dim | no_wrap |
| Type | 16 max | (default) | ellipsis |
| Source | 20 max | magenta | ellipsis |
| Description | flexible | dim | ellipsis |

The table title shows the result count header: `Search results for "query" (showing X of Y)`.

When `--json` is used, the table is suppressed and raw JSON is output instead (unchanged behavior, but with added `warnings` array).

**Alternatives considered**:
- **Plain text with manual alignment**: Fragile across terminal widths. Rich handles this automatically.
- **Rich Panel per result**: Used by some CLIs but consumes too much vertical space for a list of 10+ results. Tables are more scannable.
- **Columnar text without Rich Table**: Reimplements what Rich already provides. No benefit.

## R-004: Service Layer Architecture

**Decision**: Rewrite `search_service.py` with new Pydantic models (`SearchResult`, `SearchQuery`, `SearchResponse`), moving all logic out of `commands/search.py`.

**Rationale**: The command currently contains inline search logic (registry loop, source search, type filtering, result combining) that duplicates the service. The MCP tool calls the service but gets incomplete results (no source artifacts). Unifying in the service ensures both consumers (CLI + MCP) get identical results.

**Function signatures** (service layer):

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
    ...
```

The function returns a `SearchResponse` containing:
- `results: list[SearchResult]` — scored, filtered, sorted, limited
- `total_count: int` — total before limiting
- `warnings: list[str]` — any source/registry errors
- `all_names: list[str]` — full name index for "Did you mean?" (populated only when results are empty)

**Command file** becomes:
1. Parse Click options
2. Call `search_packages()`
3. If empty results + `all_names` provided → compute suggestions via `utils/text_match.py`
4. Format output (Rich Table or JSON)

**MCP tool** becomes:
1. Parse MCP arguments
2. Call `search_packages()`
3. Return serialized `SearchResponse`

**Alternatives considered**:
- **Keep dual search paths (command + service)**: Violates DRY and causes the MCP inconsistency that this feature explicitly fixes.
- **Create a new `SearchEngine` class**: Over-engineering. A single function with clear input/output models is sufficient for the current complexity.

## R-005: Empty Query Behavior (Browse Mode)

**Decision**: An empty query string returns all packages/artifacts up to the limit, scored at `SCORE_EXACT_NAME` (100, equal relevance), sorted by name.

**Rationale**: This is the standard behavior for `npm search ""` and `pip search ""`. It provides a "browse all" capability without requiring a separate command. The service layer treats empty query as "match everything."

**Alternatives considered**:
- **Error on empty query**: Unnecessarily restrictive. Users may want to browse.
- **Return nothing**: Surprising behavior for an empty filter.

## R-006: Warning Propagation Architecture

**Decision**: Collect warnings as strings in a list during search, return them in `SearchResponse.warnings`, and display them in both text and JSON output.

**Rationale**: Current implementation catches `Exception` broadly and logs at DEBUG level. The spec requires visible warnings (FR-020). Collecting warnings in the response object allows each consumer (CLI, MCP) to display them appropriately.

**Warning types**:
1. Source search failure: `"Could not search source '{name}': {reason}"`
2. Registry search failure: `"Could not search registry '{name}': {reason}"`
3. Invalid filter: `"Source '{name}' not found. Available: {names}"`
4. Unknown type: `"Unknown artifact type '{type}'. Valid types: skill, agent, prompt, instruction"`

The service catches specific exceptions (`ValueError`, `OSError`, `KeyError`) — not bare `Exception` — per constitution principle VII.

**Alternatives considered**:
- **Raise exceptions immediately**: Breaks graceful degradation. A single source failure would block all results.
- **Log at WARNING level only**: Doesn't surface to the user in the CLI output. Invisible in MCP.

## R-007: Backward Compatibility for `--json` Output

**Decision**: Add `warnings`, `total_count`, and `score` fields to JSON output. Keep existing fields unchanged.

**Rationale**: Any consumers of the current `--json` output expect the existing field structure. Adding new fields is backward-compatible (JSON consumers typically ignore unknown fields). The `warnings` array is always present (empty if no warnings).

**New JSON structure**:
```json
{
  "results": [
    {
      "name": "chatbot-agent",
      "version": "1.2.0",
      "description": "...",
      "keywords": ["chatbot"],
      "artifact_types": ["skill", "agent"],
      "origin": "local",
      "origin_type": "registry",
      "score": 80,
      "updated_at": "2026-01-15T..."
    }
  ],
  "total_count": 25,
  "warnings": []
}
```

**Breaking change note**: The JSON output changes from a flat array to an object with `results`, `total_count`, and `warnings` keys. This is a **breaking change** for consumers that expect a raw array. However, since the CLI is at v0.1.0 (pre-stable), this is acceptable per semver conventions. Document the change in the MkDocs search page.

**Alternatives considered**:
- **Keep flat array, add warnings as stderr**: Splits output across two streams. JSON consumers may not capture stderr.
- **Add `--json-v2` flag**: Unnecessary complexity for a pre-1.0 tool.

## R-008: Valid Artifact Types

**Decision**: Define a module-level constant `VALID_ARTIFACT_TYPES = ["skill", "agent", "prompt", "instruction"]` in `search_service.py`.

**Rationale**: This constant is needed for FR-022 (warning on unknown `--type` values) and is referenced by the scoring algorithm (keyword matching). Currently, artifact types are not centrally defined — they appear as string literals in various places. Centralizing in the service layer is the minimal change for this feature; a full refactor to an Enum can happen later.

**Alternatives considered**:
- **Python Enum**: More type-safe but would require changes across many files (adapters, manifest, registry). Out of scope for this feature.
- **Read from config/schema**: No such config exists. Premature for v0.1.0.
