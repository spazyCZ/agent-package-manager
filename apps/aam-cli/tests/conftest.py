"""Shared test fixtures for AAM CLI tests.

Provides common fixtures used across unit and integration tests.

Reference: tasks.md T006.
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
from click.testing import CliRunner

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


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click test runner.

    Returns:
        Configured CliRunner with isolated filesystem.
    """
    return CliRunner(mix_stderr=False)


@pytest.fixture
def tmp_aam_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary ~/.aam/ directory and override HOME.

    This ensures tests don't touch the real user's config.

    Args:
        tmp_path: Pytest temporary directory.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        Path to the temporary home directory.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    # -----
    # Create .aam directory
    # -----
    aam_dir = fake_home / ".aam"
    aam_dir.mkdir()

    return fake_home


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a local bare git repository with sample SKILL.md files.

    This factory creates a bare repo, clones it, adds sample artifacts,
    and commits them. Useful for integration testing git operations.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        Path to the bare repository.
    """
    bare_repo = tmp_path / "test-repo.git"
    work_tree = tmp_path / "work-tree"

    # -----
    # Create bare repository
    # -----
    subprocess.run(
        ["git", "init", "--bare", str(bare_repo)],
        check=True,
        capture_output=True,
    )

    # -----
    # Clone and add sample content
    # -----
    subprocess.run(
        ["git", "clone", str(bare_repo), str(work_tree)],
        check=True,
        capture_output=True,
    )

    # Create sample skill
    skill_dir = work_tree / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test Skill\nA skill for testing.")

    # Create sample agent
    agent_dir = work_tree / "agents" / "test-agent"
    agent_dir.mkdir(parents=True)
    (agent_dir / "agent.yaml").write_text("name: test-agent\ndescription: Test agent\n")

    # -----
    # Commit and push
    # -----
    subprocess.run(
        ["git", "add", "."],
        cwd=work_tree,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=test@test.com", "-c", "user.name=Test",
         "commit", "-m", "Initial commit"],
        cwd=work_tree,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=work_tree,
        check=True,
        capture_output=True,
    )

    return bare_repo


@pytest.fixture
def sample_source_config() -> dict:
    """Create a sample source configuration dict.

    Returns:
        Dict matching SourceEntry fields.
    """
    return {
        "name": "openai/skills",
        "type": "git",
        "url": "https://github.com/openai/skills",
        "ref": "main",
        "path": "",
        "last_commit": "abc123def456789012345678901234567890abcd",
        "last_fetched": "2026-02-08T10:30:00Z",
        "artifact_count": 5,
        "default": False,
    }
