"""Dependency tree inspection service for AAM.

Provides tree visualisation, dependency tracing (why), package-presence
checks, integrity auditing, duplicate detection, and pruning operations
against the universal lock file and ``.agent-packages/`` directory.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from aam_cli.core.resolver import DependencyType
from aam_cli.core.workspace import (
    read_universal_lock_file,
)
from aam_cli.utils.paths import get_packages_dir

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


class DependencyTreeNode(BaseModel):
    """A node in the resolved dependency tree."""

    name: str
    version: str
    source: str
    dep_type: DependencyType = DependencyType.DIRECT
    children: list["DependencyTreeNode"] = []
    optional: bool = False


class AuditFinding(BaseModel):
    """A security or integrity finding from ``aam audit``."""

    package_name: str
    version: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    title: str
    description: str
    finding_type: Literal["integrity", "advisory"] = "integrity"
    advisory_url: str | None = None


################################################################################
#                                                                              #
# UTILITY FUNCTIONS                                                            #
#                                                                              #
################################################################################


def _compute_dir_hash(directory: Path) -> str:
    """Compute a deterministic SHA-256 hash for a directory tree.

    Strategy: sorted file list → per-file SHA-256 → combined SHA-256
    of concatenated ``<relative_path>:<hex_digest>`` strings.

    Args:
        directory: Directory to hash.

    Returns:
        Hex digest string prefixed with ``sha256-``.
    """
    # -----
    # Collect all files, sorted for determinism
    # -----
    file_hashes: list[str] = []

    for file_path in sorted(directory.rglob("*")):
        if not file_path.is_file():
            continue
        # -----
        # Skip .lock and __pycache__ files for stability
        # -----
        if file_path.name in (".lock",) or "__pycache__" in file_path.parts:
            continue

        relative = file_path.relative_to(directory)
        file_digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        file_hashes.append(f"{relative}:{file_digest}")

    # -----
    # Combine all file hashes into a single digest
    # -----
    combined = "\n".join(file_hashes)
    final_digest = hashlib.sha256(combined.encode()).hexdigest()
    return f"sha256-{final_digest}"


def _effective_dir(project_dir: Path | None) -> Path:
    """Return resolved project directory, defaulting to cwd."""
    return (project_dir or Path.cwd()).resolve()


################################################################################
#                                                                              #
# SERVICE FUNCTIONS                                                            #
#                                                                              #
################################################################################


def get_tree(
    project_dir: Path | None = None,
    depth: int = 0,
) -> dict[str, Any]:
    """Build a dependency tree from the universal lock file.

    Reads ``package.agent.lock`` and constructs a tree rooted at a
    virtual ``root`` node, with each direct package as a child.
    Transitive dependencies are resolved from the lock file's
    ``dependencies`` map.

    Args:
        project_dir: Project root directory. Defaults to cwd.
        depth: Maximum tree depth (0 = unlimited).

    Returns:
        Dict with ``tree`` key containing a :class:`DependencyTreeNode`
        serialized as a dict, plus metadata fields.
    """
    logger.info(f"Getting dependency tree: depth={depth}")

    eff_dir = _effective_dir(project_dir)
    lock = read_universal_lock_file(eff_dir)

    root = DependencyTreeNode(
        name="root",
        version="0.0.0",
        source="local",
        dep_type=DependencyType.DIRECT,
    )

    # -----
    # Build top-level nodes for each locked package
    # -----
    def _build_node(
        name: str, current_depth: int, visited: set[str]
    ) -> DependencyTreeNode | None:
        """Recursively build a tree node.

        Args:
            name: Package name.
            current_depth: Current recursion depth.
            visited: Already-visited names to prevent infinite recursion.

        Returns:
            DependencyTreeNode or None if already visited / not in lock.
        """
        if name in visited:
            return None
        locked = lock.packages.get(name)
        if not locked:
            return None

        visited = visited | {name}
        node = DependencyTreeNode(
            name=name,
            version=locked.version,
            source=locked.source,
            dep_type=DependencyType.OPTIONAL if locked.optional else DependencyType.DIRECT,
            optional=locked.optional,
        )

        # -----
        # Recurse into children unless depth limit reached
        # -----
        if depth == 0 or current_depth < depth:
            for dep_name in locked.dependencies:
                child = _build_node(dep_name, current_depth + 1, visited)
                if child:
                    node.children.append(child)

        return node

    for pkg_name in lock.packages:
        node = _build_node(pkg_name, 1, set())
        if node:
            root.children.append(node)

    logger.info(
        f"Tree built: packages={len(lock.packages)}, "
        f"root_children={len(root.children)}"
    )

    return {
        "tree": root.model_dump(),
        "total_packages": len(lock.packages),
        "lock_file": str(get_packages_dir(eff_dir).parent / "package.agent.lock"),
    }


def get_why(
    package_name: str,
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Find which packages require a given package.

    Traverses the lock file's ``dependencies`` maps to find all packages
    that list ``package_name`` as a dependency.

    Args:
        package_name: Package name to trace.
        project_dir: Project root directory. Defaults to cwd.

    Returns:
        Dict with ``required_by`` list (each entry has ``name``,
        ``version``, ``is_direct``), ``package_name``, and ``found``.
    """
    logger.info(f"Getting dependency provenance: package='{package_name}'")

    eff_dir = _effective_dir(project_dir)
    lock = read_universal_lock_file(eff_dir)

    if package_name not in lock.packages:
        return {
            "package_name": package_name,
            "found": False,
            "required_by": [],
        }

    # -----
    # Find all packages whose dependencies include package_name
    # -----
    required_by: list[dict[str, Any]] = []

    for pkg_name, locked in lock.packages.items():
        if pkg_name == package_name:
            continue
        if package_name in locked.dependencies:
            required_by.append({
                "name": pkg_name,
                "version": locked.version,
                "constraint": locked.dependencies[package_name],
                "is_direct": not locked.optional,
            })

    # -----
    # If no package requires it, it is itself a direct root dependency
    # -----
    target = lock.packages[package_name]
    logger.info(
        f"Dependency provenance found: "
        f"package='{package_name}', required_by={len(required_by)}"
    )

    return {
        "package_name": package_name,
        "version": target.version,
        "found": True,
        "is_direct": len(required_by) == 0,
        "required_by": required_by,
    }


