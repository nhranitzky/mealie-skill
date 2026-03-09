"""
mealie organizers – Browse categories, tags, and cookbooks.

Subcommands:
  categories    List all recipe categories
  tags          List all recipe tags
  cookbooks     List all cookbooks
  cookbook <slug>   Show recipes in a cookbook
"""

from __future__ import annotations

import click
from rich.table import Table
from rich.columns import Columns
from rich import box

from scripts.utils import console, MealieClient, recipe_list_table, output_json


@click.group()
def organizers():
    """Browse recipe categories, tags, and cookbooks."""


# ── categories ───────────────────────────────────────────────────────────────

@organizers.command("categories")
@click.option("--json", "as_json", is_flag=True, default=False)
def list_categories(as_json: bool):
    """List all recipe categories."""
    client = MealieClient()
    items  = client.get_all_pages("/organizers/categories")

    if as_json:
        output_json(items)
        return

    table = Table(title=f"Categories ({len(items)})",
                  box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("Name",   style="green", min_width=20)
    table.add_column("Slug",   style="dim",   min_width=20)
    table.add_column("Recipes", justify="right", width=8)

    for c in sorted(items, key=lambda x: x.get("name", "").lower()):
        count = str(len(c.get("recipes") or []))
        table.add_row(c.get("name", "?"), c.get("slug", "?"), count)

    console.print()
    console.print(table)
    console.print()


# ── tags ─────────────────────────────────────────────────────────────────────

@organizers.command("tags")
@click.option("--json", "as_json", is_flag=True, default=False)
def list_tags(as_json: bool):
    """List all recipe tags."""
    client = MealieClient()
    items  = client.get_all_pages("/organizers/tags")

    if as_json:
        output_json(items)
        return

    # Display as a compact multi-column layout
    names = sorted(t.get("name", "?") for t in items)
    console.print()
    console.print(f"[bold]Tags[/]  ({len(names)} total)\n")
    # Split into rows of 4
    rows = [names[i:i+4] for i in range(0, len(names), 4)]
    for row in rows:
        console.print("  " + "   ".join(f"[cyan]{n}[/]" for n in row))
    console.print()


# ── cookbooks ─────────────────────────────────────────────────────────────────

@organizers.command("cookbooks")
@click.option("--json", "as_json", is_flag=True, default=False)
def list_cookbooks(as_json: bool):
    """List all cookbooks."""
    client = MealieClient()
    data   = client.get("/households/cookbooks")
    items  = data.get("items", []) if isinstance(data, dict) else data

    if as_json:
        output_json(items)
        return

    table = Table(title=f"Cookbooks ({len(items)})",
                  box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Name",        min_width=24)
    table.add_column("Slug",        min_width=20, style="dim")
    table.add_column("Description", min_width=30, style="dim")
    table.add_column("Public",      width=8)

    for cb in items:
        public = "✓" if cb.get("public") else "–"
        table.add_row(
            cb.get("name", "?"),
            cb.get("slug", "?"),
            cb.get("description", ""),
            public,
        )

    console.print()
    console.print(table)
    console.print()


@organizers.command("cookbook")
@click.argument("slug")
@click.option("--limit", "-n", default=50, show_default=True)
@click.option("--json",  "as_json", is_flag=True, default=False)
def show_cookbook(slug: str, limit: int, as_json: bool):
    """
    Show recipes in a COOKBOOK.

    \b
    Example:
        mealie organizers cookbook italian-favourites
    """
    client  = MealieClient()
    data    = client.get(f"/households/cookbooks/{slug}")
    recipes = data.get("recipes", [])[:limit]
    name    = data.get("name", slug)

    if as_json:
        output_json(recipes)
        return

    table = recipe_list_table(recipes, title=f"Cookbook: {name}  ({len(recipes)} recipes)")
    console.print()
    console.print(table)
    console.print()
