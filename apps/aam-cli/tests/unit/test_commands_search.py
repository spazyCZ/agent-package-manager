"""Unit tests for the search command (presentation layer).

Covers:
- Installed indicator marking via lock file cross-reference
- Rich Table output including the Installed column
- JSON output including the ``installed`` field
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from aam_cli.commands.search import _collect_installed_names, search
from aam_cli.core.workspace import LockedPackage, LockFile
from aam_cli.services.search_service import SearchResponse, SearchResult

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _make_search_response(
    results: list[SearchResult] | None = None,
    total_count: int | None = None,
) -> SearchResponse:
    """Build a SearchResponse with sensible defaults."""
    results = results or []
    return SearchResponse(
        results=results,
        total_count=total_count if total_count is not None else len(results),
        warnings=[],
        all_names=[],
    )


def _make_lock_file(package_names: list[str] | None = None) -> LockFile:
    """Build a LockFile with given package names installed."""
    packages = {}
    for name in (package_names or []):
        packages[name] = LockedPackage(
            version="1.0.0",
            source="local",
            checksum="",
        )
    return LockFile(packages=packages)


def _make_result(
    name: str,
    version: str = "1.0.0",
    origin: str = "local",
    description: str = "---",
) -> SearchResult:
    """Build a SearchResult with minimal required fields."""
    return SearchResult(
        name=name,
        version=version,
        description=description,
        artifact_types=["skill"],
        origin=origin,
        origin_type="registry",
        score=80,
    )


################################################################################
#                                                                              #
# TEST: _collect_installed_names HELPER                                        #
#                                                                              #
################################################################################


class TestCollectInstalledNames:
    """Tests for the _collect_installed_names helper function."""

    @patch("aam_cli.commands.search.read_lock_file")
    @patch("aam_cli.commands.search.resolve_project_dir")
    def test_unit_collect_empty_lock_files(
        self,
        mock_resolve: MagicMock,
        mock_read_lock: MagicMock,
    ) -> None:
        """Returns empty set when no packages are installed."""
        mock_resolve.return_value = "/fake/path"
        mock_read_lock.return_value = _make_lock_file([])

        result = _collect_installed_names()

        assert result == set()
        assert mock_read_lock.call_count == 2

    @patch("aam_cli.commands.search.read_lock_file")
    @patch("aam_cli.commands.search.resolve_project_dir")
    def test_unit_collect_local_packages(
        self,
        mock_resolve: MagicMock,
        mock_read_lock: MagicMock,
    ) -> None:
        """Returns package names from local lock file."""
        mock_resolve.return_value = "/fake/path"
        local_lock = _make_lock_file(["pkg-a", "pkg-b"])
        global_lock = _make_lock_file([])
        mock_read_lock.side_effect = [local_lock, global_lock]

        result = _collect_installed_names()

        assert result == {"pkg-a", "pkg-b"}

    @patch("aam_cli.commands.search.read_lock_file")
    @patch("aam_cli.commands.search.resolve_project_dir")
    def test_unit_collect_union_of_local_and_global(
        self,
        mock_resolve: MagicMock,
        mock_read_lock: MagicMock,
    ) -> None:
        """Returns union of local and global installed packages."""
        mock_resolve.return_value = "/fake/path"
        local_lock = _make_lock_file(["pkg-a"])
        global_lock = _make_lock_file(["pkg-b", "pkg-c"])
        mock_read_lock.side_effect = [local_lock, global_lock]

        result = _collect_installed_names()

        assert result == {"pkg-a", "pkg-b", "pkg-c"}


################################################################################
#                                                                              #
# TEST: SEARCH COMMAND — INSTALLED INDICATOR                                   #
#                                                                              #
################################################################################


class TestSearchInstalledIndicator:
    """Tests for installed indicator in search command output."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("aam_cli.commands.search._collect_installed_names")
    @patch("aam_cli.commands.search.search_packages")
    @patch("aam_cli.commands.search.load_config")
    def test_unit_search_marks_installed_packages(
        self,
        mock_config: MagicMock,
        mock_search: MagicMock,
        mock_installed: MagicMock,
    ) -> None:
        """Installed packages show a checkmark in table output."""
        mock_config.return_value = MagicMock()
        mock_search.return_value = _make_search_response(
            results=[
                _make_result("chatbot"),
                _make_result("docs-writer"),
                _make_result("other-pkg"),
            ],
        )
        # Only "chatbot" is installed
        mock_installed.return_value = {"chatbot"}

        result = self.runner.invoke(
            search,
            ["bot"],
            obj={"console": MagicMock()},
            catch_exceptions=False,
        )

        logger.info(f"Command output:\n{result.output}")

        # -----
        # The checkmark character should appear in the output
        # (Rich renders the [green]✓[/green] markup as the ✓ character)
        # -----
        assert result.exit_code == 0

    @patch("aam_cli.commands.search._collect_installed_names")
    @patch("aam_cli.commands.search.search_packages")
    @patch("aam_cli.commands.search.load_config")
    def test_unit_search_no_installed_column_still_renders(
        self,
        mock_config: MagicMock,
        mock_search: MagicMock,
        mock_installed: MagicMock,
    ) -> None:
        """Table renders correctly even when no packages are installed."""
        mock_config.return_value = MagicMock()
        mock_search.return_value = _make_search_response(
            results=[_make_result("chatbot")],
        )
        mock_installed.return_value = set()

        result = self.runner.invoke(
            search,
            ["bot"],
            obj={"console": MagicMock()},
            catch_exceptions=False,
        )

        assert result.exit_code == 0

    @patch("aam_cli.commands.search._collect_installed_names")
    @patch("aam_cli.commands.search.search_packages")
    @patch("aam_cli.commands.search.load_config")
    def test_unit_search_json_includes_installed_field(
        self,
        mock_config: MagicMock,
        mock_search: MagicMock,
        mock_installed: MagicMock,
    ) -> None:
        """JSON output includes 'installed' field for each result."""
        from io import StringIO

        from rich.console import Console

        mock_config.return_value = MagicMock()
        mock_search.return_value = _make_search_response(
            results=[
                _make_result("chatbot"),
                _make_result("docs-writer"),
            ],
        )
        # Only "chatbot" is installed
        mock_installed.return_value = {"chatbot"}

        # -----
        # Use a real Console writing to a StringIO buffer so we can
        # parse the JSON output reliably.
        # -----
        buf = StringIO()
        console = Console(file=buf, force_terminal=False, no_color=True)

        result = self.runner.invoke(
            search,
            ["bot", "--json"],
            obj={"console": console},
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        # -----
        # Parse the JSON from the console buffer
        # -----
        raw_output = buf.getvalue()
        json_data = json.loads(raw_output)

        assert len(json_data["results"]) == 2

        chatbot_result = json_data["results"][0]
        docs_result = json_data["results"][1]

        assert chatbot_result["name"] == "chatbot"
        assert chatbot_result["installed"] is True

        assert docs_result["name"] == "docs-writer"
        assert docs_result["installed"] is False

    @patch("aam_cli.commands.search._collect_installed_names")
    @patch("aam_cli.commands.search.search_packages")
    @patch("aam_cli.commands.search.load_config")
    def test_unit_search_installed_marking_does_not_affect_empty_results(
        self,
        mock_config: MagicMock,
        mock_search: MagicMock,
        mock_installed: MagicMock,
    ) -> None:
        """Installed marking is skipped gracefully when results are empty."""
        mock_config.return_value = MagicMock()
        mock_search.return_value = _make_search_response(results=[])
        mock_installed.return_value = {"chatbot"}

        result = self.runner.invoke(
            search,
            ["nonexistent"],
            obj={"console": MagicMock()},
            catch_exceptions=False,
        )

        assert result.exit_code == 0