def check_deps(
    project_dir: Path | None = None,
    system_only: bool = False,
) -> dict[str, Any]:
    """Check that all locked packages are physically installed.

    For each package in the lock file, verifies that its directory exists
    in ``.agent-packages/``. With ``system_only=True``, aggregates system
    dependencies across all installed manifests and runs pre-flight checks.

    Args:
        project_dir: Project root directory. Defaults to cwd.
        system_only: If True, check system dependencies only (skip
            directory presence check).

    Returns:
        Dict with ``check_type``, ``results``, ``all_passed``, and
        ``total`` fields.
    """
    logger.info(f"Checking dependencies: system_only={system_only}")

    eff_dir = _effective_dir(project_dir)

    # =====================================================================
    # system_only branch: aggregate + check system deps
    # =====================================================================
    if system_only:
        from aam_cli.core.manifest import (
            SystemDependencies,
            SystemPackages,
            load_manifest_universal,
        )
        from aam_cli.services.system_deps_service import check_system_deps

        packages_dir = get_packages_dir(eff_dir)

        # -----
        # Merge system dependencies across all installed packages
        # -----
        python_version: str | None = None
        node_version: str | None = None
        pip_pkgs: list[str] = []
        npm_pkgs: list[str] = []
        brew_pkgs: list[str] = []
        apt_pkgs: list[str] = []
        cargo_pkgs: list[str] = []
        binaries: list[str] = []
        mcp_servers: list[str] = []

        if packages_dir.is_dir():
            for pkg_dir in packages_dir.iterdir():
                if not pkg_dir.is_dir():
                    continue
                try:
                    manifest = load_manifest_universal(pkg_dir)
                    sys_deps = manifest.system_dependencies
                    if sys_deps is None:
                        continue
                    if sys_deps.python and not python_version:
                        python_version = sys_deps.python
                    if sys_deps.node and not node_version:
                        node_version = sys_deps.node
                    for item in sys_deps.packages.pip:
                        if item not in pip_pkgs:
                            pip_pkgs.append(item)
                    for item in sys_deps.packages.npm:
                        if item not in npm_pkgs:
                            npm_pkgs.append(item)
                    for item in sys_deps.packages.brew:
                        if item not in brew_pkgs:
                            brew_pkgs.append(item)
                    for item in sys_deps.packages.apt:
                        if item not in apt_pkgs:
                            apt_pkgs.append(item)
                    for item in sys_deps.packages.cargo:
                        if item not in cargo_pkgs:
                            cargo_pkgs.append(item)
                    for item in sys_deps.binaries:
                        if item not in binaries:
                            binaries.append(item)
                    for item in sys_deps.mcp_servers:
                        if item not in mcp_servers:
                            mcp_servers.append(item)
                except Exception as exc:
                    logger.debug(
                        f"Could not load manifest from '{pkg_dir}': {exc}"
                    )

        merged = SystemDependencies(
            python=python_version,
            node=node_version,
            packages=SystemPackages(
                pip=pip_pkgs,
                npm=npm_pkgs,
                brew=brew_pkgs,
                apt=apt_pkgs,
                cargo=cargo_pkgs,
            ),
            binaries=binaries,
            mcp_servers=mcp_servers,
        )

        results = check_system_deps(merged)

        check_results = []
        for r in results.passed:
            check_results.append({**r.model_dump(), "status": "ok"})
        for r in results.failed:
            check_results.append({**r.model_dump(), "status": "missing"})
        for r in results.optional_failed:
            check_results.append({**r.model_dump(), "status": "optional_missing"})

        all_passed = results.all_required_passed
        logger.info(
            f"System dep check complete: "
            f"passed={len(results.passed)}, failed={len(results.failed)}"
        )

        return {
            "check_type": "system",
            "results": check_results,
            "all_passed": all_passed,
            "total": len(check_results),
        }

    # =====================================================================
    # Default branch: check package directory presence
    # =====================================================================
    lock = read_universal_lock_file(eff_dir)
    packages_dir = get_packages_dir(eff_dir)

    from aam_cli.utils.naming import parse_package_name, to_filesystem_name

    check_results = []
    all_passed = True

    for pkg_name, locked in lock.packages.items():
        scope, base_name = parse_package_name(pkg_name)
        fs_name = to_filesystem_name(scope, base_name)
        pkg_dir = packages_dir / fs_name
        present = pkg_dir.is_dir()

        if not present:
            all_passed = False

        check_results.append({
            "name": pkg_name,
            "version": locked.version,
            "directory": str(pkg_dir),
            "present": present,
            "status": "ok" if present else "missing",
        })

    logger.info(
        f"Package presence check: total={len(check_results)}, "
        f"all_passed={all_passed}"
    )

    return {
        "check_type": "packages",
        "results": check_results,
        "all_passed": all_passed,
        "total": len(check_results),
    }


