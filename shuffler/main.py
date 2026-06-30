#!/usr/bin/env python3
"""shuffler — AI Pipeline Chaos Engineering CLI.

Usage
-----
    shuffler attack --target http://localhost:8000 --vector duplication --burst 50
"""

from __future__ import annotations

import asyncio
import sys
from enum import Enum
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .display import console, print_banner, render_report, show_banner
from .models import AttackReport
from .vectors import concurrency as duplication_vector
from .vectors import hallucination as hallucination_vector

# ── Typer app ─────────────────────────────────────────────────────────── #

app = typer.Typer(
    name="shuffler",
    help="🔥 AI Pipeline Chaos Engineering Toolkit — expose race conditions & LLM hallucinations.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


class Vector(str, Enum):
    """Supported attack vectors."""

    duplication = "duplication"
    hallucination = "hallucination"


# ── version callback ─────────────────────────────────────────────────── #


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


# ── attack command ────────────────────────────────────────────────────── #


@app.command()
def attack(
    target: str = typer.Option(
        "http://localhost:8000",
        "--target",
        "-t",
        help="URL of the target ingress point.",
    ),
    vector: Vector = typer.Option(
        ...,
        "--vector",
        "-v",
        help="Attack vector to deploy: [bold cyan]duplication[/] or [bold cyan]hallucination[/].",
        case_sensitive=False,
    ),
    burst: int = typer.Option(
        15,
        "--burst",
        "-b",
        help="Number of concurrent payloads to fire.",
        min=1,
    ),
) -> None:
    """Launch a chaos attack against an AI orchestration pipeline."""

    show_banner()

    # ── pre-flight ─────────────────────────────────────────────────── #
    console.print(
        Panel(
            f"[bold bright_white]Vector:[/] [bold magenta]{vector.value.upper()}[/]  │  "
            f"[bold bright_white]Target:[/] [bold cyan]{target}[/]  │  "
            f"[bold bright_white]Burst:[/] [bold yellow]{burst}[/]",
            title="[bold bright_white]🎯 ENGAGEMENT PARAMETERS[/]",
            border_style="bright_cyan",
            padding=(0, 2),
        )
    )
    console.print()

    # ── execute ────────────────────────────────────────────────────── #
    report: AttackReport

    with console.status(
        f"[bold red]⚡ Firing {burst} payloads → {target} [{vector.value.upper()}]…[/]",
        spinner="dots12",
        spinner_style="bold red",
    ):
        if vector == Vector.duplication:
            report = asyncio.run(duplication_vector.execute(target, burst))
        else:
            report = asyncio.run(hallucination_vector.execute(target, burst))

    # ── debrief ────────────────────────────────────────────────────── #
    render_report(report)


# ── help-interceptor wrapper ──────────────────────────────────────────── #


def cli() -> None:
    """Wrap the Typer app so the ASCII banner is shown on --help."""
    if "--help" in sys.argv or "-h" in sys.argv or len(sys.argv) == 1:
        print_banner()

    app()


# ── entry-point ───────────────────────────────────────────────────────── #

if __name__ == "__main__":
    cli()
