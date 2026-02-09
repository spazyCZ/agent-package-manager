# Quickstart: MCP Server for AAM CLI

**Branch**: `002-mcp-server-cli` | **Date**: 2026-02-08

## Prerequisites

- Python 3.11+
- AAM CLI installed (`pip install -e '.[dev]'` from `apps/aam-cli/`)
- An IDE with MCP support (Cursor, VS Code, Claude Desktop)

## 1. Install Dependencies

```bash
cd apps/aam-cli
pip install -e '.[dev]'
```

This installs FastMCP along with other dependencies.

## 2. Start the MCP Server (Manual Testing)

### stdio mode (default — for IDE integration)

```bash
aam mcp serve
```

The server starts listening on stdin/stdout for JSON-RPC messages. In this mode, you typically don't run it manually — the IDE spawns it.

### HTTP mode (for development/testing)

```bash
aam mcp serve --transport http --port 8000
```

The server starts at `http://localhost:8000/mcp`. You can test with the FastMCP client or any MCP-compatible tool.

### With write access

```bash
aam mcp serve --allow-write
```

Enables mutating tools (install, uninstall, publish, etc.).

### With logging

```bash
aam mcp serve --log-file /tmp/aam-mcp.log --log-level DEBUG
```

## 3. Configure IDE Integration

### Cursor

Create or update `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "aam": {
      "command": "aam",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

For full access (read + write):

```json
{
  "mcpServers": {
    "aam": {
      "command": "aam",
      "args": ["mcp", "serve", "--allow-write"],
      "env": {}
    }
  }
}
```

### VS Code

Add to `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "aam": {
      "command": "aam",
      "args": ["mcp", "serve"]
    }
  }
}
```

### Claude Desktop

Add to Claude Desktop's MCP config:

```json
{
  "mcpServers": {
    "aam": {
      "command": "aam",
      "args": ["mcp", "serve", "--allow-write"]
    }
  }
}
```

## 4. Test with FastMCP Client (Development)

```python
import asyncio
from fastmcp import Client

async def test_mcp():
    async with Client("http://localhost:8000/mcp") as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {len(tools)}")

        # Search for packages
        result = await client.call_tool("aam_search", {"query": "cursor"})
        print(f"Search results: {result}")

        # List installed packages
        result = await client.call_tool("aam_list", {})
        print(f"Installed: {result}")

        # Read a resource
        config = await client.read_resource("aam://config")
        print(f"Config: {config}")

asyncio.run(test_mcp())
```

## 5. Run Tests

```bash
cd apps/aam-cli

# Unit tests only
pytest tests/unit/test_mcp_*.py -v

# Integration tests
pytest tests/integration/test_mcp_integration.py -v

# All tests with coverage
pytest tests/ -v --cov=src/aam_cli --cov-report=term-missing
```

## 6. Development Workflow

1. **Make changes** to `src/aam_cli/mcp/` or `src/aam_cli/services/`
2. **Run unit tests** to verify tool registration and service logic
3. **Start HTTP server** for manual testing: `aam mcp serve --transport http`
4. **Test with FastMCP Client** or MCP Inspector
5. **Configure IDE** to test stdio integration
6. **Run full test suite** before committing

## Available Tools (Read-Only)

| Tool | Description |
|------|-------------|
| `aam_search` | Search registries for packages |
| `aam_list` | List installed packages |
| `aam_info` | Show package details |
| `aam_validate` | Validate package manifest |
| `aam_config_get` | Get configuration values |
| `aam_registry_list` | List configured registries |
| `aam_doctor` | Diagnose environment issues |

## Available Tools (Write — requires `--allow-write`)

| Tool | Description |
|------|-------------|
| `aam_install` | Install packages |
| `aam_uninstall` | Remove packages |
| `aam_publish` | Publish to registry |
| `aam_create_package` | Create package from project |
| `aam_config_set` | Set configuration values |
| `aam_registry_add` | Add a registry source |

## Available Resources

| URI | Description |
|-----|-------------|
| `aam://config` | Current AAM configuration |
| `aam://packages/installed` | Installed packages list |
| `aam://packages/{name}` | Specific package details |
| `aam://registries` | Configured registries |
| `aam://manifest` | Current project's aam.yaml |
