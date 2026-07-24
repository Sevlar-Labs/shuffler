"""Transparent L7 Reverse Proxy implementation using FastAPI & httpx."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, Request, Response

from shuffler.config import ProxyConfig
from shuffler.poisons.engine import PoisonEngine
from shuffler.poisons.network import ConnectionDroppedPoisonError
from shuffler.proxy.telemetry import log_intercept


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    client = httpx.AsyncClient(timeout=httpx.Timeout(60.0), follow_redirects=True)
    app.state.client = client
    try:
        yield
    finally:
        await client.aclose()


def create_proxy_app(proxy_name: str, proxy_config: ProxyConfig) -> FastAPI:
    """Create a FastAPI application serving as a transparent L7 reverse proxy."""
    app = FastAPI(
        title=f"Shuffler Proxy [{proxy_name}] -> {proxy_config.upstream}",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    poison_engine = PoisonEngine(proxy_config.poisons)

    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    )
    async def proxy_handler(request: Request, path: str) -> Response:
        triggered_poisons: list[str] = []

        # Pre-request poison processing (network drop, temporal latency)
        try:
            req_poisons = await poison_engine.process_request()
            triggered_poisons.extend(req_poisons)
        except ConnectionDroppedPoisonError as exc:
            log_intercept(proxy_name, request.method, path, 503, ["network"])
            return Response(
                content=str(exc),
                status_code=503,
            )

        target_base = proxy_config.upstream.rstrip("/")
        url = f"{target_base}/{path}" if path else target_base
        if request.url.query:
            url = f"{url}?{request.url.query}"

        body = await request.body()

        # Prepare headers, excluding host & content-length to let httpx compute them
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None)

        client: httpx.AsyncClient = request.app.state.client

        try:
            upstream_response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
            )

            resp_content = upstream_response.content
            media_type = upstream_response.headers.get("content-type")

            # Post-response poison processing (semantic entropy)
            resp_content, resp_poisons = poison_engine.process_response(
                resp_content, media_type
            )
            triggered_poisons.extend(resp_poisons)

            resp_headers = dict(upstream_response.headers)
            resp_headers.pop("content-encoding", None)
            resp_headers.pop("content-length", None)

            log_intercept(
                proxy_name,
                request.method,
                path,
                upstream_response.status_code,
                triggered_poisons,
            )

            return Response(
                content=resp_content,
                status_code=upstream_response.status_code,
                headers=resp_headers,
                media_type=media_type,
            )
        except httpx.HTTPError as exc:
            log_intercept(proxy_name, request.method, path, 502, ["error"])
            return Response(
                content=f"Shuffler Proxy Error: {exc}",
                status_code=502,
            )

    return app
