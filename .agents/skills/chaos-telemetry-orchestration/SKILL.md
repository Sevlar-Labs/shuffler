---
name: shuffler:chaos-telemetry-orchestration
description: Governs high-concurrency asynchronous stream logging and transaction-pair visualization. Use when modifying the attack command in shuffler/main.py, adjusting async loops, or formatting output tracking tables using the Rich console.
---

# Chaos Telemetry Orchestration

This skill governs the presentation layer and real-time execution monitoring of Shuffler's asynchronous attack engine. Because Shuffler is an open-source technical auditing utility, its output terminal must act as an objective, highly informative SRE audit log. Hiding network transactions or abstracting away payload lifecycle details compromises the utility's transparency and reduces its effectiveness as a diagnostic tool.

## When to use this skill

- Use this when modifying the `attack` command or async loops inside `shuffler/main.py`.
- Use this when adjusting concurrency thresholds, network timeouts, or handling HTTP transaction states.
- This is helpful for keeping the user interface uniform, ensuring that highly parallelized network operations remain completely transparent and chronological.

## How to use it

When designing or refactoring CLI command flows or output structures, you must strictly implement and maintain the following logging conventions:

### 1. Unified Outbound-Inbound Pair Capture
* **Convention:** Every asynchronous network task must be packaged inside a coroutine wrapper that explicitly captures both the exact mutated JSON string sent out and the raw HTTP text response received back.
* **Pattern:** Do not let tasks execute silently or return loose responses. You must keep the correlation between input payload mutation type (e.g., `EXTRA_KEY`, `TYPE_MUTATION`) and the resulting gatekeeper status code explicitly linked through a tuple or structured object return.

### 2. Comprehensive, Sequential Trace Streams
* **Convention:** Never truncate, group, or suppress individual transactions within a burst just to keep the terminal tidy. If a user sets a `--burst` value of 5 or 10, the trace log must explicitly render 5 or 10 independent sequential log entries.
* **Pattern:** Display every request chronologically as an indexed list item (`PAYLOAD 1/5`, `PAYLOAD 2/5`). Every line must render:
  * The exact outbound data block.
  * The precise inbound server response status and message payload.

### 3. High-Fidelity SRE Styling and Console Aesthetics
* **Convention:** Standard Python `print()` statements are strictly banned for core execution flows. All layout structures must rely on the `rich` library to present clean grids, panels, and text blocks.
* **Color Schemes:** Use functional color mappings to instantly communicate network states:
  * `bold yellow` for labeling outbound mutation configurations.
  * `green` for accepted or baseline HTTP transaction states (e.g., HTTP 200, HTTP 201).
  * `red` for blocked transactions, serialization failures, or network drops (e.g., HTTP 400, connection errors).
  * `dim` gray for structural boilerplate text (e.g., labels like `Outbound:` or `Inbound:`).
