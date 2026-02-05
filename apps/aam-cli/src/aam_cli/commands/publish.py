"""Publish command for AAM CLI."""

import click
from rich.console import Console
from rich.prompt import Confirm


@click.command()
@click.option("--access", type=click.Choice(["public", "private"]), default="public")
@click.option("--tag", default="latest", help="Distribution tag")
@click.option("--dry-run", is_flag=True, help="Perform a dry run without publishing")
@click.pass_context
def publish(
    ctx: click.Context,
    access: str,
    tag: str,
    dry_run: bool,
) -> None:
    """Publish a package to the registry.
    
    Must be run from the package directory containing aam.toml or pyproject.toml.
    
    Examples:
        aam publish
        aam publish --access private
        aam publish --tag beta
        aam publish --dry-run
    """
    console: Console = ctx.obj["console"]
    
    if dry_run:
        console.print("[yellow]Dry run mode - package will not be published[/yellow]\n")
    
    # TODO: Read package manifest
    package_name = "my-package"
    package_version = "1.0.0"
    
    console.print(f"[bold]Publishing:[/bold] {package_name}@{package_version}")
    console.print(f"[bold]Access:[/bold] {access}")
    console.print(f"[bold]Tag:[/bold] {tag}")
    console.print()
    
    if not dry_run:
        if not Confirm.ask("Do you want to continue?"):
            console.print("[yellow]Publish cancelled[/yellow]")
            return
        
        console.print("[dim]Packing package...[/dim]")
        console.print("[dim]Uploading to registry...[/dim]")
        console.print(f"\n[green]✓[/green] Published {package_name}@{package_version}")
    else:
        console.print("[dim]Would pack and upload package[/dim]")
        console.print(f"\n[green]✓[/green] Dry run complete - {package_name}@{package_version}")
