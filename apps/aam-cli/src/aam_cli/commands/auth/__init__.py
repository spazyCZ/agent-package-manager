"""Authentication helpers and top-level auth commands for AAM CLI."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
from pathlib import Path

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

AUTH_FILE: Path = Path.home() / ".aam" / "auth.json"

################################################################################
#                                                                              #
# AUTH HELPERS                                                                 #
#                                                                              #
################################################################################


def _load_auth() -> dict[str, str]:
    """Load auth tokens from ``~/.aam/auth.json``."""
    if AUTH_FILE.is_file():
        return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    return {}


def _save_auth(auth_data: dict[str, str]) -> None:
    """Save auth tokens to ``~/.aam/auth.json``."""
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(json.dumps(auth_data, indent=2), encoding="utf-8")
    AUTH_FILE.chmod(0o600)
    logger.info(f"Auth data saved to {AUTH_FILE}")


def get_token(registry_url: str) -> str | None:
    """Get the auth token for a registry URL."""
    auth = _load_auth()
    return auth.get(registry_url.rstrip("/"))


################################################################################
#                                                                              #
# RE-EXPORTS                                                                   #
#                                                                              #
################################################################################

from aam_cli.commands.auth.login import login  # noqa: E402
from aam_cli.commands.auth.logout import logout  # noqa: E402
from aam_cli.commands.auth.whoami import whoami  # noqa: E402
