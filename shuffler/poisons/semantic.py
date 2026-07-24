"""Semantic poison: Schema entropy & JSON payload corruption."""

from __future__ import annotations

import json
import random


def mutate_json_payload(body_bytes: bytes) -> bytes:
    """Mutate JSON payload with semantic chaos.

    Mutations include:
    - Wrapping JSON in Markdown backticks (```json ... ```)
    - Mutating numeric types into strings
    - Injecting extra unexpected keys
    """
    try:
        data = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        return f"```json\n{body_bytes.decode('utf-8', errors='ignore')}\n```".encode("utf-8")

    mutation_choice = random.choice(["markdown_fence", "type_mutation", "extra_key"])

    if mutation_choice == "markdown_fence":
        raw_str = json.dumps(data)
        return f"```json\n{raw_str}\n```".encode("utf-8")

    elif mutation_choice == "type_mutation" and isinstance(data, dict):
        mutated = False
        for k, v in list(data.items()):
            if isinstance(v, (int, float)):
                data[k] = str(v)
                mutated = True
                break
        if not mutated:
            data["_mutated_type_str"] = "12345"
        return json.dumps(data).encode("utf-8")

    elif mutation_choice == "extra_key" and isinstance(data, dict):
        data["_shuffler_poison_entropy"] = "UNEXPECTED_FIELD_ATTACK"
        return json.dumps(data).encode("utf-8")

    return json.dumps(data).encode("utf-8")
