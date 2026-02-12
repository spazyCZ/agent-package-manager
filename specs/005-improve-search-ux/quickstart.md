# Quickstart: Improve Search Command UX

**Branch**: `005-improve-search-ux` | **Date**: 2026-02-10

## Implementation Order

The implementation follows a bottom-up approach: utilities first, then service layer, then CLI command, then MCP tool, then docs. Each phase is independently testable.

### Phase 1: Utility Layer (no dependencies on other changes)

**Create** `apps/aam-cli/src/aam_cli/utils/text_match.py`:

```python
"""Text matching utilities for search scoring and fuzzy suggestions."""

import difflib
import logging

logger = logging.getLogger(__name__)

SUGGESTION_THRESHOLD = 0.6
MAX_SUGGESTIONS = 3

def find_similar_names(
    query: str,
    names: list[str],
    threshold: float = SUGGESTION_THRESHOLD,
    max_suggestions: int = MAX_SUGGESTIONS,
) -> list[str]:
    """Find names similar to query for 'Did you mean?' suggestions."""
    ...
```

**Create** `apps/aam-cli/tests/unit/test_unit_text_match.py`:

Test cases:
- `test_unit_similar_names_exact_typo` — "chatbt" → "chatbot-agent"
- `test_unit_similar_names_no_match` — "xyz" → empty list
- `test_unit_similar_names_multiple` — multiple suggestions sorted by similarity
- `test_unit_similar_names_threshold` — names below threshold excluded
- `test_unit_similar_names_max_limit` — respects max_suggestions

### Phase 2: Service Layer (depends on Phase 1)

**Rewrite** `apps/aam-cli/src/aam_cli/services/search_service.py`:

1. Add Pydantic models: `SearchResult`, `SearchResponse`
2. Add scoring constants: `SCORE_EXACT_NAME`, `SCORE_NAME_PREFIX`, etc.
3. Add `VALID_ARTIFACT_TYPES` and `VALID_SORT_OPTIONS` constants
4. Implement `compute_relevance_score()` function
5. Rewrite `search_packages()` to:
   - Accept new parameters (package_types, source_filter, registry_filter, sort_by)
   - Return `SearchResponse` instead of `list[dict]`
   - Search both registries and sources
   - Score, filter, sort results
   - Collect warnings for failures
   - Populate `all_names` when results empty

**Expand** `apps/aam-cli/tests/unit/test_services_search.py`:

New test cases:
- `test_unit_search_relevance_exact_name_first` — exact match scores highest
- `test_unit_search_relevance_prefix_before_substring` — prefix > substring
- `test_unit_search_relevance_name_before_description` — name > description
- `test_unit_search_sources_included` — source artifacts in results
- `test_unit_search_sources_only_no_registry` — works without registries
- `test_unit_search_source_failure_warning` — warning on source failure
- `test_unit_search_registry_failure_warning` — warning on registry failure
- `test_unit_search_type_filter_multiple` — multi-type filtering
- `test_unit_search_source_filter` — source name filter
- `test_unit_search_registry_filter` — registry name filter
- `test_unit_search_sort_name` — alphabetical sorting
- `test_unit_search_sort_recent` — date sorting
- `test_unit_search_empty_query_browse` — empty query returns all
- `test_unit_search_total_count_with_limit` — total_count vs limited results
- `test_unit_search_all_names_on_empty_results` — all_names populated
- `test_unit_search_unknown_type_warning` — warning for invalid type
- `test_unit_search_response_model_validation` — Pydantic model validation
- Keep existing tests (update to match new return type)

### Phase 3: CLI Command (depends on Phase 2)

**Rewrite** `apps/aam-cli/src/aam_cli/commands/search.py`:

1. Add Click options: `--type` (multiple), `--source`, `--registry`, `--sort`
2. Remove all inline search logic (registry loop, source search, type filtering)
3. Call `search_packages()` from service
4. On empty results: call `find_similar_names()` with `response.all_names`
5. Display warnings from `response.warnings`
6. Display results as `rich.table.Table`
7. Show "Showing X of Y" when truncated
8. JSON output: serialize `SearchResponse` with envelope structure

### Phase 4: MCP Tool (depends on Phase 2)

**Update** `apps/aam-cli/src/aam_cli/mcp/tools_read.py`:

1. Update `aam_search()` signature with new parameters
2. Call `search_packages()` with new parameters
3. Serialize `SearchResponse` to dict and return
4. Update existing MCP tests in `tests/unit/test_mcp_tools_read.py`

### Phase 5: Documentation

**Update** `docs/user_docs/docs/cli/search.md`:

1. Add new options to Options table: `--source`, `--registry`, `--sort`
2. Update `--type` description to mention multiple values
3. Add examples for multi-type, source filter, sorting
4. Update JSON output example with envelope structure
5. Update "Search behavior" section with relevance scoring explanation
6. Add "Did you mean?" section
7. Document the JSON output breaking change

## Key Files Reference

| File | Action | Purpose |
|------|--------|---------|
| `src/aam_cli/utils/text_match.py` | CREATE | Fuzzy matching utility |
| `src/aam_cli/services/search_service.py` | REWRITE | Unified search with scoring |
| `src/aam_cli/commands/search.py` | REWRITE | Thin presentation layer |
| `src/aam_cli/mcp/tools_read.py` | MODIFY | Update MCP tool parameters |
| `tests/unit/test_unit_text_match.py` | CREATE | Fuzzy matching tests |
| `tests/unit/test_services_search.py` | EXPAND | Service layer tests |
| `docs/user_docs/docs/cli/search.md` | UPDATE | User documentation |

## Verification

After implementation, verify:

```bash
# Run unit tests
npx nx test aam-cli

# Manual smoke tests
aam search chatbot                    # Relevance-ranked table output
aam search doc --type skill           # Type filtering
aam search doc --source google-gemini # Source filtering
aam search agent --sort name          # Alphabetical sorting
aam search chatbt                     # "Did you mean?" suggestions
aam search chatbot --json             # JSON envelope output
```
