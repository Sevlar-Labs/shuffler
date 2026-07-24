---
name: shuffler:chaos-telemetry-orchestration
description: Governs real-time L7 proxy telemetry, poison injection tracing, and multi-port listener visualization using Rich console logs. Use when modifying shuffler/proxy/telemetry.py or shuffler/main.py.
---

# Chaos Telemetry Orchestration

This skill governs the presentation layer and real-time execution monitoring of Shuffler's Universal Local L7 Chaos Proxy. Because Shuffler is an open-source technical auditing utility, its console output must act as an objective, highly informative SRE audit log. Intercepted transactions and poison pill injections must be rendered with full transparency.

## When to use this skill

- Use this when modifying the `serve` command or server management in `shuffler/main.py`.
- Use this when adjusting telemetry intercept logging in `shuffler/proxy/telemetry.py`.
- Use this when adding new poison pill notifications or Rich console display panels.

## How to use it

When designing or refactoring CLI command flows or telemetry outputs, you must strictly implement and maintain the following logging conventions:

### 1. Intercept & Poison Logging (`shuffler/proxy/telemetry.py`)
* **Convention:** Every intercepted L7 transaction passing through the proxy must be logged to the console with clear indicator tags showing whether it was a clean passthrough or if a Poison Pill was injected.
* **Pattern:** Render `[PASSTHROUGH]` for clean requests and `⚡ [POISON INJECTED: <POISON_TYPE>]` for mutated or delayed requests, annotated with the proxy name, HTTP method, request path, and resulting status code.

### 2. Multi-Port Listener Debrief (`shuffler/main.py`)
* **Convention:** On startup, render a Rich Panel for each configured proxy endpoint in `shuffler.yaml` detailing its target upstream, binding port, and active poison probabilities.
* **Pattern:** Display clear status updates as concurrent Uvicorn listeners are spawned via `asyncio.gather()`.

### 3. High-Fidelity SRE Styling and Console Aesthetics
* **Convention:** Standard Python `print()` statements are strictly banned for core execution flows. All layout structures must rely on the `rich` library to present clean grids, panels, and text blocks.
* **Color Schemes:** Use functional color mappings:
  * `bold bright_white` and `bold cyan` for proxy headers and endpoints.
  * `bold green` for upstream targets and clean HTTP 2xx transactions.
  * `bold yellow` for binding ports and HTTP verbs.
  * `bold red` for active poison pill injections (`[POISON INJECTED: SEMANTIC]`, `[POISON INJECTED: NETWORK]`) and 5xx/4xx errors.
  * `dim` gray for passthrough logs and standard boilerplate.
