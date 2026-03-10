"""Shared test fixtures for AAM CLI tests.

Provides common fixtures used across unit and integration tests.

Reference: tasks.md T006, T084.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from aam_cli.core.manifest import SystemDependencies, SystemPackages

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


################################################################################
#                                                                              #
# UAAPS v0.4.0 FIXTURES (T084)                                                #
#                                                                              #
################################################################################


@pytest.fixture
def tmp_agent_packages(tmp_path: Path) -> Path:
    """Create a ``.agent-packages/`` directory in tmp_path.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        Path to the ``.agent-packages/`` directory.
    """
    pkg_dir = tmp_path / ".agent-packages"
    pkg_dir.mkdir()
    return pkg_dir


@pytest.fixture
def sample_manifest_json(tmp_path: Path) -> Path:
    """Write a minimal valid ``package.agent.json`` to tmp_path.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        Path to the written ``package.agent.json`` file.
    """
    manifest = {
        "name": "@test/sample-pkg",
        "version": "1.0.0",
        "description": "A sample test package",
        "author": "Test Author",
        "artifacts": {
            "skills": [],
            "agents": [],
            "prompts": [],
            "instructions": [],
        },
        "dependencies": {},
    }
    manifest_path = tmp_path / "package.agent.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


@pytest.fixture
def sample_lock_file_v2(tmp_path: Path) -> Path:
    """Write a minimal ``package.agent.lock`` to tmp_path.

    Uses camelCase keys per UAAPS §13.3.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        Path to the written ``package.agent.lock`` file.
    """
    lock_data = {
        "lockVersion": 1,
        "resolvedAt": "2026-01-01T00:00:00Z",
        "resolved": {
            "@test/sample-pkg": {
                "version": "1.0.0",
                "source": "local",
                "integrity": "sha256-abc123",
                "dependencies": {},
                "optional": False,
                "peer": False,
            }
        },
        "systemChecks": {},
    }
    lock_path = tmp_path / "package.agent.lock"
    lock_path.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    return lock_path


@pytest.fixture
def sample_system_dependencies() -> SystemDependencies:
    """Return a ``SystemDependencies`` instance with one entry per dep type.

    Returns:
        :class:`SystemDependencies` with python, node, pip, npm, cargo,
        binary, and MCP server entries.
    """
    return SystemDependencies(
        python=">=3.11",
        node=">=18",
        packages=SystemPackages(
            pip=["requests>=2.28"],
            npm=["typescript"],
            brew=["jq"],
            apt=["git"],
            cargo=["ripgrep"],
        ),
        binaries=["curl"],
        mcp_servers=["filesystem"],
    )


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
