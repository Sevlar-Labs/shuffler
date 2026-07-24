import pytest
from fastapi import FastAPI
import httpx

from shuffler.config import ProxyConfig
from shuffler.poisons.engine import PoisonEngine
from shuffler.poisons.semantic import mutate_json_payload
from shuffler.proxy.server import create_proxy_app


def test_poison_engine_probabilities():
    engine = PoisonEngine({"semantic": 1.0, "temporal": 0.0})
    assert engine.should_trigger("semantic") is True
    assert engine.should_trigger("temporal") is False


def test_semantic_mutation():
    payload = b'{"status": "ok", "code": 200}'
    mutated = mutate_json_payload(payload)
    assert mutated != payload
    assert (
        b"```json" in mutated
        or b'"code": "200"' in mutated
        or b"_shuffler_poison_entropy" in mutated
    )


@pytest.mark.anyio
async def test_network_poison_interception():
    proxy_conf = ProxyConfig(
        port=8081,
        upstream="http://upstream.local",
        poisons={"network": 1.0},
    )
    proxy_app = create_proxy_app("openai", proxy_conf)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=proxy_app), base_url="http://localhost:8081"
    ) as client:
        resp = await client.get("/test")
        assert resp.status_code == 503
        assert "TCP connection severed" in resp.text


@pytest.mark.anyio
async def test_semantic_poison_end_to_end():
    upstream_app = FastAPI()

    @upstream_app.get("/data")
    async def get_data():
        return {"status": "success", "items_count": 42}

    upstream_transport = httpx.ASGITransport(app=upstream_app)

    proxy_conf = ProxyConfig(
        port=8081,
        upstream="http://upstream.local",
        poisons={"semantic": 1.0},
    )
    proxy_app = create_proxy_app("crm", proxy_conf)

    async with httpx.AsyncClient(
        transport=upstream_transport, base_url="http://upstream.local"
    ) as client:
        proxy_app.state.client = client

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=proxy_app), base_url="http://localhost:8081"
        ) as proxy_client:
            resp = await proxy_client.get("/data")
            assert resp.status_code == 200
            body = resp.text
            assert (
                "```json" in body
                or '"items_count": "42"' in body
                or "_shuffler_poison_entropy" in body
            )
