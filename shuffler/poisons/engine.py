"""Decoupled Poisons Engine for evaluating & applying chaos injections."""

from __future__ import annotations

import random
from typing import Optional

from shuffler.poisons.network import ConnectionDroppedPoisonError
from shuffler.poisons.semantic import mutate_json_payload
from shuffler.poisons.temporal import apply_temporal_poison


class PoisonEngine:
    """Evaluates poison probabilities and coordinates execution of active poisons."""

    def __init__(self, poison_configs: dict[str, float]) -> None:
        self.poisons = poison_configs

    def should_trigger(self, poison_name: str) -> bool:
        prob = self.poisons.get(poison_name, 0.0)
        if prob <= 0.0:
            return False
        return random.random() < prob

    async def process_request(self) -> list[str]:
        """Run pre-request poisons (network, temporal). Returns list of triggered poison names."""
        triggered = []

        if self.should_trigger("network"):
            triggered.append("network")
            raise ConnectionDroppedPoisonError(
                "TCP connection severed mid-flight by Shuffler network poison."
            )

        if self.should_trigger("temporal"):
            triggered.append("temporal")
            await apply_temporal_poison(latency_seconds=1.0)

        return triggered

    def process_response(
        self, content: bytes, media_type: Optional[str]
    ) -> tuple[bytes, list[str]]:
        """Run post-response payload poisons (semantic).

        Returns (new_content, triggered_poisons).
        """
        triggered = []

        if self.should_trigger("semantic"):
            triggered.append("semantic")
            content = mutate_json_payload(content)

        return content, triggered
