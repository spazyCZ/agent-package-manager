"""Registry factory — instantiate registries from configuration.

Provides a single entry point for creating registry instances from
``RegistrySource`` config objects.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

from aam_cli.core.config import RegistrySource
from aam_cli.registry.base import Registry
from aam_cli.registry.local import LocalRegistry
from aam_cli.utils.paths import parse_file_url

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# FACTORY FUNCTION                                                             #
#                                                                              #
################################################################################


def create_registry(source: RegistrySource) -> Registry:
    """Create a registry instance from a configuration source.

    Args:
        source: Registry source configuration.

    Returns:
        A :class:`Registry` implementation instance.

    Raises:
        ValueError: If the registry type is not supported.
    """
    logger.debug(
        f"Creating registry: name='{source.name}', type='{source.type}', url='{source.url}'"
    )

    if source.type == "local":
        local_path = parse_file_url(source.url)
        return LocalRegistry(name=source.name, root=local_path)

    # -----
    # Unsupported types raise immediately — no fallbacks
    # -----
    raise ValueError(
        f"Unsupported registry type '{source.type}'. "
        "Only 'local' registries are supported in this version."
    )