def audit_deps(
    project_dir: Path | None = None,
    severity: str = "all",
) -> dict[str, Any]:
    """Run integrity audit across all installed packages.

    Computes a deterministic SHA-256 hash of each installed package
    directory and compares against the ``integrity`` field stored in
    ``package.agent.lock``. Reports mismatches as CRITICAL findings.

    Args:
        project_dir: Project root directory. Defaults to cwd.
        severity: Minimum severity to include in results
            (``"critical"``, ``"high"``, ``"medium"``, ``"low"``,
            ``"info"``, or ``"all"`` to include everything).

    Returns:
        Dict with ``findings`` list (each a serialized :class:`AuditFinding`),
        ``total_checked``, ``findings_count``, and ``severity_filter``.
    """
    logger.info(f"Running dependency audit: severity='{severity}'")

    eff_dir = _effective_dir(project_dir)
    lock = read_universal_lock_file(eff_dir)
    packages_dir = get_packages_dir(eff_dir)

    from aam_cli.utils.naming import parse_package_name, to_filesystem_name

    findings: list[AuditFinding] = []
    severity_order = ["critical", "high", "medium", "low", "info"]
    min_level = severity_order.index(severity) if severity in severity_order else -1

    for pkg_name, locked in lock.packages.items():
        scope, base_name = parse_package_name(pkg_name)
        fs_name = to_filesystem_name(scope, base_name)
        pkg_dir = packages_dir / fs_name

        if not pkg_dir.is_dir():
            logger.debug(f"Package directory missing: '{pkg_dir}' — skipping audit")
            continue

        # -----
        # Compute current directory hash and compare to stored integrity
        # -----
        current_hash = _compute_dir_hash(pkg_dir)

        if locked.integrity and locked.integrity != current_hash:
            finding = AuditFinding(
                package_name=pkg_name,
                version=locked.version,
                severity="critical",
                title="Integrity check failed",
                description=(
                    f"Directory hash mismatch for '{pkg_name}@{locked.version}'. "
                    f"Expected: {locked.integrity}. "
                    f"Got: {current_hash}. "
                    "The package may have been tampered with."
                ),
                finding_type="integrity",
            )
            findings.append(finding)
            logger.warning(
                f"Integrity mismatch: package='{pkg_name}', "
                f"expected='{locked.integrity}', got='{current_hash}'"
            )
        elif not locked.integrity:
            # -----
            # No stored hash — package installed before this feature
            # -----
            finding = AuditFinding(
                package_name=pkg_name,
                version=locked.version,
                severity="info",
                title="No integrity hash recorded",
                description=(
                    f"Package '{pkg_name}@{locked.version}' has no stored "
                    "integrity hash. Reinstall to record a hash."
                ),
                finding_type="integrity",
            )
            findings.append(finding)

    # -----
    # Filter findings by severity level
    # -----
    if severity != "all":
        findings = [
            f for f in findings
            if severity_order.index(f.severity) <= min_level
        ]

    logger.info(
        f"Audit complete: checked={len(lock.packages)}, "
        f"findings={len(findings)}"
    )

    return {
        "findings": [f.model_dump() for f in findings],
        "total_checked": len(lock.packages),
        "findings_count": len(findings),
        "severity_filter": severity,
    }


