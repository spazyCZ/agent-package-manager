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

Manages AI agent artifacts: skills, agents, commands, and instructions.
Read-only tools are always available. Write tools require --allow-write.

## Tools by category

### Read-only (always available)

**Package Discovery:** search, list, available, info, recommend_skills
**Dependency Analysis:** tree, why, check, audit, dedupe, prune
**Package Integrity:** validate, verify, diff, outdated
**Source Management:** source_list, source_scan, source_candidates, source_diff
**Configuration & Diagnostics:** config_get, registry_list, doctor, init_info
**Cache:** cache_ls

### Write (require --allow-write)

**Package Management:** install, uninstall, upgrade, publish
**Package Authoring:** create_package, init_package, pack, convert
**Source Management:** source_add, source_remove, source_update
**Configuration:** config_set, registry_add, init
**Testing:** test, eval
**Cache:** cache_clean

## Resources

- `aam://config` — global AAM configuration
- `aam://packages/installed` — all installed packages
- `aam://packages/{name}` — single package detail (use `--` for scoped names)
- `aam://registries` — configured registries
- `aam://manifest` — current project manifest (package.agent.json, falling back to package.agent.yaml, then aam.yaml)
- `aam://sources` — all configured git sources
- `aam://sources/{source_id}` — single source detail
- `aam://sources/{source_id}/candidates` — discoverable packages in a source
- `aam://init_status` — workspace initialization status

## Error format

Tool errors return a dict with:
- `error`: human-readable message
- `error_code`: machine-readable code (e.g., AAM_SOURCE_NOT_FOUND, FILE_NOT_FOUND)

## Workflow recipes

**Discover and install:** search -> info -> install -> verify
**Update packages:** outdated -> upgrade -> check
**Explore sources:** source_list -> source_scan -> source_candidates -> source_add

## Skill recommendation (recommend_skills)

When the user asks which skills fit their project, call recommend_skills.
It analyzes project structure and dependencies to rank skills from configured sources.

- Use default path (current directory) when in the project root.
- Pass an explicit path for a specific project.
- Present top recommendations with score and rationale.
- Suggest installing with: `aam install <qualified_name>`
- If sources are empty, suggest: `aam source update --all`
- Combine with install (write) to install recommended skills directly.
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

    logger.info(
        f"MCP server created: allow_write={allow_write}, "
        f"version={__version__}"
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
