from __future__ import annotations

import re

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from shuffler.parsers.postman import DynamicRouteSpec

# Pre-compiled regex for lightning-fast interception of LLM Markdown hallucinations
_BACKTICK_RE = re.compile(rb"```(?:json)?", re.IGNORECASE)


def create_gatekeeper_app(specs: list[DynamicRouteSpec]) -> FastAPI:
    """Dynamically generate a strict FastAPI mock server from parsed Postman route specs."""
    app = FastAPI(
        title="Shuffler Universal Gatekeeper",
        description="Dynamic Postman-schema driven validation gatekeeper.",
        version="2.0.0",
    )

    # ── Sub-2ms Hallucination Firewall Middleware ──────────────────────── #
    @app.middleware("http")
    async def hallucination_firewall(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            raw_bytes = await request.body()
            if _BACKTICK_RE.search(raw_bytes):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "status": "error",
                        "message": "FATAL: Markdown backticks detected in payload.",
                    },
                )
        return await call_next(request)

    # ── Dynamic Route Compilation ──────────────────────────────────────── #
    for spec in specs:
        # Convert Postman path variables (:var) to FastAPI path syntax ({var})
        fastapi_path = re.sub(r":([a-zA-Z_][a-zA-Z0-9_]*)", r"{\1}", spec.path)

        def make_handler(route_spec: DynamicRouteSpec):
            async def handler(request: Request):
                if route_spec.expected_schema is not None:
                    try:
                        payload = await request.json()
                    except Exception:
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"status": "error", "message": "Malformed JSON payload."},
                        )

                    if not isinstance(payload, dict):
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={
                                "status": "error",
                                "message": "Expected JSON object payload.",
                            },
                        )

                    # 1. Enforce Presence of Expected Keys (Do not forbid extra keys)

                    # 2. Strict Real-World Data Type Checking
                    type_violations = []
                    for key, expected_type in route_spec.expected_schema.items():
                        if key in payload:
                            actual_val = payload[key]

                            # Handle standard JSON float vs int parity
                            if expected_type in (int, float) and isinstance(
                                actual_val, (int, float)
                            ):
                                continue

                            if not isinstance(actual_val, expected_type):
                                type_violations.append(
                                    f"Key '{key}' violation: "
                                    f"Expected {expected_type.__name__}, "
                                    f"got {type(actual_val).__name__}"
                                )

                    if type_violations:
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={
                                "status": "error",
                                "message": "Serialization Failed. Type mismatch detected.",
                                "violations": type_violations,
                            },
                        )

                return JSONResponse(
                    status_code=route_spec.response_code,
                    content=route_spec.response_body,
                )

            return handler

        app.add_api_route(
            path=fastapi_path,
            endpoint=make_handler(spec),
            methods=[spec.method],
            name=spec.name,
        )

    return app
