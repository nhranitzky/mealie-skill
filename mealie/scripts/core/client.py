from __future__ import annotations

import os
import sys
from typing import Any

import httpx
from rich.console import Console

_console = Console()


class MealieHTTPError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


class MealieClient:
    def __init__(self) -> None:
        url = os.environ.get("MEALIE_URL", "").rstrip("/")
        token = os.environ.get("MEALIE_API_TOKEN", "").strip()

        missing: list[str] = []
        if not url:
            missing.append("MEALIE_URL")
        if not token or token == "your-api-token-here":
            missing.append("MEALIE_API_TOKEN")

        if missing:
            _console.print(
                f"[bold red]Missing configuration:[/] {', '.join(missing)}\n"
                "Set the required environment variables.\n"
                "Create an API token in Mealie under Settings → API Tokens."
            )
            sys.exit(1)

        self._base = url
        self._http = httpx.Client(
            base_url=url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            r = self._http.request(method, f"/api{path}", **kwargs)
            r.raise_for_status()
            return r
        except httpx.HTTPStatusError as exc:
            resp = exc.response
            try:
                detail = resp.json().get("detail", resp.text[:200])
            except Exception:
                detail = str(exc)
            raise MealieHTTPError(resp.status_code, detail) from None
        except httpx.RequestError as exc:
            _console.print(f"[red]Network error:[/] {exc}")
            sys.exit(1)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params).json()

    def post(self, path: str, body: dict[str, Any] | None = None) -> Any:
        r = self._request("POST", path, json=body)
        if "json" in r.headers.get("content-type", ""):
            return r.json()
        return r.text.strip().strip('"')

    def put(self, path: str, body: dict[str, Any]) -> Any:
        r = self._request("PUT", path, json=body)
        return r.json() if r.content else {}

    def patch(self, path: str, body: dict[str, Any]) -> Any:
        r = self._request("PATCH", path, json=body)
        return r.json() if r.content else {}

    def delete(self, path: str) -> None:
        self._request("DELETE", path)

    def get_all_pages(
        self, path: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        p = dict(params or {})
        p.setdefault("perPage", 50)
        p["page"] = 1
        items: list[dict[str, Any]] = []
        while True:
            data = self.get(path, params=p)
            chunk: list[dict[str, Any]] = data.get("items", [])
            items.extend(chunk)
            total = data.get("total")
            if total is None or len(items) >= total or not chunk:
                break
            p["page"] += 1
        return items

    @property
    def base_url(self) -> str:
        return self._base
