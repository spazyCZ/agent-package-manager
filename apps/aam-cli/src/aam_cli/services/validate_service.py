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

from aam_cli.core.autodiscovery import discover_artifacts
from aam_cli.core.manifest import PackageManifest, load_manifest_universal

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# PERMISSIONS AUDIT                                                            #
#                                                                              #
################################################################################


def _audit_permissions(manifest: PackageManifest) -> list[str]:
    """Audit package permissions for overly-broad grants.

    Checks for missing permissions, unrestricted shell access,
    broad filesystem writes, network wildcards, and plain HTTP schemes.

    Args:
        manifest: Validated package manifest.

    Returns:
        List of WARN-level diagnostic strings.
    """
    warnings: list[str] = []

    if manifest.permissions is None:
        warnings.append(
            "permissions: not declared — package has no capability restrictions"
        )
        return warnings

    perms = manifest.permissions

    # -----
    # Shell audit
    # -----
    if perms.shell.allow and not perms.shell.binaries:
        warnings.append(
            "permissions.shell: allow=true with no binary allow-list — "
            "unrestricted shell access"
        )

    # -----
    # Filesystem audit
    # -----
    for grant_type, paths in [("read", perms.fs.read), ("write", perms.fs.write)]:
        for p in paths:
            if p in ("*", "**", ".", "./"):
                warnings.append(
                    f"permissions.fs.{grant_type}: '{p}' grants broad "
                    f"{grant_type} access to the entire project"
                )

    # -----
    # Network audit
    # -----
    for host in perms.network.hosts:
        if host in ("*", "**"):
            warnings.append(
                f"permissions.network.hosts: '{host}' allows connections "
                "to any host"
            )

    if "http" in perms.network.schemes:
        warnings.append(
            "permissions.network.schemes: plain 'http' scheme enabled — "
            "data may be transmitted unencrypted"
        )

    return warnings


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

    errors: list[str] = []
    warnings: list[str] = []

    # -----
    # Step 1: Parse and validate the manifest schema
    # -----
    try:
        manifest = load_manifest_universal(pkg_path)
    except FileNotFoundError:
        logger.warning(f"No manifest found at {pkg_path}")
        return {
            "valid": False,
            "package_name": None,
            "package_version": None,
            "errors": [
                "No manifest found. Run 'aam create-package' or 'aam init' first."
            ],
            "warnings": [],
            "artifact_count": 0,
            "artifacts_valid": False,
            "manifest_format": None,
            "artifacts_discovered": False,
        }
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
            "manifest_format": None,
            "artifacts_discovered": False,
        }
    except Exception as exc:
        return {
            "valid": False,
            "package_name": None,
            "package_version": None,
            "errors": [f"Failed to parse manifest: {exc}"],
            "warnings": [],
            "artifact_count": 0,
            "artifacts_valid": False,
            "manifest_format": None,
            "artifacts_discovered": False,
        }

    pkg_dir = pkg_path if pkg_path.is_dir() else pkg_path.parent

    # -----
    # Step 2: Check optional fields
    # -----
    if not manifest.description:
        errors.append("description: empty")

    if not manifest.author:
        warnings.append("author: not set (optional)")

    # -----
    # Step 3: Resolve artifacts via auto-discovery if not explicitly declared
    # -----
    artifacts_were_explicit = manifest.artifacts is not None
    resolved_artifacts = discover_artifacts(pkg_dir, manifest)

    # -----
    # Step 4: Validate artifact paths exist
    # -----
    artifacts_valid = True
    artifact_count = 0

    for _artifact_type, ref in resolved_artifacts.all_artifacts:
        artifact_count += 1
        artifact_path = pkg_dir / ref.path

        if not artifact_path.exists():
            artifacts_valid = False
            errors.append(f"{ref.path}: file not found")

    # -----
    # Step 4b: Permissions security audit (UAAPS v0.5.0)
    # -----
    perm_warnings = _audit_permissions(manifest)
    warnings.extend(perm_warnings)

    # -----
    # Step 4c: Vendor extension count warning
    # -----
    if len(manifest.vendor_extensions) > 5:
        warnings.append(
            f"vendor_extensions: {len(manifest.vendor_extensions)} extensions "
            "declared — consider reducing to improve interoperability"
        )

    # -----
    # Step 5: Validate UAAPS v0.5.0 fields
    # -----
    for env_key, env_cfg in manifest.env.items():
        if not env_key:
            errors.append("env: key must not be empty")
        elif not env_cfg.description:
            warnings.append(f"env.{env_key}: description not set (optional)")

    if manifest.system_dependencies is not None:
        sys_deps = manifest.system_dependencies
        if sys_deps.python and not sys_deps.python.strip():
            errors.append("systemDependencies.python: empty string")
        if sys_deps.node and not sys_deps.node.strip():
            errors.append("systemDependencies.node: empty string")

    # -----
    # Build report
    # -----
    is_valid = len(errors) == 0

    logger.info(
        f"Validation complete: name='{manifest.name}', "
        f"valid={is_valid}, errors={len(errors)}, warnings={len(warnings)}, "
        f"format='{manifest.manifest_format}'"
    )

    return {
        "valid": is_valid,
        "package_name": manifest.name,
        "package_version": manifest.version,
        "errors": errors,
        "warnings": warnings,
        "artifact_count": artifact_count,
        "artifacts_valid": artifacts_valid,
        "manifest_format": manifest.manifest_format,
        "artifacts_discovered": not artifacts_were_explicit,
    }
