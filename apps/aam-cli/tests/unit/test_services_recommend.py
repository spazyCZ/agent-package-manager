"""Unit tests for recommend service.

Tests cover:
- analyze_repository() repo context detection
- recommend_skills() scoring and ranking
- recommend_skills_for_repo() integration
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
################################################################################

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aam_cli.services.recommend_service import (
    RepoContext,
    SkillRecommendation,
    analyze_repository,
    recommend_skills,
    recommend_skills_for_repo,
)

################################################################################
#                                                                              #
# FIXTURES                                                                     #
################################################################################


def _make_virtual_package(
    name: str,
    source_name: str = "my-source",
    pkg_type: str = "skill",
    description: str = "",
    qualified_name: str | None = None,
) -> MagicMock:
    """Create a mock VirtualPackage."""
    vp = MagicMock()
    vp.name = name
    vp.source_name = source_name
    vp.type = pkg_type
    vp.description = description
    vp.qualified_name = qualified_name or f"{source_name}/{name}"
    return vp


def _make_index() -> MagicMock:
    """Create a mock ArtifactIndex with sample artifacts."""
    index = MagicMock()
    index.by_qualified_name = {
        "source/code-review": _make_virtual_package(
            "code-review",
            description="Review code for quality and security",
        ),
        "source/docs-writer": _make_virtual_package(
            "docs-writer",
            description="Write documentation and markdown",
        ),
        "source/python-coder": _make_virtual_package(
            "python-coder",
            description="Python development guidance",
        ),
        "source/prompt-engineering": _make_virtual_package(
            "prompt-engineering",
            description="Design prompts for LLM agents",
        ),
        "source/react-helper": _make_virtual_package(
            "react-helper",
            description="React and TypeScript helpers",
        ),
        "source/unrelated": _make_virtual_package(
            "unrelated",
            description="Something else entirely",
        ),
    }
    index.total_count = 6
    return index


################################################################################
#                                                                              #
# TESTS: analyze_repository                                                    #
#                                                                              #
################################################################################


class TestAnalyzeRepository:
    """Tests for analyze_repository()."""

    def test_unit_analyze_react_project(self, tmp_path: Path) -> None:
        """React project detected from package.json."""
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"react": "^18.0.0"}, "devDependencies": {"vite": "^6.0.0"}}'
        )
        ctx = analyze_repository(tmp_path)
        assert "react" in ctx.frontend_frameworks
        assert "react" in ctx.keywords
        assert "vite" in ctx.keywords

    def test_unit_analyze_python_project(self, tmp_path: Path) -> None:
        """Python backend detected from pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\ndependencies = ["fastapi>=0.100.0"]'
        )
        ctx = analyze_repository(tmp_path)
        assert "python" in ctx.backend_languages
        assert "fastapi" in ctx.keywords
        assert "api" in ctx.keywords

    def test_unit_analyze_llm_project(self, tmp_path: Path) -> None:
        """LLM usage detected from requirements."""
        (tmp_path / "requirements.txt").write_text("langchain\nopenai")
        ctx = analyze_repository(tmp_path)
        assert ctx.has_llm is True
        assert "llm" in ctx.keywords
        assert "prompt" in ctx.keywords

    def test_unit_analyze_docs_project(self, tmp_path: Path) -> None:
        """Docs structure detected."""
        (tmp_path / "docs").mkdir()
        ctx = analyze_repository(tmp_path)
        assert ctx.has_docs is True
        assert "docs" in ctx.keywords

    def test_unit_analyze_cursor_platform(self, tmp_path: Path) -> None:
        """Cursor platform detected from .cursor."""
        (tmp_path / ".cursor").mkdir()
        ctx = analyze_repository(tmp_path)
        assert ctx.platform == "cursor"
        assert "cursor" in ctx.keywords

    def test_unit_analyze_empty_dir(self, tmp_path: Path) -> None:
        """Empty dir gets fallback keywords."""
        ctx = analyze_repository(tmp_path)
        assert ctx.keywords
        assert "general" in ctx.keywords or "code" in ctx.keywords


################################################################################
#                                                                              #
# TESTS: recommend_skills                                                      #
#                                                                              #
################################################################################


class TestRecommendSkills:
    """Tests for recommend_skills()."""

    def test_unit_recommend_ranks_by_score(self) -> None:
        """Higher-scoring skills appear first."""
        ctx = RepoContext(
            keywords=["python", "code", "docs", "llm", "prompt"],
        )
        index = _make_index()
        recs = recommend_skills(ctx, index, limit=10)
        assert len(recs) <= 10
        scores = [r.score for r in recs]
        assert scores == sorted(scores, reverse=True)

    def test_unit_recommend_includes_rationale(self) -> None:
        """Each recommendation has non-empty rationale."""
        ctx = RepoContext(keywords=["python", "docs"])
        index = _make_index()
        recs = recommend_skills(ctx, index, limit=5)
        for r in recs:
            assert r.rationale
            assert r.qualified_name
            assert r.score >= 0

    def test_unit_recommend_respects_limit(self) -> None:
        """Limit caps number of results."""
        ctx = RepoContext(keywords=["code", "python", "docs"])
        index = _make_index()
        recs = recommend_skills(ctx, index, limit=2)
        assert len(recs) == 2

    def test_unit_recommend_empty_index(self) -> None:
        """Empty index returns empty list."""
        ctx = RepoContext(keywords=["python"])
        index = MagicMock()
        index.by_qualified_name = {}
        recs = recommend_skills(ctx, index, limit=10)
        assert recs == []


################################################################################
#                                                                              #
# TESTS: recommend_skills_for_repo                                             #
#                                                                              #
################################################################################


class TestRecommendSkillsForRepo:
    """Tests for recommend_skills_for_repo()."""

    @pytest.mark.parametrize("path_arg", [None, "."])
    def test_unit_recommend_for_repo_returns_structure(
        self, path_arg: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns expected structure with repo_context and recommendations."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "package.json").write_text('{"dependencies": {"react": "18"}}')
        index = _make_index()

        result = recommend_skills_for_repo(path=path_arg, index=index, limit=5)

        assert "repo_context" in result
        assert "recommendations" in result
        assert "install_hint" in result
        assert "total_available" in result
        assert result["repo_context"]["frontend_frameworks"] == ["react"]
        assert isinstance(result["recommendations"], list)
        assert "aam install" in result["install_hint"]
