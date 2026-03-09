"""
mealie list – List recipes from the Mealie server.

Supports filtering by category, tag, keyword search, and sorting.
Paginates automatically; use --limit / --page for manual control.
"""

from __future__ import annotations

import click

from scripts.utils import console, MealieClient, recipe_list_table, output_json


@click.command("list")
@click.option("--limit",    "-n", default=25, show_default=True, help="Recipes per page.")
@click.option("--page",     "-p", default=1,  show_default=True, help="Page number.")
@click.option("--category", "-c", default=None, help="Filter by category name.")
@click.option("--tag",      "-t", default=None, help="Filter by tag name.")
@click.option("--search",   "-s", default=None, help="Full-text search query.")
@click.option("--sort",     default="name",
              type=click.Choice(["name", "createdAt", "updatedAt", "lastMade", "rating"]),
              show_default=True, help="Sort field.")
@click.option("--desc",     is_flag=True, default=False, help="Sort descending.")
@click.option("--all",      "fetch_all", is_flag=True, default=False,
              help="Fetch ALL recipes (ignores --limit / --page).")
@click.option("--json",     "as_json", is_flag=True, default=False)
def list_recipes(limit: int, page: int, category: str | None, tag: str | None,
                 search: str | None, sort: str, desc: bool,
                 fetch_all: bool, as_json: bool):
    """
    List recipes from Mealie.

    \b
    Examples:
        mealie list
        mealie list --category "Pasta" --sort rating --desc
        mealie list --search "Chicken" --limit 10
        mealie list --all --json
    """
    client = MealieClient()

    params: dict = {
        "orderBy":        sort,
        "orderDirection": "desc" if desc else "asc",
    }
    if search:
        params["search"] = search
    if category:
        params["categories"] = category
    if tag:
        params["tags"] = tag

    if fetch_all:
        recipes = client.get_all_pages("/recipes", params)
        total   = len(recipes)
    else:
        params.update({"page": page, "perPage": limit})
        data    = client.get("/recipes", params)
        recipes = data.get("items", [])
        total   = data.get("total", 0)
        page_total = data.get("totalPages", 1)

    if as_json:
        output_json(recipes)
        return

    filters = " · ".join(f for f in [
        f"search={search!r}" if search else "",
        f"category={category!r}" if category else "",
        f"tag={tag!r}" if tag else "",
    ] if f)
    title = f"Recipes – {total} total" + (f" ({filters})" if filters else "")

    table = recipe_list_table(recipes, title=title)
    console.print()
    console.print(table)

    if not fetch_all:
        console.print(
            f"  [dim]Page {page} of {page_total}  ·  "
            f"Use --page / --limit to navigate[/]"
        )
    console.print()
