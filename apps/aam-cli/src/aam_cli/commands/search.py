"""Search command for AAM CLI."""

import click
from rich.console import Console
from rich.table import Table


@click.command()
@click.argument("query")
@click.option("--limit", "-l", default=10, help="Maximum number of results")
@click.option("--type", "-t", "package_type", help="Filter by package type (agent, skill, tool)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def search(
    ctx: click.Context,
    query: str,
    limit: int,
    package_type: str | None,
    output_json: bool,
) -> None:
    """Search for packages in the registry.
    
    Examples:
        aam search chatbot
        aam search "code assistant" --type agent
        aam search summarizer --limit 5
    """
    console: Console = ctx.obj["console"]
    
    console.print(f"[dim]Searching for '{query}'...[/dim]\n")
    
    # TODO: Implement actual search logic
    # Mock results for now
    results = [
        {"name": f"{query}-agent", "version": "1.0.0", "description": f"An agent for {query}"},
        {"name": f"{query}-skill", "version": "0.5.0", "description": f"A skill related to {query}"},
    ]
    
    if output_json:
        import json
        console.print(json.dumps(results, indent=2))
        return
    
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("Package", style="cyan", no_wrap=True)
    table.add_column("Version", style="green")
    table.add_column("Description")
    
    for result in results[:limit]:
        table.add_row(result["name"], result["version"], result["description"])
    
    console.print(table)
    console.print(f"\n[dim]Found {len(results)} packages[/dim]")
