"""
mealie stats – Show statistics about the Mealie server and recipe collection.

Category recipe counts are computed client-side by fetching all recipes
once and aggregating – this gives accurate counts regardless of what the
/organizers/categories endpoint returns.
"""

from __future__ import annotations

from collections import Counter

import click
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from scripts.utils import console, MealieClient, output_json


@click.command()
@click.option("--top", "-n", default=10, show_default=True,
              help="How many top categories / tags to display.")
@click.option("--json", "as_json", is_flag=True, default=False)
def stats(top: int, as_json: bool):
    """Display statistics about your Mealie recipe collection."""
    client = MealieClient()

    # ── Fetch all recipes (with categories + tags embedded) ───────────────────
    console.print("[dim]Loading recipes …[/]")
    all_recipes = client.get_all_pages("/recipes", {"orderBy": "name"})
    total_recipes = len(all_recipes)

    # ── Count categories and tags from the actual recipe data ─────────────────
    cat_counter: Counter = Counter()
    tag_counter: Counter = Counter()

    for r in all_recipes:
        for cat in r.get("recipeCategory") or []:
            name = cat.get("name") or cat.get("slug") or "?"
            if name:
                cat_counter[name] += 1
        for tag in r.get("tags") or []:
            name = tag.get("name") or tag.get("slug") or "?"
            if name:
                tag_counter[name] += 1

    # ── Fetch organizer totals (just counts, not per-item) ────────────────────
    cats_data = client.get("/organizers/categories", {"perPage": 1})
    tags_data = client.get("/organizers/tags",       {"perPage": 1})
    total_cats = cats_data.get("total", len(cat_counter))
    total_tags = tags_data.get("total", len(tag_counter))

    # ── Server info (best-effort) ─────────────────────────────────────────────
    try:
        app_info = client.get("/app/about")
    except SystemExit:
        app_info = {}

    if as_json:
        output_json({
            "total_recipes":    total_recipes,
            "total_categories": total_cats,
            "total_tags":       total_tags,
            "top_categories":   [{"name": n, "count": c}
                                  for n, c in cat_counter.most_common(top)],
            "top_tags":         [{"name": n, "count": c}
                                  for n, c in tag_counter.most_common(top)],
            "server":           app_info,
        })
        return

    # ── Overview panel ────────────────────────────────────────────────────────
    overview = Text()
    overview.append("  📚 Total recipes:    ", style="bold")
    overview.append(f"{total_recipes}\n")
    overview.append("  📁 Categories:       ", style="bold")
    overview.append(f"{total_cats}\n")
    overview.append("  🏷️  Tags:             ", style="bold")
    overview.append(f"{total_tags}\n")

    if app_info:
        overview.append("  🖥️  Mealie version:   ", style="bold")
        overview.append(f"{app_info.get('version', '?')}\n")

    overview.append("  🌐 Server URL:       ", style="bold")
    overview.append(f"{client.base_url}\n")

    console.print()
    console.print(Panel(overview, title="[bold green]Mealie Collection Stats[/]", expand=False))

    # ── Top categories ────────────────────────────────────────────────────────
    top_cats = cat_counter.most_common(top)
    if top_cats:
        cat_table = Table(title=f"Top {top} Categories", box=box.SIMPLE,
                          show_header=True, header_style="bold cyan")
        cat_table.add_column("Category", style="green")
        cat_table.add_column("Recipes",  justify="right", style="bold")
        for name, count in top_cats:
            cat_table.add_row(name, str(count))
        console.print(cat_table)

    # ── Top tags ──────────────────────────────────────────────────────────────
    top_tags = tag_counter.most_common(top)
    if top_tags:
        tag_table = Table(title=f"Top {top} Tags", box=box.SIMPLE,
                          show_header=True, header_style="bold cyan")
        tag_table.add_column("Tag",     style="blue")
        tag_table.add_column("Recipes", justify="right", style="bold")
        for name, count in top_tags:
            tag_table.add_row(name, str(count))
        console.print(tag_table)

    console.print()
