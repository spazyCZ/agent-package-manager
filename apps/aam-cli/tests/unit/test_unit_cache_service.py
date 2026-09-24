"""Unit tests for the cache service.

Tests for package download cache operations: get, put, verify, clean,
and list_cached.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from unittest.mock import patch

from aam_cli.services import cache_service

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# TESTS: Cache Service                                                         #
#                                                                              #
################################################################################


class TestCacheService:
    """Tests for package download cache operations."""

    def test_unit_cache_miss(self) -> None:
        """get() returns None for uncached packages."""
        with patch.object(cache_service, "CACHE_DIR", Path("/nonexistent")):
            result = cache_service.get("@test/pkg", "1.0.0")
            assert result is None

    def test_unit_put_and_get(self, tmp_path: Path) -> None:
        """put() stores an archive and get() retrieves it."""
        with patch.object(cache_service, "CACHE_DIR", tmp_path):
            archive = tmp_path / "source.aam"
            archive.write_bytes(b"fake archive content")

            cached = cache_service.put("@test/pkg", "1.0.0", archive)
            assert cached.is_file()

            result = cache_service.get("@test/pkg", "1.0.0")
            assert result is not None
            assert result.is_file()

    def test_unit_verify_integrity(self, tmp_path: Path) -> None:
        """verify() returns True for intact cache entries."""
        with patch.object(cache_service, "CACHE_DIR", tmp_path):
            archive = tmp_path / "source.aam"
            archive.write_bytes(b"test content")

            cache_service.put("@test/pkg", "1.0.0", archive)
            assert cache_service.verify("@test/pkg", "1.0.0") is True

    def test_unit_clean_all(self, tmp_path: Path) -> None:
        """clean() with no args removes all cached packages."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        with patch.object(cache_service, "CACHE_DIR", cache_dir):
            archive = tmp_path / "source.aam"
            archive.write_bytes(b"content")
            cache_service.put("@test/pkg", "1.0.0", archive)
            cache_service.put("@test/other", "2.0.0", archive)

            removed = cache_service.clean()
            assert removed == 2

    def test_unit_list_cached(self, tmp_path: Path) -> None:
        """list_cached() returns entries in the cache."""
        with patch.object(cache_service, "CACHE_DIR", tmp_path):
            archive = tmp_path / "source.aam"
            archive.write_bytes(b"content")
            cache_service.put("@test/pkg", "1.0.0", archive)

            entries = cache_service.list_cached()
            assert len(entries) >= 1
            assert entries[0]["size_bytes"] > 0
