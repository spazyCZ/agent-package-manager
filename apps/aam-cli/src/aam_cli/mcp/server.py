"""FastMCP server factory for AAM.

Creates and configures the MCP server instance with tools, resources,
and the read-only-by-default safety model.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

from fastmcp import FastMCP

from aam_cli import __version__
from aam_cli.mcp.resources import register_resources
from aam_cli.mcp.tools_read import register_read_tools
from aam_cli.mcp.tools_write import register_write_tools

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# SERVER INSTRUCTIONS                                                          #
#                                                                              #
################################################################################

SERVER_INSTRUCTIONS = """AAM (Agent Artifact Manager) MCP Server.

This server exposes AAM CLI capabilities for managing AI agent packages
(skills, agents, prompts, and instructions). Use the available tools to
search registries, inspect installed packages, validate manifests, install
new packages, manage configuration, and discover artifacts from remote
git sources.

Read-only tools are always available. These include package operations
(search, list, info, validate), configuration (config get, doctor),
source discovery (source list, source scan, source candidates, source diff),
integrity (verify, diff), and skill recommendation (aam_recommend_skills).

Write tools (install, uninstall, publish, config set, registry add,
source add, source remove, source update) are only available when the
server is started with --allow-write.

Resources provide passive data access for project context without
requiring tool calls.

## Skill recommendation (aam_recommend_skills)

When the user asks to find relevant skills for their repository, or which
skills to use for a project (e.g., "what skills fit my React + Python LLM
app?"), call aam_recommend_skills first. It analyzes the project structure
and dependencies to recommend skills from configured sources.

Optimal usage:
1. Use default path (current directory) when the user is in the project root.
2. Pass an explicit path if the user points to a specific project.
3. Present the top recommendations with score and rationale.
4. Suggest installing with: aam install <qualified_name>
5. If sources are empty, suggest: aam source enable-defaults; aam source update --all
6. Combine with aam_install (write) if --allow-write to install recommended skills.
"""

################################################################################
#                                                                              #
# SERVER FACTORY                                                               #
#                                                                              #
################################################################################


def create_mcp_server(allow_write: bool = False) -> FastMCP:
    """Create and configure the AAM MCP server instance.

    Registers all tools and resources. When ``allow_write`` is False
    (default), tools tagged with "write" are excluded from the server,
    enforcing the read-only-by-default safety model.

    Args:
        allow_write: If True, include write (mutating) tools.
            If False, only read-only tools are exposed.

    Returns:
        Configured FastMCP server instance.
    """
    logger.info(
        f"Creating MCP server: allow_write={allow_write}, version={__version__}"
    )

    # -----
    # Build exclusion set for safety model
    # -----
    exclude_tags: set[str] | None = None
    if not allow_write:
        exclude_tags = {"write"}

    # -----
    # Create the FastMCP server
    # -----
    mcp = FastMCP(
        name="aam",
        instructions=SERVER_INSTRUCTIONS,
        version=__version__,
        exclude_tags=exclude_tags,
    )

    # -----
    # Register tools and resources
    # -----
    register_read_tools(mcp)
    register_write_tools(mcp)
    register_resources(mcp)

    # Read-only: 17 (includes aam_recommend_skills)
    # Full access: 17 read + 12 write = 29
    tool_count = 17 if not allow_write else 29
    logger.info(
        f"MCP server created: tools={tool_count}, resources=8, "
        f"allow_write={allow_write}"
    )

    return mcp


################################################################################
#                                                                              #
# DEFAULT INSTANCE                                                             #
#                                                                              #
################################################################################

# Default server instance for `fastmcp run` compatibility.
# This is read-only by default. Use create_mcp_server(allow_write=True)
# for full access.
mcp = create_mcp_server(allow_write=False)
