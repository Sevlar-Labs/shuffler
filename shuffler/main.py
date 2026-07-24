#!/usr/bin/env python3
"""shuffler — Universal Local L7 Chaos Proxy."""

from __future__ import annotations

import asyncio
import sys
from typing import Optional

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .config import load_config
from .display import console, print_banner, show_banner
from .proxy.server import create_proxy_app

app = typer.Typer(
    name="shuffler",
    help="🔥 Shuffler - Universal Local L7 Chaos Proxy.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


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
    """🔥 Shuffler - Universal Local L7 Chaos Proxy."""


async def _serve_proxies(config_path: str) -> None:
    show_banner()
    console.print(f"[bold cyan]Loading Configuration:[/] {config_path}")

    try:
        config = load_config(config_path)
    except FileNotFoundError:
        console.print(
            f"[bold red]Configuration file '{config_path}' not found.[/bold red]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Failed to parse configuration:[/] {e}")
        sys.exit(1)

    tasks = []

    for name, proxy_conf in config.proxies.items():
        console.print(
            Panel(
                f"[bold bright_white]Upstream:[/] [bold green]{proxy_conf.upstream}[/]  │  "
                f"[bold bright_white]Port:[/] [bold yellow]{proxy_conf.port}[/]\n"
                f"[bold bright_white]Poisons:[/] [bold red]{proxy_conf.poisons}[/]",
                title=f"[bold bright_white]🛡️ PROXY: {name.upper()}[/]",
                border_style="bright_cyan",
                padding=(0, 2),
            )
        )

        proxy_app = create_proxy_app(name, proxy_conf)
        uv_config = uvicorn.Config(
            proxy_app,
            host="0.0.0.0",
            port=proxy_conf.port,
            log_level="warning",
        )
        server = uvicorn.Server(uv_config)
        tasks.append(server.serve())

    if not tasks:
        console.print(
            "[bold yellow]No proxies defined in config. Exiting...[/bold yellow]"
        )
        return

    console.print(
        f"[bold green]Starting {len(tasks)} concurrent listeners...[/bold green]"
    )
    await asyncio.gather(*tasks)


@app.command()
def serve(
    config: str = typer.Option(
        "shuffler.yaml",
        "--config",
        "-c",
        help="Path to shuffler.yaml config file.",
    )
) -> None:
    """Start the Shuffler Universal Local L7 Chaos Proxy."""
    try:
        asyncio.run(_serve_proxies(config))
    except KeyboardInterrupt:
        console.print("\n[bold red]Shutting down Shuffler...[/bold red]")


def cli() -> None:
    """Wrap the Typer app so the ASCII banner is shown on --help."""
    if "--help" in sys.argv or "-h" in sys.argv or len(sys.argv) == 1:
        print_banner()

    app()


if __name__ == "__main__":
    cli()
