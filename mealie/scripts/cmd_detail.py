"""
mealie detail – Show full details for a recipe.

Accepts a recipe slug (e.g. "pasta-carbonara") or a partial name
match. Displays ingredients, instructions, metadata, and a direct URL.
"""

from __future__ import annotations

import sys

import click

from scripts.utils import console, MealieClient, print_recipe_detail, output_json


def _find_recipe(client: MealieClient, identifier: str) -> dict:
    """
    Resolve `identifier` to a full recipe dict.

    Tries slug lookup first; falls back to searching by name.
    """
    # Try as slug directly
    try:
        return client.get(f"/recipes/{identifier}")
    except SystemExit:
        pass  # 404 – try search instead

    # Search by name
    data = client.get("/recipes", {"search": identifier, "perPage": 5})
    items = data.get("items", [])
    if not items:
        console.print(f"[red]No recipe found for:[/] {identifier!r}")
        sys.exit(1)

    if len(items) == 1:
        return client.get(f"/recipes/{items[0]['slug']}")

    # Multiple matches – let user pick
    console.print(f"\n[yellow]Multiple matches for {identifier!r}:[/]")
    for i, r in enumerate(items, 1):
        console.print(f"  {i}. {r['name']}  [dim]({r['slug']})[/]")
    choice = click.prompt("Enter number", type=click.IntRange(1, len(items)))
    return client.get(f"/recipes/{items[choice - 1]['slug']}")


@click.command()
@click.argument("recipe")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Output raw JSON.")
def detail(recipe: str, as_json: bool):
    """
    Show full RECIPE details (ingredients, steps, metadata).

    RECIPE can be a slug ("pasta-carbonara") or a partial name.

    \b
    Examples:
        mealie detail pasta-carbonara
        mealie detail "Chicken Soup"
        mealie detail carbonara --json
    """
    client = MealieClient()
    data   = _find_recipe(client, recipe)

    if as_json:
        output_json(data)
        return

    print_recipe_detail(data, client.base_url)
