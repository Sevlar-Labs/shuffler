from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DynamicRouteSpec:
    name: str
    method: str
    path: str
    expected_schema: dict[str, type] | None
    response_code: int
    response_body: dict[str, Any]


def parse_postman_collection(file_path: str) -> list[DynamicRouteSpec]:
    """
    Parses a Postman Collection v2.1 JSON file and extracts the atomic route primitives.
    """
    with open(file_path, "rb") as f:
        data = json.load(f)

    specs: list[DynamicRouteSpec] = []

    def _traverse(items: list[dict[str, Any]]) -> None:
        for item in items:
            if "item" in item:  # This is a folder, recurse deeper
                _traverse(item["item"])
                continue

            req = item.get("request", {})
            method = req.get("method", "GET").upper()

            # 1. Normalize the Path (Handling Postman {{variables}} and raw strings)
            url_obj = req.get("url", {})
            raw_path = url_obj.get("path", []) if isinstance(url_obj, dict) else url_obj

            if isinstance(raw_path, list):
                # Join path parts, ignoring {{base_url}} type variables at the root
                clean_parts = [p for p in raw_path if not p.startswith("{{")]
                path = "/" + "/".join(clean_parts)
            else:
                # Fallback for raw string URLs
                path = str(raw_path).split("?")[0]  # Strip query params
                path = re.sub(r"^https?://[^/]+", "", path)
                if not path.startswith("/"):
                    path = "/" + path

            # 2. Extract Body Schema Signature via Inference
            expected_schema = None
            body_obj = req.get("body", {})
            if body_obj.get("mode") == "raw" and body_obj.get("raw"):
                try:
                    sample = json.loads(body_obj["raw"])
                    if isinstance(sample, dict):
                        # Map JSON keys to their native Python types for fast strict checking
                        expected_schema = {k: type(v) for k, v in sample.items()}
                except Exception:
                    pass

            # 3. Extract Default Mock Response Example
            resp_code = 200
            resp_body = {"status": "ok", "message": "Shuffler Default Mock"}
            if item.get("response"):
                first_resp = item["response"][0]
                resp_code = first_resp.get("code", 200)
                if first_resp.get("body"):
                    try:
                        resp_body = json.loads(first_resp["body"])
                    except Exception:
                        resp_body = {"raw": first_resp["body"]}

            specs.append(
                DynamicRouteSpec(
                    name=item.get("name", path),
                    method=method,
                    path=path,
                    expected_schema=expected_schema,
                    response_code=resp_code,
                    response_body=resp_body,
                )
            )

    # Initiate recursive traversal from the root
    _traverse(data.get("item", []))
    return specs
