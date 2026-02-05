"""Registry command for AAM CLI."""

import click
from rich.console import Console
from rich.table import Table


@click.group()
@click.pass_context
def registry(ctx: click.Context) -> None:
    """Manage registry connections."""
    pass


@registry.command("list")
@click.pass_context
def registry_list(ctx: click.Context) -> None:
    """List configured registries."""
    console: Console = ctx.obj["console"]
    
    table = Table(title="Configured Registries")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Default", style="yellow")
    
    # TODO: Read actual registries
    table.add_row("default", "https://registry.aam.dev", "✓")
    
    console.print(table)


@registry.command("add")
@click.argument("name")
@click.argument("url")
@click.option("--default", is_flag=True, help="Set as default registry")
@click.pass_context
def registry_add(ctx: click.Context, name: str, url: str, default: bool) -> None:
    """Add a new registry.
    
    Examples:
        aam registry add mycompany https://registry.mycompany.com
        aam registry add private https://private.example.com --default
    """
    console: Console = ctx.obj["console"]
    
    # TODO: Actually add registry
    console.print(f"[green]✓[/green] Added registry '{name}' ({url})")
    if default:
        console.print(f"[green]✓[/green] Set '{name}' as default registry")


@registry.command("remove")
@click.argument("name")
@click.pass_context
def registry_remove(ctx: click.Context, name: str) -> None:
    """Remove a registry.
    
    Examples:
        aam registry remove mycompany
    """
    console: Console = ctx.obj["console"]
    
    if name == "default":
        console.print("[red]Cannot remove the default registry[/red]")
        return
    
    # TODO: Actually remove registry
    console.print(f"[green]✓[/green] Removed registry '{name}'")


@registry.command("set-default")
@click.argument("name")
@click.pass_context
def registry_set_default(ctx: click.Context, name: str) -> None:
    """Set a registry as default.
    
    Examples:
        aam registry set-default mycompany
    """
    console: Console = ctx.obj["console"]
    
    # TODO: Actually set default
    console.print(f"[green]✓[/green] Set '{name}' as default registry")


@registry.command("login")
@click.argument("name", required=False, default="default")
@click.option("--token", "-t", help="API token for authentication")
@click.pass_context
def registry_login(ctx: click.Context, name: str, token: str | None) -> None:
    """Login to a registry.
    
    Examples:
        aam registry login
        aam registry login mycompany --token abc123
    """
    console: Console = ctx.obj["console"]
    
    if not token:
        console.print(f"[dim]Opening browser for authentication to '{name}'...[/dim]")
        # TODO: Implement browser-based OAuth flow
    else:
        # TODO: Validate and store token
        pass
    
    console.print(f"[green]✓[/green] Logged in to '{name}'")


@registry.command("logout")
@click.argument("name", required=False, default="default")
@click.pass_context
def registry_logout(ctx: click.Context, name: str) -> None:
    """Logout from a registry.
    
    Examples:
        aam registry logout
        aam registry logout mycompany
    """
    console: Console = ctx.obj["console"]
    
    # TODO: Actually clear credentials
    console.print(f"[green]✓[/green] Logged out from '{name}'")
