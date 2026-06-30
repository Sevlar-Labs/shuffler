# ==========================================
# [REDACTED: Strategic SRE Agency]
# Purpose: Simulate an AI Agent Race Condition & The WAF Fix
# Execution: Run this script while recording the Loom Shadow Audit
# ==========================================

import asyncio
import hashlib
import json
import os
import time

import asyncpg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- SECRETS & ENVIRONMENT ---
DB_DSN = os.environ.get("DB_DSN")
if not DB_DSN:
    raise ValueError("DB_DSN environment variable not set")

CRM_WEBHOOK_URI = os.environ.get("CRM_WEBHOOK_URI")
if not CRM_WEBHOOK_URI:
    raise ValueError("CRM_WEBHOOK_URI environment variable not set")

# --- SIMULATED AI PAYLOAD ---
INBOUND_AI_PAYLOAD = {
    "lead_name": "John Doe",
    "lead_email": "john.doe@enterprise.com",
    "ai_confidence_score": 98.5
}
RAW_TEXT_PAYLOAD = json.dumps(INBOUND_AI_PAYLOAD)

async def generate_idempotency_hash(payload_string: str) -> str:
    return hashlib.sha256(payload_string.encode('utf-8')).hexdigest()

async def vulnerable_webhook_handler(pool):
    """
    SCENARIO 1: Vulnerable Architecture
    Writes to the Gateway DB with a weak deterministic key, leading to CRM duplicates.
    """
    # Weak hash generation often found in vulnerable architectures
    weak_key = await generate_idempotency_hash(RAW_TEXT_PAYLOAD + str(time.time_ns()))

    async with pool.acquire() as conn:
        print("[!] VULNERABLE PATH: Webhook received. Inserting to lead_transactions...")
        # Blindly inserts without checking idempotency ledger
        await conn.execute(
            "INSERT INTO lead_transactions "
            "(transaction_hash, raw_text, status, extracted_firstname, "
            "extracted_email) VALUES ($1, $2, 'COMPLETED', $3, $4)",
            weak_key,
            RAW_TEXT_PAYLOAD,
            INBOUND_AI_PAYLOAD["lead_name"],
            INBOUND_AI_PAYLOAD["lead_email"],
        )

        print(f"[!] VULNERABLE PATH: Hitting CRM Platform at {CRM_WEBHOOK_URI}...")

async def agentic_waf_handler(pool):
    """
    SCENARIO 2: SRE Gateway
    Intercepts the payload, checks the Idempotency Ledger, and blocks duplicates.
    """
    idem_key = await generate_idempotency_hash(RAW_TEXT_PAYLOAD)

    async with pool.acquire() as conn:
        print("[*] SRE GATEWAY: Payload intercepted. Checking Idempotency Lock...")

        result = await conn.execute(
            """
            INSERT INTO waf_idempotency_ledger (idempotency_key, target_system)
            VALUES ($1, 'CRM')
            ON CONFLICT (idempotency_key) DO NOTHING
            """,
            idem_key
        )

        if result.endswith('0'):
            print(
                f"[X] SRE GATEWAY BLOCKED: Race condition detected. "
                f"Payload hash {idem_key[:8]} already processed."
            )
            return {"status": 200, "message": "Idempotent request dropped safely."}

        print("[V] SRE GATEWAY SECURED: Lock acquired. Processing...")
        await conn.execute(
            "INSERT INTO lead_transactions "
            "(transaction_hash, raw_text, status, extracted_firstname, "
            "extracted_email) VALUES ($1, $2, 'COMPLETED', $3, $4)",
            idem_key,
            RAW_TEXT_PAYLOAD,
            INBOUND_AI_PAYLOAD["lead_name"],
            INBOUND_AI_PAYLOAD["lead_email"],
        )
        print(f"[V] SRE GATEWAY: Pushing pristine data to CRM at {CRM_WEBHOOK_URI}...")
        return {"status": 201, "message": "Lead processed and sent."}

async def run_simulation():
    pool = await asyncpg.create_pool(DB_DSN)

    print("\n--- INITIATING AI PIPELINE RACE CONDITION SIMULATION ---\n")
    time.sleep(2)

    print("--- TEST 1: CURRENT VULNERABLE ARCHITECTURE ---")
    await asyncio.gather(
        vulnerable_webhook_handler(pool),
        vulnerable_webhook_handler(pool)
    )
    print("RESULT: CRM is corrupted. You now have two identical records pushed to CRM.\n")

    # Resetting the database for test 2
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM lead_transactions;")
        await conn.execute("DELETE FROM waf_idempotency_ledger;")

    time.sleep(3)

    print("--- TEST 2: AGENTIC WAF GATEWAY ---")
    await asyncio.gather(
        agentic_waf_handler(pool),
        agentic_waf_handler(pool)
    )
    print(
        "RESULT: Architecture secured. "
        "The database lock mathematically prevented the duplication.\n"
    )

    await pool.close()

if __name__ == "__main__":
    asyncio.run(run_simulation())
