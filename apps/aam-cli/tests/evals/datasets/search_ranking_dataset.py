"""Ranking accuracy evaluation dataset for SC-001.

Contains query-expected-top-3 pairs to verify that
``compute_relevance_score()`` places the expected package in the
top 3 results for >=90% of cases.

SC-001: 90% top-3 ranking accuracy.
"""

################################################################################
#                                                                              #
# DATASET                                                                      #
#                                                                              #
################################################################################

# Each entry: (query, list_of_candidate_dicts, expected_top_3_names)
# candidate_dict: {"name": ..., "description": ..., "keywords": [...]}

RANKING_DATASET: list[dict] = [
    {
        "query": "audit",
        "candidates": [
            {"name": "audit", "description": "ASVS audit", "keywords": ["audit"]},
            {"name": "audit-agent", "description": "Agent for auditing", "keywords": []},
            {"name": "security-audit", "description": "Security tool", "keywords": ["security"]},
            {"name": "data-tool", "description": "Data processing", "keywords": ["data"]},
            {"name": "my-audit-helper", "description": "Helper", "keywords": ["audit"]},
        ],
        "expected_top_3": ["audit", "audit-agent", "my-audit-helper"],
        "must_include": "audit",
    },
    {
        "query": "chatbot",
        "candidates": [
            {"name": "chatbot", "description": "A chatbot", "keywords": ["chat"]},
            {"name": "chatbot-agent", "description": "Chat agent", "keywords": []},
            {"name": "my-chatbot-skill", "description": "Chatbot skill", "keywords": []},
            {"name": "unrelated", "description": "Nothing here", "keywords": []},
        ],
        "expected_top_3": ["chatbot", "chatbot-agent", "my-chatbot-skill"],
        "must_include": "chatbot",
    },
    {
        "query": "code",
        "candidates": [
            {"name": "code-review", "description": "Review code", "keywords": ["code"]},
            {"name": "code", "description": "Exact match", "keywords": []},
            {"name": "barcode-reader", "description": "Reads barcodes", "keywords": []},
            {"name": "my-tool", "description": "A code linting tool", "keywords": ["lint"]},
        ],
        "expected_top_3": ["code", "code-review", "barcode-reader"],
        "must_include": "code",
    },
    {
        "query": "install",
        "candidates": [
            {"name": "install-helper", "description": "Install tool", "keywords": ["install"]},
            {"name": "auto-install", "description": "Automatic installer", "keywords": []},
            {"name": "package-manager", "description": "Install packages easily", "keywords": ["install"]},
            {"name": "test-tool", "description": "Testing utility", "keywords": []},
        ],
        "expected_top_3": ["install-helper", "auto-install", "package-manager"],
        "must_include": "install-helper",
    },
    {
        "query": "data",
        "candidates": [
            {"name": "data", "description": "Data utilities", "keywords": ["data"]},
            {"name": "data-agent", "description": "Data analysis agent", "keywords": []},
            {"name": "metadata-tool", "description": "Metadata management", "keywords": []},
            {"name": "big-data-skill", "description": "Big data", "keywords": ["data"]},
            {"name": "analytics", "description": "Data analytics", "keywords": ["data"]},
        ],
        "expected_top_3": ["data", "data-agent", "big-data-skill"],
        "must_include": "data",
    },
    {
        "query": "prompt",
        "candidates": [
            {"name": "prompt-builder", "description": "Build prompts", "keywords": ["prompt"]},
            {"name": "system-prompt", "description": "System prompt manager", "keywords": []},
            {"name": "prompt", "description": "Exact match", "keywords": ["prompt"]},
            {"name": "other-tool", "description": "Unrelated tool", "keywords": []},
        ],
        "expected_top_3": ["prompt", "prompt-builder", "system-prompt"],
        "must_include": "prompt",
    },
    {
        "query": "skill",
        "candidates": [
            {"name": "skill-creator", "description": "Create skills", "keywords": ["skill"]},
            {"name": "my-skill", "description": "A custom skill", "keywords": []},
            {"name": "reskill", "description": "Reskilling tool", "keywords": []},
            {"name": "tool-x", "description": "A skill-based helper", "keywords": ["skill"]},
        ],
        "expected_top_3": ["skill-creator", "my-skill", "reskill"],
        "must_include": "skill-creator",
    },
    {
        "query": "security",
        "candidates": [
            {"name": "security", "description": "Security suite", "keywords": ["security"]},
            {"name": "security-audit", "description": "Audit tool", "keywords": []},
            {"name": "infosec", "description": "Information security", "keywords": ["security"]},
            {"name": "firewall", "description": "Network firewall", "keywords": []},
        ],
        "expected_top_3": ["security", "security-audit", "infosec"],
        "must_include": "security",
    },
    {
        "query": "doc",
        "candidates": [
            {"name": "doc-writer", "description": "Write docs", "keywords": ["doc"]},
            {"name": "document-reader", "description": "Read documents", "keywords": []},
            {"name": "docker-tool", "description": "Docker management", "keywords": []},
            {"name": "api-doc", "description": "API documentation", "keywords": ["doc"]},
        ],
        "expected_top_3": ["doc-writer", "docker-tool", "api-doc"],
        "must_include": "doc-writer",
    },
    {
        "query": "test",
        "candidates": [
            {"name": "test-runner", "description": "Run tests", "keywords": ["test"]},
            {"name": "test", "description": "Exact match", "keywords": ["test"]},
            {"name": "contest-app", "description": "Contest tool", "keywords": []},
            {"name": "qa-tool", "description": "Test automation", "keywords": ["test"]},
        ],
        "expected_top_3": ["test", "test-runner", "contest-app"],
        "must_include": "test",
    },
]
