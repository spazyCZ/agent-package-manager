"""Recommend AAM skills based on repository analysis.

Analyzes project structure and dependencies to suggest relevant skills
from configured sources. Designed for use with MCP server and IDE agents.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
################################################################################

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aam_cli.services.source_service import ArtifactIndex, VirtualPackage

################################################################################
#                                                                              #
# LOGGING                                                                      #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# DATA MODELS                                                                  #
################################################################################


@dataclass
class RepoContext:
    """Detected repository context for skill recommendation.

    Attributes:
        frontend_frameworks: Detected frontend (e.g., react, vue).
        backend_languages: Detected backend (e.g., python, node).
        has_llm: True if LLM/agent dependencies detected.
        has_docs: True if docs structure (mkdocs, docs/) present.
        has_tests: True if test framework detected.
        platform: Detected AI platform (cursor, copilot, etc.).
        keywords: Combined keywords for matching against skills.
    """

    frontend_frameworks: list[str] = field(default_factory=list)
    backend_languages: list[str] = field(default_factory=list)
    has_llm: bool = False
    has_docs: bool = False
    has_tests: bool = False
    platform: str | None = None
    keywords: list[str] = field(default_factory=list)


@dataclass
class SkillRecommendation:
    """A recommended skill with rationale.

    Attributes:
        qualified_name: Source-qualified name (e.g., source/skill-name).
        name: Unqualified artifact name.
        type: Artifact type (skill, agent, prompt, instruction).
        description: Human-readable description.
        score: Relevance score 0–100.
        rationale: Why this skill was recommended.
    """

    qualified_name: str
    name: str
    type: str
    description: str
    score: int
    rationale: str


################################################################################
#                                                                              #
# REPOSITORY ANALYSIS                                                           #
################################################################################


def analyze_repository(path: Path | str | None = None) -> RepoContext:
    """Analyze a repository to detect tech stack and generate match keywords.

    Checks package.json, pyproject.toml, requirements.txt, and directory
    structure to infer frontend, backend, LLM usage, docs, and tests.

    Args:
        path: Project root to analyze. Defaults to cwd.

    Returns:
        RepoContext with detected attributes and keywords.
    """
    root = Path(path) if path else Path.cwd()
    root = root.resolve()

    logger.info(f"Analyzing repository: root='{root}'")

    ctx = RepoContext()

    # -----
    # Frontend: package.json
    # -----
    pkg_path = root / "package.json"
    if pkg_path.is_file():
        try:
            data = json.loads(pkg_path.read_text())
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            dep_lower = {k.lower(): v for k, v in deps.items()}

            if "react" in dep_lower:
                ctx.frontend_frameworks.append("react")
                ctx.keywords.extend(["react", "frontend", "typescript", "javascript"])
            if "vue" in dep_lower:
                ctx.frontend_frameworks.append("vue")
                ctx.keywords.extend(["vue", "frontend"])
            if "vite" in dep_lower:
                ctx.keywords.append("vite")
            if "typescript" in dep_lower:
                ctx.keywords.append("typescript")
            if "tailwindcss" in dep_lower:
                ctx.keywords.append("tailwind")
            if "nx" in dep_lower:
                ctx.keywords.extend(["nx", "monorepo"])
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"Could not parse package.json: {e}")

    # -----
    # Backend: Python (pyproject.toml, requirements.txt)
    # -----
    py_content = ""
    for pyfile in ["pyproject.toml", "requirements.txt", "requirements-dev.txt"]:
        fpath = root / pyfile
        if fpath.is_file():
            py_content += fpath.read_text().lower() + " "

    if py_content:
        if "python" not in ctx.backend_languages:
            ctx.backend_languages.append("python")
        ctx.keywords.extend(["python", "backend"])
        if "fastapi" in py_content:
            ctx.keywords.extend(["fastapi", "api"])
        if "flask" in py_content:
            ctx.keywords.extend(["flask", "api"])
        if "django" in py_content:
            ctx.keywords.extend(["django"])
        if "langchain" in py_content or "langsmith" in py_content:
            ctx.has_llm = True
            ctx.keywords.extend(["llm", "langchain", "agent", "prompt"])
        if "openai" in py_content or "anthropic" in py_content:
            ctx.has_llm = True
            ctx.keywords.extend(["llm", "openai", "anthropic", "prompt"])

    # -----
    # LLM: check package.json for agent/LLM deps
    # -----
    if pkg_path.is_file() and not ctx.has_llm:
        try:
            data = json.loads(pkg_path.read_text())
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for dep in deps:
                d = dep.lower()
                if "langchain" in d or "openai" in d or "anthropic" in d or "llm" in d:
                    ctx.has_llm = True
                    ctx.keywords.extend(["llm", "agent", "prompt"])
                    break
        except (json.JSONDecodeError, OSError):
            pass

    # -----
    # Docs
    # -----
    if (root / "docs").is_dir() or (root / "mkdocs.yml").is_file():
        ctx.has_docs = True
        ctx.keywords.extend(["docs", "documentation", "mkdocs"])

    # -----
    # Tests
    # -----
    if (root / "pytest.ini").is_file() or (root / "tests").is_dir():
        ctx.keywords.extend(["test", "pytest"])
    if (root / "vitest.config").exists() or "vitest" in str(root):
        ctx.keywords.extend(["test", "vitest"])

    # -----
    # Platform
    # -----
    if (root / ".cursor").is_dir():
        ctx.platform = "cursor"
        ctx.keywords.append("cursor")
    if (root / ".github" / "copilot").is_dir():
        ctx.platform = "copilot"
    if (root / "CLAUDE.md").is_file():
        ctx.platform = "claude"

    # -----
    # General fallbacks
    # -----
    if not ctx.keywords:
        ctx.keywords = ["general", "code"]

    ctx.keywords = list(dict.fromkeys(ctx.keywords))

    logger.info(
        f"Repo context: frontend={ctx.frontend_frameworks}, "
        f"backend={ctx.backend_languages}, has_llm={ctx.has_llm}, "
        f"keywords={ctx.keywords[:10]}..."
    )

    return ctx


################################################################################
#                                                                              #
# SKILL RECOMMENDATION                                                         #
################################################################################


def recommend_skills(
    repo_context: RepoContext,
    index: ArtifactIndex,
    limit: int = 15,
) -> list[SkillRecommendation]:
    """Recommend skills from the artifact index based on repo context.

    Scores each artifact by matching repo keywords against name and
    description. Returns a ranked list with rationale.

    Args:
        repo_context: Analyzed repository context.
        index: Pre-built ArtifactIndex with available artifacts.
        limit: Maximum number of recommendations to return.

    Returns:
        Sorted list of SkillRecommendation, highest score first.
    """
    logger.info(
        f"Recommending skills: keywords={repo_context.keywords}, "
        f"limit={limit}"
    )

    keyword_set = {k.lower() for k in repo_context.keywords}
    scored: list[SkillRecommendation] = []

    for qname, vp in index.by_qualified_name.items():
        score, rationale = _score_artifact(vp, keyword_set, repo_context)
        if score > 0:
            scored.append(
                SkillRecommendation(
                    qualified_name=vp.qualified_name,
                    name=vp.name,
                    type=vp.type,
                    description=(vp.description or "")[:200],
                    score=score,
                    rationale=rationale,
                )
            )

    scored.sort(key=lambda r: (-r.score, r.qualified_name))

    return scored[:limit]


def _score_artifact(
    vp: VirtualPackage,
    keyword_set: set[str],
    ctx: RepoContext,
) -> tuple[int, str]:
    """Score a single artifact and produce rationale."""
    score = 0
    reasons: list[str] = []

    name_lower = vp.name.lower()
    desc_lower = (vp.description or "").lower()
    combined = f"{name_lower} {desc_lower}"

    for kw in keyword_set:
        if kw in name_lower:
            score += 15
            reasons.append(f"name matches '{kw}'")
        elif kw in desc_lower:
            score += 8
            reasons.append(f"description matches '{kw}'")
        elif kw in combined:
            score += 3

    # Boost for LLM projects when skill mentions prompt/agent
    if ctx.has_llm and any(t in combined for t in ["prompt", "agent", "llm"]):
        score += 10
        reasons.append("relevant for LLM/agent projects")

    # Boost for docs projects
    if ctx.has_docs and any(t in combined for t in ["doc", "documentation"]):
        score += 10
        reasons.append("relevant for documentation")

    # Boost for platform match
    if ctx.platform and ctx.platform in combined:
        score += 5
        reasons.append(f"platform matches ({ctx.platform})")

    rationale = "; ".join(reasons[:3]) if reasons else "general purpose"

    return (min(score, 100), rationale)


################################################################################
#                                                                              #
# CONVENIENCE ENTRY POINT                                                      #
################################################################################


def recommend_skills_for_repo(
    path: Path | str | None = None,
    index: ArtifactIndex | None = None,
    limit: int = 15,
) -> dict[str, Any]:
    """Analyze repository and recommend skills in one call.

    Combines analyze_repository and recommend_skills. Loads index if
    not provided.

    Args:
        path: Project root to analyze.
        index: Pre-built index. Loaded via build_source_index if None.
        limit: Max recommendations.

    Returns:
        Dict with repo_context, recommendations, and metadata.
    """
    from aam_cli.core.config import load_config
    from aam_cli.services.source_service import build_source_index

    ctx = analyze_repository(path)

    if index is None:
        config = load_config()
        index = build_source_index(config)

    recs = recommend_skills(ctx, index, limit=limit)

    return {
        "repo_context": {
            "frontend_frameworks": ctx.frontend_frameworks,
            "backend_languages": ctx.backend_languages,
            "has_llm": ctx.has_llm,
            "has_docs": ctx.has_docs,
            "platform": ctx.platform,
            "keywords": ctx.keywords,
        },
        "recommendations": [
            {
                "qualified_name": r.qualified_name,
                "name": r.name,
                "type": r.type,
                "description": r.description,
                "score": r.score,
                "rationale": r.rationale,
            }
            for r in recs
        ],
        "total_available": index.total_count,
        "install_hint": (
            "Install with: aam install <qualified_name> "
            "(e.g., aam install openai/skills/code-review)"
        ),
    }
