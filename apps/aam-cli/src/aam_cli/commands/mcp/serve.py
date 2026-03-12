"""Start the AAM MCP server."""

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

logger = logging.getLogger(__name__)

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
    """Configure logging for the MCP server."""
    handlers: list[logging.Handler] = []

    if log_file:
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)
    else:
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
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command("serve")
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
    """Start the AAM MCP server."""
    _configure_logging(log_level, log_file, transport)

    logger.info(
        f"Starting MCP server: transport={transport}, port={port}, "
        f"allow_write={allow_write}"
    )

    from aam_cli.mcp.server import create_mcp_server

    server = create_mcp_server(allow_write=allow_write)

    def _handle_shutdown(signum: int, frame: Any) -> None:  # noqa: ARG001
        """Handle SIGINT/SIGTERM for graceful shutdown."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, shutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    if transport == "stdio":
        logger.info("Running MCP server with stdio transport")
        server.run(transport="stdio")
    else:
        logger.info(f"Running MCP server with HTTP transport on port {port}")
        server.run(transport="sse", host="0.0.0.0", port=port)
