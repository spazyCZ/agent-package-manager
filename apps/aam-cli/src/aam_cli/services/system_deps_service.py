"""System dependency pre-flight checks and auto-installation.

Verifies OS-level and runtime system requirements declared in
package manifests before installation proceeds.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import importlib.metadata
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel

from aam_cli.core.manifest import SystemDependencies

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# MODELS                                                                       #
#                                                                              #
################################################################################


class SystemCheckResult(BaseModel):
    """Result of a single system dependency check."""

    name: str
    dep_type: str
    required: bool
    found: bool
    found_version: str | None = None
    found_path: str | None = None
    install_hint: str | None = None


class SystemCheckResults(BaseModel):
    """Aggregated results of all system dependency checks."""

    passed: list[SystemCheckResult] = []
    failed: list[SystemCheckResult] = []
    optional_failed: list[SystemCheckResult] = []

    @property
    def all_required_passed(self) -> bool:
        """Return True if all required dependency checks passed."""
        return len(self.failed) == 0


################################################################################
#                                                                              #
# CHECK FUNCTIONS                                                              #
#                                                                              #
################################################################################


def _check_python(required_version: str) -> SystemCheckResult:
    """Check system python3 binary version.

    Uses ``subprocess.run(["python3", "--version"])`` to check the
    system ``python3`` binary, NOT ``sys.version_info`` which reflects
    the CLI's own venv and would give a false positive in virtualenv
    environments.

    Args:
        required_version: Version constraint string (e.g. ">=3.11").

    Returns:
        SystemCheckResult for the python dependency.
    """
    try:
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Output is typically "Python 3.11.5"
            version_str = result.stdout.strip().replace("Python ", "")
            python_path = shutil.which("python3")
            return SystemCheckResult(
                name="python",
                dep_type="runtime",
                required=True,
                found=True,
                found_version=version_str,
                found_path=python_path,
            )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.debug(f"python3 check failed: {exc}")

    return SystemCheckResult(
        name="python",
        dep_type="runtime",
        required=True,
        found=False,
        install_hint="Install Python 3.11+ from https://python.org",
    )


def _check_node(required_version: str) -> SystemCheckResult:
    """Check system node binary version.

    Args:
        required_version: Version constraint string (e.g. ">=18").

    Returns:
        SystemCheckResult for the node dependency.
    """
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Output is typically "v18.17.0"
            version_str = result.stdout.strip().lstrip("v")
            node_path = shutil.which("node")
            return SystemCheckResult(
                name="node",
                dep_type="runtime",
                required=True,
                found=True,
                found_version=version_str,
                found_path=node_path,
            )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.debug(f"node check failed: {exc}")

    return SystemCheckResult(
        name="node",
        dep_type="runtime",
        required=True,
        found=False,
        install_hint="Install Node.js from https://nodejs.org",
    )


def _check_binary(binary_name: str) -> SystemCheckResult:
    """Check if a binary is available on PATH via ``shutil.which()``.

    Args:
        binary_name: Name of the binary to locate.

    Returns:
        SystemCheckResult for the binary dependency.
    """
    path = shutil.which(binary_name)
    if path:
        return SystemCheckResult(
            name=binary_name,
            dep_type="binary",
            required=True,
            found=True,
            found_path=path,
        )

    return SystemCheckResult(
        name=binary_name,
        dep_type="binary",
        required=True,
        found=False,
        install_hint=f"Install '{binary_name}' and ensure it is on PATH",
    )


def _check_pip_package(package_name: str) -> SystemCheckResult:
    """Check if a pip package is installed via ``importlib.metadata``.

    Uses ``importlib.metadata.version()`` for fast, subprocess-free
    package detection.

    Args:
        package_name: Name of the pip package.

    Returns:
        SystemCheckResult for the pip dependency.
    """
    try:
        version = importlib.metadata.version(package_name)
        return SystemCheckResult(
            name=package_name,
            dep_type="pip",
            required=True,
            found=True,
            found_version=version,
        )
    except importlib.metadata.PackageNotFoundError:
        return SystemCheckResult(
            name=package_name,
            dep_type="pip",
            required=True,
            found=False,
            install_hint=f"pip install {package_name}",
        )


def _check_npm_package(package_name: str) -> SystemCheckResult:
    """Check if an npm package is installed globally.

    Uses ``subprocess.run(["npm", "list", "-g", "--json"])`` and
    parses the JSON output for the package name.

    Args:
        package_name: Name of the npm package.

    Returns:
        SystemCheckResult for the npm dependency.
    """
    try:
        result = subprocess.run(
            ["npm", "list", "-g", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 or result.stdout:
            data = json.loads(result.stdout)
            deps = data.get("dependencies", {})
            if package_name in deps:
                version = deps[package_name].get("version", "unknown")
                return SystemCheckResult(
                    name=package_name,
                    dep_type="npm",
                    required=True,
                    found=True,
                    found_version=version,
                )
    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
    ) as exc:
        logger.debug(f"npm check failed for '{package_name}': {exc}")

    return SystemCheckResult(
        name=package_name,
        dep_type="npm",
        required=True,
        found=False,
        install_hint=f"npm install -g {package_name}",
    )


def _check_cargo_package(package_name: str) -> SystemCheckResult:
    """Check if a cargo package is installed.

    Uses ``subprocess.run(["cargo", "install", "--list"])`` and
    parses the output for package names (UAAPS section 13.7).

    Args:
        package_name: Name of the cargo package.

    Returns:
        SystemCheckResult for the cargo dependency.
    """
    try:
        result = subprocess.run(
            ["cargo", "install", "--list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            # Output format: "package_name v1.0.0:\n    binary_name\n"
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith(package_name + " "):
                    # Parse version from "package_name v1.0.0:"
                    parts = line.split()
                    version = parts[1].lstrip("v").rstrip(":") if len(parts) > 1 else None
                    return SystemCheckResult(
                        name=package_name,
                        dep_type="cargo",
                        required=True,
                        found=True,
                        found_version=version,
                    )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.debug(f"cargo check failed for '{package_name}': {exc}")

    return SystemCheckResult(
        name=package_name,
        dep_type="cargo",
        required=True,
        found=False,
        install_hint=f"cargo install {package_name}",
    )


def _check_brew_package(package_name: str) -> SystemCheckResult:
    """Check if a Homebrew package is installed.

    Uses ``brew list --versions <package>`` to detect the package.
    Returns ``found=False`` with a Homebrew install hint if brew
    itself is not available.

    Args:
        package_name: Name of the brew formula.

    Returns:
        SystemCheckResult for the brew dependency.
    """
    try:
        result = subprocess.run(
            ["brew", "list", "--versions", package_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Output format: "package_name 1.2.3"
            parts = result.stdout.strip().split()
            version = parts[1] if len(parts) > 1 else None
            return SystemCheckResult(
                name=package_name,
                dep_type="brew",
                required=True,
                found=True,
                found_version=version,
            )
    except FileNotFoundError:
        logger.debug(f"brew not found — cannot check '{package_name}'")
        return SystemCheckResult(
            name=package_name,
            dep_type="brew",
            required=True,
            found=False,
            install_hint="Install Homebrew: https://brew.sh",
        )
    except subprocess.TimeoutExpired as exc:
        logger.debug(f"brew check timed out for '{package_name}': {exc}")

    return SystemCheckResult(
        name=package_name,
        dep_type="brew",
        required=True,
        found=False,
        install_hint=f"brew install {package_name}",
    )


def _check_apt_package(package_name: str) -> SystemCheckResult:
    """Check if a Debian/Ubuntu package is installed.

    Uses ``dpkg -s <package>`` and checks the exit code. Returns
    ``found=False`` with an informational hint if dpkg is not available
    (non-Debian system).

    Args:
        package_name: Name of the apt/dpkg package.

    Returns:
        SystemCheckResult for the apt dependency.
    """
    try:
        result = subprocess.run(
            ["dpkg", "-s", package_name],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            # Parse version from "Version: x.y.z" line
            version = None
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    version = line.split(":", 1)[1].strip()
                    break
            return SystemCheckResult(
                name=package_name,
                dep_type="apt",
                required=True,
                found=True,
                found_version=version,
            )
    except FileNotFoundError:
        logger.debug(f"dpkg not found — cannot check '{package_name}'")
        return SystemCheckResult(
            name=package_name,
            dep_type="apt",
            required=True,
            found=False,
            install_hint="apt is not available on this system",
        )
    except subprocess.TimeoutExpired as exc:
        logger.debug(f"dpkg check timed out for '{package_name}': {exc}")

    return SystemCheckResult(
        name=package_name,
        dep_type="apt",
        required=True,
        found=False,
        install_hint=f"sudo apt-get install {package_name}",
    )


def _check_mcp_server(server_name: str) -> SystemCheckResult:
    """Check if an MCP server is configured.

    Parses ``~/.claude/.mcp.json`` for server names. This path is
    Claude Code-specific; other platforms may use different locations.

    Args:
        server_name: Name of the MCP server to check.

    Returns:
        SystemCheckResult for the MCP server dependency.
    """
    mcp_config_path = Path.home() / ".claude" / ".mcp.json"

    try:
        if mcp_config_path.is_file():
            data = json.loads(mcp_config_path.read_text(encoding="utf-8"))
            servers = data.get("mcpServers", {})
            if server_name in servers:
                return SystemCheckResult(
                    name=server_name,
                    dep_type="mcp",
                    required=True,
                    found=True,
                    found_path=str(mcp_config_path),
                )
    except (json.JSONDecodeError, OSError) as exc:
        logger.debug(f"MCP config check failed for '{server_name}': {exc}")

    return SystemCheckResult(
        name=server_name,
        dep_type="mcp",
        required=True,
        found=False,
        install_hint=f"Install MCP server '{server_name}' via 'mcp install {server_name}'",
    )


################################################################################
#                                                                              #
# SERVICE FUNCTIONS                                                            #
#                                                                              #
################################################################################


def check_system_deps(
    system_deps: SystemDependencies,
) -> SystemCheckResults:
    """Run pre-flight checks for all declared system dependencies.

    Verifies OS-level and runtime system requirements declared in a
    package manifest. Each check is wrapped in try/except to handle
    missing binaries gracefully.

    Args:
        system_deps: System dependencies from a package manifest.

    Returns:
        Aggregated :class:`SystemCheckResults` with passed, failed,
        and optional_failed lists.
    """
    logger.info("Running system dependency pre-flight checks")

    results = SystemCheckResults()

    # -----
    # Check python runtime
    # -----
    if system_deps.python:
        check = _check_python(system_deps.python)
        if check.found:
            results.passed.append(check)
        else:
            results.failed.append(check)

    # -----
    # Check node runtime
    # -----
    if system_deps.node:
        check = _check_node(system_deps.node)
        if check.found:
            results.passed.append(check)
        else:
            results.failed.append(check)

    # -----
    # Check binaries
    # -----
    for binary in system_deps.binaries:
        check = _check_binary(binary)
        if check.found:
            results.passed.append(check)
        else:
            results.failed.append(check)

    # -----
    # Check pip packages
    # -----
    for pkg in system_deps.packages.pip:
        check = _check_pip_package(pkg)
        if check.found:
            results.passed.append(check)
        else:
            results.failed.append(check)

    # -----
    # Check npm packages
    # -----
    for pkg in system_deps.packages.npm:
        check = _check_npm_package(pkg)
        if check.found:
            results.passed.append(check)
        else:
            results.failed.append(check)

    # -----
    # Check cargo packages
    # -----
    for pkg in system_deps.packages.cargo:
        check = _check_cargo_package(pkg)
        if check.found:
            results.passed.append(check)
        else:
            results.failed.append(check)

    # -----
    # Check brew packages
    # -----
    for pkg in system_deps.packages.brew:
        check = _check_brew_package(pkg)
        if check.found:
            results.passed.append(check)
        else:
            results.failed.append(check)

    # -----
    # Check apt packages
    # -----
    for pkg in system_deps.packages.apt:
        check = _check_apt_package(pkg)
        if check.found:
            results.passed.append(check)
        else:
            results.failed.append(check)

    # -----
    # Check MCP servers
    # -----
    for server in system_deps.mcp_servers:
        check = _check_mcp_server(server)
        if check.found:
            results.passed.append(check)
        else:
            results.failed.append(check)

    logger.info(
        f"System dep checks complete: "
        f"passed={len(results.passed)}, "
        f"failed={len(results.failed)}, "
        f"optional_failed={len(results.optional_failed)}"
    )

    return results


################################################################################
#                                                                              #
# AUTO-INSTALL                                                                 #
#                                                                              #
################################################################################


def auto_install_system_deps(
    missing: list[SystemCheckResult],
    allow_sudo: bool,
) -> dict[str, bool]:
    """Attempt to auto-install missing system dependencies.

    Supports automatic installation for pip and npm packages. Brew/apt
    packages require ``allow_sudo=True``. Binary dependencies are always
    rejected with instructions. MCP servers are installed via ``mcp install``
    if the ``mcp`` CLI is on PATH.

    Args:
        missing: List of failed system check results to attempt installing.
        allow_sudo: Whether to allow operations that may require sudo
            (brew/apt package managers).

    Returns:
        Dict mapping dependency names to installation success booleans.
    """
    logger.info(
        f"Auto-installing {len(missing)} missing system deps "
        f"(allow_sudo={allow_sudo})"
    )

    install_results: dict[str, bool] = {}

    for dep in missing:
        # -----
        # pip packages
        # -----
        if dep.dep_type == "pip":
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep.name],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                success = result.returncode == 0
                install_results[dep.name] = success
                if success:
                    logger.info(f"Auto-installed pip package: {dep.name}")
                else:
                    logger.warning(
                        f"Failed to install pip package '{dep.name}': "
                        f"{result.stderr.strip()}"
                    )
            except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
                logger.warning(f"pip install failed for '{dep.name}': {exc}")
                install_results[dep.name] = False

        # -----
        # npm packages
        # -----
        elif dep.dep_type == "npm":
            try:
                result = subprocess.run(
                    ["npm", "install", "-g", dep.name],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                success = result.returncode == 0
                install_results[dep.name] = success
                if success:
                    logger.info(f"Auto-installed npm package: {dep.name}")
                else:
                    logger.warning(
                        f"Failed to install npm package '{dep.name}': "
                        f"{result.stderr.strip()}"
                    )
            except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
                logger.warning(f"npm install failed for '{dep.name}': {exc}")
                install_results[dep.name] = False

        # -----
        # brew/apt packages — gated behind allow_sudo
        # -----
        elif dep.dep_type in ("brew", "apt"):
            if not allow_sudo:
                logger.warning(
                    f"Skipping {dep.dep_type} install for '{dep.name}': "
                    f"--allow-sudo not set"
                )
                install_results[dep.name] = False
                continue

            if dep.dep_type == "brew":
                cmd = ["brew", "install", dep.name]
            else:
                cmd = ["sudo", "apt-get", "install", "-y", dep.name]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                success = result.returncode == 0
                install_results[dep.name] = success
                if success:
                    logger.info(
                        f"Auto-installed {dep.dep_type} package: {dep.name}"
                    )
                else:
                    logger.warning(
                        f"Failed to install {dep.dep_type} package "
                        f"'{dep.name}': {result.stderr.strip()}"
                    )
            except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
                logger.warning(
                    f"{dep.dep_type} install failed for '{dep.name}': {exc}"
                )
                install_results[dep.name] = False

        # -----
        # Binary dependencies — always rejected with instructions
        # -----
        elif dep.dep_type == "binary":
            logger.info(
                f"Cannot auto-install binary '{dep.name}'. "
                f"Hint: {dep.install_hint}"
            )
            install_results[dep.name] = False

        # -----
        # MCP servers — install via mcp CLI if available
        # -----
        elif dep.dep_type == "mcp":
            mcp_path = shutil.which("mcp")
            if not mcp_path:
                logger.warning(
                    f"Cannot auto-install MCP server '{dep.name}': "
                    f"'mcp' CLI not found on PATH"
                )
                install_results[dep.name] = False
                continue

            try:
                result = subprocess.run(
                    ["mcp", "install", dep.name],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                success = result.returncode == 0
                install_results[dep.name] = success
                if success:
                    logger.info(f"Auto-installed MCP server: {dep.name}")
                else:
                    logger.warning(
                        f"Failed to install MCP server '{dep.name}': "
                        f"{result.stderr.strip()}"
                    )
            except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
                logger.warning(
                    f"MCP install failed for '{dep.name}': {exc}"
                )
                install_results[dep.name] = False

        # -----
        # Runtime dependencies (python, node) — cannot auto-install
        # -----
        elif dep.dep_type == "runtime":
            logger.info(
                f"Cannot auto-install runtime '{dep.name}'. "
                f"Hint: {dep.install_hint}"
            )
            install_results[dep.name] = False

        # -----
        # Unknown dep type — skip
        # -----
        else:
            logger.warning(
                f"Unknown dep type '{dep.dep_type}' for '{dep.name}', "
                f"skipping auto-install"
            )
            install_results[dep.name] = False

    logger.info(
        f"Auto-install complete: "
        f"{sum(1 for v in install_results.values() if v)}/{len(install_results)} "
        f"succeeded"
    )

    return install_results
