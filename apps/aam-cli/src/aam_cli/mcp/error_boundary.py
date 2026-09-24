"""Shared error-handling decorator for MCP tools.

Catches known exception types raised by AAM services and converts
them into structured ``{"error": ..., "error_code": ...}`` dicts
so that LLM clients receive parseable error responses instead of
raw Python tracebacks.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import functools
import logging
from typing import Any, Callable

from aam_cli.services.governance_service import PolicyViolationError

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# ERROR CODE EXTRACTION                                                        #
#                                                                              #
################################################################################


def _extract_error_code(exc: Exception) -> str:
    """Extract a structured error code from an exception.

    AAM services embed error codes in square brackets at the start of
    the message, e.g. ``[AAM_SOURCE_NOT_FOUND] Source 'foo' not found``.
    This helper extracts the bracketed code if present.

    Args:
        exc: The exception to inspect.

    Returns:
        The extracted error code, or a fallback based on exception type.
    """
    # -----
    # Check for a ``code`` attribute first (PolicyViolationError, etc.)
    # -----
    code = getattr(exc, "code", None)
    if code:
        return str(code)

    # -----
    # Check for bracketed code in the message: [AAM_SOME_CODE] ...
    # -----
    msg = str(exc)
    if msg.startswith("[") and "]" in msg:
        return msg[1:msg.index("]")]

    # -----
    # Fallback to exception class name
    # -----
    return type(exc).__name__


################################################################################
#                                                                              #
# DECORATOR                                                                    #
#                                                                              #
################################################################################


def mcp_error_boundary(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that wraps an MCP tool function with error handling.

    Catches ``ValueError``, ``FileNotFoundError``, ``RuntimeError``,
    ``PermissionError``, ``OSError``, and the AAM-specific
    ``PolicyViolationError`` and returns structured error dicts.
    Unexpected exceptions are logged and re-raised so FastMCP can
    surface them as internal errors.

    Args:
        func: The MCP tool function to wrap.

    Returns:
        Wrapped function with error boundary.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except PolicyViolationError as exc:
            logger.warning(
                "MCP tool %s returned PolicyViolationError: %s",
                func.__name__, exc,
            )
            return {
                "error": exc.violation.message,
                "error_code": f"AAM_POLICY_VIOLATION_{exc.violation.rule.upper()}",
            }
        except ValueError as exc:
            logger.warning(
                "MCP tool %s returned ValueError: %s",
                func.__name__, exc,
            )
            return {
                "error": str(exc),
                "error_code": _extract_error_code(exc),
            }
        except FileNotFoundError as exc:
            logger.warning(
                "MCP tool %s returned FileNotFoundError: %s",
                func.__name__, exc,
            )
            return {
                "error": str(exc),
                "error_code": "FILE_NOT_FOUND",
            }
        except PermissionError as exc:
            logger.warning(
                "MCP tool %s returned PermissionError: %s",
                func.__name__, exc,
            )
            return {
                "error": str(exc),
                "error_code": "PERMISSION_DENIED",
            }
        except RuntimeError as exc:
            logger.error(
                "MCP tool %s returned RuntimeError: %s",
                func.__name__, exc,
            )
            return {
                "error": str(exc),
                "error_code": _extract_error_code(exc),
            }
        except OSError as exc:
            logger.error(
                "MCP tool %s returned OSError: %s",
                func.__name__, exc,
            )
            return {
                "error": str(exc),
                "error_code": "OS_ERROR",
            }

    return wrapper
