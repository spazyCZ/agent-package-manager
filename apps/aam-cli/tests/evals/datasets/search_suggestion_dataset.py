"""Suggestion hit-rate evaluation dataset for SC-005.

Contains misspelled-query-expected-suggestion pairs to verify that
``find_similar_names()`` returns the intended package for >=80% of
cases.

SC-005: 80% suggestion hit rate.
"""

################################################################################
#                                                                              #
# DATASET                                                                      #
#                                                                              #
################################################################################

# Each entry: (misspelled_query, all_known_names, expected_suggestion)

SUGGESTION_DATASET: list[dict] = [
    {
        "query": "chatbt",
        "names": ["chatbot", "chatbot-agent", "data-tool", "code-review"],
        "expected": "chatbot",
    },
    {
        "query": "audiit",
        "names": ["audit", "audit-agent", "security-audit", "data-tool"],
        "expected": "audit",
    },
    {
        "query": "skil",
        "names": ["skill", "skill-builder", "agent-tool", "prompt"],
        "expected": "skill",
    },
    {
        "query": "promt",
        "names": ["prompt", "prompt-builder", "agent", "skill"],
        "expected": "prompt",
    },
    {
        "query": "instal",
        "names": ["install", "install-helper", "uninstall", "upgrade"],
        "expected": "install",
    },
    {
        "query": "serch",
        "names": ["search", "search-tool", "list", "info"],
        "expected": "search",
    },
    {
        "query": "codereview",
        "names": ["code-review", "code-review-agent", "audit", "test"],
        "expected": "code-review",
    },
    {
        "query": "dat-tool",
        "names": ["data-tool", "data-agent", "analytics", "test"],
        "expected": "data-tool",
    },
    {
        "query": "securty",
        "names": ["security", "security-audit", "firewall", "test"],
        "expected": "security",
    },
    {
        "query": "chatbot-agnt",
        "names": ["chatbot-agent", "chatbot", "data-tool", "skill"],
        "expected": "chatbot-agent",
    },
]
