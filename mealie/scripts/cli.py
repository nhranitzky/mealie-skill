from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Annotated, Any, cast

import click
import typer

from .core.client import MealieClient, MealieHTTPError
from .core.display import console, print_recipe_detail, recipe_list_table
from .core.mealplan import app as mealplan_app
from .core.organizers import app as organizers_app
from .core.shopping import app as shopping_app
from .output import OutputFormat, output_json, render_error

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    help="Mealie CLI - manage your self-hosted recipe server from the terminal.",
)
app.add_typer(mealplan_app, name="mealplan")
app.add_typer(shopping_app, name="shopping")
app.add_typer(organizers_app, name="organizers")

OutputOption = Annotated[
    OutputFormat,
    typer.Option("--output", "-o", help="Output format: text or json."),
]


# ── list ──────────────────────────────────────────────────────────────────────

@app.command("list")
def list_recipes(
    limit: Annotated[int, typer.Option("--limit", "-n", help="Recipes per page.")] = 25,
    page: Annotated[int, typer.Option("--page", "-p", help="Page number.")] = 1,
    category: Annotated[
        str | None, typer.Option("--category", "-c", help="Filter by category.")
    ] = None,
    tag: Annotated[str | None, typer.Option("--tag", "-t", help="Filter by tag.")] = None,
    search: Annotated[
        str | None, typer.Option("--search", "-s", help="Full-text search.")
    ] = None,
    sort: Annotated[str, typer.Option(help="Sort field.")] = "name",
    desc: Annotated[bool, typer.Option("--desc/--asc", help="Sort descending.")] = False,
    fetch_all: Annotated[bool, typer.Option("--all", help="Fetch ALL recipes.")] = False,
    output: OutputOption = OutputFormat.text,
) -> None:
    """List recipes from Mealie."""
    client = MealieClient()
    params: dict[str, Any] = {"orderBy": sort, "orderDirection": "desc" if desc else "asc"}
    if search:
        params["search"] = search
    if category:
        params["categories"] = category
    if tag:
        params["tags"] = tag

    try:
        if fetch_all:
            recipes = client.get_all_pages("/recipes", params)
            total, page_total = len(recipes), 1
        else:
            params.update({"page": page, "perPage": limit})
            data = client.get("/recipes", params)
            recipes = data.get("items", [])
            total = data.get("total", 0)
            page_total = data.get("totalPages", 1)
    except MealieHTTPError as exc:
        render_error(str(exc), output, code=str(exc.status_code))

    if output == OutputFormat.json:
        output_json(recipes)
        return

    filters = " · ".join(f for f in [
        f"search={search!r}" if search else "",
        f"category={category!r}" if category else "",
        f"tag={tag!r}" if tag else "",
    ] if f)
    title = f"Recipes - {total} total" + (f" ({filters})" if filters else "")

    console.print()
    console.print(recipe_list_table(recipes, title=title))
    if not fetch_all:
        console.print(f"  [dim]Page {page} of {page_total}  ·  Use --page / --limit to navigate[/]")
    console.print()


# ── detail ────────────────────────────────────────────────────────────────────

def _find_recipe(client: MealieClient, identifier: str) -> Any:
    try:
        return client.get(f"/recipes/{identifier}")
    except MealieHTTPError as exc:
        if exc.status_code != 404:
            raise

    data = client.get("/recipes", {"search": identifier, "perPage": 5})
    items = data.get("items", [])
    if not items:
        console.print(f"[red]No recipe found for:[/] {identifier!r}")
        sys.exit(1)
    if len(items) == 1:
        return client.get(f"/recipes/{items[0]['slug']}")

    console.print(f"\n[yellow]Multiple matches for {identifier!r}:[/]")
    for i, r in enumerate(items, 1):
        console.print(f"  {i}. {r['name']}  [dim]({r['slug']})[/]")
    choice = typer.prompt("Enter number", type=int)
    if not 1 <= choice <= len(items):
        console.print("[red]Invalid choice.[/]")
        sys.exit(1)
    return client.get(f"/recipes/{items[choice - 1]['slug']}")


