from __future__ import annotations

import sys
from datetime import date, timedelta
from typing import Annotated

import typer
from rich import box
from rich.table import Table
from rich.text import Text

from ..output import OutputFormat, output_json
from .client import MealieClient
from .display import console

app = typer.Typer(help="View and manage the household meal plan.")

MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]
OutputOption = Annotated[OutputFormat, typer.Option("--output", "-o")]


@app.command("show")
def show_mealplan(
    start: Annotated[str | None, typer.Option(metavar="YYYY-MM-DD", help="Start date.")] = None,
    end: Annotated[str | None, typer.Option(metavar="YYYY-MM-DD", help="End date.")] = None,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Display the meal plan for a date range (default: current week)."""
    client = MealieClient()
    today = date.today()

    if start:
        d_start = date.fromisoformat(start)
        d_end = date.fromisoformat(end) if end else d_start + timedelta(days=6)
    else:
        d_start = today - timedelta(days=today.weekday())
        d_end = d_start + timedelta(days=6)

    params = {"startDate": d_start.isoformat(), "endDate": d_end.isoformat()}
    data = client.get("/households/mealplans", params)
    items = data.get("items") or (data if isinstance(data, list) else [])

    if output == OutputFormat.json:
        output_json(items)
        return

    table = Table(
        title=f"Meal Plan  {d_start}  ->  {d_end}",
        box=box.ROUNDED, show_header=True, header_style="bold cyan", show_lines=True,
    )
    table.add_column("Date", width=12, no_wrap=True)
    table.add_column("Type", width=12)
    table.add_column("Recipe", min_width=30)
    table.add_column("ID", width=8, style="dim")

    for entry in sorted(items, key=lambda e: (e.get("date", ""), e.get("entryType", ""))):
        recipe_name = (
            entry["recipe"].get("name", "?") if entry.get("recipe") else entry.get("title", "?")
        )
        meal_type = entry.get("entryType", "?")
        entry_id = str(entry.get("id", "?"))[:8]
        type_color = {"breakfast": "yellow", "lunch": "cyan",
                      "dinner": "green", "snack": "magenta"}.get(meal_type, "white")
        table.add_row(
            entry.get("date", "?"), Text(meal_type, style=type_color), recipe_name, entry_id
        )

    console.print()
    if not items:
        console.print(f"[yellow]No meal plan entries for {d_start} - {d_end}[/]")
    else:
        console.print(table)
    console.print()


@app.command("add")
def add_entry(
    date_str: Annotated[str, typer.Argument(metavar="DATE", help="Date (YYYY-MM-DD).")],
    recipe_slug: Annotated[str, typer.Argument(help="Recipe slug.")],
    meal_type: Annotated[str, typer.Option("--type", help="Meal type.")] = "dinner",
    output: OutputOption = OutputFormat.text,
) -> None:
    """Add RECIPE_SLUG to the meal plan on DATE."""
    if meal_type not in MEAL_TYPES:
        console.print(
            f"[red]Invalid meal type:[/] {meal_type!r}. Choose from: {', '.join(MEAL_TYPES)}"
        )
        sys.exit(1)

    client = MealieClient()
    recipe = client.get(f"/recipes/{recipe_slug}")
    recipe_id = recipe.get("id")
    if not recipe_id:
        console.print(f"[red]Recipe not found:[/] {recipe_slug!r}")
        sys.exit(1)

    result = client.post("/households/mealplans", {
        "date": date_str, "entryType": meal_type, "recipeId": recipe_id,
    })

    if output == OutputFormat.json:
        output_json(result)
        return
    console.print(
        f"\n[green]✅  Added[/] [bold]{recipe['name']}[/] to [bold]{date_str}[/] ({meal_type})\n"
    )


@app.command("remove")
def remove_entry(
    entry_id: Annotated[int, typer.Argument(help="Meal plan entry ID.")],
) -> None:
    """Remove a meal plan entry by its numeric ID."""
    MealieClient().delete(f"/households/mealplans/{entry_id}")
    console.print(f"\n[green]✅  Meal plan entry {entry_id} removed.[/]\n")


@app.command("random")
def add_random(
    date_str: Annotated[str, typer.Argument(metavar="DATE", help="Date (YYYY-MM-DD).")],
    meal_type: Annotated[str, typer.Option("--type", help="Meal type.")] = "dinner",
    output: OutputOption = OutputFormat.text,
) -> None:
    """Insert a random recipe into the meal plan on DATE."""
    client = MealieClient()
    result = client.post("/households/mealplans/random", {"date": date_str, "entryType": meal_type})

    if output == OutputFormat.json:
        output_json(result)
        return
    name = result.get("recipe", {}).get("name") or "?"
    console.print(
        f"\n[green]✅  Random recipe added:[/] [bold]{name}[/] -> {date_str} ({meal_type})\n"
    )
