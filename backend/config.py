"""Shared settings for the Campus Customs backend: paths, the one model, and limits."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

BACKEND_DIR = Path(__file__).resolve().parent
ROOT = BACKEND_DIR.parent
PROMPTS_DIR = BACKEND_DIR / "prompts"
ORIGINAL_DB = ROOT / "data" / "campus_customs.db"
WORKING_DB = Path(os.getenv("CAMPUS_CUSTOMS_DB") or ROOT / "data" / "campus_customs_new.db")
MCP_CONFIG = ROOT / ".mcp.json"
AUDIT_PATH = Path(os.getenv("CAMPUS_AUDIT_PATH") or ROOT / "output" / "audit_trail.json")

load_dotenv(find_dotenv(usecwd=True))  # .env in the project folder or any parent folder

# HW5 rule: every agent uses gpt-6-luna through Portkey. Deliberately not an env
# override, so a stray PORTKEY_MODEL in .env cannot switch an agent's model.
MODEL_NAME = "gpt-6-luna"
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")

# gpt-6-luna on Portkey/Azure only allows tool calls on /chat/completions when
# reasoning_effort is "none". No temperature/top_p: the gateway rejects them.
MODEL_SETTINGS = OpenAIChatModelSettings(openai_reasoning_effort="none")

# ---- token / loop guardrails -------------------------------------------------
MAX_DELEGATION_DEPTH = 3        # boss -> specialist -> specialist -> specialist, no deeper
MAX_DELEGATIONS_PER_TICKET = 6  # total hand-offs across the whole ticket run
MAX_TOOL_RESULT_CHARS = 12_000  # truncate anything bigger before it hits the context
# One RunUsage object is shared by every agent in a ticket run, so these caps
# apply to the ticket as a whole, not per agent.
TICKET_USAGE_LIMITS = UsageLimits(
    request_limit=40,
    tool_calls_limit=60,
    total_tokens_limit=150_000,
)


def portkey_key() -> str:
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY not found. Copy .env.example to .env in the project folder and add your key.")
    return key


def get_model() -> OpenAIChatModel:
    """gpt-6-luna via the Portkey gateway (OpenAI-compatible)."""
    client = AsyncOpenAI(
        api_key=portkey_key(),
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": portkey_key()},
    )
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
