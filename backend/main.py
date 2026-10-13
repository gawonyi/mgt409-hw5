"""Campus Customs desk API (FastAPI). The React board (Problem 8) calls these routes.

Run from backend/:  uvicorn main:app --reload --port 8000   ->  http://localhost:8000
Docs:              http://localhost:8000/docs

Every shop read and write goes through the campus-customs MCP server. Agents
can only prepare payment requests; the ONLY route that moves cash is
POST /api/payment-requests/{id}/approve, which needs a human's name.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from contextlib import asynccontextmanager
from typing import Any

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import agents
import audit
from config import ORIGINAL_DB, WORKING_DB
from mcp_client import call_human_tool, close_route_client
from models import ApprovalRequest, RunStatus, TicketRunResult

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_route_client()


app = FastAPI(title="Campus Customs Desk API", version="1.0", lifespan=lifespan)

# The Vite dev server (Problem 8) runs on 5173.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RUNS: dict[str, RunStatus] = {}          # run_id -> status/result
LATEST_RUN: dict[int, str] = {}          # ticket_id -> latest run_id
_TASKS: set[asyncio.Task] = set()
_run_lock = asyncio.Lock()               # one ticket run at a time: they share one cash account
TEST_MODEL = None                        # tests swap in a scripted model; production uses gpt-6-luna


def _active_run() -> RunStatus | None:
    return next((r for r in RUNS.values() if r.state == "running"), None)


def _system_log(step: str, ticket_id: int, detail: dict[str, Any], agent: str = "human") -> None:
    audit.log(run_id="desk", ticket_id=ticket_id, agent=agent, depth=0, chain=[agent], step=step, detail=detail)


# ------------------------------------------------------------------ tickets


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "working_db": WORKING_DB.name, "running": _active_run() is not None}


@app.get("/api/tickets")
async def list_tickets() -> dict:
    """The three tickets, each with status (open | awaiting_approval | resolved) and pending requests."""
    tickets = (await call_human_tool("list_tickets", {}))["tickets"]
    pending = (await call_human_tool("list_payment_requests", {"status": "pending"}))["requests"]
    active = _active_run()
    for t in tickets:
        t["pending_request_ids"] = [r["id"] for r in pending if r["ticket_id"] == t["id"]]
        t["latest_run_id"] = LATEST_RUN.get(t["id"])
        t["running"] = bool(active and active.ticket_id == t["id"])
    return {"tickets": tickets}


@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: int) -> dict:
    """One ticket with its notes, payment requests, and the latest agent outcome (summary per agent)."""
    ticket = await call_human_tool("get_ticket", {"ticket_id": ticket_id})
    if not ticket.get("found"):
        raise HTTPException(404, f"No ticket {ticket_id}")
    requests = (await call_human_tool("list_payment_requests", {"ticket_id": ticket_id}))["requests"]
    run = RUNS.get(LATEST_RUN.get(ticket_id, ""))
    return {"ticket": ticket, "payment_requests": requests, "latest_run": run}


@app.post("/api/tickets/{ticket_id}/run", status_code=202)
async def run_ticket(ticket_id: int) -> RunStatus:
    """Start the agent team on one ticket in the background. Poll /api/runs/{run_id} and /api/events."""
    ticket = await call_human_tool("get_ticket", {"ticket_id": ticket_id})
    if not ticket.get("found"):
        raise HTTPException(404, f"No ticket {ticket_id}")
    if ticket["status"] == "resolved":
        raise HTTPException(409, f"Ticket {ticket_id} is already resolved. Reset the database to rerun.")
    if _active_run() or _run_lock.locked():
        raise HTTPException(409, "Another ticket is running; wait for it to finish.")

    placeholder = f"pending-{ticket_id}-{len(RUNS) + 1}"
    status = RunStatus(run_id=placeholder, ticket_id=ticket_id, state="running")
    RUNS[placeholder] = status
    LATEST_RUN[ticket_id] = placeholder

    async def worker() -> None:
        async with _run_lock:
            try:
                result: TicketRunResult = await agents.run_ticket(ticket_id, model=TEST_MODEL)
                status.result = result
                status.state = "error" if result.error else "done"
            except Exception as exc:  # surface the real error to the board
                status.result = TicketRunResult(run_id=placeholder, ticket_id=ticket_id, error=str(exc))
                status.state = "error"
            if status.result and status.result.run_id != placeholder:
                RUNS[status.result.run_id] = status
                status.run_id = status.result.run_id
                LATEST_RUN[ticket_id] = status.run_id

    task = asyncio.create_task(worker())
    _TASKS.add(task)
    task.add_done_callback(_TASKS.discard)
    return status


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str) -> RunStatus:
    """State of one run (running | done | error) and, when done, the Boss's TicketOutcome."""
    if run_id not in RUNS:
        raise HTTPException(404, f"No run {run_id}")
    return RUNS[run_id]


