<p align="center">
  <img src="./banner.svg" alt="Shuffler Banner" width="100%" />
</p>

Early-stage: interfaces may change.

**A local chaos proxy for AI agent integrations, inspired by Toxiproxy.** Intercept traffic between probabilistic AI agents and deterministic systems to test resilience against network and semantic chaos.

## Overview

Shuffler is a transparent, local L7 reverse proxy that engineering teams install to intercept traffic between AI agents (OpenAI, Anthropic, custom LLM orchestrators) and deterministic backends (CRMs, databases, external APIs).

It injects **Poison Pills** into live data streams to expose brittleness before production deployment:

1. **Semantic (Schema Entropy)** — Randomly mutates clean JSON payloads (wrapping in markdown fences ` ```json...``` `, converting integers to strings, adding extra unexpected keys) to test downstream parser resilience.
2. **Temporal (Network Latency)** — Injects artificial latency (e.g. 45s) to test if agent orchestrators lack Agentic Mutexes and trigger semantic race conditions.
3. **Network (Connection Drops)** — Severs TCP connections mid-stream to test streaming and drop recovery.

## Architecture

```
┌─────────────────┐             ┌─────────────────────┐             ┌──────────────────┐
│  AI Agent       │   HTTP      │  Shuffler L7 Proxy  │   HTTP      │  Real Upstream   │
│  (Orchestrator) │ ──────────► │  (localhost:8081)   │ ──────────► │  (OpenAI, CRM)   │
│                 │             │                     │             │                  │
└─────────────────┘             └──────────┬──────────┘             └──────────────────┘
                                           │
                                ┌──────────▼──────────┐
                                │   Poisons Engine    │
                                │  (Semantic/Network) │
                                └─────────────────────┘
```

## Prerequisites

- Python 3.11+
- `httpx`, `fastapi`, `uvicorn`, `pyyaml`, `pydantic`

## Installation

### Option A: Global Installation (Recommended for End Users / SREs)

```bash
pipx install --editable . --force
```

After installation, the **`shuffler`** binary is available system-wide.

### Option B: Virtual Environment (Recommended for Contributors)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Declarative Configuration (`shuffler.yaml`)

Shuffler is governed by a declarative `shuffler.yaml` file defining proxies, upstreams, and poison injection probabilities:

```yaml
proxies:
  openai:
    port: 8081
    upstream: "https://api.openai.com"
    poisons:
      semantic: 0.15
      temporal: 0.05
  crm:
    port: 8082
    upstream: "http://localhost:8000"
    poisons:
      network: 0.10
```

## Usage

Start the multi-port proxy listeners:

```bash
shuffler serve --config shuffler.yaml
```

Shuffler will spin up concurrent Uvicorn listeners on ports `8081` and `8082`, transparently proxying requests to upstreams while injecting Poison Pills according to configured probabilities.

## Testing

Run the automated test suite:

```bash
python -m pytest -v
```

## License

Licensed under the **MIT License**. See [LICENSE](./LICENSE) for details.
