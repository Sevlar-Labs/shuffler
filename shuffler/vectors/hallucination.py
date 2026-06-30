"""Hallucination / schema-entropy attack vector.

Sends payloads with the ``X-Chaos-Mode: hallucination`` header so the
target AI agent wraps its JSON response in markdown backticks — exactly
the corruption path implemented in the original ``chaos_agent.py``.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Final

import httpx

from shuffler.models import AttackReport, PayloadResult

# ── static payload ─────────────────────────────────────────────────────── #

_INBOUND_AI_PAYLOAD: Final[dict[str, object]] = {
    "lead_name": "Jane Smith",
    "lead_email": "jane.smith@enterprise.com",
    "ai_confidence_score": 95.2,
}

_RAW_TEXT: Final[str] = json.dumps(_INBOUND_AI_PAYLOAD)


def _detect_corruption(body: str) -> bool:
    """Return ``True`` if the response body contains markdown-wrapped JSON
    (the hallucination artefact produced by chaos_agent.py)."""
    return "```json" in body or "```" in body


async def _fire_single(
    client: httpx.AsyncClient,
    target: str,
    index: int,
) -> PayloadResult:
    """Deliver one hallucination-mode payload and inspect the response."""
    try:
        resp = await client.post(
            f"{target.rstrip('/')}/agent/extract",
            json={"raw_text": _RAW_TEXT},
            headers={"X-Chaos-Mode": "hallucination"},
        )
        corrupted = _detect_corruption(resp.text)
        return PayloadResult(
            index=index,
            status_code=resp.status_code,
            body=resp.text,
            is_corrupted=corrupted,
        )
    except httpx.HTTPError as exc:
        return PayloadResult(
            index=index,
            status_code=0,
            body="",
            error=str(exc),
        )


async def execute(target: str, burst: int) -> AttackReport:
    """Fire *burst* hallucination payloads at *target*.

    Every odd-numbered request should return markdown-wrapped JSON,
    corrupting downstream CRM parsers.  Returns a populated
    :class:`AttackReport`.
    """
    report = AttackReport(vector="hallucination", target=target)

    t0 = time.perf_counter()

    async with httpx.AsyncClient(timeout=httpx.Timeout(45.0)) as client:
        tasks = [_fire_single(client, target, i) for i in range(burst)]
        results: list[PayloadResult] = await asyncio.gather(*tasks)

    report.execution_time_s = round(time.perf_counter() - t0, 4)
    report.results = results
    report.payloads_sent = len(results)
    report.response_codes = [r.status_code for r in results]

    return report
