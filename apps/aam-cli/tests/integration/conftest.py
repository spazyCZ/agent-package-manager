"""Shared fixtures for integration tests.

Provides temporary registries, workspaces, sample packages,
and pre-configured MCP server/client instances for end-to-end testing.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
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


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Create a temporary .aam/ workspace directory.

    Returns:
        Path to the temporary project root with .aam/ created.
    """
    workspace = tmp_path / ".aam"
    workspace.mkdir()
    packages_dir = workspace / "packages"
    packages_dir.mkdir()
    return tmp_path


@pytest.fixture
def sample_package(tmp_path: Path) -> Path:
    """Create a valid sample package with aam.yaml and artifacts.

    Returns:
        Path to the sample package directory.
    """
    pkg_dir = tmp_path / "sample-pkg"
    pkg_dir.mkdir()

    # -----
    # Create aam.yaml manifest
    # -----
    manifest_content = """name: sample-pkg
version: 1.0.0
description: A sample package for testing
author: Test Author
artifacts:
  skills:
    - name: test-skill
      path: skills/test-skill/
      description: A test skill
  agents: []
  prompts: []
  instructions: []
dependencies: {}
platforms:
  cursor:
    skill_scope: project
    deploy_instructions_as: rules
"""
    (pkg_dir / "aam.yaml").write_text(manifest_content)

    # -----
    # Create artifact directory
    # -----
    skill_dir = pkg_dir / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test Skill\nA skill for testing.")

    logger.debug(f"Created sample package at {pkg_dir}")
    return pkg_dir
