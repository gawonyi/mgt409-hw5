"""The only way the backend touches shop data: the campus-customs MCP server from .mcp.json.

Each agent gets a filtered view of one shared MCP connection that exposes only
the tools its role needs. The two cash-moving tools are never exposed to any
agent; only the human approval route calls them (call_human_tool).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic_ai.mcp import MCPToolset

from config import MCP_CONFIG, ROOT

HUMAN_ONLY_TOOLS = frozenset({"execute_approved_payment", "reject_payment_request"})

_COMMON = {"get_shop_date", "get_ticket", "list_tickets"}
ROLE_TOOLS: dict[str, frozenset[str]] = {
    "boss": frozenset(_COMMON | {"get_cash_balance", "list_payment_requests", "update_ticket_status"}),
    "inventory": frozenset(_COMMON | {
        "check_stock_by_sku_size", "list_vendors", "list_open_invoices", "get_sku_pricing",
        "request_restock_purchase", "add_ticket_note",
    }),
    "accounting": frozenset(_COMMON | {
        "get_cash_balance", "get_invoice", "list_open_invoices", "list_payments", "list_payment_requests",
        "get_sku_pricing", "quote_bulk_discount", "get_lease_rent_due", "list_vendors",
        "request_invoice_payment", "request_rent_payment", "request_restock_purchase", "add_ticket_note",
    }),
    "facilities": frozenset(_COMMON | {"get_lease_rent_due", "list_payments", "list_payment_requests", "add_ticket_note"}),
    "customer_service": frozenset(_COMMON | {
        "check_stock_by_sku_size", "get_sku_pricing", "quote_bulk_discount", "list_vendors", "add_ticket_note",
    }),
}
assert not any(HUMAN_ONLY_TOOLS & tools for tools in ROLE_TOOLS.values())


def _transport() -> StdioTransport:
    cfg = json.loads(MCP_CONFIG.read_text())["mcpServers"]["campus-customs"]
    command = sys.executable if cfg["command"] in ("python", "python3") else cfg["command"]
    env = dict(cfg.get("env") or {})
    if os.getenv("CAMPUS_CUSTOMS_DB"):  # test override only; never send API keys to the server
        env["CAMPUS_CUSTOMS_DB"] = os.environ["CAMPUS_CUSTOMS_DB"]
    return StdioTransport(command=command, args=cfg["args"], env=env or None, cwd=str(ROOT))


def shared_toolset() -> MCPToolset:
    """One MCP connection per ticket run; enter it with `async with` before running agents."""
    return MCPToolset(Client(_transport()))


def role_toolset(base: MCPToolset, role: str):
    allowed = ROLE_TOOLS[role]
    return base.filtered(lambda ctx, tool_def: tool_def.name in allowed)


# One long-lived MCP connection for the API routes, so the board's polling does
# not start a new server process per request.
_route_client: Client | None = None
_route_lock = asyncio.Lock()


async def _get_route_client() -> Client:
    global _route_client
    async with _route_lock:
        if _route_client is None or not _route_client.is_connected():
            _route_client = Client(_transport())
            await _route_client.__aenter__()
        return _route_client


async def close_route_client() -> None:
    """Drop the shared connection (on shutdown, and after a DB reset so the server re-creates its tables)."""
    global _route_client
    async with _route_lock:
        if _route_client is not None:
            try:
                await _route_client.__aexit__(None, None, None)
            finally:
                _route_client = None


async def call_human_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """For the API routes only (human approve / reject, board reads)."""
    client = await _get_route_client()
    result = await client.call_tool(name, args)
    return result.data if result.data is not None else json.loads(result.content[0].text)
