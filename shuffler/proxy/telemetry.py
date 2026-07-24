"""Real-time console telemetry and tracing for Shuffler proxy traffic."""

from __future__ import annotations

from rich.console import Console

console = Console()


def log_intercept(
    proxy_name: str,
    method: str,
    path: str,
    status_code: int,
    poisons_triggered: list[str],
) -> None:
    """Log an intercepted L7 request/response pair with active poison annotations."""
    if poisons_triggered:
        poisons_str = ", ".join(poisons_triggered).upper()
        console.print(
            f"[bold red]⚡ [POISON INJECTED: {poisons_str}][/bold red] "
            f"[bold cyan][{proxy_name.upper()}][/bold cyan] "
            f"[yellow]{method}[/yellow] /{path} -> [bold magenta]HTTP {status_code}[/bold magenta]"
        )
    else:
        console.print(
            f"[dim][PASSTHROUGH][/dim] "
            f"[bold cyan][{proxy_name.upper()}][/bold cyan] "
            f"[green]{method}[/green] /{path} -> [dim]HTTP {status_code}[/dim]"
        )
