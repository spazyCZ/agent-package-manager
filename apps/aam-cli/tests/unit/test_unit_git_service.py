"""Unit tests for git subprocess wrapper service.

Tests git clone, fetch, head sha, diff, retry logic, cache path
computation, and cache validation — all with mocked subprocess calls.

Reference: tasks.md T019.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aam_cli.services.git_service import (
    GitCloneError,
    GitError,
    check_git_available,
    clone_shallow,
    diff_file_names,
    fetch,
    get_cache_dir,
    get_head_sha,
    validate_cache,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CHECK GIT AVAILABLE                                                          #
#                                                                              #
################################################################################


class TestCheckGitAvailable:
    """Tests for git availability check."""

    @patch("aam_cli.services.git_service._run_git")
    def test_unit_git_available(self, mock_run: MagicMock) -> None:
        """Returns True when git --version succeeds."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="git version 2.43.0"
        )
        assert check_git_available() is True

    @patch("aam_cli.services.git_service._run_git")
    def test_unit_git_not_available(self, mock_run: MagicMock) -> None:
        """Returns False when git --version fails."""
        mock_run.side_effect = FileNotFoundError()
        assert check_git_available() is False


################################################################################
#                                                                              #
# CLONE TESTS                                                                  #
#                                                                              #
################################################################################


class TestCloneShallow:
    """Tests for shallow clone with full clone fallback."""

    @patch("aam_cli.services.git_service._run_with_retry")
    def test_unit_shallow_clone_success(
        self, mock_retry: MagicMock, tmp_path: Path
    ) -> None:
        """Shallow clone succeeds on first try."""
        target = tmp_path / "repo"
        mock_retry.return_value = MagicMock(returncode=0)

        result = clone_shallow("https://github.com/test/repo", target)

        assert result == target
        mock_retry.assert_called_once()
        # Verify it was called with --depth
        args = mock_retry.call_args[0][0]
        assert "--depth" in args

    @patch("aam_cli.services.git_service._run_with_retry")
    def test_unit_shallow_clone_fallback_to_full(
        self, mock_retry: MagicMock, tmp_path: Path
    ) -> None:
        """Falls back to full clone when shallow fails."""
        target = tmp_path / "repo"

        # First call (shallow) raises, second call (full) succeeds
        mock_retry.side_effect = [
            GitCloneError("shallow not supported"),
            MagicMock(returncode=0),
        ]

        result = clone_shallow("https://github.com/test/repo", target)

        assert result == target
        assert mock_retry.call_count == 2
        # Second call should NOT have --depth
        second_args = mock_retry.call_args_list[1][0][0]
        assert "--depth" not in second_args

    @patch("aam_cli.services.git_service._run_with_retry")
    def test_unit_clone_failure_raises(
        self, mock_retry: MagicMock, tmp_path: Path
    ) -> None:
        """Both shallow and full clone failing raises GitCloneError."""
        target = tmp_path / "repo"
        mock_retry.side_effect = GitCloneError("network error")

        with pytest.raises(GitCloneError):
            clone_shallow("https://github.com/test/repo", target)


################################################################################
#                                                                              #
# FETCH TESTS                                                                  #
#                                                                              #
################################################################################


