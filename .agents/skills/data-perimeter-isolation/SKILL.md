---
name: shuffler:data-perimeter-isolation
description: Establishes a strict data perimeter and intellectual property firewall to protect third-party proprietary data assets. Use when adding test schemas, modifying .gitignore configurations, or ensuring vendor-specific production data never enters repository tracking.
---

# Data Perimeter Isolation

This skill enforces strict compliance and legal firewalls regarding third-party proprietary data assets. As an open-source utility, Shuffler must never inadvertently leak, hardcode, or store production API schemas from enterprise targets (e.g., live HubSpot, Salesforce, or Stripe accounts) within its repository history.

## When to use this skill

- Use this when adding new test collections, API fixtures, or Postman files to the repository.
- Use this when adjusting repository tracking configurations, such as `.gitignore` or Docker environments.
- This is helpful for protecting proprietary intellectual property and ensuring the public codebase remains safe and compliant for open-source distribution.

## How to use it

When manipulating files, creating schemas, or setting up testing environments, you must strictly implement and maintain the following data protection protocols:

### 1. Zero-Trust Local Isolation
* **Protocol:** Mandate that all core testing relies exclusively on non-proprietary mock primitives (e.g., `examples/dummy_crm.postman_collection.json`). Real production client data, exported schemas, or proprietary JSON dumps must never be committed to the repository under any circumstances.

### 2. Automated Git Guardrails
* **Protocol:** Ensure that any customer-specific production schema files, local `.env` files containing API keys, or live telemetry dumps are explicitly captured by local ignoring mechanisms. If asked to test against a live endpoint locally, verify that the configuration and authentication context are entirely untracked.

### 3. Abstracting Vendor Footprints
* **Protocol:** When creating default schemas or templates for the community, keys and endpoints must be genericized. Use universally understood placeholders (e.g., `/api/v1/leads`, `customer_id`, or `lead_score`) instead of client-specific or vendor-specific architectures that could betray a proprietary system's internal structure.
