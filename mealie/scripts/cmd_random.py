"""
mealie random – Get a random recipe suggestion.

Fetches all recipes (or a filtered subset) and picks one at random.
Useful for "what should I cook tonight?" scenarios.
"""

from __future__ import annotations

import random

import click

from scripts.utils import console, MealieClient, print_recipe_detail, output_json


@click.command()
@click.option("--category", "-c", default=None, help="Restrict to a category.")
@click.option("--tag",      "-t", default=None, help="Restrict to a tag.")
@click.option("--count",    "-n", default=1, show_default=True, type=int,
              help="Number of suggestions.")
@click.option("--open",     "-o", "show_detail", is_flag=True, default=False,
              help="Show full recipe detail for the first suggestion.")
@click.option("--json",     "as_json", is_flag=True, default=False)
def random_recipe(category: str | None, tag: str | None,
                  count: int, show_detail: bool, as_json: bool):
    """
    Suggest a random recipe from your Mealie collection.

    \b
    Examples:
        mealie random
        mealie random --category Italian --count 3
        mealie random --tag quick --open
    """
    client = MealieClient()
    params: dict = {}
    if category:
        params["categories"] = category
    if tag:
        params["tags"] = tag

    all_recipes = client.get_all_pages("/recipes", params)

    if not all_recipes:
        console.print("[yellow]No recipes found with the given filters.[/]")
        return

    picks = random.sample(all_recipes, min(count, len(all_recipes)))

    if as_json:
        output_json(picks)
        return

    console.print()
    for i, r in enumerate(picks, 1):
        name  = r.get("name", "?")
        slug  = r.get("slug", "?")
        cats  = ", ".join(c["name"] for c in (r.get("recipeCategory") or []))
        tags  = ", ".join(t["name"] for t in (r.get("tags") or []))
        label = "🎲 Random pick" if count == 1 else f"🎲 Pick {i}"
        console.print(
            f"[bold]{label}:[/]  [green]{name}[/]  [dim]({slug})[/]\n"
            + (f"  [dim]Categories:[/] {cats}\n" if cats else "")
            + (f"  [dim]Tags:[/]       {tags}\n" if tags else "")
            + f"  [dim]URL:[/]         {client.base_url}/recipe/{slug}"
        )
        console.print()

    if show_detail and picks:
        full = client.get(f"/recipes/{picks[0]['slug']}")
        print_recipe_detail(full, client.base_url)