class TestFetch:
    """Tests for git fetch with reset."""

    @patch("aam_cli.services.git_service._run_git")
    @patch("aam_cli.services.git_service._run_with_retry")
    def test_unit_fetch_success(
        self, mock_retry: MagicMock, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Fetch and reset succeed."""
        mock_retry.return_value = MagicMock(returncode=0)
        mock_run.return_value = MagicMock(returncode=0)

        fetch(tmp_path, ref="main")

        mock_retry.assert_called_once()
        # Should call reset --hard
        mock_run.assert_called()


################################################################################
#                                                                              #
# HEAD SHA TESTS                                                               #
#                                                                              #
################################################################################


class TestGetHeadSha:
    """Tests for HEAD commit SHA retrieval."""

    @patch("aam_cli.services.git_service._run_git")
    def test_unit_head_sha_success(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Returns trimmed SHA on success."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123def456789012345678901234567890abcd\n",
        )

        result = get_head_sha(tmp_path)

        assert result == "abc123def456789012345678901234567890abcd"

    @patch("aam_cli.services.git_service._run_git")
    def test_unit_head_sha_failure_raises(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Raises GitError when rev-parse fails."""
        mock_run.return_value = MagicMock(
            returncode=128, stderr="fatal: not a git repository"
        )

        with pytest.raises(GitError):
            get_head_sha(tmp_path)


################################################################################
#                                                                              #
# DIFF FILE NAMES TESTS                                                        #
#                                                                              #
################################################################################


class TestDiffFileNames:
    """Tests for git diff --name-status parsing."""

    @patch("aam_cli.services.git_service._run_git")
    def test_unit_diff_classifies_correctly(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Added, modified, and deleted files are classified correctly."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="A\tnew-file.md\nM\tchanged-file.md\nD\tdeleted-file.md\n",
        )

        result = diff_file_names(tmp_path, "aaa", "bbb")

        assert result["added"] == ["new-file.md"]
        assert result["modified"] == ["changed-file.md"]
        assert result["deleted"] == ["deleted-file.md"]

    @patch("aam_cli.services.git_service._run_git")
    def test_unit_diff_handles_rename(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Renamed files are classified as modified."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="R100\trenamed-file.md\n",
        )

        result = diff_file_names(tmp_path, "aaa", "bbb")

        assert result["modified"] == ["renamed-file.md"]

    @patch("aam_cli.services.git_service._run_git")
    def test_unit_diff_empty(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Empty diff returns empty lists."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=""
        )

        result = diff_file_names(tmp_path, "aaa", "bbb")

        assert result["added"] == []
        assert result["modified"] == []
        assert result["deleted"] == []

    @patch("aam_cli.services.git_service._run_git")
    def test_unit_diff_failure_raises(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Raises GitError when diff command fails."""
        mock_run.return_value = MagicMock(
            returncode=1, stderr="fatal: bad revision"
        )

        with pytest.raises(GitError):
            diff_file_names(tmp_path, "aaa", "bbb")


################################################################################
#                                                                              #
# CACHE PATH TESTS                                                             #
#                                                                              #
################################################################################


class TestCachePath:
    """Tests for cache directory computation."""

    @patch("aam_cli.services.git_service.get_global_aam_dir")
    def test_unit_cache_dir_structure(
        self, mock_global: MagicMock, tmp_path: Path
    ) -> None:
        """Cache path follows host/owner/repo structure."""
        mock_global.return_value = tmp_path

        result = get_cache_dir("github.com", "openai", "skills")

        expected = tmp_path / "cache" / "git" / "github.com" / "openai" / "skills"
        assert result == expected


################################################################################
#                                                                              #
# CACHE VALIDATION TESTS                                                       #
#                                                                              #
################################################################################


class TestValidateCache:
    """Tests for cache directory validation."""

    def test_unit_validate_nonexistent_returns_false(
        self, tmp_path: Path
    ) -> None:
        """Non-existent directory returns False."""
        assert validate_cache(tmp_path / "nonexistent") is False

    def test_unit_validate_no_git_dir_removes_and_returns_false(
        self, tmp_path: Path
    ) -> None:
        """Directory without .git is corrupted — removed and returns False."""
        cache_dir = tmp_path / "repo"
        cache_dir.mkdir()
        (cache_dir / "somefile.txt").write_text("data")

        result = validate_cache(cache_dir)

        assert result is False
        assert not cache_dir.exists()

    @patch("aam_cli.services.git_service._run_git")
    def test_unit_validate_git_status_failure(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Git status failure indicates corruption — dir removed."""
        cache_dir = tmp_path / "repo"
        cache_dir.mkdir()
        (cache_dir / ".git").mkdir()

        mock_run.return_value = MagicMock(
            returncode=128, stderr="fatal: error"
        )

        result = validate_cache(cache_dir)

        assert result is False
        assert not cache_dir.exists()

    @patch("aam_cli.services.git_service._run_git")
    def test_unit_validate_healthy_cache(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Healthy cache with .git and clean status returns True."""
        cache_dir = tmp_path / "repo"
        cache_dir.mkdir()
        (cache_dir / ".git").mkdir()

        mock_run.return_value = MagicMock(
            returncode=0, stdout=""
        )

        result = validate_cache(cache_dir)

        assert result is True


################################################################################
#                                                                              #
# RETRY LOGIC TESTS                                                            #
#                                                                              #
################################################################################


class TestRetryLogic:
    """Tests for retry with exponential backoff."""

    @patch("aam_cli.services.git_service.time.sleep")
    @patch("aam_cli.services.git_service._run_git")
    def test_unit_retry_succeeds_on_second_attempt(
        self, mock_run: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Retry succeeds on second attempt after first failure."""
        from aam_cli.services.git_service import _run_with_retry

        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="temporary error"),
            MagicMock(returncode=0, stdout="success"),
        ]

        result = _run_with_retry(["test"], operation_name="test op")

        assert result.returncode == 0
        assert mock_run.call_count == 2
        mock_sleep.assert_called_once_with(1.0)

    @patch("aam_cli.services.git_service.time.sleep")
    @patch("aam_cli.services.git_service._run_git")
    def test_unit_retry_exhausted_raises(
        self, mock_run: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """All retries failing raises the specified error class."""
        from aam_cli.services.git_service import _run_with_retry

        mock_run.return_value = MagicMock(
            returncode=1, stderr="persistent error"
        )

        with pytest.raises(GitCloneError, match="persistent error"):
            _run_with_retry(
                ["test"],
                error_class=GitCloneError,
                operation_name="clone",
            )

        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2  # sleeps between attempts
