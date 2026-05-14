from __future__ import annotations

import sys
from typing import Annotated, Any

import typer
from rich import box
from rich.table import Table
from rich.text import Text

from ..output import OutputFormat, output_json
from .client import MealieClient
from .display import console

app = typer.Typer(help="Manage Mealie shopping lists.")
OutputOption = Annotated[OutputFormat, typer.Option("--output", "-o")]


@app.command("lists")
def list_lists(output: OutputOption = OutputFormat.text) -> None:
    """Show all shopping lists."""
    client = MealieClient()
    items  = client.get("/households/shopping/lists").get("items", [])

    if output == OutputFormat.json:
        output_json(items)
        return

    table = Table(title="Shopping Lists", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("ID",    style="dim", width=36, no_wrap=True)
    table.add_column("Name",  min_width=24)
    table.add_column("Items", justify="right", width=7)

    for lst in items:
        table.add_row(lst.get("id", "?"), lst.get("name", "?"),
                      str(len(lst.get("listItems") or [])))
    console.print()
    console.print(table)
    console.print()


@app.command("show")
def show_list(
    list_id: Annotated[str, typer.Argument(help="Shopping list ID.")],
    checked: Annotated[bool, typer.Option("--checked", help="Include checked items.")] = False,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Show items in a shopping list."""
    client = MealieClient()
    params: dict[str, Any] = {"perPage": 200, "orderBy": "position", "shoppingListId": list_id}
    if not checked:
        params["checked"] = "false"
    items = client.get("/households/shopping/items", params).get("items", [])

    if output == OutputFormat.json:
        output_json(items)
        return

    list_name = client.get(f"/households/shopping/lists/{list_id}").get("name", list_id)
    table = Table(title=f"Shopping List: {list_name}", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("",     width=3)
    table.add_column("Item", min_width=28)
    table.add_column("Qty",  justify="right", width=8)
    table.add_column("Unit", width=10)
    table.add_column("Note", style="dim", min_width=18)

    for item in items:
        is_checked = item.get("checked", False)
        check = Text("✓", style="green") if is_checked else Text("○", style="dim")
        food  = (item.get("food") or {}).get("name") or item.get("note") or "?"
        qty   = str(item.get("quantity") or "")
        unit  = (item.get("unit") or {}).get("name") or ""
        note  = item.get("note") or ""
        table.add_row(check, Text(food, style="dim" if is_checked else ""), qty, unit, note)

    console.print()
    console.print("[yellow]Shopping list is empty.[/]" if not items else table)
    console.print()


@app.command("add")
def add_item(
    list_id:   Annotated[str, typer.Argument(help="Shopping list ID.")],
    item_text: Annotated[str, typer.Argument(help="Item to add.")],
    qty:  Annotated[float | None, typer.Option("--qty",  "-q", help="Quantity.")] = None,
    unit: Annotated[str | None,   typer.Option("--unit", "-u", help="Unit.")] = None,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Add a text item to a shopping list."""
    client = MealieClient()
    body: dict[str, Any] = {
        "shoppingListId": list_id, "note": item_text, "isFood": False, "checked": False,
    }
    if qty is not None:
        body["quantity"] = qty
    if unit:
        body["unitValue"] = unit

    result = client.post("/households/shopping/items", body)
    if output == OutputFormat.json:
        output_json(result)
        return
    console.print(f"\n[green]✅  Added:[/] {item_text}\n")


@app.command("recipe")
def add_recipe(
    list_id:     Annotated[str, typer.Argument(help="Shopping list ID.")],
    recipe_slug: Annotated[str, typer.Argument(help="Recipe slug.")],
    servings: Annotated[
        int | None, typer.Option("--servings", "-s", help="Override servings.")
    ] = None,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Add all ingredients of RECIPE_SLUG to a shopping list."""
    client = MealieClient()
    recipe = client.get(f"/recipes/{recipe_slug}")
    if not recipe:
        console.print(f"[red]Recipe not found:[/] {recipe_slug!r}")
        sys.exit(1)

    body: dict[str, Any] = {"id": list_id, "recipes": [{"id": recipe.get("id")}]}
    if servings is not None:
        body["recipes"][0]["recipeIncrementQuantity"] = servings

    result = client.post(f"/households/shopping/lists/{list_id}/recipe", body)
    if output == OutputFormat.json:
        output_json(result)
        return
    console.print(
        f"\n[green]✅  Ingredients of[/] [bold]{recipe['name']}[/] added to shopping list.\n"
    )


@app.command("check")
def check_item(
    item_id: Annotated[str, typer.Argument(help="Shopping list item ID.")],
    output: OutputOption = OutputFormat.text,
) -> None:
    """Toggle the checked state of a shopping list item."""
    client    = MealieClient()
    item      = client.get(f"/households/shopping/items/{item_id}")
    new_state = not item.get("checked", False)
    result    = client.patch(f"/households/shopping/items/{item_id}", {"checked": new_state})

    if output == OutputFormat.json:
        output_json(result)
        return
    food        = (item.get("food") or {}).get("name") or item.get("note") or item_id
    state_label = "[green]checked[/]" if new_state else "[yellow]unchecked[/]"
    console.print(f"\n[green]✅[/] {food!r} marked as {state_label}.\n")


@app.command("clear")
def clear_list(
    list_id:   Annotated[str, typer.Argument(help="Shopping list ID.")],
    clear_all: Annotated[bool, typer.Option("--all", help="Remove ALL items.")] = False,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Remove checked items from a shopping list (--all to wipe everything)."""
    client = MealieClient()
    params: dict[str, Any] = {"shoppingListId": list_id, "perPage": 500}
    if not clear_all:
        params["checked"] = "true"
    items = client.get("/households/shopping/items", params).get("items", [])

    if not items:
        if output == OutputFormat.json:
            output_json({"cleared": 0})
        else:
            console.print("[yellow]Nothing to clear.[/]")
        return

    for item in items:
        client.delete(f"/households/shopping/items/{item['id']}")

    word = "all" if clear_all else "checked"
    if output == OutputFormat.json:
        output_json({"cleared": len(items), "type": word})
        return
    console.print(f"\n[green]✅  Cleared {len(items)} {word} item(s).[/]\n")
