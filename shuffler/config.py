"""Configuration parsing for Shuffler."""

from __future__ import annotations

import yaml
from pydantic import BaseModel, Field


class ProxyConfig(BaseModel):
    port: int
    upstream: str
    poisons: dict[str, float] = Field(default_factory=dict)


class ShufflerConfig(BaseModel):
    proxies: dict[str, ProxyConfig]


def load_config(path: str) -> ShufflerConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return ShufflerConfig(**data)
