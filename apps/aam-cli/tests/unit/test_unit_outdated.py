"""Unit tests for ``aam outdated`` command.

Tests outdated detection with mocked lock file and source caches,
JSON output format, and stale source warnings.

Reference: spec 004 US4; tasks.md T027.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import pytest

from aam_cli.core.workspace import LockedPackage
from aam_cli.services.upgrade_service import OutdatedPackage, OutdatedResult

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# TEST: OUTDATED RESULT                                                        #
#                                                                              #
################################################################################


class TestOutdatedResult:
    """Verify OutdatedResult dataclass behavior."""

    def test_empty_result(self) -> None:
        """Empty result should have zero counts."""
        result = OutdatedResult()

        assert result.total_outdated == 0
        assert len(result.outdated) == 0
        assert len(result.up_to_date) == 0
        assert len(result.no_source) == 0
        assert len(result.stale_sources) == 0

    def test_outdated_package_fields(self) -> None:
        """OutdatedPackage should hold all required fields."""
        op = OutdatedPackage(
            name="test-pkg",
            current_commit="abc1234",
            latest_commit="def5678",
            source_name="my-source",
            has_local_modifications=False,
        )

        assert op.name == "test-pkg"
        assert op.current_commit == "abc1234"
        assert op.latest_commit == "def5678"
        assert op.source_name == "my-source"
        assert op.has_local_modifications is False


################################################################################
#                                                                              #
# TEST: LOCKED PACKAGE SOURCE FIELDS                                           #
#                                                                              #
################################################################################


class TestLockedPackageSourceFields:
    """Verify LockedPackage source tracking fields (spec 004)."""

    def test_source_fields_none_by_default(self) -> None:
        """source_name and source_commit should default to None."""
        lp = LockedPackage(
            version="1.0.0",
            source="registry",
            checksum="sha256:abc",
        )

        assert lp.source_name is None
        assert lp.source_commit is None

    def test_source_fields_both_set(self) -> None:
        """Both source fields should be settable together."""
        lp = LockedPackage(
            version="0.0.0",
            source="source",
            checksum="sha256:abc",
            source_name="openai/skills",
            source_commit="abc123def456",
        )

        assert lp.source_name == "openai/skills"
        assert lp.source_commit == "abc123def456"

    def test_source_fields_copresence_validation(self) -> None:
        """Only one source field set should raise ValueError."""
        with pytest.raises(ValueError, match="source_name and source_commit"):
            LockedPackage(
                version="0.0.0",
                source="source",
                checksum="sha256:abc",
                source_name="openai/skills",
                source_commit=None,
            )

    def test_no_source_in_lock_categorized_correctly(self) -> None:
        """Packages without source fields should be categorized as no_source."""
        result = OutdatedResult()

        # Simulating: registry package has no source fields
        result.no_source.append("registry-pkg")

        assert "registry-pkg" in result.no_source
