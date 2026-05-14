from __future__ import annotations

import textwrap
from typing import Any

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

console = Console()


def recipe_list_table(recipes: list[dict[str, Any]], title: str = "Recipes") -> Table:
    t = Table(title=title, box=box.ROUNDED, show_header=True,
              header_style="bold cyan", show_lines=False)
    t.add_column("#",          justify="right", width=4,  style="dim")
    t.add_column("Name",       min_width=28)
    t.add_column("Slug",       min_width=20, style="dim")
    t.add_column("Categories", min_width=18, style="green")
    t.add_column("Tags",       min_width=18, style="blue")
    t.add_column("Rating",     justify="right", width=8)

    for i, r in enumerate(recipes, 1):
        cats   = ", ".join(c["name"] for c in (r.get("recipeCategory") or []))
        tags   = ", ".join(tg["name"] for tg in (r.get("tags") or []))
        rating = r.get("rating")
        stars  = f"{'★' * int(rating)}{'☆' * (5 - int(rating))}" if rating else "-"
        t.add_row(str(i), r.get("name", "?"), r.get("slug", "?"),
                  cats or "-", tags or "-", stars)
    return t


def print_recipe_detail(recipe: dict[str, Any], base_url: str) -> None:
    name       = recipe.get("name") or "?"
    slug       = recipe.get("slug") or ""
    desc       = recipe.get("description") or ""
    yield_qty  = recipe.get("recipeYield") or ""
    total_time = recipe.get("totalTime") or recipe.get("cookTime") or ""
    prep_time  = recipe.get("prepTime") or ""
    rating     = recipe.get("rating")
    cats       = [c["name"] for c in (recipe.get("recipeCategory") or [])]
    tags       = [tg["name"] for tg in (recipe.get("tags") or [])]
    source_url = recipe.get("orgURL") or ""

    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="bold dim", no_wrap=True)
    meta.add_column()

    if desc:
        meta.add_row("📝 Description", textwrap.fill(desc, 72))
    if yield_qty:
        meta.add_row("🍽️  Yield",      yield_qty)
    if prep_time:
        meta.add_row("⏱️  Prep time",  prep_time)
    if total_time:
        meta.add_row("⏰ Total time",  total_time)
    if cats:
        meta.add_row("📁 Categories", ", ".join(cats))
    if tags:
        meta.add_row("🏷️  Tags",       ", ".join(tags))
    if rating:
        stars = f"{'★' * int(rating)}{'☆' * (5 - int(rating))}"
        meta.add_row("⭐ Rating",      f"{stars} ({rating})")
    if source_url:
        meta.add_row("🔗 Source",      source_url)
    meta.add_row("🌐 Mealie URL",    f"{base_url}/recipe/{slug}")

    ingredients = recipe.get("recipeIngredient") or []
    ing_lines: list[str] = []
    for ing in ingredients:
        if isinstance(ing, dict):
            qty  = ing.get("quantity") or ""
            unit = (ing.get("unit") or {}).get("name") or ing.get("unitValue") or ""
            food = (ing.get("food") or {}).get("name") or ing.get("note") or ""
            note = ing.get("note") or ""
            ing_parts = " ".join(str(p) for p in [qty, unit, food] if p)
            if note and note != food:
                ing_parts += f" ({note})"
            ing_lines.append(f"  • {ing_parts.strip()}" if ing_parts.strip() else f"  • {note}")
        else:
            ing_lines.append(f"  • {ing}")

    instructions = recipe.get("recipeInstructions") or []
    step_lines: list[str] = []
    for i, step in enumerate(instructions, 1):
        text = step.get("text") or step.get("title") or "" if isinstance(step, dict) else str(step)
        if text:
            wrapped = textwrap.fill(text, 74, subsequent_indent="     ")
            step_lines.append(f"  {i:2}. {wrapped}")

    parts: list[Any] = [meta]
    if ing_lines:
        parts += [Rule("Ingredients", style="dim"), Text("\n".join(ing_lines))]
    if step_lines:
        parts += [Rule("Instructions", style="dim"), Text("\n".join(step_lines))]

    console.print()
    console.print(Panel(Group(*parts), title=f"[bold green]🍴 {name}[/]", expand=False))
    console.print()
