"""Config command for AAM CLI."""

import click
from rich.console import Console
from rich.table import Table


@click.group()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Manage AAM configuration."""
    pass


@config.command("get")
@click.argument("key", required=False)
@click.pass_context
def config_get(ctx: click.Context, key: str | None) -> None:
    """Get configuration value(s).
    
    If KEY is not provided, shows all configuration.
    
    Examples:
        aam config get
        aam config get registry
    """
    console: Console = ctx.obj["console"]
    
    # TODO: Read actual config
    config_values = {
        "registry": "https://registry.aam.dev",
        "cache_dir": "~/.aam/cache",
        "timeout": "30",
        "verify_ssl": "true",
    }
    
    if key:
        if key in config_values:
            console.print(f"{key}={config_values[key]}")
        else:
            console.print(f"[red]Unknown configuration key: {key}[/red]")
    else:
        table = Table(title="AAM Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        
        for k, v in config_values.items():
            table.add_row(k, v)
        
        console.print(table)


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """Set a configuration value.
    
    Examples:
        aam config set registry https://my-registry.example.com
        aam config set timeout 60
    """
    console: Console = ctx.obj["console"]
    
    # TODO: Actually save config
    console.print(f"[green]✓[/green] Set {key}={value}")


@config.command("delete")
@click.argument("key")
@click.pass_context
def config_delete(ctx: click.Context, key: str) -> None:
    """Delete a configuration value.
    
    Examples:
        aam config delete registry
    """
    console: Console = ctx.obj["console"]
    
    # TODO: Actually delete config
    console.print(f"[green]✓[/green] Deleted {key}")


@config.command("list")
@click.pass_context
def config_list(ctx: click.Context) -> None:
    """List all configuration values."""
    ctx.invoke(config_get)