def dedupe_deps(
    project_dir: Path | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Detect and remove duplicate packages in nested sub-namespace directories.

    v1 scope: scan ``.agent-packages/`` for packages that appear in more
    than one sub-namespace directory (a layout produced by pre-update
    installs or migration from ``.aam/packages/``). Hoists compatible
    versions to the root level.

    Post-v1-install packages are always flat (resolver fails on conflicts),
    so ``dedupe`` is most useful for migrated or legacy installs.

    Args:
        project_dir: Project root directory. Defaults to cwd.
        dry_run: If True, report what would be done without making changes.

    Returns:
        Dict with ``would_dedupe`` / ``deduped`` list of package names,
        ``packages_changed``, and ``dry_run`` flag.
    """
    logger.info(f"Running dedupe: dry_run={dry_run}")

    eff_dir = _effective_dir(project_dir)
    packages_dir = get_packages_dir(eff_dir)

    if not packages_dir.is_dir():
        return {
            "would_dedupe": [],
            "deduped": [],
            "packages_changed": 0,
            "dry_run": dry_run,
        }

    # -----
    # Look for packages that have sub-namespace copies
    # e.g., .agent-packages/@scope/pkg  vs  .agent-packages/pkg
    # -----
    seen_bases: dict[str, list[Path]] = {}

    for entry in packages_dir.iterdir():
        if not entry.is_dir():
            continue
        # -----
        # Collect base names — strip scope prefix if present
        # -----
        base = entry.name.split("__")[-1] if "__" in entry.name else entry.name
        seen_bases.setdefault(base, []).append(entry)

    duplicates: list[str] = []
    for base, paths in seen_bases.items():
        if len(paths) > 1:
            duplicates.append(base)
            if not dry_run:
                # -----
                # Remove non-root copies (keep the shortest path — root-level)
                # -----
                sorted_paths = sorted(paths, key=lambda p: len(p.parts))
                for path_to_remove in sorted_paths[1:]:
                    logger.info(f"Removing duplicate: '{path_to_remove}'")
                    shutil.rmtree(path_to_remove, ignore_errors=True)

    packages_changed = len(duplicates) if not dry_run else 0

    logger.info(
        f"Dedupe complete: duplicates={len(duplicates)}, "
        f"packages_changed={packages_changed}, dry_run={dry_run}"
    )

    result_key = "would_dedupe" if dry_run else "deduped"
    return {
        result_key: duplicates,
        "packages_changed": packages_changed,
        "dry_run": dry_run,
    }


def prune_deps(
    project_dir: Path | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Remove directories in ``.agent-packages/`` not tracked in the lock file.

    Compares the on-disk directory listing against lock file entries and
    removes any directories not in the lock file.

    Args:
        project_dir: Project root directory. Defaults to cwd.
        dry_run: If True, report what would be removed without removing.

    Returns:
        Dict with ``would_remove`` / ``removed`` list of directory names,
        ``packages_removed``, and ``dry_run`` flag.
    """
    logger.info(f"Running prune: dry_run={dry_run}")

    eff_dir = _effective_dir(project_dir)
    packages_dir = get_packages_dir(eff_dir)

    if not packages_dir.is_dir():
        return {
            "would_remove": [],
            "removed": [],
            "packages_removed": 0,
            "dry_run": dry_run,
        }

    lock = read_universal_lock_file(eff_dir)

    from aam_cli.utils.naming import parse_package_name, to_filesystem_name

    # -----
    # Build set of expected directory names from lock file
    # -----
    expected_dirs: set[str] = set()
    for pkg_name in lock.packages:
        scope, base_name = parse_package_name(pkg_name)
        expected_dirs.add(to_filesystem_name(scope, base_name))

    # -----
    # Find directories not in lock file
    # -----
    to_remove: list[str] = []

    for entry in packages_dir.iterdir():
        if not entry.is_dir():
            continue
        # -----
        # Skip internal directories (e.g., .downloads, .lock)
        # -----
        if entry.name.startswith("."):
            continue
        if entry.name not in expected_dirs:
            to_remove.append(entry.name)

    if not dry_run:
        for dir_name in to_remove:
            path = packages_dir / dir_name
            logger.info(f"Pruning unlisted directory: '{path}'")
            shutil.rmtree(path, ignore_errors=True)

    packages_removed = len(to_remove) if not dry_run else 0

    logger.info(
        f"Prune complete: found={len(to_remove)}, "
        f"removed={packages_removed}, dry_run={dry_run}"
    )

    result_key = "would_remove" if dry_run else "removed"
    return {
        result_key: to_remove,
        "packages_removed": packages_removed,
        "dry_run": dry_run,
    }
