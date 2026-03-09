"""
mealie search – Full-text recipe search with optional filters.

Supports Mealie's smart search (quoted literals, category/tag filters).
Shows a ranked results table and lets you drill into a single result.
"""

from __future__ import annotations

import sys

import click

from scripts.utils import (
    console, MealieClient, recipe_list_table, print_recipe_detail, output_json
)


@click.command()
@click.argument("query", nargs=-1, required=True)
@click.option("--category", "-c", default=None, help="Restrict to a category.")
@click.option("--tag",      "-t", default=None, help="Restrict to a tag.")
@click.option("--limit",    "-n", default=20, show_default=True)
@click.option("--open",     "-o", "open_first", is_flag=True, default=False,
              help="If exactly one match, show full detail automatically.")
@click.option("--json",     "as_json", is_flag=True, default=False)
def search(query: tuple[str, ...], category: str | None, tag: str | None,
           limit: int, open_first: bool, as_json: bool):
    """
    Search recipes in Mealie by QUERY (full-text).

    \b
    Examples:
        mealie search chicken
        mealie search "pasta" --category Italian
        mealie search soup --tag winter --open
        mealie search risotto --json
    """
    q = " ".join(query)
    client = MealieClient()

    params: dict = {"search": q, "perPage": limit, "page": 1}
    if category:
        params["categories"] = category
    if tag:
        params["tags"] = tag

    data  = client.get("/recipes", params)
    items = data.get("items", [])
    total = data.get("total", 0)

    if as_json:
        output_json(items)
        return

    if not items:
        console.print(f"\n[yellow]No recipes found for:[/] {q!r}\n")
        return

    title = f"Search: {q!r}  –  {total} match(es)"
    table = recipe_list_table(items, title=title)
    console.print()
    console.print(table)
    console.print()

    # Auto-open if exactly one result + --open flag
    if open_first and len(items) == 1:
        full = client.get(f"/recipes/{items[0]['slug']}")
        print_recipe_detail(full, client.base_url)
    elif open_first and len(items) > 1:
        console.print("[dim]Use --open with a more specific query to auto-open a single result.[/]")
        console.print()
