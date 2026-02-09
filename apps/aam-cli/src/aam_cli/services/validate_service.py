"""Validate service for AAM.

Validates AAM package manifests and artifact paths.
Returns structured validation reports.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from aam_cli.core.manifest import load_manifest

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# SERVICE FUNCTIONS                                                            #
#                                                                              #
################################################################################


def validate_package(path: Path) -> dict[str, Any]:
    """Validate a package manifest and its artifact paths.

    Checks that ``aam.yaml`` is syntactically correct, all required
    fields are present, and all referenced artifact paths exist on disk.

    Validation failures are reported in the returned ValidationReport
    (``valid=false``, populated ``errors`` list) rather than raised
    as exceptions.

    Args:
        path: Path to the package directory containing ``aam.yaml``.

    Returns:
        ValidationReport dict per data-model.md. Always returns a
        report; never raises for domain validation failures.
    """
    logger.info(f"Validating package at: {path}")

    pkg_path = Path(path).resolve()
    manifest_file = pkg_path / "aam.yaml" if pkg_path.is_dir() else pkg_path

    # -----
    # Check manifest file exists
    # -----
    if not manifest_file.exists():
        logger.warning(f"No aam.yaml found at {pkg_path}")
        return {
            "valid": False,
            "package_name": None,
            "package_version": None,
            "errors": [
                "No aam.yaml found. Run 'aam create-package' or 'aam init' first."
            ],
            "warnings": [],
            "artifact_count": 0,
            "artifacts_valid": False,
        }

    pkg_dir = manifest_file.parent
    errors: list[str] = []
    warnings: list[str] = []

    # -----
    # Step 1: Parse and validate the manifest schema
    # -----
    try:
        manifest = load_manifest(pkg_dir)
    except ValidationError as exc:
        pydantic_errors: list[str] = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            pydantic_errors.append(f"{field}: {msg}")

        return {
            "valid": False,
            "package_name": None,
            "package_version": None,
            "errors": pydantic_errors,
            "warnings": [],
            "artifact_count": 0,
            "artifacts_valid": False,
        }
    except Exception as exc:
        return {
            "valid": False,
            "package_name": None,
            "package_version": None,
            "errors": [f"Failed to parse aam.yaml: {exc}"],
            "warnings": [],
            "artifact_count": 0,
            "artifacts_valid": False,
        }

    # -----
    # Step 2: Check optional fields
    # -----
    if not manifest.description:
        errors.append("description: empty")

    if not manifest.author:
        warnings.append("author: not set (optional)")

    # -----
    # Step 3: Validate artifact paths exist
    # -----
    artifacts_valid = True
    artifact_count = 0

    for _artifact_type, ref in manifest.all_artifacts:
        artifact_count += 1
        artifact_path = pkg_dir / ref.path

        if not artifact_path.exists():
            artifacts_valid = False
            errors.append(f"{ref.path}: file not found")

    # -----
    # Build report
    # -----
    is_valid = len(errors) == 0

    logger.info(
        f"Validation complete: name='{manifest.name}', "
        f"valid={is_valid}, errors={len(errors)}, warnings={len(warnings)}"
    )

    return {
        "valid": is_valid,
        "package_name": manifest.name,
        "package_version": manifest.version,
        "errors": errors,
        "warnings": warnings,
        "artifact_count": artifact_count,
        "artifacts_valid": artifacts_valid,
    }
