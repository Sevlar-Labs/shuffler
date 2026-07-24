---
name: shuffler:behavioral-fidelity-simulation
description: Enforces precise behavioral alignment of the Universal Local L7 Chaos Proxy with real-world agentic transport physics and Poison Pills. Use when modifying shuffler/proxy/server.py, shuffler/poisons/, or shuffler.yaml configuration rules.
---

# Behavioral Fidelity Simulation

This skill enforces strict adherence to real-world software transport layers during agentic chaos proxying. Standard LLM agents instinctively build "perfectly sanitized" endpoints that reject all schema structural anomalies. Doing so breaks Shuffler's primary goal: acting as an accurate, transparent L7 proxy ("Toxiproxy for Agentic Systems") to test downstream agentic resilience against Poison Pills.

## When to use this skill

- Use this when modifying the proxy routing logic inside `shuffler/proxy/server.py`.
- Use this when altering or adding new Poison Pill engines inside `shuffler/poisons/` (`semantic.py`, `temporal.py`, `network.py`).
- Use this when adjusting `shuffler.yaml` declarative proxy schema and poison rules.

## How to use it

When writing or refactoring proxy handlers or poison injection logic, you must strictly implement and maintain the following core behavioral conditions:

### 1. Transparent Reverse Proxying
* **Real-World Behavior:** Shuffler acts as a transparent local sandbox (`localhost:8081`, `localhost:8082`) intercepting traffic between probabilistic AI agents (OpenAI, Anthropic) and deterministic systems (CRMs, DBs).
* **Implementation Protocol:** Forward headers, paths, query parameters, and raw payload bodies faithfully to upstreams while scrubbing `host` and `content-length` headers to prevent upstream drops.

### 2. Decoupled Poison Pill Injection
* **Real-World Behavior:** Real-world enterprise APIs and LLM backends fail probabilistically due to network jitter, connection resets, or markdown/formatting entropy.
* **Implementation Protocol:** 
  * **Semantic Poison (`semantic.py`):** Inject schema entropy into clean JSON payloads (markdown fences ` ```json...``` `, primitive type conversions, extra unexpected keys).
  * **Temporal Poison (`temporal.py`):** Inject artificial latency (`asyncio.sleep`) to expose missing agentic mutexes and race conditions.
  * **Network Poison (`network.py`):** Sever TCP connections mid-flight with HTTP 503 to test agent streaming and drop handling.

### 3. Multi-Port Listener Concurrency
* **Real-World Behavior:** Multi-agent architectures route OpenAI traffic to one port and CRM/Database traffic to another port simultaneously.
* **Implementation Protocol:** Read declarative `shuffler.yaml` definitions and launch concurrent `uvicorn.Server` listeners via `asyncio.gather()`.
