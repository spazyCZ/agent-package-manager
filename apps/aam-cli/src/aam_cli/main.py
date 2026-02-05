"""Main entry point for AAM CLI."""

import click
from rich.console import Console

from aam_cli import __version__
from aam_cli.commands import install, search, publish, config, registry

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="aam")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """AAM - Agent Package Manager.
    
    A package manager for AI agents, skills, and tools.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["console"] = console


# Register command groups
cli.add_command(install.install)
cli.add_command(search.search)
cli.add_command(publish.publish)
cli.add_command(config.config)
cli.add_command(registry.registry)


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Display AAM information and configuration."""
    console = ctx.obj["console"]
    console.print(f"[bold blue]AAM CLI[/bold blue] v{__version__}")
    console.print("\n[bold]Configuration:[/bold]")
    console.print("  Registry: https://registry.aam.dev")
    console.print("  Cache: ~/.aam/cache")


@cli.command()
@click.argument("package_name")
@click.option("--version", "-V", help="Specific version to show")
@click.pass_context
def show(ctx: click.Context, package_name: str, version: str | None) -> None:
    """Show detailed information about a package."""
    console = ctx.obj["console"]
    console.print(f"[bold]Package:[/bold] {package_name}")
    if version:
        console.print(f"[bold]Version:[/bold] {version}")
    console.print("\n[dim]Fetching package details...[/dim]")


@cli.command()
@click.pass_context
def list(ctx: click.Context) -> None:
    """List installed packages."""
    console = ctx.obj["console"]
    console.print("[bold]Installed Packages:[/bold]")
    console.print("[dim]No packages installed yet.[/dim]")


if __name__ == "__main__":
    cli()
