"""Unit tests for governance policy evaluation.

Tests ``check_install_policy()``, ``check_publish_policy()``, and
``PolicyViolationError``.

Reference: tasks.md T079.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import pytest

from aam_cli.core.config import AamConfig
from aam_cli.services.governance_service import (
    PolicyViolationError,
    check_install_policy,
    check_publish_policy,
)

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


def _config_with_install_policy(**kwargs) -> AamConfig:
    """Build an AamConfig with governance.install_policy set to kwargs."""
    raw = {
        "default_platform": "cursor",
        "governance": {
            "install_policy": kwargs,
        },
    }
    return AamConfig.model_validate(raw)


def _config_with_publish_policy(**kwargs) -> AamConfig:
    """Build an AamConfig with governance.publish_policy set to kwargs."""
    raw = {
        "default_platform": "cursor",
        "governance": {
            "publish_policy": kwargs,
        },
    }
    return AamConfig.model_validate(raw)


################################################################################
#                                                                              #
# TESTS: check_install_policy                                                  #
#                                                                              #
################################################################################


class TestCheckInstallPolicy:
    """Tests for ``check_install_policy()``."""

    def test_unit_empty_allowed_scopes_allows_all(self) -> None:
        """Empty allowed_scopes permits any package name."""
        config = _config_with_install_policy(allowed_scopes=[])
        result = check_install_policy(
            package_name="unscoped-pkg",
            version="1.0.0",
            tags=[],
            signed=False,
            config=config,
        )
        assert result.allowed is True

    def test_unit_scoped_package_matches_scope(self) -> None:
        """Scoped package @myorg/pkg is permitted when @myorg in allowed_scopes."""
        config = _config_with_install_policy(allowed_scopes=["@myorg"])
        result = check_install_policy(
            package_name="@myorg/pkg",
            version="1.0.0",
            tags=[],
            signed=False,
            config=config,
        )
        assert result.allowed is True

    def test_unit_unscoped_blocked_when_scopes_configured(self) -> None:
        """Unscoped package is blocked when allowed_scopes is non-empty."""
        config = _config_with_install_policy(allowed_scopes=["@myorg"])
        with pytest.raises(PolicyViolationError) as exc_info:
            check_install_policy(
                package_name="unscoped-pkg",
                version="1.0.0",
                tags=[],
                signed=False,
                config=config,
            )
        err = exc_info.value
        assert err.violation.rule == "allowed_scopes"
        assert "unscoped-pkg" in err.violation.package_name

    def test_unit_blocked_packages_glob_blocks_match(self) -> None:
        """blocked_packages glob @sketchy/* blocks @sketchy/pkg."""
        config = _config_with_install_policy(blocked_packages=["@sketchy/*"])
        with pytest.raises(PolicyViolationError) as exc_info:
            check_install_policy(
                package_name="@sketchy/pkg",
                version="1.0.0",
                tags=[],
                signed=False,
                config=config,
            )
        err = exc_info.value
        assert err.violation.rule == "blocked_packages"

    def test_unit_blocked_packages_glob_allows_non_match(self) -> None:
        """blocked_packages glob @sketchy/* allows @safe/pkg."""
        config = _config_with_install_policy(blocked_packages=["@sketchy/*"])
        result = check_install_policy(
            package_name="@safe/pkg",
            version="1.0.0",
            tags=[],
            signed=False,
            config=config,
        )
        assert result.allowed is True

    def test_unit_require_tag_blocks_untagged_package(self) -> None:
        """require_tag blocks a package with no matching tag."""
        config = _config_with_install_policy(require_tag="stable")
        with pytest.raises(PolicyViolationError) as exc_info:
            check_install_policy(
                package_name="@myorg/pkg",
                version="1.0.0",
                tags=[],
                signed=False,
                config=config,
            )
        err = exc_info.value
        assert err.violation.rule == "require_tag"

    def test_unit_require_tag_allows_tagged_package(self) -> None:
        """require_tag permits a package that carries the required tag."""
        config = _config_with_install_policy(require_tag="stable")
        result = check_install_policy(
            package_name="@myorg/pkg",
            version="1.0.0",
            tags=["stable", "v2"],
            signed=False,
            config=config,
        )
        assert result.allowed is True

    def test_unit_require_signature_blocks_unsigned(self) -> None:
        """require_signature=True blocks packages where signed=False."""
        config = _config_with_install_policy(require_signature=True)
        with pytest.raises(PolicyViolationError) as exc_info:
            check_install_policy(
                package_name="@myorg/pkg",
                version="1.0.0",
                tags=[],
                signed=False,
                config=config,
            )
        err = exc_info.value
        assert err.violation.rule == "require_signature"

    def test_unit_require_signature_allows_signed(self) -> None:
        """require_signature=True allows packages where signed=True."""
        config = _config_with_install_policy(require_signature=True)
        result = check_install_policy(
            package_name="@myorg/pkg",
            version="1.0.0",
            tags=[],
            signed=True,
            config=config,
        )
        assert result.allowed is True

    def test_unit_policy_violation_error_has_rule_and_message(self) -> None:
        """PolicyViolationError carries violation.rule, .package_name, .message."""
        config = _config_with_install_policy(require_signature=True)
        with pytest.raises(PolicyViolationError) as exc_info:
            check_install_policy(
                package_name="@myorg/pkg",
                version="1.0.0",
                tags=[],
                signed=False,
                config=config,
            )
        err = exc_info.value
        assert hasattr(err, "violation")
        assert hasattr(err.violation, "rule")
        assert hasattr(err.violation, "package_name")
        assert hasattr(err.violation, "message")
        assert err.violation.message


################################################################################
#                                                                              #
# TESTS: check_publish_policy                                                  #
#                                                                              #
################################################################################


class TestCheckPublishPolicy:
    """Tests for ``check_publish_policy()``."""

    def test_unit_publish_no_policy_allows(self) -> None:
        """Empty publish policy allows publishing."""
        config = _config_with_publish_policy()
        result = check_publish_policy(signed=False, config=config)
        assert result.allowed is True

    def test_unit_publish_require_signature_blocks_unsigned(self) -> None:
        """require_signature=True in publish policy blocks unsigned publish."""
        config = _config_with_publish_policy(require_signature=True)
        with pytest.raises(PolicyViolationError) as exc_info:
            check_publish_policy(signed=False, config=config)
        err = exc_info.value
        assert err.violation.rule == "require_signature"

    def test_unit_publish_require_signature_allows_signed(self) -> None:
        """require_signature=True allows signed publish."""
        config = _config_with_publish_policy(require_signature=True)
        result = check_publish_policy(signed=True, config=config)
        assert result.allowed is True
