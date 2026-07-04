#!/usr/bin/env python3
"""shuffler — Universal Postman-Schema Driven Chaos Engineering CLI."""

from __future__ import annotations

import asyncio
import json
import random
import sys
from enum import Enum
from typing import Optional

import httpx
import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .display import console, print_banner, show_banner
from .gatekeeper.server import create_gatekeeper_app
from .parsers.postman import parse_postman_collection

app = typer.Typer(
    name="shuffler",
    help="🔥 AI Pipeline Chaos Engineering Toolkit — Universal Postman-Schema Driven Gatekeeper.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


class Vector(str, Enum):
    """Supported attack vectors."""

    duplication = "duplication"
    hallucination = "hallucination"


def version_callback(value: bool) -> None:
    """Print the version string and exit immediately."""
    if value:
        _console = Console()
        _console.print(
            f"[bold bright_cyan]Shuffler CLI[/] — Version [bold bright_white]{__version__}[/]"
        )
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show the application's version and exit.",
    ),
) -> None:
    """🔥 AI Pipeline Chaos Engineering Toolkit."""


@app.command()
def serve(
    collection: str = typer.Option(
        ...,
        "--collection",
        "-c",
        help="Path to Postman Collection JSON.",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to run the Universal Gatekeeper server on.",
    ),
) -> None:
    """Compile and serve a strict FastAPI mock gatekeeper from a Postman collection."""
    show_banner()

    console.print(
        Panel(
            f"[bold bright_white]Collection:[/] [bold cyan]{collection}[/]  │  "
            f"[bold bright_white]Port:[/] [bold yellow]{port}[/]",
            title="[bold bright_white]🛡️ GATEKEEPER BOOTSTRAP[/]",
            border_style="bright_cyan",
            padding=(0, 2),
        )
    )
    console.print()

    console.print(f"[bold cyan]Parsing Postman Collection:[/] {collection}")
    specs = parse_postman_collection(collection)

    console.print(f"[bold green]Compiling Strict Gatekeeper with {len(specs)} routes...[/]")
    gatekeeper_app = create_gatekeeper_app(specs)

    console.print(f"[bold bright_white]Launching Gatekeeper on[/] [bold yellow]0.0.0.0:{port}[/]…")
    uvicorn.run(gatekeeper_app, host="0.0.0.0", port=port, log_level="info")


