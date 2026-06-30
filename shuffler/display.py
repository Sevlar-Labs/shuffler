"""Rich-powered terminal display helpers for shuffler.

All terminal output is routed through this module — no raw ``print()``
calls anywhere else in the codebase.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from shuffler.models import AttackReport

console: Console = Console()


# ── branding ──────────────────────────────────────────────────────────── #

_BANNER: str = r"""
 ███████╗██╗  ██╗██╗   ██╗███████╗███████╗██╗     ███████╗██████╗
 ██╔════╝██║  ██║██║   ██║██╔════╝██╔════╝██║     ██╔════╝██╔══██╗
 ███████╗███████║██║   ██║█████╗  █████╗  ██║     █████╗  ██████╔╝
 ╚════██║██╔══██║██║   ██║██╔══╝  ██╔══╝  ██║     ██╔══╝  ██╔══██╗
 ███████║██║  ██║╚██████╔╝██║     ██║     ███████╗███████╗██║  ██║
 ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝     ╚══════╝╚══════╝╚═╝  ╚═╝
"""


def show_banner() -> None:
    """Print the ASCII banner inside a styled Rich panel."""
    banner_text = Text("\n")
    colors = [
        "bold #FF0000",
        "bold #FF1A00",
        "bold #FF3300",
        "bold #FF4D00",
        "bold #FF6600",
        "bold #FF8000",
    ]
    for line, color in zip(_BANNER.strip("\n").splitlines(), colors):
        banner_text.append(line + "\n", style=color)

    console.print(
        Panel(
            banner_text,
            title="[bold bright_white]SHUFFLER v1.0[/]",
            subtitle="[dim]AI Pipeline Chaos Engineering Toolkit[/dim]",
            border_style="bold #FF3300",
            padding=(0, 2),
        )
    )


# Clean public alias for the help-interceptor in main.py.
print_banner = show_banner


# ── attack summary table ─────────────────────────────────────────────── #


def _style_code(code: int) -> str:
    """Return a Rich-markup string coloured by HTTP status category."""
    if code == 0:
        return "[bold red]ERR[/bold red]"
    if 200 <= code < 300:
        return f"[bold green]{code}[/bold green]"
    if 300 <= code < 400:
        return f"[bold yellow]{code}[/bold yellow]"
    return f"[bold red]{code}[/bold red]"


def render_report(report: AttackReport) -> None:
    """Print a penetration-test-style results table."""

    # ── summary table ──────────────────────────────────────────────── #
    table = Table(
        title="[bold bright_white]⚡ ATTACK DEBRIEF ⚡[/]",
        title_style="bold",
        border_style="bright_red",
        show_lines=True,
        padding=(0, 1),
    )

    table.add_column("Field", style="bold bright_cyan", min_width=18)
    table.add_column("Value", min_width=36)

    # vector
    vec_style = "bold red" if report.vector == "hallucination" else "bold magenta"
    table.add_row("Vector Used", f"[{vec_style}]{report.vector.upper()}[/{vec_style}]")

    # target
    table.add_row("Target", f"[bold bright_white]{report.target}[/]")

    # payloads
    table.add_row("Payloads Sent", f"[bold yellow]{report.payloads_sent}[/]")

    # response codes
    codes_str = ", ".join(_style_code(c) for c in report.unique_codes) or "[dim]—[/dim]"
    table.add_row("Target Response Codes", codes_str)

    # execution time
    time_colour = "bold green" if report.execution_time_s < 5.0 else "bold red"
    table.add_row(
        "Execution Time",
        f"[{time_colour}]{report.execution_time_s:.4f}s[/{time_colour}]",
    )

    console.print()
    console.print(table)

    # ── per-payload breakdown ──────────────────────────────────────── #
    detail = Table(
        title="[bold bright_white]📡 PAYLOAD LOG[/]",
        border_style="dim",
        show_lines=False,
        padding=(0, 1),
    )

    detail.add_column("#", style="dim", width=4, justify="right")
    detail.add_column("Status", width=10, justify="center")
    detail.add_column("Corrupted", width=10, justify="center")
    detail.add_column("Detail", overflow="fold")

    for r in report.results:
        status = _style_code(r.status_code)
        corrupt_flag = "[bold red]YES[/]" if r.is_corrupted else "[bold green]CLEAN[/]"
        detail_text = r.error if r.error else r.body[:80]
        detail.add_row(str(r.index), status, corrupt_flag, detail_text)

    console.print(detail)
    console.print()

    # ── verdict panel ──────────────────────────────────────────────── #
    if report.failure_count > 0 or report.corrupted_count > 0:
        verdict = (
            f"[bold red]VULNERABLE.[/bold red]  "
            f"{report.failure_count} failure(s), "
            f"{report.corrupted_count} corrupted response(s) detected."
        )
        border = "bold red"
    else:
        verdict = (
            "[bold green]ALL PAYLOADS RETURNED CLEAN.[/bold green]  "
            "Target may have idempotency controls in place."
        )
        border = "bold green"

    console.print(
        Panel(
            verdict,
            title="[bold bright_white]VERDICT[/]",
            border_style=border,
            padding=(1, 2),
        )
    )
