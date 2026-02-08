"""SHA-256 checksum utilities for package integrity verification.

Provides helpers to calculate and verify SHA-256 checksums on ``.aam``
archive files.  Checksums are stored in the ``sha256:<hex>`` format used
throughout the registry metadata and lock files.

Decision reference: R-002 in research.md.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import hashlib
import logging
from pathlib import Path

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

# Buffer size for streaming hash computation (64 KB)
_HASH_BUFFER_SIZE: int = 65536

# Prefix used in checksum strings
CHECKSUM_PREFIX: str = "sha256:"

################################################################################
#                                                                              #
# FUNCTIONS                                                                    #
#                                                                              #
################################################################################


def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 hash of a file.

    Reads the file in chunks to support large archives without loading
    the entire file into memory.

    Args:
        file_path: Path to the file to hash.

    Returns:
        The SHA-256 hex digest prefixed with ``sha256:``, e.g.
        ``"sha256:a1b2c3d4e5f6..."``.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """
    logger.debug(f"Calculating SHA-256 checksum: path='{file_path}'")

    sha256 = hashlib.sha256()

    with file_path.open("rb") as fh:
        while True:
            chunk = fh.read(_HASH_BUFFER_SIZE)
            if not chunk:
                break
            sha256.update(chunk)

    digest = f"{CHECKSUM_PREFIX}{sha256.hexdigest()}"
    logger.debug(f"SHA-256 computed: path='{file_path}', checksum='{digest[:30]}...'")
    return digest


def verify_sha256(file_path: Path, expected: str) -> bool:
    """Verify a file's SHA-256 checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected: Expected checksum in ``sha256:<hex>`` format.

    Returns:
        ``True`` if the computed checksum matches *expected*, ``False``
        otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    logger.debug(f"Verifying SHA-256 checksum: path='{file_path}', expected='{expected[:30]}...'")

    actual = calculate_sha256(file_path)
    matches = actual == expected

    if matches:
        logger.debug(f"Checksum verification passed: path='{file_path}'")
    else:
        logger.warning(
            f"Checksum verification FAILED: path='{file_path}', "
            f"expected='{expected[:30]}...', actual='{actual[:30]}...'"
        )

    return matches
