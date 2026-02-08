"""DNS verification utilities for AAM registry domains.

Provides helpers to verify that DNS nameserver delegation is correctly
configured for ``aamregistry.io`` and its subdomains.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import socket
from dataclasses import dataclass, field

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

EXPECTED_NAMESERVERS: set[str] = {
    "ns-cloud-e1.googledomains.com",
    "ns-cloud-e2.googledomains.com",
    "ns-cloud-e3.googledomains.com",
    "ns-cloud-e4.googledomains.com",
}

DEFAULT_DOMAIN: str = "aamregistry.io"

################################################################################
#                                                                              #
# DATA CLASSES                                                                 #
#                                                                              #
################################################################################


@dataclass
class DnsVerificationResult:
    """Result of a DNS verification check."""

    domain: str
    resolved_nameservers: list[str] = field(default_factory=list)
    expected_nameservers: set[str] = field(default_factory=lambda: set(EXPECTED_NAMESERVERS))
    is_valid: bool = False
    missing_nameservers: list[str] = field(default_factory=list)
    extra_nameservers: list[str] = field(default_factory=list)
    error: str | None = None


################################################################################
#                                                                              #
# FUNCTIONS                                                                    #
#                                                                              #
################################################################################


def verify_dns(
    domain: str = DEFAULT_DOMAIN,
    expected: set[str] | None = None,
) -> DnsVerificationResult:
    """Verify that DNS nameservers are correctly configured for a domain.

    Performs a NS record lookup and compares the results against the
    expected Google Cloud DNS nameservers.

    Args:
        domain: The domain to verify. Defaults to ``aamregistry.io``.
        expected: Custom set of expected nameservers. Defaults to the
            Google Cloud DNS nameservers for ``aamregistry.io``.

    Returns:
        A ``DnsVerificationResult`` with resolution details.
    """
    if expected is None:
        expected = set(EXPECTED_NAMESERVERS)

    result = DnsVerificationResult(
        domain=domain,
        expected_nameservers=expected,
    )

    logger.info(f"Verifying DNS for domain: {domain}")

    # -----
    # Step 1: Resolve NS records
    # -----
    import contextlib

    with contextlib.suppress(socket.gaierror):
        socket.getaddrinfo(domain, None, socket.AF_INET)

    try:
        import subprocess

        proc = subprocess.run(
            ["dig", "+short", "NS", domain],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if proc.returncode != 0:
            result.error = f"dig command failed: {proc.stderr.strip()}"
            logger.error(result.error)
            return result

        raw_ns = proc.stdout.strip()
        if not raw_ns:
            result.error = f"No NS records found for {domain}. DNS may not be propagated yet."
            logger.warning(result.error)
            return result

        # Parse nameservers — dig returns trailing dots, strip them
        resolved = [ns.rstrip(".").lower() for ns in raw_ns.splitlines() if ns.strip()]
        result.resolved_nameservers = sorted(resolved)

    except FileNotFoundError:
        result.error = (
            "'dig' command not found. Install dnsutils "
            "(apt install dnsutils) or bind-utils (yum install bind-utils)."
        )
        logger.error(result.error)
        return result
    except subprocess.TimeoutExpired:
        result.error = "DNS lookup timed out after 10 seconds."
        logger.error(result.error)
        return result

    # -----
    # Step 2: Compare against expected nameservers
    # -----
    resolved_set = {ns.lower() for ns in result.resolved_nameservers}
    expected_lower = {ns.lower() for ns in expected}

    result.missing_nameservers = sorted(expected_lower - resolved_set)
    result.extra_nameservers = sorted(resolved_set - expected_lower)
    result.is_valid = expected_lower.issubset(resolved_set)

    if result.is_valid:
        logger.info(f"DNS verification passed for {domain}")
    else:
        logger.warning(
            f"DNS verification failed for {domain}: missing={result.missing_nameservers}"
        )

    return result


def verify_domain_resolves(domain: str = DEFAULT_DOMAIN) -> bool:
    """Quick check whether a domain resolves to any IP address.

    Args:
        domain: The domain to check. Defaults to ``aamregistry.io``.

    Returns:
        ``True`` if the domain resolves, ``False`` otherwise.
    """
    try:
        socket.getaddrinfo(domain, None)
        logger.info(f"Domain {domain} resolves successfully")
        return True
    except socket.gaierror:
        logger.warning(f"Domain {domain} does not resolve")
        return False
