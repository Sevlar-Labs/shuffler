import asyncio
import json
import os

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, Header
from pydantic import BaseModel

load_dotenv()

# Initialize the API Framework
app = FastAPI()

# Configure the Live Probabilistic Model
# It requires the API key to be exported in your terminal environment
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))
model = genai.GenerativeModel("gemini-3.1-flash-lite")

_hallucination_lock: asyncio.Lock = asyncio.Lock()
_hallucination_counter: int = 0


class LeadInput(BaseModel):
    raw_text: str


@app.post("/agent/extract")
async def extract_lead(payload: LeadInput, x_chaos_mode: str = Header(default="normal")):
    print(f"\n--- [INGESTION] Raw payload received: '{payload.raw_text}' ---")
    print(f"[*] Chaos Header Status: {x_chaos_mode.upper()}")

    # The Prompt: Forcing deterministic structure from a probabilistic mind
    prompt = (
        "    You are a data extraction agent. Extract the lead information from the "
        "following text and return strictly valid JSON.\n"
        "    CRITICAL STRUCTURE INSTRUCTIONS:\n"
        "    1. Return a single, flat JSON object {}, NOT an array [].\n"
        '    2. Use lower-case keys exactly as written here: "firstname" and "email".\n'
        "    3. If the email address is missing from the text, return the value as "
        '"unknown@example.com" so the system has a valid primary key.\n\n'
        f"    Text: {payload.raw_text}\n"
    )

    # ---------------------------------------------------------
    # CHAOS VECTOR A: TEMPORAL ENTROPY (The Latency Strike)
    # ---------------------------------------------------------
    if x_chaos_mode == "latency":
        print(
            "[FATAL] Kill Switch Activated: Injecting 35-second temporal delay "
            "to shatter orchestrator timeout limits..."
        )
        await asyncio.sleep(35)
        # The orchestrator will panic and double-fire during this sleep window.

    print("[*] Contacting the live LLM...")
    response = model.generate_content(prompt)
    ai_output = response.text.strip()

    # ---------------------------------------------------------
    # CHAOS VECTOR B: SCHEMA ENTROPY (The Data Hallucination)
    # ---------------------------------------------------------
    if x_chaos_mode == "hallucination":
        global _hallucination_counter
        async with _hallucination_lock:
            _hallucination_counter += 1
            current_count = _hallucination_counter
        if current_count % 2 != 0:
            print(
                "[FATAL] Kill Switch Activated: Mutating payload to corrupt CRM "
                "schema boundaries..."
            )
            # Wrapping the output in markdown backticks destroys legacy CRM JSON parsers.
            return {"raw_output": f"```json\n{ai_output}\n```"}
        else:
            print("[V] Recovering from hallucination on retry...")

    # ---------------------------------------------------------
    # STEADY STATE: NORMAL EXECUTION
    # ---------------------------------------------------------
    print("[V] Extraction successful. Returning mapped JSON to orchestrator.")
    try:
        # Strip potential markdown formatting to ensure a clean handoff
        clean_json = ai_output.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"[!] Natural parsing error: {e}")
        return {"error": "Failed to parse LLM output."}
