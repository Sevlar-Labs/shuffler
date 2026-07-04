---
name: shuffler:behavioral-fidelity-simulation
description: Enforces precise behavioral alignment of the local mock validation layers with legacy enterprise API transport physics. Use when modifying shuffler/gatekeeper/server.py or altering how endpoints process extra keys versus type mutations.
---

# Behavioral Fidelity Simulation

This skill enforces strict adherence to real-world software transport layers during chaos simulation testing. Standard LLM agents instinctively build "perfectly sanitized" endpoints that reject all schema structural anomalies. Doing so breaks Shuffler's primary goal: acting as an accurate diagnostic mirror for flawed, production-grade enterprise API gateways.

## When to use this skill

- Use this when modifying the validation parameters inside `shuffler/gatekeeper/server.py`.
- Use this when altering how the mock server processes incoming JSON structures, webhooks, or object parameters.
- This is helpful for ensuring that Shuffler accurately reflects real-world SaaS boundaries (specifically HubSpot behavior matrices) to maintain maximum engineering credibility during technical evaluations.

## How to use it

When writing or refactoring the server-side ingress validation code, you must strictly implement and maintain the following three behavioral conditions:

### 1. Lax Enforcement on Schema Structural Hallucinations (Extra Keys)
* **Real-World Behavior:** Enterprise CRMs are built to be flexible data buckets. If an AI agent injects an undocumented, hallucinated property key into an API call, the gateway strips it out and successfully ingests the valid parameters.
* **Implementation Protocol:** If an incoming payload contains keys not declared in the matching Postman collection lock, the server **must not** throw an error. It must accept the payload and return an `HTTP 201 Created` or `HTTP 200 OK` transaction state.

### 2. Strict Enforcement on Serialization Type Mutations
* **Real-World Behavior:** Production database constraints and framework serialization engines (such as Pydantic, Marshmallow, or Jackson) are completely rigid regarding primitives. Passing a alphanumeric text string into a strictly defined integer or float column causes a fatal processing crash.
* **Implementation Protocol:** Iterate through intersecting keys defined in the Postman schema lock. If an incoming value violates its primitive contract (e.g., a string injected into an inferred numeric field), the server **must** instantly reject the transaction and return an `HTTP 400 Bad Request` status.

### 3. Deliberate Idempotency Blindness (Concurrency Race Conditions)
* **Real-World Behavior:** Legacy API configurations lack atomic distributed locks. When multi-threaded network clients fire multiple identical requests simultaneously due to transport retries, the server creates redundant target rows.
* **Implementation Protocol:** Do not implement database locks, deduplication tokens, or memory caches to trap repeat operations on the mock server. If 5 identical payloads arrive concurrently, the server must process all 5 independently and return an `HTTP 201 Created` code for each.
