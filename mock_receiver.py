#!/usr/bin/env python3
"""mock_receiver — Dummy enterprise CRM ingress (HubSpot / Salesforce stand-in).

Exposes a single POST endpoint that accepts AI-extracted lead payloads,
validates them, and prints colour-coded Rich panels to the terminal so
an operator can visually confirm clean vs. corrupted data flow.

Run standalone:
    uvicorn mock_receiver:app --host 0.0.0.0 --port 8001 --reload
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ── globals ───────────────────────────────────────────────────────────── #

app = FastAPI(
    title="Mock CRM Receiver",
    description="Simulated enterprise CRM lead ingress for the shuffler sandbox.",
    version="1.0.0",
)

console: Console = Console(force_terminal=True)

# Thread-safe running counter
_lock = threading.Lock()
_lead_counter: int = 0

# Regex that catches markdown-wrapped JSON (the hallucination artefact)
_BACKTICK_RE = re.compile(r"```(?:json)?", re.IGNORECASE)


# ── helpers ───────────────────────────────────────────────────────────── #


def _increment_counter() -> int:
    """Atomically bump the lead counter and return the new value."""
    global _lead_counter
    with _lock:
        _lead_counter += 1
        return _lead_counter


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _render_success_panel(count: int, payload: dict[str, Any]) -> None:
    """Print a green panel showing the parsed lead data."""
    tbl = Table(
        show_header=False,
        border_style="green",
        padding=(0, 1),
        expand=True,
    )
    tbl.add_column("Key", style="bold bright_cyan", min_width=14)
    tbl.add_column("Value", style="bright_white")

    for key, value in payload.items():
        tbl.add_row(str(key), str(value))

    header = Text.assemble(
        ("✔ LEAD ACCEPTED  ", "bold green"),
        (f"[#{count}]  ", "bold yellow"),
        (_timestamp(), "dim"),
    )

    console.print()
    console.print(
        Panel(
            tbl,
            title=header,
            border_style="bold green",
            subtitle="[dim]200 OK — payload persisted[/dim]",
            padding=(1, 2),
        )
    )


def _render_error_panel(reason: str, raw_body: str) -> None:
    """Print a red FATAL panel when incoming JSON is malformed."""
    body_preview = raw_body[:300] + ("…" if len(raw_body) > 300 else "")

    detail = Table(
        show_header=False,
        border_style="red",
        padding=(0, 1),
        expand=True,
    )
    detail.add_column("Field", style="bold bright_red", min_width=14)
    detail.add_column("Value", style="bright_white")
    detail.add_row("Reason", reason)
    detail.add_row("Timestamp", _timestamp())
    detail.add_row("Raw Body", body_preview)

    console.print()
    console.print(
        Panel(
            detail,
            title="[bold red]██ FATAL PARSE ERROR ██[/bold red]",
            border_style="bold red",
            subtitle="[dim red]Corrupted payload — CRM integrity at risk[/dim red]",
            padding=(1, 2),
        )
    )


# ── exception handler ─────────────────────────────────────────────────── #


@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: log a fatal panel and return 422."""
    raw = ""
    try:
        raw = (await request.body()).decode("utf-8", errors="replace")
    except Exception:
        pass

    _render_error_panel(reason=str(exc), raw_body=raw)

    return JSONResponse(
        status_code=422,
        content={"error": "Unprocessable payload", "detail": str(exc)},
    )


# ── endpoints ─────────────────────────────────────────────────────────── #


@app.post("/crm/v1/leads", status_code=201)
async def receive_lead(request: Request) -> dict[str, Any]:
    """Ingest a lead payload.

    * Valid JSON → green success panel, 201 Created.
    * Markdown-wrapped / malformed → red FATAL panel, 200 OK
      (acknowledges receipt but flags corruption).
    """
    raw_body: str = (await request.body()).decode("utf-8", errors="replace")

    # ── corruption detection ───────────────────────────────────────── #
    if _BACKTICK_RE.search(raw_body):
        _render_error_panel(
            reason="Payload contains raw markdown backticks (```json) — "
            "hallucination artefact detected.",
            raw_body=raw_body,
        )
        return {
            "status": "error",
            "message": "Corrupted payload ingested — markdown backticks detected.",
        }

    # ── JSON parse attempt ─────────────────────────────────────────── #
    try:
        payload: dict[str, Any] = json.loads(raw_body)
    except (json.JSONDecodeError, ValueError) as exc:
        _render_error_panel(reason=f"JSON decode failure: {exc}", raw_body=raw_body)
        return {
            "status": "error",
            "message": "Malformed JSON — could not decode payload.",
        }

    # ── nested wrapper detection ───────────────────────────────────── #
    # chaos_agent.py sometimes returns {"raw_output": "```json\n…\n```"}
    if "raw_output" in payload:
        inner = str(payload["raw_output"])
        if _BACKTICK_RE.search(inner):
            _render_error_panel(
                reason="Nested raw_output field contains markdown backticks — "
                "hallucination artefact detected inside JSON wrapper.",
                raw_body=raw_body,
            )
            return {
                "status": "error",
                "message": "Corrupted nested payload — markdown backticks in raw_output.",
            }

    # ── success ────────────────────────────────────────────────────── #
    count = _increment_counter()
    _render_success_panel(count, payload)

    return {
        "status": "ok",
        "message": f"Lead #{count} persisted successfully.",
        "lead": payload,
    }


# ── health probe ──────────────────────────────────────────────────────── #


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "healthy"}
