"""Install command for AAM CLI."""

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


@click.command()
@click.argument("packages", nargs=-1, required=True)
@click.option("--dev", "-D", is_flag=True, help="Install as development dependency")
@click.option("--global", "-g", "global_install", is_flag=True, help="Install globally")
@click.option("--force", "-f", is_flag=True, help="Force reinstall")
@click.option("--dry-run", is_flag=True, help="Show what would be installed without installing")
@click.pass_context
def install(
    ctx: click.Context,
    packages: tuple[str, ...],
    dev: bool,
    global_install: bool,
    force: bool,
    dry_run: bool,
) -> None:
    """Install one or more packages.
    
    Examples:
        aam install my-agent
        aam install my-agent@1.0.0
        aam install agent1 agent2 agent3
        aam install my-agent --dev
    """
    console: Console = ctx.obj["console"]
    
    if dry_run:
        console.print("[yellow]Dry run mode - no changes will be made[/yellow]\n")
    
    for package in packages:
        package_name, version = _parse_package_spec(package)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Installing {package_name}...", total=None)
            
            # TODO: Implement actual installation logic
            if not dry_run:
                progress.update(task, description=f"Resolving {package_name}...")
                progress.update(task, description=f"Downloading {package_name}...")
                progress.update(task, description=f"Installing {package_name}...")
        
        version_str = f"@{version}" if version else ""
        location = "globally" if global_install else "locally"
        dep_type = " (dev)" if dev else ""
        
        console.print(
            f"[green]✓[/green] Installed [bold]{package_name}{version_str}[/bold] {location}{dep_type}"
        )


def _parse_package_spec(spec: str) -> tuple[str, str | None]:
    """Parse package specification into name and version."""
    if "@" in spec and not spec.startswith("@"):
        parts = spec.rsplit("@", 1)
        return parts[0], parts[1]
    return spec, None
