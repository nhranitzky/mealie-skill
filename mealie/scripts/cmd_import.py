"""
mealie import      – Import a recipe from a website URL.
mealie import-json – Import a recipe from a local schema.org/Recipe JSON file.

The JSON import uses Mealie's  POST /api/recipes/create/html-or-json  endpoint.
The body must be  {"data": "<json-as-string>"}  – i.e. the JSON content is
serialised to a string and placed in the "data" key.  Mealie handles all
schema.org → internal-format parsing on the server side.

Accepted file formats:
  .json / .jsonld   – raw JSON
  .html / .htm      – first <script type="application/ld+json"> block extracted
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import click

from scripts.utils import console, MealieClient, output_json, print_recipe_detail


# ═══════════════════════════════════════════════════════════════════════════════
# URL import
# ═══════════════════════════════════════════════════════════════════════════════

@click.command("import")
@click.argument("url")
@click.option("--tag", "-t", "tags", multiple=True,
              help="Assign a tag to the imported recipe (repeatable).")
@click.option("--open", "-o", "show_detail", is_flag=True, default=False,
              help="Show full recipe detail after import.")
@click.option("--json", "as_json", is_flag=True, default=False)
def import_url(url: str, tags: tuple[str, ...], show_detail: bool, as_json: bool):
    """
    Import a recipe from a website URL into Mealie.

    Mealie's built-in scraper supports hundreds of recipe sites
    (Chefkoch, Allrecipes, BBC Good Food, NYT Cooking, and many more).

    \b
    Examples:
        mealie import https://www.chefkoch.de/rezepte/12345/Spaghetti.html
        mealie import https://example.com/recipe --tag Italian --tag Pasta
        mealie import https://example.com/recipe --open
    """
    client = MealieClient()
    console.print(f"\n[dim]Importing from:[/] {url} ...")

    body: dict = {"url": url, "includeTags": True}
    if tags:
        body["tags"] = [{"name": t} for t in tags]

    slug = client.post("/recipes/create/url", body)

    if as_json:
        output_json({"url": url, "slug": slug})
        return

    console.print(
        f"[bold green]✅  Recipe imported![/]  slug=[bold]{slug}[/]\n"
        f"  🌐 {client.base_url}/recipe/{slug}"
    )
    if show_detail:
        recipe = client.get(f"/recipes/{slug}")
        print_recipe_detail(recipe, client.base_url)
    else:
        console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# JSON file import  (1:1 passthrough to Mealie)
# ═══════════════════════════════════════════════════════════════════════════════

def _read_json_from_file(path: Path) -> dict | list:
    """
    Read and return the JSON payload from a file.

    .json / .jsonld  – parsed as-is.
    .html / .htm     – the FIRST <script type="application/ld+json"> block is extracted.
    """
    text   = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix in (".html", ".htm"):
        pattern = re.compile(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            re.DOTALL | re.IGNORECASE,
        )
        match = pattern.search(text)
        if not match:
            console.print("[red]No <script type=\"application/ld+json\"> block found in HTML.[/]")
            sys.exit(1)
        text = match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        console.print(f"[red]JSON parse error:[/] {exc}")
        sys.exit(1)


@click.command("import-json")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--open", "-o", "show_detail", is_flag=True, default=False,
              help="Show full recipe detail after import.")
@click.option("--json", "as_json", is_flag=True, default=False)
def import_json(file: Path, show_detail: bool, as_json: bool):
    """
    Import a recipe from a local schema.org/Recipe JSON file into Mealie.

    Uses POST /api/recipes/create/html-or-json.  The JSON is serialised to a
    string and sent as {"data": "<json-string>"}.  Mealie handles all
    schema.org → internal-format conversion on the server side.

    \b
    Accepted file formats:
      .json / .jsonld   raw schema.org/Recipe JSON
      .html / .htm      page saved locally – first ld+json block is used

    \b
    Examples:
        mealie import-json recipe.json
        mealie import-json recipe.jsonld --open
        mealie import-json saved_page.html --json
    """
    client = MealieClient()
    console.print(f"\n[dim]Reading:[/] {file} ...")

    # Read the file; extract ld+json block from HTML if needed
    raw_content = _read_json_from_file(file)

    # Mealie expects {"data": "<serialised-json-string>"}
    # The server parses the string as schema.org JSON internally
    data_string = json.dumps(raw_content, ensure_ascii=False)
    body = {"data": data_string}

    console.print("[dim]Sending to Mealie (POST /api/recipes/create/html-or-json) …[/]")
    result = client.post("/recipes/create/html-or-json", body)

    # Response is a plain slug string (possibly with surrounding quotes)
    if isinstance(result, str):
        slug = result.strip().strip('"')
    elif isinstance(result, dict):
        slug = result.get("slug") or result.get("id") or str(result)
    else:
        slug = str(result)

    if as_json:
        output_json({"file": str(file), "slug": slug})
        return

    console.print(
        f"[bold green]✅  Recipe imported![/]  slug=[bold]{slug}[/]\n"
        f"  🌐 {client.base_url}/recipe/{slug}"
    )
    if show_detail:
        recipe = client.get(f"/recipes/{slug}")
        print_recipe_detail(recipe, client.base_url)
    else:
        console.print()
