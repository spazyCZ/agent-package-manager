# Data Model: Improve Search Command UX

**Branch**: `005-improve-search-ux` | **Date**: 2026-02-10

## Entity Relationship

```
SearchQuery ──calls──▶ search_packages() ──returns──▶ SearchResponse
                                                         │
                                                         ├── results: list[SearchResult]
                                                         ├── total_count: int
                                                         ├── warnings: list[str]
                                                         └── all_names: list[str]
```

## Entities

### SearchResult

A unified search result representing either a registry package or a source artifact. Used by both CLI display and MCP tool response.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | `str` | Yes | Package or artifact name (e.g., "chatbot-agent") |
| version | `str` | Yes | Version string (e.g., "1.2.0" or "source@da66c7c") |
| description | `str` | Yes | Human-readable description (empty string if none) |
| keywords | `list[str]` | Yes | Package keywords from manifest (empty list for sources) |
| artifact_types | `list[str]` | Yes | Artifact types: "skill", "agent", "prompt", "instruction" |
| origin | `str` | Yes | Origin label: registry name (e.g., "local") or source qualified name (e.g., "[source] google-gemini/gemini-cli:skills") |
| origin_type | `str` | Yes | Discriminator: "registry" or "source" |
| score | `int` | Yes | Relevance score (0-100). See research.md R-001 for tiers. |
| updated_at | `str` | No | ISO 8601 timestamp of last update (empty for sources without date info) |

**Validation rules**:
- `name` must be non-empty
- `score` must be >= 0 and <= 100
- `origin_type` must be one of: "registry", "source"
- `artifact_types` entries must be from: "skill", "agent", "prompt", "instruction"

**Pydantic model location**: `apps/aam-cli/src/aam_cli/services/search_service.py`

### SearchQuery

The user's search parameters. Not persisted — constructed from CLI arguments or MCP tool parameters for each invocation.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| query | `str` | Yes | — | Search string (case-insensitive). Empty string = browse mode. |
| limit | `int` | Yes | 10 | Maximum results to return. Valid range: 1-50. |
| package_types | `list[str]` | No | None (all) | Filter by artifact types (OR logic). |
| source_filter | `str` | No | None (all) | Limit to a specific git source name. |
| registry_filter | `str` | No | None (all) | Limit to a specific registry name. |
| sort_by | `str` | Yes | "relevance" | Sort order: "relevance", "name", "recent". |

**Validation rules**:
- `limit` must be between `MIN_SEARCH_LIMIT` (1) and `MAX_SEARCH_LIMIT` (50)
- `sort_by` must be one of: "relevance", "name", "recent"
- `package_types` entries (if provided) are validated against `VALID_ARTIFACT_TYPES`; unknown types generate a warning but do not error

**Note**: `SearchQuery` is used internally for documentation clarity. The service function accepts these as individual parameters rather than requiring callers to construct a query object. This keeps the API simple for both CLI and MCP consumers.

### SearchResponse

Response envelope returned by the search service. Contains results, metadata, and any warnings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| results | `list[SearchResult]` | Yes | Scored, filtered, sorted, and limited results |
| total_count | `int` | Yes | Total matches before limiting (for "Showing X of Y") |
| warnings | `list[str]` | Yes | User-facing warning messages (empty list if none) |
| all_names | `list[str]` | Yes | Full name index from all sources. Populated only when `results` is empty (for "Did you mean?" computation). Empty list otherwise. |

**Validation rules**:
- `total_count` >= len(`results`)
- `warnings` may be empty but must not be None

**Pydantic model location**: `apps/aam-cli/src/aam_cli/services/search_service.py`

## Constants

Defined in `apps/aam-cli/src/aam_cli/services/search_service.py`:

| Constant | Value | Description |
|----------|-------|-------------|
| `MIN_SEARCH_LIMIT` | 1 | Minimum allowed limit (existing) |
| `MAX_SEARCH_LIMIT` | 50 | Maximum allowed limit (existing) |
| `DEFAULT_SEARCH_LIMIT` | 10 | Default limit (existing) |
| `VALID_ARTIFACT_TYPES` | `["skill", "agent", "prompt", "instruction"]` | Valid type filter values |
| `VALID_SORT_OPTIONS` | `["relevance", "name", "recent"]` | Valid sort options |
| `SCORE_EXACT_NAME` | 100 | Score for exact name match |
| `SCORE_NAME_PREFIX` | 80 | Score for name-starts-with match |
| `SCORE_NAME_CONTAINS` | 60 | Score for name-contains match |
| `SCORE_KEYWORD_MATCH` | 50 | Score for keyword exact match |
| `SCORE_DESCRIPTION_CONTAINS` | 30 | Score for description-contains match |
| ~~`SUGGESTION_THRESHOLD`~~ | — | Moved to `text_match.py` (see below) |
| ~~`MAX_SUGGESTIONS`~~ | — | Moved to `text_match.py` (see below) |

Defined in `apps/aam-cli/src/aam_cli/utils/text_match.py` **(canonical owner)**:

| Constant | Value | Description |
|----------|-------|-------------|
| `SUGGESTION_THRESHOLD` | 0.6 | Minimum similarity ratio for "Did you mean?" suggestions |
| `MAX_SUGGESTIONS` | 3 | Maximum number of suggestions to return |

> **Note**: These constants are owned by `text_match.py` (the module that uses them). They are NOT duplicated in `search_service.py`. If the service layer needs these values, it should import from `text_match`.

## State Transitions

No state transitions — search is a stateless read-only operation. Each invocation builds the full result set from the current registry index and source cache.

## Relationship to Existing Models

| Existing Model | Relationship | Location |
|---------------|-------------|----------|
| `PackageIndexEntry` | Registry search results are converted from `PackageIndexEntry` to `SearchResult` | `registry/base.py` |
| `VirtualPackage` | Source artifacts are converted from `VirtualPackage` to `SearchResult` | `services/source_service.py` |
| `AamConfig` | Provides `registries` and `sources` lists for search scope | `core/config.py` |
| `RegistrySource` | Individual registry to search; `name` used for origin label | `core/config.py` |
| `SourceEntry` | Individual source to index; `name` used for origin label | `core/config.py` |
| `ArtifactIndex` | Built by `build_source_index()`, iterated for source matches | `services/source_service.py` |
