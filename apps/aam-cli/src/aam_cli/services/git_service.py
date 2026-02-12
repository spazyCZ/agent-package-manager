"""Git subprocess wrapper for clone, fetch, and diff operations.

Provides a safe interface to the system ``git`` binary with retry
logic, error handling, and cache path management.

All git operations are performed via ``subprocess.run()`` to avoid
heavyweight Python git library dependencies.

Reference: plan.md Phase 2, tasks T016–T018.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import hashlib
import logging
import shutil
import subprocess
import time
from pathlib import Path

from aam_cli.utils.paths import get_global_aam_dir

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

# Retry configuration (exponential backoff)
MAX_RETRIES: int = 3
RETRY_DELAYS: list[float] = [1.0, 2.0, 4.0]

# Git command timeout in seconds
GIT_TIMEOUT: int = 120

# Cache directory name under ~/.aam/
CACHE_DIR_NAME: str = "cache"
GIT_CACHE_DIR_NAME: str = "git"


################################################################################
#                                                                              #
# EXCEPTIONS                                                                   #
#                                                                              #
################################################################################


class GitError(Exception):
    """Raised when a git operation fails after all retries."""


class GitNotAvailableError(GitError):
    """Raised when the ``git`` binary is not found on PATH."""


class GitCloneError(GitError):
    """Raised when git clone fails after retries."""


class GitFetchError(GitError):
    """Raised when git fetch fails after retries."""


class GitCacheCorruptedError(GitError):
    """Raised when the cached clone directory is corrupted."""


################################################################################
#                                                                              #
# INTERNAL HELPERS                                                             #
#                                                                              #
################################################################################


def _run_git(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = GIT_TIMEOUT,
) -> subprocess.CompletedProcess[str]:
    """Execute a git command via subprocess.

    Args:
        args: Git subcommand and arguments (without leading ``git``).
        cwd: Working directory for the command.
        timeout: Maximum execution time in seconds.

    Returns:
        Completed process result.

    Raises:
        GitError: If the command fails.
    """
    cmd = ["git"] + args
    logger.debug(f"Running git command: {' '.join(cmd)}, cwd={cwd}")

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        logger.debug(
            f"Git command failed: returncode={result.returncode}, "
            f"stderr='{result.stderr.strip()}'"
        )

    return result


def _run_with_retry(
    args: list[str],
    cwd: Path | None = None,
    error_class: type[GitError] = GitError,
    operation_name: str = "git operation",
) -> subprocess.CompletedProcess[str]:
    """Execute a git command with exponential backoff retry.

    Retries up to ``MAX_RETRIES`` times with delays of 1s, 2s, 4s
    between attempts.

    Args:
        args: Git subcommand and arguments.
        cwd: Working directory for the command.
        error_class: Exception class to raise on final failure.
        operation_name: Human-readable operation name for logging.

    Returns:
        Completed process result on success.

    Raises:
        GitError: (or subclass) if all retries fail.
    """
    last_error: str = ""

    for attempt in range(MAX_RETRIES):
        try:
            result = _run_git(args, cwd=cwd)

            if result.returncode == 0:
                return result

            last_error = result.stderr.strip()

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {delay}s: {last_error}"
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"{operation_name} failed after {MAX_RETRIES} attempts: {last_error}"
                )

        except subprocess.TimeoutExpired:
            last_error = f"Command timed out after {GIT_TIMEOUT}s"
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.warning(
                    f"{operation_name} timed out (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {delay}s"
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"{operation_name} timed out after {MAX_RETRIES} attempts"
                )

    raise error_class(
        f"{operation_name} failed after {MAX_RETRIES} attempts: {last_error}"
    )


################################################################################
#                                                                              #
# CACHE PATH MANAGEMENT                                                        #
#                                                                              #
################################################################################


def get_cache_dir(host: str, owner: str, repo: str) -> Path:
    """Compute the cache directory path for a git source.

    Structure: ``~/.aam/cache/git/{host}/{owner}/{repo}/``

    Args:
        host: Repository host (e.g., ``github.com``).
        owner: Repository owner.
        repo: Repository name.

    Returns:
        Absolute path to the cache directory.
    """
    cache_path = (
        get_global_aam_dir()
        / CACHE_DIR_NAME
        / GIT_CACHE_DIR_NAME
        / host
        / owner
        / repo
    )
    logger.debug(f"Cache path: {cache_path}")
    return cache_path


def get_cache_dir_from_url(clone_url: str) -> Path:
    """Compute cache directory from a clone URL using a hash fallback.

    This is a convenience wrapper when host/owner/repo are not
    separately available. It hashes the URL for a deterministic path.

    Args:
        clone_url: Full clone URL.

    Returns:
        Absolute path to the cache directory.
    """
    url_hash = hashlib.sha256(clone_url.encode()).hexdigest()[:16]
    cache_path = (
        get_global_aam_dir()
        / CACHE_DIR_NAME
        / GIT_CACHE_DIR_NAME
        / url_hash
    )
    return cache_path


################################################################################
#                                                                              #
# PUBLIC API                                                                   #
#                                                                              #
################################################################################


def check_git_available() -> bool:
    """Check if the ``git`` binary is available on PATH.

    Returns:
        ``True`` if git is available, ``False`` otherwise.
    """
    logger.debug("Checking git availability")

    try:
        result = _run_git(["--version"])
        if result.returncode == 0:
            version = result.stdout.strip()
            logger.info(f"Git is available: {version}")
            return True
    except FileNotFoundError:
        pass

    logger.warning("Git is not available on PATH")
    return False


def clone_shallow(
    clone_url: str,
    target_dir: Path,
    ref: str = "main",
    depth: int = 1,
) -> Path:
    """Clone a git repository with a shallow depth.

    Falls back to a full clone if the server does not support shallow
    clones (e.g., older git servers or certain configurations).

    Args:
        clone_url: Repository URL to clone.
        target_dir: Directory to clone into.
        ref: Branch, tag, or commit to check out.
        depth: Shallow clone depth (default: 1).

    Returns:
        Path to the cloned repository directory.

    Raises:
        GitCloneError: If the clone fails after all retries.
    """
    logger.info(
        f"Cloning repository: url='{clone_url}', "
        f"target='{target_dir}', ref='{ref}', depth={depth}"
    )

    # -----
    # Ensure parent directory exists
    # -----
    target_dir.mkdir(parents=True, exist_ok=True)

    # -----
    # Step 1: Try shallow clone first
    # -----
    try:
        _run_with_retry(
            ["clone", "--depth", str(depth), "--branch", ref, clone_url, str(target_dir)],
            error_class=GitCloneError,
            operation_name=f"shallow clone of {clone_url}",
        )
        logger.info(f"Shallow clone completed: target='{target_dir}'")
        return target_dir

    except GitCloneError as shallow_err:
        # -----
        # Step 2: Shallow clone failed — try full clone as fallback
        # Some servers don't support shallow clones
        # -----
        logger.warning(
            f"Shallow clone failed, falling back to full clone: {shallow_err}"
        )

        # Clean up any partial clone
        if target_dir.exists():
            shutil.rmtree(target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)

        _run_with_retry(
            ["clone", "--branch", ref, clone_url, str(target_dir)],
            error_class=GitCloneError,
            operation_name=f"full clone of {clone_url}",
        )
        logger.info(f"Full clone completed: target='{target_dir}'")
        return target_dir


def fetch(repo_dir: Path, ref: str = "main") -> None:
    """Fetch latest changes from the remote for a specific ref.

    Args:
        repo_dir: Path to the local repository.
        ref: Remote ref to fetch.

    Raises:
        GitFetchError: If the fetch fails after all retries.
    """
    logger.info(f"Fetching updates: repo='{repo_dir}', ref='{ref}'")

    _run_with_retry(
        ["fetch", "origin", ref],
        cwd=repo_dir,
        error_class=GitFetchError,
        operation_name=f"fetch of ref '{ref}'",
    )

    # -----
    # Reset working tree to match the fetched ref
    # -----
    reset_result = _run_git(
        ["reset", "--hard", f"origin/{ref}"],
        cwd=repo_dir,
    )
    if reset_result.returncode != 0:
        logger.warning(
            f"Reset to origin/{ref} failed, trying FETCH_HEAD: "
            f"{reset_result.stderr.strip()}"
        )
        _run_git(["reset", "--hard", "FETCH_HEAD"], cwd=repo_dir)

    logger.info(f"Fetch and reset complete: repo='{repo_dir}'")


def get_head_sha(repo_dir: Path) -> str:
    """Get the current HEAD commit SHA.

    Args:
        repo_dir: Path to the local repository.

    Returns:
        Full 40-character commit SHA string.

    Raises:
        GitError: If the command fails.
    """
    logger.debug(f"Getting HEAD SHA: repo='{repo_dir}'")

    result = _run_git(["rev-parse", "HEAD"], cwd=repo_dir)
    if result.returncode != 0:
        raise GitError(
            f"Failed to get HEAD SHA: {result.stderr.strip()}"
        )

    sha = result.stdout.strip()
    logger.debug(f"HEAD SHA: {sha}")
    return sha


def diff_file_names(
    repo_dir: Path,
    old_sha: str,
    new_sha: str,
) -> dict[str, list[str]]:
    """Get lists of changed files between two commits.

    Args:
        repo_dir: Path to the local repository.
        old_sha: Base commit SHA.
        new_sha: Target commit SHA.

    Returns:
        Dict with keys ``added``, ``modified``, ``deleted``,
        each mapping to a list of file paths.

    Raises:
        GitError: If the diff command fails.
    """
    logger.info(
        f"Diffing commits: repo='{repo_dir}', "
        f"old='{old_sha[:8]}', new='{new_sha[:8]}'"
    )

    result = _run_git(
        ["diff", "--name-status", old_sha, new_sha],
        cwd=repo_dir,
    )
    if result.returncode != 0:
        raise GitError(
            f"Failed to diff commits: {result.stderr.strip()}"
        )

    # -----
    # Parse git diff --name-status output
    # Format: STATUS\tFILENAME
    # -----
    added: list[str] = []
    modified: list[str] = []
    deleted: list[str] = []

    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t", maxsplit=1)
        if len(parts) != 2:
            continue

        status, filepath = parts
        status = status.strip()

        if status.startswith("A"):
            added.append(filepath)
        elif status.startswith("M") or status.startswith("R"):
            modified.append(filepath)
        elif status.startswith("D"):
            deleted.append(filepath)

    logger.info(
        f"Diff result: added={len(added)}, "
        f"modified={len(modified)}, deleted={len(deleted)}"
    )

    return {
        "added": added,
        "modified": modified,
        "deleted": deleted,
    }


def validate_cache(cache_dir: Path) -> bool:
    """Validate that a cached clone directory is not corrupted.

    Checks that the directory contains a valid git repository by
    running ``git status``. If the cache is corrupted, it is deleted
    to allow a fresh clone.

    Args:
        cache_dir: Path to the cached clone directory.

    Returns:
        ``True`` if the cache is valid, ``False`` if it was
        corrupted and removed.
    """
    logger.debug(f"Validating cache: path='{cache_dir}'")

    if not cache_dir.exists():
        logger.debug("Cache directory does not exist")
        return False

    # -----
    # Check if .git directory exists
    # -----
    git_dir = cache_dir / ".git"
    if not git_dir.is_dir():
        logger.warning(
            f"Cache corrupted (no .git directory): path='{cache_dir}'"
        )
        shutil.rmtree(cache_dir)
        return False

    # -----
    # Run git status to verify repository integrity
    # -----
    result = _run_git(["status", "--porcelain"], cwd=cache_dir)
    if result.returncode != 0:
        logger.warning(
            f"Cache corrupted (git status failed): path='{cache_dir}', "
            f"error='{result.stderr.strip()}'"
        )
        shutil.rmtree(cache_dir)
        return False

    logger.debug(f"Cache is valid: path='{cache_dir}'")
    return True
