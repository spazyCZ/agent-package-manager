"""Unit tests for permissions security audit.

Tests for ``_audit_permissions()`` in the validate service, covering
missing permissions, unrestricted shell, broad filesystem writes,
plain HTTP schemes, and clean permission sets.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

from aam_cli.core.manifest import (
    FsPermissions,
    NetworkPermissions,
    PackageManifest,
    PermissionsConfig,
    ShellPermissions,
)
from aam_cli.services.validate_service import _audit_permissions

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# TESTS: Permissions Audit                                                     #
#                                                                              #
################################################################################


class TestPermissionsAudit:
    """Tests for _audit_permissions function."""

    def test_unit_no_permissions_warns(self) -> None:
        """Missing permissions field generates a warning."""
        manifest = PackageManifest(
            name="test-pkg", version="1.0.0", description="Test",
        )
        warnings = _audit_permissions(manifest)
        assert len(warnings) == 1
        assert "not declared" in warnings[0]

    def test_unit_unrestricted_shell_warns(self) -> None:
        """Shell allow=True with no binaries generates warning."""
        manifest = PackageManifest(
            name="test-pkg", version="1.0.0", description="Test",
            permissions=PermissionsConfig(
                shell=ShellPermissions(allow=True, binaries=[]),
            ),
        )
        warnings = _audit_permissions(manifest)
        assert any("unrestricted shell" in w for w in warnings)

    def test_unit_broad_fs_write_warns(self) -> None:
        """Wildcard fs.write generates warning."""
        manifest = PackageManifest(
            name="test-pkg", version="1.0.0", description="Test",
            permissions=PermissionsConfig(
                fs=FsPermissions(write=["*"]),
            ),
        )
        warnings = _audit_permissions(manifest)
        assert any("broad" in w and "write" in w for w in warnings)

    def test_unit_http_scheme_warns(self) -> None:
        """Plain http scheme generates warning."""
        manifest = PackageManifest(
            name="test-pkg", version="1.0.0", description="Test",
            permissions=PermissionsConfig(
                network=NetworkPermissions(schemes=["http", "https"]),
            ),
        )
        warnings = _audit_permissions(manifest)
        assert any("http" in w and "unencrypted" in w for w in warnings)

    def test_unit_clean_permissions_no_warnings(self) -> None:
        """Reasonable permissions generate no warnings."""
        manifest = PackageManifest(
            name="test-pkg", version="1.0.0", description="Test",
            permissions=PermissionsConfig(
                fs=FsPermissions(read=["./src"]),
                network=NetworkPermissions(hosts=["api.example.com"]),
                shell=ShellPermissions(allow=True, binaries=["node"]),
            ),
        )
        warnings = _audit_permissions(manifest)
        assert warnings == []
