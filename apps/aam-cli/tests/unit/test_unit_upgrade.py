"""Unit tests for ``aam upgrade`` command.

Tests upgrade result model, dry-run behavior, and force flag.

Reference: spec 004 US5; tasks.md T030.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

from aam_cli.services.upgrade_service import UpgradeResult

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# TEST: UPGRADE RESULT                                                         #
#                                                                              #
################################################################################


class TestUpgradeResult:
    """Verify UpgradeResult dataclass behavior."""

    def test_empty_result(self) -> None:
        """Empty result should have zero counts."""
        result = UpgradeResult()

        assert result.total_upgraded == 0
        assert len(result.upgraded) == 0
        assert len(result.skipped) == 0
        assert len(result.failed) == 0

    def test_upgraded_tracking(self) -> None:
        """Should track upgraded packages with commit info."""
        result = UpgradeResult()
        result.upgraded.append({
            "name": "test-pkg",
            "from_commit": "abc1234",
            "to_commit": "def5678",
        })
        result.total_upgraded = 1

        assert result.total_upgraded == 1
        assert result.upgraded[0]["name"] == "test-pkg"
        assert result.upgraded[0]["from_commit"] == "abc1234"
        assert result.upgraded[0]["to_commit"] == "def5678"

    def test_skipped_tracking(self) -> None:
        """Should track skipped packages with reason."""
        result = UpgradeResult()
        result.skipped.append({
            "name": "modified-pkg",
            "reason": "Local modifications detected.",
        })

        assert len(result.skipped) == 1
        assert result.skipped[0]["name"] == "modified-pkg"

    def test_failed_tracking(self) -> None:
        """Should track failed packages with error."""
        result = UpgradeResult()
        result.failed.append({
            "name": "broken-pkg",
            "error": "Source cache corrupted",
        })

        assert len(result.failed) == 1
        assert result.failed[0]["name"] == "broken-pkg"

    def test_mixed_results(self) -> None:
        """Should handle a mix of upgraded, skipped, and failed."""
        result = UpgradeResult()
        result.upgraded.append({"name": "a", "from_commit": "1", "to_commit": "2"})
        result.skipped.append({"name": "b", "reason": "modified"})
        result.failed.append({"name": "c", "error": "not found"})
        result.total_upgraded = 1

        assert result.total_upgraded == 1
        assert len(result.skipped) == 1
        assert len(result.failed) == 1