@app.command("detail")
def detail(
    recipe: Annotated[str, typer.Argument(help="Recipe slug or partial name.")],
    output: OutputOption = OutputFormat.text,
) -> None:
    """Show full RECIPE details (ingredients, steps, metadata)."""
    client = MealieClient()
    try:
        data = _find_recipe(client, recipe)
    except MealieHTTPError as exc:
        render_error(str(exc), output, code=str(exc.status_code))

    if output == OutputFormat.json:
        output_json(data)
        return
    print_recipe_detail(data, client.base_url)


# ── search ────────────────────────────────────────────────────────────────────

@app.command("search")
def search_cmd(
    query: Annotated[list[str], typer.Argument(help="Search terms.")],
    category: Annotated[str | None, typer.Option("--category", "-c")] = None,
    tag: Annotated[str | None, typer.Option("--tag", "-t")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n")] = 20,
    open_first: Annotated[
        bool, typer.Option("--open", "-o", help="Auto-open single result.")
    ] = False,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Search recipes in Mealie by QUERY (full-text)."""
    q = " ".join(query)
    client = MealieClient()
    params: dict[str, Any] = {"search": q, "perPage": limit, "page": 1}
    if category:
        params["categories"] = category
    if tag:
        params["tags"] = tag

    try:
        data = client.get("/recipes", params)
        items = data.get("items", [])
        total = data.get("total", 0)
    except MealieHTTPError as exc:
        render_error(str(exc), output, code=str(exc.status_code))

    if output == OutputFormat.json:
        output_json(items)
        return

    if not items:
        console.print(f"\n[yellow]No recipes found for:[/] {q!r}\n")
        return

    console.print()
    console.print(recipe_list_table(items, title=f"Search: {q!r}  -  {total} match(es)"))
    console.print()

    if open_first and len(items) == 1:
        full = client.get(f"/recipes/{items[0]['slug']}")
        print_recipe_detail(full, client.base_url)
    elif open_first:
        console.print(
            "[dim]Use --open with a more specific query to auto-open a single result.[/]\n"
        )


# ── import ────────────────────────────────────────────────────────────────────

@app.command("import")
def import_url(
    url: Annotated[str, typer.Argument(help="Recipe website URL.")],
    tags: Annotated[
        list[str] | None, typer.Option("--tag", "-t", help="Assign tag (repeatable).")
    ] = None,
    show_detail: Annotated[bool, typer.Option("--open", help="Show detail after import.")] = False,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Import a recipe from a website URL into Mealie."""
    client = MealieClient()
    console.print(f"\n[dim]Importing from:[/] {url} ...")
    body: dict[str, Any] = {"url": url, "includeTags": True}
    if tags:
        body["tags"] = [{"name": t} for t in tags]

    try:
        slug = client.post("/recipes/create/url", body)
    except MealieHTTPError as exc:
        render_error(str(exc), output, code=str(exc.status_code))

    if output == OutputFormat.json:
        output_json({"url": url, "slug": slug})
        return

    console.print(f"[bold green]✅  Recipe imported![/]  slug=[bold]{slug}[/]\n"
                  f"  🌐 {client.base_url}/recipe/{slug}")
    if show_detail:
        print_recipe_detail(client.get(f"/recipes/{slug}"), client.base_url)
    else:
        console.print()


# ── import-json ───────────────────────────────────────────────────────────────

def _read_json_from_file(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in (".html", ".htm"):
        pattern = re.compile(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            re.DOTALL | re.IGNORECASE,
        )
        match = pattern.search(text)
        if not match:
            console.print('[red]No <script type="application/ld+json"> block found in HTML.[/]')
            sys.exit(1)
        text = match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        console.print(f"[red]JSON parse error:[/] {exc}")
        sys.exit(1)


@app.command("import-json")
def import_json_file(
    file: Annotated[Path, typer.Argument(help="schema.org/Recipe JSON or HTML file.")],
    tags: Annotated[list[str] | None, typer.Option("--tag", "-t")] = None,
    show_detail: Annotated[bool, typer.Option("--open", help="Show detail after import.")] = False,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Import a recipe from a local schema.org/Recipe JSON file."""
    if not file.exists():
        render_error(f"File not found: {file}", output)

    client = MealieClient()
    console.print(f"\n[dim]Reading:[/] {file} ...")
    raw_content = _read_json_from_file(file)
    console.print("[dim]Sending to Mealie (POST /api/recipes/create/html-or-json) ...[/]")

    try:
        result = client.post(
            "/recipes/create/html-or-json",
            {"data": json.dumps(raw_content, ensure_ascii=False)},
        )
    except MealieHTTPError as exc:
        render_error(str(exc), output, code=str(exc.status_code))

    slug = (
        result.strip().strip('"') if isinstance(result, str) else result.get("slug") or str(result)
    )

    if tags:
        existing = client.get(f"/recipes/{slug}")
        existing_tags = existing.get("tags") or []
        client.patch(f"/recipes/{slug}", {"tags": existing_tags + [{"name": t} for t in tags]})

    if output == OutputFormat.json:
        output_json({"file": str(file), "slug": slug})
        return

    console.print(f"[bold green]✅  Recipe imported![/]  slug=[bold]{slug}[/]\n"
                  f"  🌐 {client.base_url}/recipe/{slug}")
    if show_detail:
        print_recipe_detail(client.get(f"/recipes/{slug}"), client.base_url)
    else:
        console.print()


# ── random ────────────────────────────────────────────────────────────────────

@app.command("random")
def random_recipe(
    category: Annotated[str | None, typer.Option("--category", "-c")] = None,
    tag: Annotated[str | None, typer.Option("--tag", "-t")] = None,
    count: Annotated[int, typer.Option("--count", "-n")] = 1,
    show_detail: Annotated[
        bool, typer.Option("--open", help="Show detail of first pick.")
    ] = False,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Suggest a random recipe from your Mealie collection."""
    client = MealieClient()
    params: dict[str, Any] = {}
    if category:
        params["categories"] = category
    if tag:
        params["tags"] = tag

    try:
        all_recipes = client.get_all_pages("/recipes", params)
    except MealieHTTPError as exc:
        render_error(str(exc), output, code=str(exc.status_code))

    if not all_recipes:
        console.print("[yellow]No recipes found with the given filters.[/]")
        return

    picks = random.sample(all_recipes, min(count, len(all_recipes)))

    if output == OutputFormat.json:
        output_json(picks)
        return

    console.print()
    for i, r in enumerate(picks, 1):
        cats = ", ".join(c["name"] for c in (r.get("recipeCategory") or []))
        tags = ", ".join(tg["name"] for tg in (r.get("tags") or []))
        label = "🎲 Random pick" if count == 1 else f"🎲 Pick {i}"
        console.print(
            f"[bold]{label}:[/]  [green]{r.get('name', '?')}[/]  [dim]({r.get('slug', '?')})[/]\n"
            + (f"  [dim]Categories:[/] {cats}\n" if cats else "")
            + (f"  [dim]Tags:[/]       {tags}\n" if tags else "")
            + f"  [dim]URL:[/]         {client.base_url}/recipe/{r.get('slug', '?')}"
        )
        console.print()

    if show_detail and picks:
        print_recipe_detail(client.get(f"/recipes/{picks[0]['slug']}"), client.base_url)


# ── stats ─────────────────────────────────────────────────────────────────────

@app.command("stats")
def stats(
    top: Annotated[int, typer.Option("--top", "-n", help="Number of top categories/tags.")] = 10,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Display statistics about your Mealie recipe collection."""
    from rich import box
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    client = MealieClient()
    console.print("[dim]Loading recipes ...[/]")

    try:
        all_recipes = client.get_all_pages("/recipes", {"orderBy": "name"})
    except MealieHTTPError as exc:
        render_error(str(exc), output, code=str(exc.status_code))

    cat_counter: Counter[str] = Counter()
    tag_counter: Counter[str] = Counter()
    for r in all_recipes:
        for cat in r.get("recipeCategory") or []:
            if name := cat.get("name") or cat.get("slug"):
                cat_counter[name] += 1
        for tg in r.get("tags") or []:
            if name := tg.get("name") or tg.get("slug"):
                tag_counter[name] += 1

    cats_data = client.get("/organizers/categories", {"perPage": 1})
    tags_data = client.get("/organizers/tags", {"perPage": 1})
    total_cats = cats_data.get("total", len(cat_counter))
    total_tags = tags_data.get("total", len(tag_counter))

    try:
        app_info = client.get("/app/about")
    except (MealieHTTPError, SystemExit):
        app_info = {}

    if output == OutputFormat.json:
        output_json({
            "total_recipes": len(all_recipes),
            "total_categories": total_cats,
            "total_tags": total_tags,
            "top_categories": [{"name": n, "count": c} for n, c in cat_counter.most_common(top)],
            "top_tags": [{"name": n, "count": c} for n, c in tag_counter.most_common(top)],
            "server": app_info,
        })
        return

    overview = Text()
    overview.append("  📚 Total recipes:    ", style="bold")
    overview.append(f"{len(all_recipes)}\n")
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

    if top_cats := cat_counter.most_common(top):
        t = Table(title=f"Top {top} Categories", box=box.SIMPLE, header_style="bold cyan")
        t.add_column("Category", style="green")
        t.add_column("Recipes", justify="right", style="bold")
        for name, cnt in top_cats:
            t.add_row(name, str(cnt))
        console.print(t)

    if top_tags := tag_counter.most_common(top):
        t = Table(title=f"Top {top} Tags", box=box.SIMPLE, header_style="bold cyan")
        t.add_column("Tag", style="blue")
        t.add_column("Recipes", justify="right", style="bold")
        for name, cnt in top_tags:
            t.add_row(name, str(cnt))
        console.print(t)

    console.print()


# ── schema ────────────────────────────────────────────────────────────────────

@app.command("schema", hidden=True)
def schema_cmd() -> None:
    """Output a JSON schema of all commands for skill generation."""
    click_app = cast(click.Group, typer.main.get_command(app))

    def _param(p: click.Parameter) -> dict[str, Any]:
        type_obj = p.type
        type_name = getattr(type_obj, "name", str(type_obj))
        choices = None
        if isinstance(type_obj, click.Choice):
            choices = list(type_obj.choices)
            type_name = "choice"
        default = p.default() if callable(p.default) else p.default
        return {
            "name": p.name,
            "type": type_name,
            "required": p.required,
            "default": default,
            "help": getattr(p, "help", None),
            "choices": choices,
        }

    def _cmd(name: str, cmd: click.Command) -> dict[str, Any]:
        entry: dict[str, Any] = {"name": name, "help": cmd.help or ""}
        if isinstance(cmd, click.Group):
            entry["subcommands"] = [
                _cmd(sub_name, cmd.commands[sub_name])
                for sub_name in cmd.commands
            ]
        else:
            entry["params"] = [_param(p) for p in cmd.params if p.name != "help"]
        return entry

    schema: dict[str, Any] = {
        "cli": "mealie-cli",
        "launcher": "bin/mealie-cli",
        "commands": [
            _cmd(name, click_app.commands[name])
            for name in click_app.commands
            if not click_app.commands[name].hidden
        ],
    }
    print(json.dumps(schema, indent=2, ensure_ascii=False))


def main() -> None:
    app(prog_name="mealie-cli")
