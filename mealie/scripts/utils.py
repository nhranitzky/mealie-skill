"""
Shared utilities for the Mealie CLI.

Provides:
- MealieClient   : thin HTTP wrapper (reads MEALIE_URL + MEALIE_API_TOKEN from .env)
- output_json    : pretty-print sanitised JSON
- console        : shared Rich Console
- Rich table / panel helpers for recipes, meal plans, shopping lists
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Any

import requests
 
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
 

console = Console()

# ---------------------------------------------------------------------------
# Configuration – loaded once from .env
# ---------------------------------------------------------------------------

def _load_config() -> tuple[str, str]:
    """Return (base_url, api_token) from the .env file."""
 
    url   = os.environ.get("MEALIE_URL", "").rstrip("/")
    token = os.environ.get("MEALIE_API_TOKEN", "").strip()

    missing: list[str] = []
    if not url:
        missing.append("MEALIE_URL")
    if not token or token == "your-api-token-here":
        missing.append("MEALIE_API_TOKEN")

    if missing:
        console.print(
            f"[bold red]Missing configuration:[/] {', '.join(missing)}\n"
            f"Edit [bold].env[/] and set the required values.\n"
            "Create an API token in Mealie under Settings → API Tokens."
        )
        sys.exit(1)

    return url, token


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

class MealieClient:
    """
    Lightweight wrapper around the Mealie REST API.

    The token is stored internally and never echoed or returned to callers
    in a way that could be forwarded to an LLM.
    """

    def __init__(self) -> None:
        self._base, _token = _load_config()
        self._headers = {
            "Authorization": f"Bearer {_token}",
            "Accept":        "application/json",
            "Content-Type":  "application/json",
        }

    # ── low-level ────────────────────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self._base}/api{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        try:
            r = requests.request(method, self._url(path), headers=self._headers, **kwargs)
            r.raise_for_status()
            return r
        except requests.HTTPError as exc:
            _http_error(exc)
        except requests.RequestException as exc:
            console.print(f"[red]Network error:[/] {exc}")
            sys.exit(1)

    def get(self, path: str, params: dict | None = None) -> Any:
        return self._request("GET", path, params=params, timeout=15).json()

    def post(self, path: str, body: dict | None = None) -> Any:
        r = self._request("POST", path, json=body, timeout=30)
        ct = r.headers.get("Content-Type", "")
        if "json" in ct:
            return r.json()
        return r.text.strip().strip('"')   # slug returned as plain string

    def put(self, path: str, body: dict) -> Any:
        r = self._request("PUT", path, json=body, timeout=15)
        return r.json() if r.content else {}

    def patch(self, path: str, body: dict) -> Any:
        r = self._request("PATCH", path, json=body, timeout=15)
        return r.json() if r.content else {}

    def delete(self, path: str) -> None:
        self._request("DELETE", path, timeout=15)

    # ── high-level helpers ───────────────────────────────────────────────────

    def get_all_pages(self, path: str, params: dict | None = None) -> list[dict]:
        """Fetch all pages for a paginated endpoint and return combined items."""
        p = dict(params or {})
        p.setdefault("perPage", 50)
        p["page"] = 1
        items: list[dict] = []
        while True:
            data = self.get(path, params=p)
            chunk = data.get("items", [])
            items.extend(chunk)
            if len(items) >= data.get("total", 0):
                break
            p["page"] += 1
        return items

    @property
    def base_url(self) -> str:
        return self._base


def _http_error(exc: requests.HTTPError) -> None:
    resp = exc.response
    status = resp.status_code if resp is not None else "?"
    try:
        detail = resp.json().get("detail", resp.text[:200])
    except Exception:
        detail = str(exc)
    console.print(f"[bold red]HTTP {status}:[/] {detail}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def output_json(data: Any) -> None:
    """Dump sanitised data as indented JSON to stdout."""
    print(json.dumps(_sanitise(data), indent=2, ensure_ascii=False))


def _sanitise(obj: Any) -> Any:
    """Recursively strip fields that look like tokens / passwords."""
    _BAD = {"token", "password", "secret", "api_key", "apikey"}
    if isinstance(obj, dict):
        return {k: _sanitise(v) for k, v in obj.items()
                if k.lower() not in _BAD and "token" not in k.lower()}
    if isinstance(obj, list):
        return [_sanitise(i) for i in obj]
    return obj


# ---------------------------------------------------------------------------
# Rich display helpers
# ---------------------------------------------------------------------------

def recipe_list_table(recipes: list[dict], title: str = "Recipes") -> Table:
    """Return a Rich table for a list of recipe summaries."""
    t = Table(title=title, box=box.ROUNDED, show_header=True,
              header_style="bold cyan", show_lines=False)
    t.add_column("#",           justify="right", width=4,  style="dim")
    t.add_column("Name",        min_width=28)
    t.add_column("Slug",        min_width=20, style="dim")
    t.add_column("Categories",  min_width=18, style="green")
    t.add_column("Tags",        min_width=18, style="blue")
    t.add_column("Rating",      justify="right", width=8)

    for i, r in enumerate(recipes, 1):
        cats = ", ".join(c["name"] for c in (r.get("recipeCategory") or []))
        tags = ", ".join(t_["name"] for t_ in (r.get("tags") or []))
        rating = r.get("rating")
        stars = (f"{'★' * int(rating)}{'☆' * (5 - int(rating))}" if rating else "–")
        t.add_row(str(i), r.get("name", "?"), r.get("slug", "?"),
                  cats or "–", tags or "–", stars)
    return t


def print_recipe_detail(recipe: dict, base_url: str) -> None:
    """Render a full recipe as a rich panel."""
    name       = recipe.get("name") or "?"
    slug       = recipe.get("slug") or ""
    desc       = recipe.get("description") or ""
    yield_qty  = recipe.get("recipeYield") or ""
    total_time = recipe.get("totalTime") or recipe.get("cookTime") or ""
    prep_time  = recipe.get("prepTime") or ""
    rating     = recipe.get("rating")
    cats       = [c["name"] for c in (recipe.get("recipeCategory") or [])]
    tags       = [t["name"] for t in (recipe.get("tags") or [])]
    source_url = recipe.get("orgURL") or ""

    # ── metadata grid ────────────────────────────────────────────────────────
    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="bold dim", no_wrap=True)
    meta.add_column()

    if desc:
        meta.add_row("📝 Description", textwrap.fill(desc, 72))
    if yield_qty:
        meta.add_row("🍽️  Yield",      yield_qty)
    if prep_time:
        meta.add_row("⏱️  Prep time",   prep_time)
    if total_time:
        meta.add_row("⏰ Total time",   total_time)
    if cats:
        meta.add_row("📁 Categories",  ", ".join(cats))
    if tags:
        meta.add_row("🏷️  Tags",        ", ".join(tags))
    if rating:
        stars = f"{'★' * int(rating)}{'☆' * (5 - int(rating))}"
        meta.add_row("⭐ Rating",       f"{stars} ({rating})")
    if source_url:
        meta.add_row("🔗 Source",       source_url)
    meta.add_row("🌐 Mealie URL",    f"{base_url}/recipe/{slug}")

    # ── ingredients ──────────────────────────────────────────────────────────
    ingredients = recipe.get("recipeIngredient") or []
    ing_lines: list[str] = []
    for ing in ingredients:
        if isinstance(ing, dict):
            qty   = ing.get("quantity") or ""
            unit  = (ing.get("unit") or {}).get("name") or ing.get("unitValue") or ""
            food  = (ing.get("food") or {}).get("name") or ing.get("note") or ""
            note  = ing.get("note") or ""
            parts = " ".join(str(p) for p in [qty, unit, food] if p)
            if note and note != food:
                parts += f" ({note})"
            ing_lines.append(f"  • {parts.strip()}" if parts.strip() else f"  • {note}")
        else:
            ing_lines.append(f"  • {ing}")

    # ── instructions ─────────────────────────────────────────────────────────
    instructions = recipe.get("recipeInstructions") or []
    step_lines: list[str] = []
    for i, step in enumerate(instructions, 1):
        if isinstance(step, dict):
            text = step.get("text") or step.get("title") or ""
        else:
            text = str(step)
        if text:
            wrapped = textwrap.fill(text, 74, subsequent_indent="     ")
            step_lines.append(f"  {i:2}. {wrapped}")

    # ── compose panel ─────────────────────────────────────────────────────────
    from rich.rule import Rule
    from rich.console import Group

    parts: list[Any] = [meta]

    if ing_lines:
        parts += [Rule("Ingredients", style="dim"),
                  Text("\n".join(ing_lines))]
    if step_lines:
        parts += [Rule("Instructions", style="dim"),
                  Text("\n".join(step_lines))]

    console.print()
    console.print(Panel(Group(*parts),
                        title=f"[bold green]🍴 {name}[/]",
                        expand=False))
    console.print()
