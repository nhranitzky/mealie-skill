from __future__ import annotations

from typing import Annotated

import typer
from rich import box
from rich.table import Table

from ..output import OutputFormat, output_json
from .client import MealieClient
from .display import console, recipe_list_table

app = typer.Typer(help="Browse recipe categories, tags, and cookbooks.")
OutputOption = Annotated[OutputFormat, typer.Option("--output", "-o")]


@app.command("categories")
def list_categories(output: OutputOption = OutputFormat.text) -> None:
    """List all recipe categories."""
    client = MealieClient()
    items  = client.get_all_pages("/organizers/categories")

    if output == OutputFormat.json:
        output_json(items)
        return

    table = Table(title=f"Categories ({len(items)})", box=box.SIMPLE, header_style="bold cyan")
    table.add_column("Name",    style="green", min_width=20)
    table.add_column("Slug",    style="dim",   min_width=20)
    table.add_column("Recipes", justify="right", width=8)

    for c in sorted(items, key=lambda x: x.get("name", "").lower()):
        table.add_row(c.get("name", "?"), c.get("slug", "?"), str(len(c.get("recipes") or [])))

    console.print()
    console.print(table)
    console.print()


@app.command("tags")
def list_tags(output: OutputOption = OutputFormat.text) -> None:
    """List all recipe tags."""
    client = MealieClient()
    items  = client.get_all_pages("/organizers/tags")

    if output == OutputFormat.json:
        output_json(items)
        return

    names = sorted(t.get("name", "?") for t in items)
    console.print()
    console.print(f"[bold]Tags[/]  ({len(names)} total)\n")
    for row in [names[i:i + 4] for i in range(0, len(names), 4)]:
        console.print("  " + "   ".join(f"[cyan]{n}[/]" for n in row))
    console.print()


@app.command("cookbooks")
def list_cookbooks(output: OutputOption = OutputFormat.text) -> None:
    """List all cookbooks."""
    client = MealieClient()
    data   = client.get("/households/cookbooks")
    items  = data.get("items", []) if isinstance(data, dict) else data

    if output == OutputFormat.json:
        output_json(items)
        return

    table = Table(title=f"Cookbooks ({len(items)})", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Name",        min_width=24)
    table.add_column("Slug",        min_width=20, style="dim")
    table.add_column("Description", min_width=30, style="dim")
    table.add_column("Public",      width=8)

    for cb in items:
        table.add_row(cb.get("name", "?"), cb.get("slug", "?"),
                      cb.get("description", ""), "✓" if cb.get("public") else "-")
    console.print()
    console.print(table)
    console.print()


@app.command("cookbook")
def show_cookbook(
    slug:   Annotated[str, typer.Argument(help="Cookbook slug.")],
    limit:  Annotated[int, typer.Option("--limit", "-n")] = 50,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Show recipes in a COOKBOOK."""
    client  = MealieClient()
    data    = client.get(f"/households/cookbooks/{slug}")
    recipes = data.get("recipes", [])[:limit]

    if output == OutputFormat.json:
        output_json(recipes)
        return

    console.print()
    name = data.get("name", slug)
    console.print(recipe_list_table(recipes, title=f"Cookbook: {name}  ({len(recipes)} recipes)"))
    console.print()
