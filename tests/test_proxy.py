import httpx
import pytest
from fastapi import FastAPI, Request

from shuffler.config import ProxyConfig, load_config
from shuffler.proxy.server import create_proxy_app


def test_config_parsing(tmp_path):
    config_file = tmp_path / "shuffler.yaml"
    config_file.write_text(
        """
proxies:
  openai:
    port: 8081
    upstream: "https://api.openai.com"
    poisons:
      semantic: 0.20
  crm:
    port: 8082
    upstream: "http://localhost:9000"
    poisons:
      temporal: 0.10
"""
    )

    config = load_config(str(config_file))
    assert len(config.proxies) == 2
    assert config.proxies["openai"].port == 8081
    assert config.proxies["openai"].upstream == "https://api.openai.com"
    assert config.proxies["openai"].poisons["semantic"] == 0.20
    assert config.proxies["crm"].port == 8082


@pytest.mark.anyio
async def test_proxy_app_creation():
    proxy_conf = ProxyConfig(
        port=8081,
        upstream="https://httpbin.org",
        poisons={"semantic": 0.1},
    )
    app = create_proxy_app("openai", proxy_conf)
    assert isinstance(app, FastAPI)


@pytest.mark.anyio
async def test_proxy_forwarding():
    upstream_app = FastAPI()

    @upstream_app.post("/v1/chat/completions")
    async def chat(request: Request):
        data = await request.json()
        return {"id": "chatcmpl-123", "received": data}

    upstream_transport = httpx.ASGITransport(app=upstream_app)

    proxy_conf = ProxyConfig(
        port=8081,
        upstream="http://upstream.local",
        poisons={},
    )
    proxy_app = create_proxy_app("openai", proxy_conf)

    async with httpx.AsyncClient(
        transport=upstream_transport, base_url="http://upstream.local"
    ) as client:
        proxy_app.state.client = client

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=proxy_app), base_url="http://localhost:8081"
        ) as proxy_client:
            resp = await proxy_client.post(
                "/v1/chat/completions", json={"prompt": "hello"}
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == "chatcmpl-123"
            assert data["received"] == {"prompt": "hello"}
