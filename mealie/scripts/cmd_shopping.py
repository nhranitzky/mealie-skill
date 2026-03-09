"""
mealie shopping – Manage Mealie shopping lists.

Subcommands:
  lists              Show all shopping lists
  show  <list-id>    Show items in a list
  add   <list-id> <item>  Add a text item
  recipe <list-id> <slug> Link a recipe (adds all ingredients)
  check  <item-id>   Toggle an item's checked state
  clear  <list-id>   Remove all checked items
"""

from __future__ import annotations

import sys

import click
from rich.table import Table
from rich.text import Text
from rich import box

from scripts.utils import console, MealieClient, output_json


# ── group ────────────────────────────────────────────────────────────────────

@click.group()
def shopping():
    """Manage Mealie shopping lists."""


@shopping.command("lists")
@click.option("--json", "as_json", is_flag=True, default=False)
def list_lists(as_json: bool):
    """Show all shopping lists."""
    client = MealieClient()
    data   = client.get("/households/shopping/lists")
    items  = data.get("items", [])

    if as_json:
        output_json(items)
        return

    table = Table(title="Shopping Lists", box=box.ROUNDED,
                  header_style="bold cyan", show_header=True)
    table.add_column("ID",   style="dim",  width=36, no_wrap=True)
    table.add_column("Name", min_width=24)
    table.add_column("Items", justify="right", width=7)

    for lst in items:
        n_items = len(lst.get("listItems") or [])
        table.add_row(lst.get("id", "?"), lst.get("name", "?"), str(n_items))

    console.print()
    console.print(table)
    console.print()


@shopping.command("show")
@click.argument("list_id")
@click.option("--checked",  is_flag=True, default=False, help="Show checked items too.")
@click.option("--json",     "as_json", is_flag=True, default=False)
def show_list(list_id: str, checked: bool, as_json: bool):
    """
    Show items in a shopping list.

    \b
    Example:
        mealie shopping show <list-id>
        mealie shopping show <list-id> --checked
    """
    client = MealieClient()
    params = {"perPage": 200, "orderBy": "position"}
    if not checked:
        params["checked"] = "false"
    data   = client.get(f"/households/shopping/items", {**params, "shoppingListId": list_id})
    items  = data.get("items", [])

    if as_json:
        output_json(items)
        return

    list_info = client.get(f"/households/shopping/lists/{list_id}")
    list_name = list_info.get("name", list_id)

    table = Table(
        title=f"Shopping List: {list_name}",
        box=box.ROUNDED, show_header=True, header_style="bold cyan",
    )
    table.add_column("",      width=3)           # check mark
    table.add_column("Item",  min_width=28)
    table.add_column("Qty",   justify="right", width=8)
    table.add_column("Unit",  width=10)
    table.add_column("Note",  style="dim", min_width=18)

    for item in items:
        is_checked = item.get("checked", False)
        check = Text("✓", style="green") if is_checked else Text("○", style="dim")
        food  = (item.get("food") or {}).get("name") or item.get("note") or "?"
        qty   = str(item.get("quantity") or "")
        unit  = (item.get("unit") or {}).get("name") or ""
        note  = item.get("note") or ""
        style = "dim" if is_checked else ""
        table.add_row(check, Text(food, style=style), qty, unit, note)

    console.print()
    if not items:
        console.print("[yellow]Shopping list is empty.[/]")
    else:
        console.print(table)
    console.print()


@shopping.command("add")
@click.argument("list_id")
@click.argument("item_text")
@click.option("--qty",  "-q", default=None, type=float, help="Quantity.")
@click.option("--unit", "-u", default=None, help="Unit (e.g. 'kg', 'g', 'ml').")
@click.option("--json", "as_json", is_flag=True, default=False)
def add_item(list_id: str, item_text: str, qty: float | None, unit: str | None, as_json: bool):
    """
    Add a text item to a shopping list.

    \b
    Examples:
        mealie shopping add <list-id> "Olive oil"
        mealie shopping add <list-id> Milk --qty 2 --unit litre
    """
    client = MealieClient()
    body: dict = {
        "shoppingListId": list_id,
        "note":           item_text,
        "isFood":         False,
        "checked":        False,
    }
    if qty is not None:
        body["quantity"] = qty
    if unit:
        body["unitValue"] = unit

    result = client.post("/households/shopping/items", body)
    if as_json:
        output_json(result)
        return
    console.print(f"\n[green]✅  Added:[/] {item_text}\n")


@shopping.command("recipe")
@click.argument("list_id")
@click.argument("recipe_slug")
@click.option("--servings", "-s", default=None, type=int,
              help="Override servings (uses recipe default otherwise).")
@click.option("--json", "as_json", is_flag=True, default=False)
def add_recipe(list_id: str, recipe_slug: str, servings: int | None, as_json: bool):
    """
    Add all ingredients of RECIPE_SLUG to a shopping list.

    \b
    Example:
        mealie shopping recipe <list-id> pasta-carbonara
        mealie shopping recipe <list-id> spaghetti-bolognese --servings 4
    """
    client = MealieClient()
    recipe = client.get(f"/recipes/{recipe_slug}")
    if not recipe:
        console.print(f"[red]Recipe not found:[/] {recipe_slug!r}")
        sys.exit(1)

    recipe_id = recipe.get("id")
    body: dict = {"id": list_id, "recipes": [{"id": recipe_id}]}
    if servings is not None:
        body["recipes"][0]["recipeIncrementQuantity"] = servings

    result = client.post(f"/households/shopping/lists/{list_id}/recipe", body)
    if as_json:
        output_json(result)
        return
    console.print(
        f"\n[green]✅  Ingredients of[/] [bold]{recipe['name']}[/] "
        f"added to shopping list.\n"
    )


@shopping.command("clear")
@click.argument("list_id")
@click.option("--all", "clear_all", is_flag=True, default=False,
              help="Remove ALL items (not just checked ones).")
@click.option("--json", "as_json", is_flag=True, default=False)
def clear_list(list_id: str, clear_all: bool, as_json: bool):
    """
    Remove checked items from a shopping list.
    Use --all to wipe the entire list.
    """
    client = MealieClient()
    params = {"shoppingListId": list_id, "perPage": 500}
    if not clear_all:
        params["checked"] = "true"
    data  = client.get("/households/shopping/items", params)
    items = data.get("items", [])

    if not items:
        if as_json:
            output_json({"cleared": 0})
        else:
            console.print("[yellow]Nothing to clear.[/]")
        return

    for item in items:
        client.delete(f"/households/shopping/items/{item['id']}")

    word = "all" if clear_all else "checked"
    if as_json:
        output_json({"cleared": len(items), "type": word})
        return
    console.print(f"\n[green]✅  Cleared {len(items)} {word} item(s).[/]\n")


@shopping.command("check")
@click.argument("item_id")
@click.option("--json", "as_json", is_flag=True, default=False)
def check_item(item_id: str, as_json: bool):
    """
    Toggle the checked state of a shopping list item.

    \b
    Example:
        mealie shopping check <item-id>
    """
    client = MealieClient()
    item = client.get(f"/households/shopping/items/{item_id}")
    new_state = not item.get("checked", False)
    result = client.patch(f"/households/shopping/items/{item_id}", {"checked": new_state})
    if as_json:
        output_json(result)
        return
    state_label = "[green]checked[/]" if new_state else "[yellow]unchecked[/]"
    food = (item.get("food") or {}).get("name") or item.get("note") or item_id
    console.print(f"\n[green]✅[/] {food!r} marked as {state_label}.\n")
