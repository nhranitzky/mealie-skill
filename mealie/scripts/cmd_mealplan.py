"""
mealie mealplan – View and manage the household meal plan.

Subcommands:
  show   [--week / --date START --end END]   Display the meal plan calendar
  add    <date> <recipe-slug> [--type TYPE]  Add a recipe to the plan
  random <date> [--type TYPE]               Insert a random recipe
  remove <entry-id>                          Delete a meal plan entry
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

import click
from rich.table import Table
from rich.text import Text
from rich import box

from scripts.utils import console, MealieClient, output_json

MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]
TODAY = date.today()


# ── group ────────────────────────────────────────────────────────────────────

@click.group()
def mealplan():
    """View and manage the household meal plan."""


@mealplan.command("show")
@click.option("--week",  is_flag=True, default=False,
              help="Show the current week (Mon–Sun). Default.")
@click.option("--start", default=None, metavar="YYYY-MM-DD",
              help="Start date of a custom range.")
@click.option("--end",   default=None, metavar="YYYY-MM-DD",
              help="End date of a custom range.")
@click.option("--json",  "as_json", is_flag=True, default=False)
def show_mealplan(week: bool, start: str | None, end: str | None, as_json: bool):
    """
    Display the meal plan for a date range.

    \b
    Examples:
        mealie mealplan show
        mealie mealplan show --start 2024-06-01 --end 2024-06-07
        mealie mealplan show --json
    """
    client = MealieClient()

    # Determine date range
    if start:
        d_start = date.fromisoformat(start)
        d_end   = date.fromisoformat(end) if end else d_start + timedelta(days=6)
    else:
        # Default: current week Mon–Sun
        d_start = TODAY - timedelta(days=TODAY.weekday())
        d_end   = d_start + timedelta(days=6)

    params = {"startDate": d_start.isoformat(), "endDate": d_end.isoformat()}
    data   = client.get("/households/mealplans", params)
    items  = data.get("items") or (data if isinstance(data, list) else [])

    if as_json:
        output_json(items)
        return

    table = Table(
        title=f"Meal Plan  {d_start}  →  {d_end}",
        box=box.ROUNDED, show_header=True, header_style="bold cyan", show_lines=True,
    )
    table.add_column("Date",   width=12, no_wrap=True)
    table.add_column("Type",   width=12)
    table.add_column("Recipe", min_width=30)
    table.add_column("ID",     width=8, style="dim")

    for entry in sorted(items, key=lambda e: (e.get("date", ""), e.get("entryType", ""))):
        recipe_name = "?"
        if entry.get("recipe"):
            recipe_name = entry["recipe"].get("name", "?")
        elif entry.get("title"):
            recipe_name = entry["title"]

        meal_type  = entry.get("entryType", "?")
        entry_id   = str(entry.get("id", "?"))[:8]
        entry_date = entry.get("date", "?")

        type_color = {"breakfast": "yellow", "lunch": "cyan",
                      "dinner": "green", "snack": "magenta"}.get(meal_type, "white")
        table.add_row(
            entry_date,
            Text(meal_type, style=type_color),
            recipe_name,
            entry_id,
        )

    console.print()
    if not items:
        console.print(f"[yellow]No meal plan entries for {d_start} – {d_end}[/]")
    else:
        console.print(table)
    console.print()


@mealplan.command("add")
@click.argument("date_str", metavar="DATE")
@click.argument("recipe_slug")
@click.option("--type", "meal_type", default="dinner",
              type=click.Choice(MEAL_TYPES), show_default=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def add_entry(date_str: str, recipe_slug: str, meal_type: str, as_json: bool):
    """
    Add RECIPE_SLUG to the meal plan on DATE.

    \b
    Examples:
        mealie mealplan add 2024-06-10 pasta-carbonara
        mealie mealplan add 2024-06-11 chicken-soup --type lunch
    """
    client = MealieClient()

    # Resolve slug → recipe id
    recipe = client.get(f"/recipes/{recipe_slug}")
    recipe_id = recipe.get("id")
    if not recipe_id:
        console.print(f"[red]Recipe not found:[/] {recipe_slug!r}")
        sys.exit(1)

    body = {
        "date":      date_str,
        "entryType": meal_type,
        "recipeId":  recipe_id,
    }
    result = client.post("/households/mealplans", body)

    if as_json:
        output_json(result)
        return

    console.print(
        f"\n[green]✅  Added[/] [bold]{recipe['name']}[/] "
        f"to [bold]{date_str}[/] ({meal_type})\n"
    )


@mealplan.command("remove")
@click.argument("entry_id", type=int)
def remove_entry(entry_id: int):
    """Remove a meal plan entry by its numeric ID.

    Find IDs with `mealie mealplan show`.
    """
    client = MealieClient()
    client.delete(f"/households/mealplans/{entry_id}")
    console.print(f"\n[green]✅  Meal plan entry {entry_id} removed.[/]\n")


@mealplan.command("random")
@click.argument("date_str", metavar="DATE")
@click.option("--type", "meal_type", default="dinner",
              type=click.Choice(MEAL_TYPES), show_default=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def add_random(date_str: str, meal_type: str, as_json: bool):
    """
    Insert a random recipe into the meal plan on DATE.

    \b
    Example:
        mealie mealplan random 2024-06-12 --type lunch
    """
    client = MealieClient()
    body   = {"date": date_str, "entryType": meal_type}
    result = client.post("/households/mealplans/random", body)

    if as_json:
        output_json(result)
        return

    name = result.get("recipe", {}).get("name") or "?"
    console.print(f"\n[green]✅  Random recipe added:[/] [bold]{name}[/] → {date_str} ({meal_type})\n")
