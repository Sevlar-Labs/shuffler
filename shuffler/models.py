"""Typed data models for shuffler attack results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PayloadResult:
    """Result of a single payload delivery."""

    index: int
    status_code: int
    body: str
    is_corrupted: bool = False
    error: str | None = None


@dataclass(slots=True)
class AttackReport:
    """Aggregated report produced after an attack run completes."""

    vector: str
    target: str
    payloads_sent: int = 0
    response_codes: list[int] = field(default_factory=list)
    execution_time_s: float = 0.0
    results: list[PayloadResult] = field(default_factory=list)

    # --- derived helpers -------------------------------------------------- #

    @property
    def unique_codes(self) -> list[int]:
        """Deduplicated, sorted status codes observed."""
        return sorted(set(self.response_codes))

    @property
    def success_count(self) -> int:
        return sum(1 for c in self.response_codes if 200 <= c < 300)

    @property
    def failure_count(self) -> int:
        return sum(1 for c in self.response_codes if c >= 400)

    @property
    def corrupted_count(self) -> int:
        return sum(1 for r in self.results if r.is_corrupted)
