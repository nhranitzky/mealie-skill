from __future__ import annotations

import json
import sys
from enum import StrEnum
from typing import Any

from rich.console import Console

console = Console()
err_console = Console(stderr=True)


class OutputFormat(StrEnum):
    text = "text"
    json = "json"


def output_json(data: Any) -> None:
    """Print sanitised raw data as pretty JSON."""
    console.print_json(json.dumps(_sanitise(data), ensure_ascii=False))


_bad = {"token", "password", "secret", "api_key", "apikey"}


def _sanitise(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _sanitise(v) for k, v in obj.items()
                if k.lower() not in _bad and "token" not in k.lower()}
    if isinstance(obj, list):
        return [_sanitise(i) for i in obj]
    return obj


def render_error(message: str, fmt: OutputFormat, code: str = "error") -> None:
    if fmt == OutputFormat.json:
        err_console.print_json(json.dumps({"error": message, "code": code}))
    else:
        err_console.print(f"[bold red]Error:[/bold red] {message}")
    sys.exit(1)
