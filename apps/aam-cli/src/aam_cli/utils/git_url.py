"""Git source URL parsing and decomposition.

Parses various git repository URL formats into a normalized
``GitSourceURL`` dataclass with components needed for cloning,
scanning, and display naming.

Supported formats:
  - HTTPS:       ``https://github.com/{owner}/{repo}``
  - Tree URL:    ``https://github.com/{owner}/{repo}/tree/{ref}/{path}``
  - SSH:         ``git@github.com:{owner}/{repo}.git``
  - git+https:   ``git+https://github.com/{owner}/{repo}.git``
  - Shorthand:   ``{owner}/{repo}[@ref][#sha]``

Reference: ``docs/work/git_repo_skills.md`` Section 4.1.1
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import re
from dataclasses import dataclass

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

# Owner/repo name character validation pattern
_NAME_CHARS = re.compile(r"^[a-zA-Z0-9._-]+$")

# Allowed clone URL schemes
ALLOWED_SCHEMES: set[str] = {"https://", "git@", "git+https://"}

# Default git reference when none is specified
DEFAULT_REF: str = "main"

# -----
# Regex patterns for each supported format
# -----

# HTTPS URL with optional /tree/{ref}/{path} suffix
# Matches: https://github.com/owner/repo[/tree/ref[/path]]
_HTTPS_PATTERN = re.compile(
    r"^https?://(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<repo>[^/]+?)"
    r"(?:\.git)?"
    r"(?:/tree/(?P<ref>[^/]+)(?:/(?P<path>.+))?)?"
    r"$"
)

# SSH URL: git@host:owner/repo.git
_SSH_PATTERN = re.compile(
    r"^git@(?P<host>[^:]+):(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$"
)

# git+https:// URL: git+https://host/owner/repo.git
_GIT_HTTPS_PATTERN = re.compile(
    r"^git\+https://(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$"
)

# Shorthand: owner/repo[@ref][#sha]
# Must not start with http, git@, or git+ to avoid matching other formats
_SHORTHAND_PATTERN = re.compile(
    r"^(?P<owner>[a-zA-Z0-9._-]+)/(?P<repo>[a-zA-Z0-9._-]+)"
    r"(?:@(?P<ref>[a-zA-Z0-9._/-]+))?"
    r"(?:#(?P<sha>[a-fA-F0-9]+))?"
    r"$"
)

# Default host for shorthand format
DEFAULT_HOST: str = "github.com"

################################################################################
#                                                                              #
# DATA MODEL                                                                   #
#                                                                              #
################################################################################


@dataclass(frozen=True)
class GitSourceURL:
    """Parsed components of a git source URL.

    All supported URL formats are normalized into this structure.
    The ``clone_url`` is always a full URL suitable for ``git clone``.

    Attributes:
        host: Repository host (e.g., ``github.com``).
        owner: Repository owner or organization.
        repo: Repository name (without ``.git`` suffix).
        ref: Git reference — branch, tag, or commit SHA.
        path: Subdirectory scan scope (empty for full repo).
        clone_url: Full clone URL (HTTPS or SSH).
        display_name: Human-readable name for UI display.
        source_format: Format of the original input URL.
    """

    host: str
    owner: str
    repo: str
    ref: str
    path: str
    clone_url: str
    display_name: str
    source_format: str  # "https", "ssh", "shorthand", "tree_url", "git_https"


################################################################################
#                                                                              #
# DISPLAY NAME GENERATION                                                      #
#                                                                              #
################################################################################


def _generate_display_name(
    owner: str,
    repo: str,
    path: str,
    name_override: str | None,
) -> str:
    """Generate a display name from URL components.

    Naming convention:
      - No path:  ``{owner}/{repo}``
      - With path: ``{owner}/{repo}:{path_suffix}``
      - Override:  uses ``name_override`` directly

    Args:
        owner: Repository owner.
        repo: Repository name.
        path: Subdirectory path (may be empty).
        name_override: User-specified custom name, if any.

    Returns:
        Display name string.
    """
    if name_override:
        return name_override

    base = f"{owner}/{repo}"
    if not path:
        return base

    # -----
    # Use the last component of the path as the suffix
    # e.g., "skills/.curated" -> ".curated"
    # -----
    suffix = path.rstrip("/").rsplit("/", maxsplit=1)[-1]
    return f"{base}:{suffix}"


################################################################################
#                                                                              #
# URL SCHEME VALIDATION                                                        #
#                                                                              #
################################################################################


def _validate_clone_url(clone_url: str) -> None:
    """Validate that a clone URL uses an allowed scheme.

    Args:
        clone_url: The clone URL to validate.

    Raises:
        ValueError: If the URL scheme is not in ``ALLOWED_SCHEMES``.
    """
    for scheme in ALLOWED_SCHEMES:
        if clone_url.startswith(scheme):
            return

    raise ValueError(
        f"Unsupported URL scheme in '{clone_url}'. "
        f"Allowed schemes: {', '.join(sorted(ALLOWED_SCHEMES))}"
    )


def _validate_name_chars(value: str, field: str) -> None:
    """Validate that a name contains only allowed characters.

    Args:
        value: String to validate.
        field: Field name for error messages.

    Raises:
        ValueError: If value contains invalid characters.
    """
    if not value:
        raise ValueError(f"{field} must not be empty")
    if not _NAME_CHARS.match(value):
        raise ValueError(
            f"Invalid {field} '{value}': must match [a-zA-Z0-9._-]+"
        )


################################################################################
#                                                                              #
# FORMAT-SPECIFIC PARSERS                                                      #
#                                                                              #
################################################################################


def _parse_https(
    source: str,
    ref_override: str | None,
    path_override: str | None,
    name_override: str | None,
) -> GitSourceURL | None:
    """Try to parse an HTTPS URL (including tree URLs).

    Args:
        source: Raw source string.
        ref_override: Explicit ref from CLI flag.
        path_override: Explicit path from CLI flag.
        name_override: Custom name override.

    Returns:
        Parsed ``GitSourceURL`` or ``None`` if not an HTTPS URL.
    """
    match = _HTTPS_PATTERN.match(source)
    if not match:
        return None

    host = match.group("host")
    owner = match.group("owner")
    repo = match.group("repo")
    url_ref = match.group("ref")
    url_path = match.group("path")

    # -----
    # Determine format: tree_url if /tree/ was present, else https
    # -----
    source_format = "tree_url" if url_ref else "https"

    # CLI overrides take precedence over URL-embedded values
    ref = ref_override or url_ref or DEFAULT_REF
    path = path_override if path_override is not None else (url_path or "")

    clone_url = f"https://{host}/{owner}/{repo}"

    _validate_name_chars(owner, "owner")
    _validate_name_chars(repo, "repo")

    display_name = _generate_display_name(owner, repo, path, name_override)

    return GitSourceURL(
        host=host,
        owner=owner,
        repo=repo,
        ref=ref,
        path=path,
        clone_url=clone_url,
        display_name=display_name,
        source_format=source_format,
    )


def _parse_ssh(
    source: str,
    ref_override: str | None,
    path_override: str | None,
    name_override: str | None,
) -> GitSourceURL | None:
    """Try to parse an SSH URL (``git@host:owner/repo.git``).

    Args:
        source: Raw source string.
        ref_override: Explicit ref from CLI flag.
        path_override: Explicit path from CLI flag.
        name_override: Custom name override.

    Returns:
        Parsed ``GitSourceURL`` or ``None`` if not an SSH URL.
    """
    match = _SSH_PATTERN.match(source)
    if not match:
        return None

    host = match.group("host")
    owner = match.group("owner")
    repo = match.group("repo")

    ref = ref_override or DEFAULT_REF
    path = path_override or ""

    clone_url = f"git@{host}:{owner}/{repo}.git"

    _validate_name_chars(owner, "owner")
    _validate_name_chars(repo, "repo")

    display_name = _generate_display_name(owner, repo, path, name_override)

    return GitSourceURL(
        host=host,
        owner=owner,
        repo=repo,
        ref=ref,
        path=path,
        clone_url=clone_url,
        display_name=display_name,
        source_format="ssh",
    )


def _parse_git_https(
    source: str,
    ref_override: str | None,
    path_override: str | None,
    name_override: str | None,
) -> GitSourceURL | None:
    """Try to parse a ``git+https://`` URL.

    Args:
        source: Raw source string.
        ref_override: Explicit ref from CLI flag.
        path_override: Explicit path from CLI flag.
        name_override: Custom name override.

    Returns:
        Parsed ``GitSourceURL`` or ``None`` if not a git+https URL.
    """
    match = _GIT_HTTPS_PATTERN.match(source)
    if not match:
        return None

    host = match.group("host")
    owner = match.group("owner")
    repo = match.group("repo")

    ref = ref_override or DEFAULT_REF
    path = path_override or ""

    clone_url = f"git+https://{host}/{owner}/{repo}.git"

    _validate_name_chars(owner, "owner")
    _validate_name_chars(repo, "repo")

    display_name = _generate_display_name(owner, repo, path, name_override)

    return GitSourceURL(
        host=host,
        owner=owner,
        repo=repo,
        ref=ref,
        path=path,
        clone_url=clone_url,
        display_name=display_name,
        source_format="git_https",
    )


def _parse_shorthand(
    source: str,
    ref_override: str | None,
    path_override: str | None,
    name_override: str | None,
) -> GitSourceURL | None:
    """Try to parse a shorthand reference (``owner/repo[@ref][#sha]``).

    Shorthand is assumed to refer to GitHub unless another host is
    configured.

    Args:
        source: Raw source string.
        ref_override: Explicit ref from CLI flag.
        path_override: Explicit path from CLI flag.
        name_override: Custom name override.

    Returns:
        Parsed ``GitSourceURL`` or ``None`` if not a shorthand format.
    """
    # -----
    # Guard: reject strings that look like full URLs
    # -----
    if source.startswith(("http://", "https://", "git@", "git+")):
        return None

    match = _SHORTHAND_PATTERN.match(source)
    if not match:
        return None

    owner = match.group("owner")
    repo = match.group("repo")
    shorthand_ref = match.group("ref")
    shorthand_sha = match.group("sha")

    # -----
    # Precedence: CLI flag > #sha > @ref > default
    # -----
    if ref_override:
        ref = ref_override
    elif shorthand_sha:
        ref = shorthand_sha
    elif shorthand_ref:
        ref = shorthand_ref
    else:
        ref = DEFAULT_REF

    path = path_override or ""
    host = DEFAULT_HOST
    clone_url = f"https://{host}/{owner}/{repo}"

    _validate_name_chars(owner, "owner")
    _validate_name_chars(repo, "repo")

    display_name = _generate_display_name(owner, repo, path, name_override)

    return GitSourceURL(
        host=host,
        owner=owner,
        repo=repo,
        ref=ref,
        path=path,
        clone_url=clone_url,
        display_name=display_name,
        source_format="shorthand",
    )


################################################################################
#                                                                              #
# PUBLIC API                                                                   #
#                                                                              #
################################################################################


def parse(
    source: str,
    ref: str | None = None,
    path: str | None = None,
    name: str | None = None,
) -> GitSourceURL:
    """Parse a git source string into a ``GitSourceURL``.

    Tries each supported format in order:
      1. SSH (``git@``)
      2. git+https (``git+https://``)
      3. HTTPS / tree URL (``https://``)
      4. Shorthand (``owner/repo``)

    Args:
        source: Git source string in any supported format.
        ref: Optional ref override (branch, tag, commit SHA).
        path: Optional subdirectory path override.
        name: Optional custom display name.

    Returns:
        Parsed :class:`GitSourceURL` instance.

    Raises:
        ValueError: If the source string cannot be parsed or
            contains invalid characters.
    """
    logger.info(f"Parsing git source URL: source='{source}'")

    source = source.strip()
    if not source:
        raise ValueError("Source URL must not be empty")

    # -----
    # Try each format parser in order of specificity
    # -----
    parsers = [
        _parse_ssh,
        _parse_git_https,
        _parse_https,
        _parse_shorthand,
    ]

    for parser_fn in parsers:
        result = parser_fn(source, ref, path, name)
        if result is not None:
            _validate_clone_url(result.clone_url)
            logger.info(
                f"URL parsed: format='{result.source_format}', "
                f"host='{result.host}', owner='{result.owner}', "
                f"repo='{result.repo}', ref='{result.ref}', "
                f"path='{result.path}', display_name='{result.display_name}'"
            )
            return result

    raise ValueError(
        f"Cannot parse git source '{source}'. "
        "Supported formats: HTTPS URL, SSH (git@...), "
        "git+https://, shorthand (owner/repo)"
    )
