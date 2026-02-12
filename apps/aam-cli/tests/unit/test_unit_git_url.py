"""Unit tests for git URL parsing and decomposition.

Tests all supported URL formats: HTTPS, SSH, git+https, tree URL,
and shorthand, including edge cases and invalid inputs.

Reference: tasks.md T009.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import pytest

from aam_cli.utils.git_url import (
    DEFAULT_HOST,
    DEFAULT_REF,
    parse,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# SHORTHAND FORMAT TESTS                                                       #
#                                                                              #
################################################################################


class TestShorthandParsing:
    """Tests for shorthand format: owner/repo[@ref][#sha]."""

    def test_unit_basic_shorthand(self) -> None:
        """Parse basic owner/repo shorthand."""
        result = parse("openai/skills")
        assert result.host == DEFAULT_HOST
        assert result.owner == "openai"
        assert result.repo == "skills"
        assert result.ref == DEFAULT_REF
        assert result.path == ""
        assert result.clone_url == f"https://{DEFAULT_HOST}/openai/skills"
        assert result.display_name == "openai/skills"
        assert result.source_format == "shorthand"

    def test_unit_shorthand_with_ref(self) -> None:
        """Parse owner/repo@branch shorthand."""
        result = parse("openai/skills@develop")
        assert result.ref == "develop"
        assert result.owner == "openai"
        assert result.repo == "skills"

    def test_unit_shorthand_with_sha(self) -> None:
        """Parse owner/repo#sha shorthand."""
        result = parse("openai/skills#abc123def456")
        assert result.ref == "abc123def456"
        assert result.source_format == "shorthand"

    def test_unit_shorthand_with_path_override(self) -> None:
        """Path override creates scoped display name."""
        result = parse("openai/skills", path="skills/.curated")
        assert result.path == "skills/.curated"
        assert result.display_name == "openai/skills:.curated"

    def test_unit_shorthand_with_ref_override(self) -> None:
        """CLI ref override takes precedence over @ref in shorthand."""
        result = parse("openai/skills@develop", ref="v2.0")
        assert result.ref == "v2.0"

    def test_unit_shorthand_with_name_override(self) -> None:
        """Custom name override replaces auto-generated name."""
        result = parse("openai/skills", name="my-skills")
        assert result.display_name == "my-skills"

    def test_unit_shorthand_dots_and_underscores(self) -> None:
        """Owner and repo can contain dots and underscores."""
        result = parse("my.org/my_repo")
        assert result.owner == "my.org"
        assert result.repo == "my_repo"


################################################################################
#                                                                              #
# HTTPS FORMAT TESTS                                                           #
#                                                                              #
################################################################################


class TestHttpsParsing:
    """Tests for HTTPS URL format."""

    def test_unit_basic_https(self) -> None:
        """Parse basic HTTPS URL."""
        result = parse("https://github.com/openai/skills")
        assert result.host == "github.com"
        assert result.owner == "openai"
        assert result.repo == "skills"
        assert result.ref == DEFAULT_REF
        assert result.path == ""
        assert result.clone_url == "https://github.com/openai/skills"
        assert result.source_format == "https"

    def test_unit_https_with_git_suffix(self) -> None:
        """Parse HTTPS URL with .git suffix."""
        result = parse("https://github.com/openai/skills.git")
        assert result.repo == "skills"
        assert result.clone_url == "https://github.com/openai/skills"

    def test_unit_https_gitlab(self) -> None:
        """Parse HTTPS URL from GitLab."""
        result = parse("https://gitlab.com/mygroup/myproject")
        assert result.host == "gitlab.com"
        assert result.owner == "mygroup"
        assert result.repo == "myproject"

    def test_unit_https_self_hosted(self) -> None:
        """Parse HTTPS URL from self-hosted git server."""
        result = parse("https://git.example.com/team/repo")
        assert result.host == "git.example.com"


################################################################################
#                                                                              #
# TREE URL FORMAT TESTS                                                        #
#                                                                              #
################################################################################


class TestTreeUrlParsing:
    """Tests for GitHub/GitLab tree URL format with embedded ref and path."""

    def test_unit_tree_url_with_branch_and_path(self) -> None:
        """Parse full tree URL with branch and path."""
        result = parse(
            "https://github.com/openai/skills/tree/main/skills/.curated"
        )
        assert result.host == "github.com"
        assert result.owner == "openai"
        assert result.repo == "skills"
        assert result.ref == "main"
        assert result.path == "skills/.curated"
        assert result.display_name == "openai/skills:.curated"
        assert result.source_format == "tree_url"

    def test_unit_tree_url_branch_only(self) -> None:
        """Parse tree URL with branch but no path."""
        result = parse("https://github.com/openai/skills/tree/develop")
        assert result.ref == "develop"
        assert result.path == ""
        assert result.source_format == "tree_url"

    def test_unit_tree_url_with_nested_path(self) -> None:
        """Parse tree URL with deeply nested path."""
        result = parse(
            "https://github.com/org/repo/tree/main/a/b/c/.experimental"
        )
        assert result.path == "a/b/c/.experimental"
        assert result.display_name == "org/repo:.experimental"

    def test_unit_tree_url_ref_override(self) -> None:
        """CLI ref override takes precedence over URL-embedded ref."""
        result = parse(
            "https://github.com/openai/skills/tree/main/skills",
            ref="v2.0",
        )
        assert result.ref == "v2.0"

    def test_unit_tree_url_path_override(self) -> None:
        """CLI path override takes precedence over URL-embedded path."""
        result = parse(
            "https://github.com/openai/skills/tree/main/skills/.curated",
            path="skills/.system",
        )
        assert result.path == "skills/.system"
        assert result.display_name == "openai/skills:.system"


################################################################################
#                                                                              #
# SSH FORMAT TESTS                                                             #
#                                                                              #
################################################################################


class TestSshParsing:
    """Tests for SSH URL format: git@host:owner/repo.git."""

    def test_unit_basic_ssh(self) -> None:
        """Parse basic SSH URL."""
        result = parse("git@github.com:openai/skills.git")
        assert result.host == "github.com"
        assert result.owner == "openai"
        assert result.repo == "skills"
        assert result.clone_url == "git@github.com:openai/skills.git"
        assert result.source_format == "ssh"

    def test_unit_ssh_without_git_suffix(self) -> None:
        """Parse SSH URL without .git suffix."""
        result = parse("git@github.com:openai/skills")
        assert result.repo == "skills"
        assert result.source_format == "ssh"

    def test_unit_ssh_with_ref_and_path(self) -> None:
        """Parse SSH URL with CLI ref and path overrides."""
        result = parse(
            "git@github.com:openai/skills.git",
            ref="develop",
            path="skills/.curated",
        )
        assert result.ref == "develop"
        assert result.path == "skills/.curated"


################################################################################
#                                                                              #
# GIT+HTTPS FORMAT TESTS                                                       #
#                                                                              #
################################################################################


class TestGitHttpsParsing:
    """Tests for git+https:// URL format."""

    def test_unit_basic_git_https(self) -> None:
        """Parse git+https:// URL."""
        result = parse("git+https://github.com/openai/skills.git")
        assert result.host == "github.com"
        assert result.owner == "openai"
        assert result.repo == "skills"
        assert result.clone_url == "git+https://github.com/openai/skills.git"
        assert result.source_format == "git_https"

    def test_unit_git_https_without_suffix(self) -> None:
        """Parse git+https:// URL without .git suffix."""
        result = parse("git+https://github.com/openai/skills")
        assert result.repo == "skills"


################################################################################
#                                                                              #
# DISPLAY NAME TESTS                                                           #
#                                                                              #
################################################################################


class TestDisplayName:
    """Tests for display name generation."""

    def test_unit_no_path_gives_owner_repo(self) -> None:
        """No path produces simple owner/repo name."""
        result = parse("openai/skills")
        assert result.display_name == "openai/skills"

    def test_unit_path_gives_suffixed_name(self) -> None:
        """Path produces owner/repo:suffix name."""
        result = parse("openai/skills", path="skills/.curated")
        assert result.display_name == "openai/skills:.curated"

    def test_unit_deep_path_uses_last_component(self) -> None:
        """Deep path uses only the last component as suffix."""
        result = parse("openai/skills", path="a/b/c/special")
        assert result.display_name == "openai/skills:special"

    def test_unit_name_override_wins(self) -> None:
        """User-specified name always wins."""
        result = parse(
            "openai/skills",
            path="skills/.curated",
            name="custom-name",
        )
        assert result.display_name == "custom-name"


################################################################################
#                                                                              #
# INVALID INPUT TESTS                                                          #
#                                                                              #
################################################################################


class TestInvalidInputs:
    """Tests for error handling on invalid inputs."""

    def test_unit_empty_string_raises(self) -> None:
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            parse("")

    def test_unit_whitespace_only_raises(self) -> None:
        """Whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            parse("   ")

    def test_unit_single_word_raises(self) -> None:
        """Single word without slash raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse"):
            parse("justarepo")

    def test_unit_three_slashes_raises(self) -> None:
        """Three-part path is not a valid shorthand."""
        with pytest.raises(ValueError, match="Cannot parse"):
            parse("a/b/c")

    def test_unit_http_without_owner_repo(self) -> None:
        """HTTP URL without owner/repo pattern raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse"):
            parse("https://example.com")


################################################################################
#                                                                              #
# FROZEN DATACLASS TESTS                                                       #
#                                                                              #
################################################################################


class TestFrozenDataclass:
    """Tests for GitSourceURL immutability."""

    def test_unit_frozen_prevents_mutation(self) -> None:
        """GitSourceURL fields cannot be modified after creation."""
        result = parse("openai/skills")
        with pytest.raises(AttributeError):
            result.ref = "other"  # type: ignore[misc]
