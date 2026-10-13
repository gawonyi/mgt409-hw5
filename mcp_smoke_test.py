"""Problem 4 smoke test: a Portkey-backed agent calls each Campus Customs MCP tool.

The agent connects to the MCP server listed in .mcp.json (the same file Claude
Code / Cursor read), gets one plain-English prompt per tool, and must answer by
calling the tool. The script records the prompt, the tool the model actually
called, its arguments, and the raw tool output, then checks that output against
data/campus_customs_new.db and writes output/mcp_smoke.json.

Run:  python3 mcp_smoke_test.py            (default model gpt-6-luna)
      python3 mcp_smoke_test.py --model gpt-5.6-luna
      python3 mcp_smoke_test.py --list-models
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import find_dotenv, load_dotenv
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from openai import AsyncOpenAI, OpenAI
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "campus_customs_new.db"
MCP_CONFIG = ROOT / ".mcp.json"
OUT_PATH = ROOT / "output" / "mcp_smoke.json"

load_dotenv(find_dotenv(usecwd=True))  # .env in the project folder or any parent folder
# HW5 requires gpt-6-luna; HW5_MODEL / --model override it on purpose only.
DEFAULT_MODEL = os.getenv("HW5_MODEL", "gpt-6-luna")
BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
# gpt-6-luna on Portkey (Azure) rejects tool calls on /chat/completions unless
# reasoning_effort is "none", so we send it explicitly. Override with HW5_REASONING_EFFORT.
MODEL_SETTINGS = OpenAIChatModelSettings(openai_reasoning_effort=os.getenv("HW5_REASONING_EFFORT", "none"))

INSTRUCTIONS = """You are testing the Campus Customs MCP server.
Answer every question by calling exactly one campus-customs MCP tool.
Report only values the tool returned. If a tool did not return it, say you do not know.
Keep the answer to one or two sentences."""

# One prompt per Problem 3 tool. `check` pulls the same facts straight from the
# DB so the script can prove the tool output is real, not just plausible.
TESTS: list[dict[str, Any]] = [
    {
        "ticket": 101,
        "expected_tool": "check_stock_by_sku_size",
        "prompt": "Ticket 101: Tauhid Zaman wants one CC-TEE-WHITE in size S. "
        "Use the campus-customs MCP server to check whether that size is in stock.",
        "check_sql": "SELECT qty AS qty_on_hand, location FROM inventory WHERE sku='CC-TEE-WHITE' AND size='S'",
    },
    {
        "ticket": 102,
        "expected_tool": "get_lease_rent_due",
        "prompt": "Ticket 102 is a rent notice for lease 1. Use the campus-customs MCP server "
        "to look up the landlord, monthly rent, and next due date.",
        "check_sql": "SELECT landlord, monthly_rent, next_due FROM leases WHERE id=1",
    },
    {
        "ticket": 103,
        "expected_tool": "get_sku_pricing",
        "prompt": "Ticket 103: the Yale AI Club wants a bulk discount on CC-HOOD-NAVY hoodies. "
        "Use the campus-customs MCP server to get the unit cost and list price.",
        "check_sql": "SELECT unit_cost, list_price FROM pricing WHERE sku='CC-HOOD-NAVY'",
    },
]


def portkey_key() -> str:
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        sys.exit("PORTKEY_API_KEY not found. Copy .env.example to .env in the project folder and add your key.")
    return key


def get_model(name: str) -> Model:
    client = AsyncOpenAI(
        api_key=portkey_key(),
        base_url=BASE_URL,
        default_headers={"x-portkey-api-key": portkey_key()},
    )
    return OpenAIChatModel(name, provider=OpenAIProvider(openai_client=client))


def mcp_toolset() -> MCPToolset:
    """Start the server exactly as .mcp.json describes it."""
    cfg = json.loads(MCP_CONFIG.read_text())["mcpServers"]["campus-customs"]
    command = cfg["command"]
    # Use this interpreter so the server sees the same installed packages (venv-safe).
    if Path(command).name.startswith("python"):
        command = sys.executable
    transport = StdioTransport(command=command, args=cfg["args"], env=cfg.get("env") or None, cwd=str(ROOT))
    return MCPToolset(Client(transport))


def db_expected(sql: str) -> dict:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(sql).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def as_json(content: Any) -> Any:
    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    if hasattr(content, "model_dump"):
        return content.model_dump()
    return content


async def run_tests(model: Model, model_name: str) -> dict:
    agent = Agent(model, instructions=INSTRUCTIONS, toolsets=[mcp_toolset()], model_settings=MODEL_SETTINGS)
    results = []
    async with agent:
        for t in TESTS:
            entry: dict[str, Any] = {"ticket": t["ticket"], "prompt": t["prompt"]}
            try:
                run = await agent.run(t["prompt"])
            except Exception as exc:  # show the real error, never fake a result
                entry["error"] = f"{type(exc).__name__}: {exc}"
                results.append(entry)
                print(f"[{t['ticket']}] ERROR {entry['error']}")
                continue
            calls = [p for m in run.new_messages() for p in m.parts if isinstance(p, ToolCallPart)]
            returns = {p.tool_call_id: p for m in run.new_messages() for p in m.parts if isinstance(p, ToolReturnPart)}
            if not calls:
                entry["error"] = "Model answered without calling a tool."
            else:
                call = calls[0]
                output = as_json(returns[call.tool_call_id].content) if call.tool_call_id in returns else None
                expected = db_expected(t["check_sql"])
                matches = isinstance(output, dict) and all(output.get(k) == v for k, v in expected.items())
                entry.update(
                    tool_name=call.tool_name,
                    tool_args=call.args_as_dict(),
                    tool_output=output,
                    model_answer=run.output,
                    db_check={
                        "database": "data/campus_customs_new.db",
                        "sql": t["check_sql"],
                        "expected": expected,
                        "matches_db": matches,
                    },
                )
            results.append(entry)
            status = "OK" if entry.get("db_check", {}).get("matches_db") else "CHECK"
            print(f"[{t['ticket']}] {status} tool={entry.get('tool_name')} -> {entry.get('tool_output') or entry.get('error')}")
    return {
        "test": "Problem 4 MCP smoke test",
        "mcp_config": ".mcp.json (server: campus-customs)",
        "client": "PydanticAI agent via Portkey",
        "model": model_name,
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "all_match_db": all(r.get("db_check", {}).get("matches_db") for r in results),
        "results": results,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--list-models", action="store_true")
    args = ap.parse_args()

    if args.list_models:
        client = OpenAI(api_key=portkey_key(), base_url=BASE_URL, default_headers={"x-portkey-api-key": portkey_key()})
        for m in client.models.list():
            print(m.id)
        return

    report = asyncio.run(run_tests(get_model(args.model), args.model))
    OUT_PATH.parent.mkdir(exist_ok=True)
    # Keep the vibe-coder evidence already in the file; this script only owns its own section.
    existing = json.loads(OUT_PATH.read_text()) if OUT_PATH.exists() else {"test": report["test"]}
    existing["supporting_portkey_test"] = {
        "description": "Automated check: a gpt-6-luna agent on Portkey connects through .mcp.json, "
                       "chooses and calls each tool itself, and every output is compared with the database.",
        **{k: v for k, v in report.items() if k != "test"},
    }
    OUT_PATH.write_text(json.dumps(existing, indent=2))
    print(f"\nWrote {OUT_PATH.relative_to(ROOT)}  (all_match_db={report['all_match_db']})")
    if not report["all_match_db"]:
        print("Next step: read the CHECK/ERROR lines above; try --model gpt-5.6-luna if the model skipped tools.")


if __name__ == "__main__":
    main()
