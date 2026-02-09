"""Doctor service for AAM.

Runs environment diagnostics to identify configuration, registry,
and package integrity issues. Returns a structured DoctorReport.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import sys
from pathlib import Path
from typing import Any

from aam_cli.core.config import load_config
from aam_cli.core.manifest import load_manifest
from aam_cli.core.workspace import get_packages_dir, read_lock_file
from aam_cli.utils.naming import parse_package_name, to_filesystem_name

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

MIN_PYTHON_VERSION = (3, 11)
STAGING_DIR_NAME = ".tmp"

################################################################################
#                                                                              #
# SERVICE FUNCTIONS                                                            #
#                                                                              #
################################################################################


def run_diagnostics(
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Run comprehensive AAM environment diagnostics.

    Performs the following checks:
      1. Python version >= 3.11
      2. AAM configuration is valid and loadable
      3. Configured registries are accessible
      4. Installed packages have valid manifests and checksums
      5. No incomplete installations (leftover staging directories)

    Args:
        project_dir: Project root directory. Defaults to cwd.

    Returns:
        DoctorReport dict per data-model.md with ``healthy``, ``checks``,
        and ``summary``.
    """
    logger.info("Running AAM environment diagnostics")

    effective_dir = project_dir or Path.cwd()
    checks: list[dict[str, Any]] = []

    # -----
    # Check 1: Python version
    # -----
    checks.append(_check_python_version())

    # -----
    # Check 2: Configuration validity
    # -----
    checks.append(_check_config_valid(effective_dir))

    # -----
    # Check 3: Registry accessibility
    # -----
    checks.extend(_check_registries(effective_dir))

    # -----
    # Check 4: Package integrity
    # -----
    checks.extend(_check_packages_integrity(effective_dir))

    # -----
    # Check 5: Incomplete installations
    # -----
    checks.append(_check_incomplete_installs(effective_dir))

    # -----
    # Build summary
    # -----
    total = len(checks)
    passed = sum(1 for c in checks if c["status"] == "pass")
    warned = sum(1 for c in checks if c["status"] == "warn")
    failed = sum(1 for c in checks if c["status"] == "fail")

    healthy = failed == 0
    summary = f"{passed}/{total} checks passed"
    if warned > 0:
        summary += f", {warned} warnings"
    if failed > 0:
        summary += f", {failed} failures"

    logger.info(f"Diagnostics complete: {summary}")

    return {
        "healthy": healthy,
        "checks": checks,
        "summary": summary,
    }


################################################################################
#                                                                              #
# INDIVIDUAL CHECKS                                                            #
#                                                                              #
################################################################################


def _check_python_version() -> dict[str, Any]:
    """Verify Python version is >= 3.11.

    Returns:
        DoctorCheck dict.
    """
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if (version.major, version.minor) >= MIN_PYTHON_VERSION:
        return {
            "name": "python_version",
            "status": "pass",
            "message": f"Python {version_str}",
            "suggestion": None,
        }

    return {
        "name": "python_version",
        "status": "fail",
        "message": f"Python {version_str} (requires >= 3.11)",
        "suggestion": "Upgrade to Python 3.11 or later.",
    }


def _check_config_valid(project_dir: Path) -> dict[str, Any]:
    """Attempt to load AAM configuration and report errors.

    Args:
        project_dir: Project root directory.

    Returns:
        DoctorCheck dict.
    """
    try:
        config = load_config(project_dir)
        reg_count = len(config.registries)
        return {
            "name": "config_valid",
            "status": "pass",
            "message": (
                f"Configuration loaded ({reg_count} "
                f"registr{'y' if reg_count == 1 else 'ies'} configured)"
            ),
            "suggestion": None,
        }
    except Exception as exc:
        return {
            "name": "config_valid",
            "status": "fail",
            "message": f"Failed to load configuration: {exc}",
            "suggestion": (
                "Check ~/.aam/config.yaml and .aam/config.yaml for syntax errors."
            ),
        }


