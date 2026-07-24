"""Temporal poison: artificial latency injection."""

from __future__ import annotations

import asyncio


async def apply_temporal_poison(latency_seconds: float = 2.0) -> None:
    """Inject artificial delay into the request/response pipeline."""
    await asyncio.sleep(latency_seconds)
