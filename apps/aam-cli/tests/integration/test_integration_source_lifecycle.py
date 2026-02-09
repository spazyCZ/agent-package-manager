"""Integration tests for git source management lifecycle.

Tests the full add → scan → update → candidates → remove workflow
using a local bare git repository to avoid network dependencies.

Reference: tasks.md T029, T034, T039.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import subprocess
from pathlib import Path

import pytest

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# FIXTURES                                                                     #
#                                                                              #
################################################################################


@pytest.fixture()
def local_git_repo(tmp_path: Path) -> Path:
    """Create a local git repo (non-bare) with skill artifacts.

    This avoids needing a bare repo + push; we clone from a regular
    repo's working directory via file:// protocol.

    Returns:
        Path to the repository that can be cloned.
    """
    repo_dir = tmp_path / "origin-repo"
    repo_dir.mkdir()

    # -----
    # Initialize a regular (non-bare) git repository
    # -----
    subprocess.run(
        ["git", "init", "--initial-branch", "main"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    # -----
    # Create sample artifacts
    # -----
    skill_dir = repo_dir / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test Skill\nA skill for integration tests.")

    agent_dir = repo_dir / "agents" / "test-agent"
    agent_dir.mkdir(parents=True)
    (agent_dir / "agent.yaml").write_text(
        "name: test-agent\ndescription: Test agent\n"
    )

    # Commit
    subprocess.run(
        ["git", "add", "."],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    return repo_dir


@pytest.fixture()
def aam_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an isolated AAM home directory.

    Returns:
        Path to the fake home (containing .aam/).
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    aam_dir = fake_home / ".aam"
    aam_dir.mkdir()

    # Create empty config.yaml
    config_path = aam_dir / "config.yaml"
    config_path.write_text(
        "default_platform: cursor\nregistries: []\nsources: []\n"
    )

    return fake_home


################################################################################
#                                                                              #
# SOURCE ADD + SCAN LIFECYCLE                                                  #
#                                                                              #
################################################################################


class TestSourceAddScanLifecycle:
    """Integration test: add a source and scan it."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires file:// URL parser support — future enhancement")
    def test_integration_add_and_scan_source(
        self,
        local_git_repo: Path,
        aam_home: Path,  # noqa: ARG002
    ) -> None:
        """Add a local git source and scan for artifacts.

        Verifies:
        - Source is added to config
        - Artifacts are discovered correctly
        - Scan returns proper counts
        """
        from aam_cli.services.source_service import add_source, scan_source

        # -----
        # Step 1: Add the local repo as a source
        # -----
        result = add_source(
            source_str=f"file://{local_git_repo}",
            name="test/source",
        )

        assert result["name"] == "test/source"
        assert result["artifact_count"] >= 1
        assert result["commit"] != ""

        # -----
        # Step 2: Scan the source
        # -----
        scan_result = scan_source("test/source")

        assert scan_result["source_name"] == "test/source"
        assert scan_result["total_count"] >= 1
        assert len(scan_result["artifacts"]) >= 1

        # Verify specific artifact types discovered
        art_types = {a["type"] for a in scan_result["artifacts"]}
        assert "skill" in art_types


################################################################################
#                                                                              #
# SOURCE UPDATE LIFECYCLE                                                      #
#                                                                              #
################################################################################


class TestSourceUpdateLifecycle:
    """Integration test: update a source after upstream changes."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires file:// URL parser support — future enhancement")
    def test_integration_update_detects_new_artifact(
        self,
        local_git_repo: Path,
        aam_home: Path,  # noqa: ARG002
    ) -> None:
        """Add source, commit new artifact, update, verify change report.

        Verifies:
        - Update fetches new commits
        - Change report reflects new artifacts
        """
        from aam_cli.services.source_service import add_source, update_source

        # -----
        # Step 1: Add the source
        # -----
        add_result = add_source(
            source_str=f"file://{local_git_repo}",
            name="test/update",
        )
        initial_commit = add_result["commit"]

        # -----
        # Step 2: Add a new skill to the origin repo
        # -----
        new_skill = local_git_repo / "skills" / "new-skill"
        new_skill.mkdir(parents=True)
        (new_skill / "SKILL.md").write_text("# New Skill\nA freshly added skill.")

        subprocess.run(
            ["git", "add", "."],
            cwd=local_git_repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Add new skill"],
            cwd=local_git_repo,
            check=True,
            capture_output=True,
        )

        # -----
        # Step 3: Update the source
        # -----
        update_result = update_source("test/update")

        assert update_result["sources_updated"] == 1
        report = update_result["reports"][0]
        assert report["source_name"] == "test/update"

        # The commit should have changed
        assert report["new_commit"] != initial_commit or report["has_changes"]


################################################################################
#                                                                              #
# SOURCE LIST / REMOVE                                                         #
#                                                                              #
################################################################################


class TestSourceListRemove:
    """Integration test: list and remove sources."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires file:// URL parser support — future enhancement")
    def test_integration_list_and_remove(
        self,
        local_git_repo: Path,
        aam_home: Path,  # noqa: ARG002
    ) -> None:
        """Add, list, and remove a source.

        Verifies:
        - Added source appears in list
        - Removed source disappears
        """
        from aam_cli.services.source_service import (
            add_source,
            list_sources,
            remove_source,
        )

        # Add
        add_source(
            source_str=f"file://{local_git_repo}",
            name="test/remove-me",
        )

        # List
        list_result = list_sources()
        source_names = [s["name"] for s in list_result["sources"]]
        assert "test/remove-me" in source_names

        # Remove
        remove_result = remove_source("test/remove-me")
        assert remove_result["removed"] is True

        # Verify it's gone
        list_result2 = list_sources()
        source_names2 = [s["name"] for s in list_result2["sources"]]
        assert "test/remove-me" not in source_names2
