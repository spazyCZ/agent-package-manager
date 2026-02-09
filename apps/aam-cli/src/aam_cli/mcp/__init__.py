"""AAM MCP Server module.

Exposes AAM CLI capabilities as an MCP (Model Context Protocol) server
for IDE agent integration.
"""

from aam_cli.mcp.server import create_mcp_server, mcp

__all__ = ["create_mcp_server", "mcp"]