@app.command()
def attack(
    collection: str = typer.Option(
        ...,
        "--collection",
        "-c",
        help="Path to Postman Collection JSON.",
    ),
    vector: Vector = typer.Option(
        ...,
        "--vector",
        "-v",
        help="Attack vector: [bold cyan]duplication[/] or [bold cyan]hallucination[/].",
        case_sensitive=False,
    ),
    burst: int = typer.Option(
        50,
        "--burst",
        "-b",
        help="Number of concurrent payloads to fire.",
        min=1,
    ),
    target_host: str = typer.Option(
        "http://localhost:8000",
        help="Base URL of the target gateway",
    ),
) -> None:
    """Launch a universal chaos attack dynamically derived from a Postman collection."""
    show_banner()

    console.print("[bold red]Initializing Universal Chaos Engine...[/bold red]")
    specs = parse_postman_collection(collection)

    # Isolate mutable routes for attack
    targets = [s for s in specs if s.method in ("POST", "PUT", "PATCH") and s.expected_schema]

    if not targets:
        console.print(
            "[bold red]No valid POST/PUT routes with schemas found in collection.[/bold red]"
        )
        raise typer.Exit(1)

    target = targets[0]  # Select first valid target for MVP

    # Render Target Debrief
    table = Table(
        title="[bold bright_white]🎯 TARGET ACQUIRED DEBRIEF[/]",
        title_style="bold",
        border_style="bright_yellow",
        show_lines=True,
        padding=(0, 1),
    )
    table.add_column("Property", style="bold bright_cyan", min_width=20)
    table.add_column("Value", style="bright_white", min_width=40)

    table.add_row("Selected Target API", f"[bold yellow]{target.method} {target.path}[/]")
    schema_keys = list(target.expected_schema.keys())
    table.add_row("Target Schema Keys", f"[bold green]{schema_keys}[/]")
    table.add_row("Attack Vector", f"[bold red]{vector.value.upper()}[/]")
    table.add_row("Burst Size", f"[bold magenta]{burst}[/]")

    console.print()
    console.print(table)
    console.print(
        f"\n[bold yellow]Target Acquired:[/] [bold bright_white]{target.method} {target.path}[/]"
    )
    console.print(f"[bold yellow]Schema Lock:[/] {schema_keys}")
    console.print(f"[bold red]Deploying {burst} payloads using vector: {vector.value}…[/]")

    # --- EXECUTION ENGINE ---
    # 1. Generate a valid payload based on the inferred schema types
    dummy_payload = {}
    for key, val_type in target.expected_schema.items():
        if val_type is int:
            dummy_payload[key] = 99
        elif val_type is float:
            dummy_payload[key] = 0.99
        else:
            dummy_payload[key] = "chaos_test"

    # --- VECTOR STATUS ---
    if vector.lower() == "hallucination":
        console.print(
            "[bold red]🧪 VECTOR ACTIVE: Probabilistic hallucination"
            " mutations enabled...[/bold red]"
        )
    elif vector.lower() == "duplication":
        console.print(
            "[bold yellow]🧪 VECTOR ACTIVE: Firing exact duplicate"
            " payloads concurrently...[/bold yellow]"
        )

    target_url = f"{target_host.rstrip('/')}{target.path}"
    console.print(f"[dim]Assembling payload: {dummy_payload}[/dim]")
    console.print("[bold yellow]Executing asynchronous burst...[/bold yellow]\n")

    # 2. Fire the concurrent burst
    async def _fire_burst() -> None:
        async def _send_and_capture(
            client: httpx.AsyncClient, payload_str: str, mutation_label: str
        ) -> tuple[str, str, httpx.Response | Exception]:
            try:
                resp = await client.request(
                    method=target.method,
                    url=target_url,
                    content=payload_str,
                    headers={"Content-Type": "application/json"},
                )
                return (payload_str, mutation_label, resp)
            except Exception as e:
                return (payload_str, mutation_label, e)

        async with httpx.AsyncClient() as client:
            tasks = []
            for idx in range(burst):
                payload_copy = dummy_payload.copy()
                raw_json_str: str | None = None
                mutation_label = "CLEAN_DUPLICATE"

                if vector.lower() == "hallucination":
                    chaos_type = random.choice(["extra_key", "type_mutation", "markdown_fence"])
                    mutation_label = chaos_type.upper()

                    if chaos_type == "extra_key":
                        payload_copy["ai_inferred_sentiment"] = f"Variant-{idx} High Interest"
                        raw_json_str = json.dumps(payload_copy)
                    elif chaos_type == "type_mutation":
                        numeric_keys = [
                            k for k, v in target.expected_schema.items() if v in (int, float)
                        ]
                        if numeric_keys:
                            payload_copy[random.choice(numeric_keys)] = "MALFORMED_STRING_VAL"
                        raw_json_str = json.dumps(payload_copy)
                    elif chaos_type == "markdown_fence":
                        raw_json_str = f"```json\n{json.dumps(payload_copy)}\n```"
                else:
                    raw_json_str = json.dumps(payload_copy)

                if raw_json_str is not None:
                    tasks.append(_send_and_capture(client, raw_json_str, mutation_label))

            results = await asyncio.gather(*tasks)

            # --- FULL SEQUENCE TRACER PANEL ---
            console.print("\n╭─────────────────── 🔍 FULL BURST TRACE LOG ───────────────────╮")

            accepted = 0
            blocked = 0

            for idx, (req_str, mut_label, r) in enumerate(results):
                console.print(
                    f"│ ➜ [bold yellow]PAYLOAD {idx + 1}/{burst}"
                    f" | TYPE: [{mut_label}][/bold yellow]"
                )
                console.print(f"│   [dim]Outbound:[/dim] {req_str}")

                if isinstance(r, httpx.Response):
                    status_color = "green" if r.status_code in (200, 201, 202, 204) else "red"
                    console.print(
                        f"│   [dim]Inbound :[/dim] "
                        f"[bold {status_color}]HTTP {r.status_code}"
                        f"[/bold {status_color}] -> {r.text}"
                    )

                    if r.status_code in (200, 201, 202, 204):
                        accepted += 1
                    else:
                        blocked += 1
                else:
                    console.print(
                        "│   [dim]Inbound :[/dim] [bold red]NETWORK ERROR / DROPPED[/bold red]"
                    )
                    blocked += 1

                console.print("│")  # Spacer between payloads

            console.print("╰───────────────────────────────────────────────────────────────╯\n")

            # --- ATTACK DEBRIEF ---
            console.print("╭──────────────────────────────────────────────╮")
            console.print("│             ⚡ ATTACK DEBRIEF ⚡             │")
            console.print("├──────────────────────────────────────────────┤")
            console.print(
                f"│ [bold green]Gatekeeper Accepted (2xx):[/bold green] {accepted:<15} │"
            )
            console.print(f"│ [bold red]Gatekeeper Blocked (4xx/5xx):[/bold red] {blocked:<12} │")
            console.print("╰──────────────────────────────────────────────╯")

    asyncio.run(_fire_burst())


def cli() -> None:
    """Wrap the Typer app so the ASCII banner is shown on --help."""
    if "--help" in sys.argv or "-h" in sys.argv or len(sys.argv) == 1:
        print_banner()

    app()


if __name__ == "__main__":
    cli()
