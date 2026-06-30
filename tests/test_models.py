"""Tests for shuffler.models — AttackReport and PayloadResult invariants.

Verifies that the core dataclasses correctly aggregate concurrent attack
results and compute derived metrics (success_count, failure_count,
corrupted_count) used by the verdict panel.
"""

from __future__ import annotations

import pytest

from shuffler.models import AttackReport, PayloadResult

# ── PayloadResult ─────────────────────────────────────────────────────── #


class TestPayloadResult:
    """PayloadResult is a frozen, slotted dataclass — verify immutability and defaults."""

    def test_defaults(self) -> None:
        """A clean payload should default to not-corrupted with no error."""
        r = PayloadResult(index=0, status_code=200, body='{"ok": true}')
        assert r.is_corrupted is False
        assert r.error is None

    def test_frozen_immutability(self) -> None:
        """Attempting to mutate a frozen dataclass must raise AttributeError."""
        r = PayloadResult(index=0, status_code=200, body="")
        with pytest.raises(AttributeError):
            r.index = 1  # type: ignore[misc]

    def test_corrupted_flag_explicit(self) -> None:
        """Explicitly marking a result as corrupted must persist."""
        r = PayloadResult(index=1, status_code=200, body="bad", is_corrupted=True)
        assert r.is_corrupted is True

    def test_error_field(self) -> None:
        """A transport failure should carry the error string and a zero status code."""
        r = PayloadResult(index=2, status_code=0, body="", error="Connection refused")
        assert r.status_code == 0
        assert r.error == "Connection refused"


# ── AttackReport ──────────────────────────────────────────────────────── #


class TestAttackReport:
    """AttackReport derived properties must correctly aggregate results."""

    @pytest.fixture()
    def mixed_report(self) -> AttackReport:
        """A report with a realistic mix of clean, corrupted, and failed payloads."""
        return AttackReport(
            vector="hallucination",
            target="http://localhost:8000",
            payloads_sent=5,
            response_codes=[200, 201, 200, 422, 500],
            results=[
                PayloadResult(index=0, status_code=200, body="ok"),
                PayloadResult(index=1, status_code=201, body="ok"),
                PayloadResult(index=2, status_code=200, body="ok", is_corrupted=True),
                PayloadResult(index=3, status_code=422, body="err", is_corrupted=True),
                PayloadResult(index=4, status_code=500, body="err", error="timeout"),
            ],
        )

    def test_success_count(self, mixed_report: AttackReport) -> None:
        """2xx codes count as successes."""
        assert mixed_report.success_count == 3  # 200, 201, 200

    def test_failure_count(self, mixed_report: AttackReport) -> None:
        """4xx and 5xx codes count as failures."""
        assert mixed_report.failure_count == 2  # 422, 500

    def test_corrupted_count(self, mixed_report: AttackReport) -> None:
        """Corruption count is driven by the PayloadResult.is_corrupted flag."""
        assert mixed_report.corrupted_count == 2

    def test_unique_codes_sorted_and_deduped(self, mixed_report: AttackReport) -> None:
        """unique_codes must be sorted ascending with no duplicates."""
        assert mixed_report.unique_codes == [200, 201, 422, 500]

    # ── edge cases ──────────────────────────────────────────────────── #

    def test_empty_report_zeroes(self) -> None:
        """An empty report must return zero for all derived counters."""
        r = AttackReport(vector="duplication", target="http://x")
        assert r.success_count == 0
        assert r.failure_count == 0
        assert r.corrupted_count == 0
        assert r.unique_codes == []
        assert r.payloads_sent == 0

    def test_all_successes(self) -> None:
        """When every payload succeeds, failure and corruption are zero."""
        r = AttackReport(
            vector="duplication",
            target="http://x",
            payloads_sent=3,
            response_codes=[200, 200, 201],
            results=[
                PayloadResult(index=i, status_code=c, body="ok")
                for i, c in enumerate([200, 200, 201])
            ],
        )
        assert r.success_count == 3
        assert r.failure_count == 0
        assert r.corrupted_count == 0

    def test_all_failures(self) -> None:
        """When every payload fails, success count is zero."""
        r = AttackReport(
            vector="hallucination",
            target="http://x",
            payloads_sent=2,
            response_codes=[500, 502],
            results=[
                PayloadResult(index=0, status_code=500, body="", error="Internal Server Error"),
                PayloadResult(index=1, status_code=502, body="", error="Bad Gateway"),
            ],
        )
        assert r.success_count == 0
        assert r.failure_count == 2

    def test_transport_errors_counted_as_non_success(self) -> None:
        """Status code 0 (transport error) is neither a 2xx success nor a 4xx+ failure."""
        r = AttackReport(
            vector="duplication",
            target="http://x",
            payloads_sent=1,
            response_codes=[0],
            results=[
                PayloadResult(index=0, status_code=0, body="", error="Connection refused"),
            ],
        )
        assert r.success_count == 0
        # 0 < 400, so the current implementation does not count it as a failure
        assert r.failure_count == 0
