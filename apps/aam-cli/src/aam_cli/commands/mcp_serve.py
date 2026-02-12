"""MCP serve command for AAM CLI.

Provides ``aam mcp serve`` to start the MCP (Model Context Protocol) server
for IDE agent integration.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import signal
import sys
from typing import Any

import click

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# COMMAND GROUP                                                                #
#                                                                              #
################################################################################


@click.group()
@click.pass_context
def mcp(ctx: click.Context) -> None:
    """MCP (Model Context Protocol) server for IDE agent integration."""
    pass


################################################################################
#                                                                              #
# LOGGING CONFIGURATION                                                        #
#                                                                              #
################################################################################


def _configure_logging(
    log_level: str,
    log_file: str | None,
    transport: str,
) -> None:
    """Configure logging for the MCP server.

    In stdio mode, stdout is reserved for JSON-RPC so all application
    logging must go to stderr or a log file. In HTTP mode, logging
    can go to stderr.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional path to a log file.
        transport: Transport type ("stdio" or "http").
    """
    handlers: list[logging.Handler] = []

    if log_file:
        # -----
        # Log to file if specified
        # -----
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)
    else:
        # -----
        # Default: log to stderr (never stdout in stdio mode)
        # -----
        stderr_handler = logging.StreamHandler(sys.stderr)
        handlers.append(stderr_handler)

    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[%(filename)s:%(lineno)d] - %(message)s"
    )

    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers,
        force=True,
    )

    logger.info(
        f"Logging configured: level={log_level}, "
        f"log_file={log_file}, transport={transport}"
    )


################################################################################
#                                                                              #
# SERVE COMMAND                                                                #
#                                                                              #
################################################################################


@mcp.command("serve")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"], case_sensitive=False),
    default="stdio",
    show_default=True,
    help="Transport protocol for MCP communication.",
)
@click.option(
    "--port",
    type=click.IntRange(1, 65535),
    default=8000,
    show_default=True,
    help="HTTP port (only used with --transport http).",
)
@click.option(
    "--allow-write",
    is_flag=True,
    default=False,
    show_default=True,
    help="Enable write (mutating) tools. Read-only by default.",
)
@click.option(
    "--log-file",
    type=click.Path(),
    default=None,
    help="Path to log file. Defaults to stderr.",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    show_default=True,
    help="Logging level.",
)
@click.pass_context
def serve(
    ctx: click.Context,  # noqa: ARG001
    transport: str,
    port: int,
    allow_write: bool,
    log_file: str | None,
    log_level: str,
) -> None:
    """Start the AAM MCP server.

    Exposes AAM CLI capabilities as MCP tools and resources for IDE agents
    (Cursor, VS Code, Claude Desktop, Windsurf).

    In stdio mode (default), stdout is reserved for JSON-RPC. All application
    logging goes to stderr or the specified --log-file.

    By default only read-only tools are exposed. Use --allow-write to enable
    package install, uninstall, publish, config set, and registry add tools.

    Examples::

        # Start with stdio transport (default, for IDE integration)
        aam mcp serve

        # Start with HTTP transport on a custom port
        aam mcp serve --transport http --port 9000

        # Enable write tools for full access
        aam mcp serve --allow-write

        # Log to a file at DEBUG level
        aam mcp serve --log-file /tmp/aam-mcp.log --log-level DEBUG
    """
    # -----
    # Step 1: Configure logging
    # -----
    _configure_logging(log_level, log_file, transport)

    logger.info(
        f"Starting MCP server: transport={transport}, port={port}, "
        f"allow_write={allow_write}"
    )

    # -----
    # Step 2: Create the server
    # -----
    from aam_cli.mcp.server import create_mcp_server

    server = create_mcp_server(allow_write=allow_write)

    # -----
    # Step 3: Set up graceful shutdown
    # -----
    def _handle_shutdown(signum: int, frame: Any) -> None:  # noqa: ARG001
        """Handle SIGINT/SIGTERM for graceful shutdown."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, shutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    # -----
    # Step 4: Run the server
    # -----
    if transport == "stdio":
        logger.info("Running MCP server with stdio transport")
        server.run(transport="stdio")
    else:
        logger.info(f"Running MCP server with HTTP transport on port {port}")
        server.run(transport="sse", host="0.0.0.0", port=port)
