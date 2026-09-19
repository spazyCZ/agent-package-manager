"""Unit tests for UAAPS-aligned pkg create path and manifest mapping."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

from pathlib import Path

from aam_cli.commands.pkg.create import _artifact_target_path, _generate_manifest_dict
from aam_cli.detection.scanner import DetectedArtifact


################################################################################
#                                                                              #
# TEST CASES                                                                   #
#                                                                              #
################################################################################


def test_unit_legacy_prompt_maps_to_commands_path() -> None:
    """Legacy detected prompt artifacts are emitted into commands/."""
    artifact = DetectedArtifact(
        name="welcome",
        type="prompt",
        source_path=Path("prompts/welcome.md"),
    )

    target_path = _artifact_target_path(artifact, organize="copy")

    assert target_path == "commands/welcome.md"


def test_unit_legacy_instruction_maps_to_rules_path() -> None:
    """Legacy detected instruction artifacts are emitted into rules/."""
    artifact = DetectedArtifact(
        name="python-standards",
        type="instruction",
        source_path=Path("instructions/python-standards.md"),
    )

    target_path = _artifact_target_path(artifact, organize="copy")

    assert target_path == "rules/python-standards.md"


def test_unit_generate_manifest_uses_commands_and_rules_keys() -> None:
    """Manifest generation uses UAAPS artifact keys for legacy scanner types."""
    artifacts = [
        DetectedArtifact(
            name="welcome",
            type="prompt",
            source_path=Path("prompts/welcome.md"),
        ),
        DetectedArtifact(
            name="python-standards",
            type="instruction",
            source_path=Path("instructions/python-standards.md"),
        ),
    ]

    manifest_data = _generate_manifest_dict(
        name="test-pkg",
        version="1.0.0",
        description="Test package",
        author="",
        license_str="Apache-2.0",
        artifacts=artifacts,
        organize="copy",
    )

    assert "commands" in manifest_data["artifacts"]
    assert "rules" in manifest_data["artifacts"]
    assert manifest_data["artifacts"]["commands"][0]["path"] == "commands/welcome.md"
    assert manifest_data["artifacts"]["rules"][0]["path"] == "rules/python-standards.md"
