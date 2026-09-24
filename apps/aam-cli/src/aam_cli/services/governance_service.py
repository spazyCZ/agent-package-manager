"""Client-side governance policy enforcement.

Evaluates install and publish policies from the user's configuration
to block disallowed operations before any resolution or file operations.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import fnmatch
import logging

from pydantic import BaseModel

from aam_cli.core.config import AamConfig
from aam_cli.utils.naming import parse_package_name

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# DATA MODELS                                                                  #
#                                                                              #
################################################################################


class PolicyViolation(BaseModel):
    """A single governance policy violation."""

    rule: str
    package_name: str
    message: str


class PolicyResult(BaseModel):
    """Result of evaluating governance policies."""

    allowed: bool
    violations: list[PolicyViolation] = []


################################################################################
#                                                                              #
# EXCEPTIONS                                                                   #
#                                                                              #
################################################################################


class PolicyViolationError(Exception):
    """Raised when a governance policy blocks an operation."""

    def __init__(self, violation: PolicyViolation) -> None:
        self.violation = violation
        super().__init__(violation.message)


################################################################################
#                                                                              #
# FUNCTIONS                                                                    #
#                                                                              #
################################################################################


def check_install_policy(
    package_name: str,
    version: str,
    tags: list[str],
    signed: bool,
    config: AamConfig,
) -> PolicyResult:
    """Evaluate install governance policies against a package.

    Checks the following rules in order, raising on the first violation:
      1. ``allowed_scopes`` — if non-empty, the package must have a scope
         that appears in the allow-list.
      2. ``require_signature`` — the package must be signed.
      3. ``require_tag`` — the specified tag must be present.
      4. ``blocked_packages`` — the package name must not match any
         blocked glob pattern (via ``fnmatch.fnmatchcase``).

    This function is called once per package in the full resolved
    dependency graph, including all transitive and optional dependencies
    — not just the direct CLI argument.

    The ``signed`` bool is derived by checking whether the package's
    registry metadata includes a ``signature`` field (e.g. a Sigstore
    bundle or GPG detached signature).  v1 only supports
    registry-provided signatures, not local file ``.sig`` verification.

    Args:
        package_name: Full package name (e.g. ``"@scope/pkg"`` or
            ``"my-pkg"``).
        version: The resolved version string.
        tags: Distribution tags associated with the package version.
        signed: Whether the package has a valid signature from its
            registry.
        config: The loaded AAM configuration containing governance
            policies.

    Returns:
        ``PolicyResult(allowed=True)`` when all checks pass.

    Raises:
        PolicyViolationError: On the first policy violation found.
    """
    policy = config.governance.install_policy

    # -----
    # Extract scope from the package name
    # -----
    scope, _ = parse_package_name(package_name)

    # -----
    # Rule 1: allowed_scopes
    # -----
    if policy.allowed_scopes:
        if not scope:
            violation = PolicyViolation(
                rule="allowed_scopes",
                package_name=package_name,
                message=(
                    f"Package '{package_name}' has no scope, but policy "
                    f"requires one of: {policy.allowed_scopes}"
                ),
            )
            logger.warning(
                "Governance violation: %s", violation.message
            )
            raise PolicyViolationError(violation)

        scope_with_at = f"@{scope}"
        if scope_with_at not in policy.allowed_scopes:
            violation = PolicyViolation(
                rule="allowed_scopes",
                package_name=package_name,
                message=(
                    f"Package '{package_name}' scope '{scope_with_at}' "
                    f"is not in allowed scopes: {policy.allowed_scopes}"
                ),
            )
            logger.warning(
                "Governance violation: %s", violation.message
            )
            raise PolicyViolationError(violation)

    # -----
    # Rule 2: require_signature
    # -----
    if policy.require_signature and not signed:
        violation = PolicyViolation(
            rule="require_signature",
            package_name=package_name,
            message=(
                f"Package '{package_name}' is not signed, but policy "
                f"requires a valid signature"
            ),
        )
        logger.warning("Governance violation: %s", violation.message)
        raise PolicyViolationError(violation)

    # -----
    # Rule 3: require_tag
    # -----
    if policy.require_tag and policy.require_tag not in tags:
        violation = PolicyViolation(
            rule="require_tag",
            package_name=package_name,
            message=(
                f"Package '{package_name}' does not have required tag "
                f"'{policy.require_tag}'; available tags: {tags}"
            ),
        )
        logger.warning("Governance violation: %s", violation.message)
        raise PolicyViolationError(violation)

    # -----
    # Rule 4: blocked_packages
    # -----
    for pattern in policy.blocked_packages:
        if fnmatch.fnmatchcase(package_name, pattern):
            violation = PolicyViolation(
                rule="blocked_packages",
                package_name=package_name,
                message=(
                    f"Package '{package_name}' matches blocked pattern "
                    f"'{pattern}'"
                ),
            )
            logger.warning(
                "Governance violation: %s", violation.message
            )
            raise PolicyViolationError(violation)

    logger.debug(
        "Governance install policy passed for '%s@%s'",
        package_name,
        version,
    )
    return PolicyResult(allowed=True)


def check_publish_policy(
    signed: bool,
    config: AamConfig,
) -> PolicyResult:
    """Evaluate publish governance policies.

    Args:
        signed: Whether the package will be published with a valid
            signature.
        config: The loaded AAM configuration containing governance
            policies.

    Returns:
        ``PolicyResult(allowed=True)`` when all checks pass.

    Raises:
        PolicyViolationError: If the publish policy requires a signature
            and the package is unsigned.
    """
    policy = config.governance.publish_policy

    if policy.require_signature and not signed:
        violation = PolicyViolation(
            rule="require_signature",
            package_name="",
            message=(
                "Publish policy requires a valid signature, but the "
                "package is not signed"
            ),
        )
        logger.warning("Governance violation: %s", violation.message)
        raise PolicyViolationError(violation)

    logger.debug("Governance publish policy passed")
    return PolicyResult(allowed=True)