# ------------------------------------------------------------------- events


def _event_view(e: dict[str, Any]) -> dict[str, Any]:
    """Board-friendly shape: who acted, what they said, which tools they used."""
    d = e.get("detail", {})
    view = {k: e.get(k) for k in ("seq", "ts", "run_id", "ticket_id", "agent", "depth", "step")}
    if e["step"] == "model_response":
        view["said"] = d.get("text") or None
        view["tools"] = [{"name": c["tool"], "args": c["args"]} for c in d.get("tool_calls", [])]
    elif e["step"] == "model_request":
        view["tool_results"] = [{"name": p["tool_result"], "content": p["content"]}
                                for p in d.get("parts", []) if "tool_result" in p]
    elif e["step"] in ("delegate", "delegate_refused"):
        view.update(to=d.get("to"), task=d.get("task"), reason=d.get("reason"))
    elif e["step"] == "agent_end":
        view["output"] = d.get("output")
    else:
        view["detail"] = d
    return view


@app.get("/api/events")
async def events(
    since: int = Query(0, description="Only events with seq greater than this"),
    ticket_id: int | None = None,
    limit: int = Query(200, le=500),
) -> dict:
    """Recent agent events since `since` (what each agent said, delegations, tools used)."""
    items = [e for e in audit.RECENT_EVENTS if e["seq"] > since and (ticket_id is None or e["ticket_id"] == ticket_id)]
    items = items[-limit:]
    return {"last_seq": audit.RECENT_EVENTS[-1]["seq"] if audit.RECENT_EVENTS else 0,
            "events": [_event_view(e) for e in items]}


# ----------------------------------------------------------------- payments


@app.get("/api/payment-requests")
async def payment_requests(status: str | None = None, ticket_id: int | None = None) -> dict:
    """Payment requests the agents prepared (filter by status pending | approved | rejected)."""
    args: dict[str, Any] = {}
    if status:
        args["status"] = status
    if ticket_id is not None:
        args["ticket_id"] = ticket_id
    return await call_human_tool("list_payment_requests", args)


@app.post("/api/payment-requests/{request_id}/approve")
async def approve_payment(request_id: int, body: ApprovalRequest) -> dict:
    """HUMAN ACTION. The only route that moves cash: executes one pending request after a person clicks Approve."""
    result = await call_human_tool("execute_approved_payment",
                                   {"request_id": request_id, "approved_by": body.approved_by})
    if not result.get("executed"):
        raise HTTPException(409, result.get("message", "Payment not executed."))
    _system_log("human_approval", result["ticket_id"], result)
    return result


@app.post("/api/payment-requests/{request_id}/reject")
async def reject_payment(request_id: int, body: ApprovalRequest) -> dict:
    """HUMAN ACTION. Reject a pending request; no money moves and the ticket goes back to open."""
    result = await call_human_tool("reject_payment_request",
                                   {"request_id": request_id, "decided_by": body.approved_by, "note": body.note})
    if not result.get("rejected"):
        raise HTTPException(409, result.get("message", "Request not rejected."))
    _system_log("human_rejection", result["ticket_id"], {**result, "by": body.approved_by, "note": body.note})
    return result


# --------------------------------------------------------------------- cash


@app.get("/api/cash")
async def cash() -> dict:
    """Current checking balance from cash_accounts, plus what is pending approval."""
    result = await call_human_tool("get_cash_balance", {})
    if not result.get("found"):
        raise HTTPException(500, result.get("message", "No checking account."))
    return result


@app.get("/api/payments")
async def payments() -> dict:
    """Payments that actually left checking (each with who approved it)."""
    return await call_human_tool("list_payments", {})


# -------------------------------------------------------------------- reset


@app.post("/api/reset")
async def reset() -> dict:
    """Restore data/campus_customs_new.db from the untouched original for a fresh run.

    Clears run state in memory. The audit trail is NOT cleared: it is append-only.
    """
    if _active_run() or _run_lock.locked():
        raise HTTPException(409, "A ticket is running; wait for it to finish before resetting.")
    await close_route_client()  # restart the MCP server so it re-creates payment_requests
    shutil.copyfile(ORIGINAL_DB, WORKING_DB)
    RUNS.clear()
    LATEST_RUN.clear()
    cash_now = await call_human_tool("get_cash_balance", {})  # also recreates payment_requests
    _system_log("db_reset", 0, {"copied_from": ORIGINAL_DB.name, "to": WORKING_DB.name,
                                "checking_balance": cash_now.get("balance")}, agent="system")
    return {"reset": True, "working_db": WORKING_DB.name, "checking_balance": cash_now.get("balance")}
