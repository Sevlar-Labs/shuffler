"""Duplication / race-condition attack vector.

Fires *burst* concurrent HTTP POST requests against the target ingress
to expose missing idempotency guards — the exact vulnerability
demonstrated in the original ``test_runner.py``.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Final

import httpx

from shuffler.models import AttackReport, PayloadResult

# ── static payload (mirrors the original test_runner.py fixture) ──────── #

_INBOUND_AI_PAYLOAD: Final[dict[str, object]] = {
    "lead_name": "John Doe",
    "lead_email": "john.doe@enterprise.com",
    "ai_confidence_score": 98.5,
}

_RAW_TEXT: Final[str] = json.dumps(_INBOUND_AI_PAYLOAD)


async def _fire_single(
    client: httpx.AsyncClient,
    target: str,
    index: int,
) -> PayloadResult:
    """Deliver one POST payload and capture the outcome."""
    try:
        resp = await client.post(
            f"{target.rstrip('/')}/agent/extract",
            json={"raw_text": _RAW_TEXT},
            headers={"X-Chaos-Mode": "normal"},
        )
        return PayloadResult(
            index=index,
            status_code=resp.status_code,
            body=resp.text,
        )
    except httpx.HTTPError as exc:
        return PayloadResult(
            index=index,
            status_code=0,
            body="",
            error=str(exc),
        )


async def execute(target: str, burst: int) -> AttackReport:
    """Launch *burst* concurrent duplicate payloads at *target*.

    Returns a fully-populated :class:`AttackReport`.
    """
    report = AttackReport(vector="duplication", target=target)

    t0 = time.perf_counter()

    async with httpx.AsyncClient(timeout=httpx.Timeout(45.0)) as client:
        tasks = [_fire_single(client, target, i) for i in range(burst)]
        results: list[PayloadResult] = await asyncio.gather(*tasks)

    report.execution_time_s = round(time.perf_counter() - t0, 4)
    report.results = results
    report.payloads_sent = len(results)
    report.response_codes = [r.status_code for r in results]

    return report