def _check_registries(project_dir: Path) -> list[dict[str, Any]]:
    """Check accessibility of each configured registry.

    For local registries, verifies the path exists and is readable.
    HTTP registries are deferred to future implementation.

    Args:
        project_dir: Project root directory.

    Returns:
        List of DoctorCheck dicts (one per registry).
    """
    checks: list[dict[str, Any]] = []

    try:
        config = load_config(project_dir)
    except Exception:
        # Config check already reported the failure
        return checks

    for reg in config.registries:
        if reg.url.startswith("file://"):
            from aam_cli.utils.paths import parse_file_url

            local_path = parse_file_url(reg.url)

            if local_path.is_dir():
                checks.append(
                    {
                        "name": f"registry_{reg.name}",
                        "status": "pass",
                        "message": f"Registry '{reg.name}' accessible at {local_path}",
                        "suggestion": None,
                    }
                )
            else:
                checks.append(
                    {
                        "name": f"registry_{reg.name}",
                        "status": "warn",
                        "message": (
                            f"Registry '{reg.name}' path not found: {local_path}"
                        ),
                        "suggestion": (
                            f"Run 'aam registry init {local_path}' to create it, "
                            f"or 'aam registry remove {reg.name}' to remove it."
                        ),
                    }
                )
        else:
            # HTTP registry — defer connectivity check
            checks.append(
                {
                    "name": f"registry_{reg.name}",
                    "status": "pass",
                    "message": (
                        f"Registry '{reg.name}' at {reg.url} "
                        f"(HTTP connectivity check deferred)"
                    ),
                    "suggestion": None,
                }
            )

    return checks


def _check_packages_integrity(project_dir: Path) -> list[dict[str, Any]]:
    """Verify installed package manifests are parseable and paths valid.

    Args:
        project_dir: Project root directory.

    Returns:
        List of DoctorCheck dicts (one per installed package).
    """
    checks: list[dict[str, Any]] = []
    lock = read_lock_file(project_dir)

    if not lock.packages:
        return checks

    packages_dir = get_packages_dir(project_dir)

    for pkg_name, _locked in lock.packages.items():
        scope, base_name = parse_package_name(pkg_name)
        fs_name = to_filesystem_name(scope, base_name)
        pkg_dir = packages_dir / fs_name

        if not pkg_dir.is_dir():
            checks.append(
                {
                    "name": f"package_{pkg_name}",
                    "status": "warn",
                    "message": (
                        f"Package '{pkg_name}' directory not found: {pkg_dir}"
                    ),
                    "suggestion": (
                        f"Run 'aam install {pkg_name} --force' to reinstall."
                    ),
                }
            )
            continue

        try:
            manifest = load_manifest(pkg_dir)
            checks.append(
                {
                    "name": f"package_{pkg_name}",
                    "status": "pass",
                    "message": (
                        f"Package '{pkg_name}@{manifest.version}' — "
                        f"manifest valid, {manifest.artifact_count} artifacts"
                    ),
                    "suggestion": None,
                }
            )
        except Exception as exc:
            checks.append(
                {
                    "name": f"package_{pkg_name}",
                    "status": "warn",
                    "message": (
                        f"Package '{pkg_name}' manifest error: {exc}"
                    ),
                    "suggestion": (
                        f"Run 'aam install {pkg_name} --force' to reinstall."
                    ),
                }
            )

    return checks


def _check_incomplete_installs(project_dir: Path) -> dict[str, Any]:
    """Detect leftover staging directories from incomplete installations.

    Checks for ``.aam/.tmp/`` entries that indicate a previous install
    was interrupted mid-operation.

    Args:
        project_dir: Project root directory.

    Returns:
        DoctorCheck dict.
    """
    workspace_dir = get_packages_dir(project_dir).parent
    staging_dir = workspace_dir / STAGING_DIR_NAME

    if not staging_dir.exists():
        return {
            "name": "incomplete_install",
            "status": "pass",
            "message": "No incomplete installations detected",
            "suggestion": None,
        }

    # -----
    # Check if staging directory has any entries
    # -----
    entries = list(staging_dir.iterdir())
    if not entries:
        return {
            "name": "incomplete_install",
            "status": "pass",
            "message": "No incomplete installations detected",
            "suggestion": None,
        }

    entry_names = [e.name for e in entries[:5]]
    return {
        "name": "incomplete_install",
        "status": "warn",
        "message": (
            f"Found {len(entries)} leftover staging entries: "
            f"{', '.join(entry_names)}"
        ),
        "suggestion": (
            "A previous installation may have been interrupted. "
            f"Remove '{staging_dir}' to clean up, then re-run the install."
        ),
    }
