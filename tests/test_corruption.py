"""Tests for corruption detection — mock_receiver.py validation logic.

Isolates and exercises the three-layer corruption detection in the CRM
receiver endpoint:

1. Top-level raw markdown backticks in the request body.
2. Nested ``raw_output`` field containing markdown backticks (the
   hallucination wrapper produced by chaos_agent.py).
3. Malformed / non-JSON payloads.

All tests use FastAPI's synchronous TestClient so we never introduce
blocking I/O into an async context.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from mock_receiver import _BACKTICK_RE, app

# ── regex unit tests ──────────────────────────────────────────────────── #


class TestBacktickRegex:
    """Verify the compiled regex catches markdown-wrapped JSON artefacts."""

    @pytest.mark.parametrize(
        "text",
        [
            '```json\n{"name": "test"}\n```',
            '```JSON\n{"name": "test"}\n```',
            '```\n{"name": "test"}\n```',
            'preamble text ```json {"x":1} ``` trailing',
        ],
        ids=["lower-json", "upper-JSON", "bare-backticks", "embedded"],
    )
    def test_detects_backtick_variants(self, text: str) -> None:
        assert _BACKTICK_RE.search(text) is not None

    @pytest.mark.parametrize(
        "text",
        [
            '{"name": "clean"}',
            "plain text without any backticks",
            '{"code": "x = 1"}',
            "",
        ],
        ids=["clean-json", "plain-text", "json-with-code-key", "empty"],
    )
    def test_passes_clean_payloads(self, text: str) -> None:
        assert _BACKTICK_RE.search(text) is None


# ── endpoint integration tests ────────────────────────────────────────── #


class TestCRMReceiveEndpoint:
    """Integration tests for POST /crm/v1/leads corruption detection."""

    @pytest.fixture()
    def client(self) -> TestClient:
        return TestClient(app)

    # ── clean payloads ────────────────────────────────────────────── #

    def test_clean_json_accepted_with_201(self, client: TestClient) -> None:
        """A well-formed JSON lead should be persisted and return 201 + status ok."""
        payload: dict[str, str] = {
            "firstname": "Alice",
            "email": "alice@example.com",
        }
        resp = client.post("/crm/v1/leads", content=json.dumps(payload))
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "ok"
        assert body["lead"] == payload

    # ── top-level backtick corruption ─────────────────────────────── #

    def test_raw_markdown_backticks_flagged_as_error(self, client: TestClient) -> None:
        """Raw markdown ``` in the request body must be caught as a hallucination artefact."""
        corrupted_body: str = '```json\n{"firstname": "Bob", "email": "bob@x.com"}\n```'
        resp = client.post("/crm/v1/leads", content=corrupted_body)
        body = resp.json()
        assert body["status"] == "error"
        assert "backtick" in body["message"].lower()

    # ── nested raw_output corruption ──────────────────────────────── #

    def test_nested_raw_output_backticks_flagged(self, client: TestClient) -> None:
        """The chaos_agent sometimes returns {\"raw_output\": \"```json...```\"}.
        The receiver must detect the corruption — the top-level raw-body
        regex fires first because json.dumps preserves literal backticks,
        but either detection layer satisfies the invariant."""
        nested_payload: str = json.dumps(
            {"raw_output": '```json\n{"firstname": "Carol"}\n```'}
        )
        resp = client.post("/crm/v1/leads", content=nested_payload)
        body = resp.json()
        assert body["status"] == "error"
        assert "backtick" in body["message"].lower() or "raw_output" in body["message"].lower()

    # ── malformed JSON ────────────────────────────────────────────── #

    def test_malformed_json_flagged_as_error(self, client: TestClient) -> None:
        """Completely broken JSON must be caught by the JSON decode fallback."""
        resp = client.post("/crm/v1/leads", content="{this is not valid json!!!")
        body = resp.json()
        assert body["status"] == "error"
        assert "malformed" in body["message"].lower() or "json" in body["message"].lower()

    # ── health probe ──────────────────────────────────────────────── #

    def test_healthz_returns_healthy(self, client: TestClient) -> None:
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json() == {"status": "healthy"}
