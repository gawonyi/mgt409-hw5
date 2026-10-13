"""Campus Customs MCP server.

The single data-access layer for the Campus Customs agent team. Every shop
fact an agent uses comes from a SQL query in this file against
data/campus_customs_new.db. If a record is missing, the tool says so instead
of guessing.

Money rule enforced here, not just in prompts:
  * Agents can only CREATE payment requests (status 'pending'). Amounts are
    read from the database, never taken from the model.
  * Only execute_approved_payment / reject_payment_request change cash, and
    the backend hides those two tools from every agent; they are called by
    the human Approve button (Problem 7).

Run:  python3 mcp_server/server.py   (stdio; see .mcp.json)
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from fastmcp import FastMCP

DB_PATH = Path(
    os.getenv("CAMPUS_CUSTOMS_DB")
    or Path(__file__).resolve().parent.parent / "data" / "campus_customs_new.db"
)

mcp = FastMCP("campus-customs")

# Payment requests live next to the shop tables so the whole state of a run
# (including what is waiting for a human) is in one file and resets with it.
PAYMENT_REQUESTS_DDL = """
CREATE TABLE IF NOT EXISTS payment_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    kind TEXT NOT NULL,              -- invoice | rent | purchase_order
    ref_id INTEGER NOT NULL,         -- invoices.id | leases.id | vendors.id
    payee TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    reason TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',   -- pending | approved | rejected
    created_at TEXT NOT NULL,
    decided_by TEXT,
    decided_at TEXT,
    decision_note TEXT
)
"""


@contextmanager
def _db(write: bool = False) -> Iterator[sqlite3.Connection]:
    uri = f"file:{DB_PATH}?mode={'rw' if write else 'ro'}"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        if write:
            conn.commit()
    except Exception:
        if write:
            conn.rollback()
        raise
    finally:
        conn.close()


def _query(sql: str, params: tuple = ()) -> list[dict]:
    with _db() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _ensure_tables() -> None:
    with _db(write=True) as conn:
        conn.execute(PAYMENT_REQUESTS_DDL)


def _shop_date() -> str | None:
    rows = _query("SELECT date_today FROM desk LIMIT 1")
    return rows[0]["date_today"] if rows else None


def _checking_balance() -> float | None:
    rows = _query("SELECT balance FROM cash_accounts WHERE name = 'checking'")
    return rows[0]["balance"] if rows else None


def _pending_total() -> float:
    rows = _query("SELECT COALESCE(SUM(amount), 0) AS t FROM payment_requests WHERE status = 'pending'")
    return round(rows[0]["t"], 2)


def _days_between(later: str, earlier: str) -> int:
    return _query("SELECT CAST(julianday(?) - julianday(?) AS INTEGER) AS d", (later, earlier))[0]["d"]


# ---------------------------------------------------------------- read tools


@mcp.tool
def get_shop_date() -> dict:
    """Return the shop's current date (desk.date_today, YYYY-MM-DD) and any desk notes.

    All 'overdue' / 'due in N days' judgments must use this date, not the real calendar.
    """
    rows = _query("SELECT date_today, notes FROM desk LIMIT 1")
    if not rows:
        return {"found": False, "message": "desk table is empty."}
    return {"found": True, "date_today": rows[0]["date_today"], "notes": rows[0]["notes"]}


@mcp.tool
def list_tickets() -> dict:
    """List every ticket with id, type, requester, subject, and status (open | awaiting_approval | resolved)."""
    rows = _query("SELECT id, type, requester, subject, status, created_at FROM tickets ORDER BY id")
    return {"count": len(rows), "tickets": rows}


@mcp.tool
def get_ticket(ticket_id: int) -> dict:
    """Return one ticket's full row: type, requester, subject, sku, size, qty, lease_id, invoice_id, status, notes, created_at.

    The linked keys (sku/size, lease_id, invoice_id) tell you which other tools to call next.
    """
    rows = _query("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    if not rows:
        return {"found": False, "ticket_id": ticket_id, "message": f"No ticket {ticket_id}."}
    return {"found": True, **rows[0]}


@mcp.tool
def check_stock_by_sku_size(sku: str, size: str) -> dict:
    """Look up how many units of one SKU in one size are on the shelf.

    Reads the inventory table. Returns the item name, size, quantity on
    hand, aisle location, and whether it is in stock. Also lists the
    quantities of the other sizes of the same SKU so an agent can offer
    an alternative when the requested size is out.
    """
    rows = _query("SELECT sku, name, size, qty, location FROM inventory WHERE sku = ?", (sku,))
    if not rows:
        return {"found": False, "sku": sku, "message": f"No inventory rows for SKU {sku}."}

    match = next((r for r in rows if r["size"] == size), None)
    other_sizes = [{"size": r["size"], "qty": r["qty"]} for r in rows if r["size"] != size]
    if match is None:
        return {
            "found": False,
            "sku": sku,
            "size": size,
            "message": f"SKU {sku} has no size {size} in inventory.",
            "other_sizes": other_sizes,
        }
    return {
        "found": True,
        "sku": match["sku"],
        "name": match["name"],
        "size": match["size"],
        "qty_on_hand": match["qty"],
        "location": match["location"],
        "in_stock": match["qty"] > 0,
        "other_sizes": other_sizes,
    }


@mcp.tool
def get_lease_rent_due(lease_id: int) -> dict:
    """Look up a shop lease: space, landlord, monthly rent, and next due date.

    Reads the leases table, plus desk.date_today to report how many days
    remain until rent is due. Use this to confirm that a rent notice
    matches the real lease before any payment is prepared.
    """
    rows = _query(
        "SELECT id, space_name, landlord, monthly_rent, next_due, notes FROM leases WHERE id = ?",
        (lease_id,),
    )
    if not rows:
        return {"found": False, "lease_id": lease_id, "message": f"No lease with id {lease_id}."}
    lease = rows[0]
    today = _shop_date()
    return {
        "found": True,
        "lease_id": lease["id"],
        "space_name": lease["space_name"],
        "landlord": lease["landlord"],
        "monthly_rent": lease["monthly_rent"],
        "next_due": lease["next_due"],
        "shop_date_today": today,
        "days_until_due": _days_between(lease["next_due"], today) if today else None,
        "notes": lease["notes"],
    }


@mcp.tool
def get_sku_pricing(sku: str) -> dict:
    """Look up the unit cost and list price for a SKU.

    Reads the pricing table. Returns unit cost, list price, and the
    per-unit margin (list price minus unit cost), which is the most room
    there is for any discount before the shop sells at a loss.
    """
    rows = _query("SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?", (sku,))
    if not rows:
        return {"found": False, "sku": sku, "message": f"No pricing row for SKU {sku}."}
    p = rows[0]
    return {
        "found": True,
        "sku": p["sku"],
        "unit_cost": p["unit_cost"],
        "list_price": p["list_price"],
        "unit_margin": round(p["list_price"] - p["unit_cost"], 2),
    }


@mcp.tool
def quote_bulk_discount(sku: str, qty: int, discount_pct: float) -> dict:
    """Price a bulk order of `qty` units of `sku` at `discount_pct` percent off list (e.g. 10 = 10%).

    Reads the pricing table and does the arithmetic in Python so no agent
    has to. Returns dollars: list total, discounted unit price, discounted
    total, customer savings, unit cost, margin per unit after discount, and
    margin percent of the discounted price.
    """
    rows = _query("SELECT unit_cost, list_price FROM pricing WHERE sku = ?", (sku,))
    if not rows:
        return {"found": False, "sku": sku, "message": f"No pricing row for SKU {sku}."}
    if qty <= 0 or not (0 <= discount_pct < 100):
        return {"found": False, "message": "qty must be > 0 and discount_pct between 0 and 100."}
    cost, price = rows[0]["unit_cost"], rows[0]["list_price"]
    unit_price = round(price * (1 - discount_pct / 100), 2)
    return {
        "found": True,
        "sku": sku,
        "qty": qty,
        "discount_pct": discount_pct,
        "list_price": price,
        "list_total": round(price * qty, 2),
        "discounted_unit_price": unit_price,
        "discounted_total": round(unit_price * qty, 2),
        "customer_savings": round((price - unit_price) * qty, 2),
        "unit_cost": cost,
        "unit_margin_after_discount": round(unit_price - cost, 2),
        "margin_pct_of_price": round((unit_price - cost) / unit_price * 100, 1) if unit_price else None,
    }


@mcp.tool
def list_vendors() -> dict:
    """List every vendor with id, name, specialty, and lead_days (days from order to delivery)."""
    rows = _query("SELECT id, name, specialty, lead_days FROM vendors ORDER BY id")
    return {"count": len(rows), "vendors": rows}


@mcp.tool
def get_invoice(invoice_id: int) -> dict:
    """Return one vendor invoice with its vendor, amount, due date, status, and days overdue vs. the shop date.

    Reads invoices joined to vendors, plus desk.date_today.
    """
    rows = _query(
        """SELECT i.id, i.vendor_id, v.name AS vendor_name, v.lead_days AS vendor_lead_days,
                  i.amount, i.due_date, i.status, i.description
           FROM invoices i LEFT JOIN vendors v ON v.id = i.vendor_id WHERE i.id = ?""",
        (invoice_id,),
    )
    if not rows:
        return {"found": False, "invoice_id": invoice_id, "message": f"No invoice {invoice_id}."}
    inv = rows[0]
    today = _shop_date()
    overdue = _days_between(today, inv["due_date"]) if today else None
    return {
        "found": True,
        **inv,
        "shop_date_today": today,
        "days_overdue": overdue if overdue and overdue > 0 and inv["status"] == "open" else 0,
    }


@mcp.tool
def list_open_invoices(sku: str | None = None) -> dict:
    """List vendor invoices with status 'open'. Pass `sku` to keep only invoices whose description mentions that SKU.

    Reads invoices joined to vendors. Use it before ordering stock (is a
    reprint already on order?) and before shipping (is the item tied to an
    unpaid bill?).
    """
    sql = """SELECT i.id, i.vendor_id, v.name AS vendor_name, i.amount, i.due_date, i.status, i.description
             FROM invoices i LEFT JOIN vendors v ON v.id = i.vendor_id WHERE i.status = 'open'"""
    params: tuple = ()
    if sku:
        sql += " AND i.description LIKE ?"
        params = (f"%{sku}%",)
    rows = _query(sql + " ORDER BY i.due_date", params)
    return {"count": len(rows), "total_open": round(sum(r["amount"] for r in rows), 2), "invoices": rows}


@mcp.tool
def get_cash_balance() -> dict:
    """Return the checking balance (cash_accounts), the total of payment requests still pending approval, and what would be left if all were approved. Dollars."""
    rows = _query("SELECT name, balance, date FROM cash_accounts WHERE name = 'checking'")
    if not rows:
        return {"found": False, "message": "No checking account in cash_accounts."}
    pending = _pending_total()
    return {
        "found": True,
        "account": "checking",
        "balance": rows[0]["balance"],
        "as_of": rows[0]["date"],
        "pending_requests_total": pending,
        "balance_after_pending": round(rows[0]["balance"] - pending, 2),
    }


@mcp.tool
def list_payments() -> dict:
    """List money that has actually left the shop (payments table): kind, ref_id, amount, account, paid_at, approved_by."""
    rows = _query("SELECT * FROM payments ORDER BY id")
    return {"count": len(rows), "total_paid": round(sum(r["amount"] for r in rows), 2), "payments": rows}


@mcp.tool
def list_payment_requests(ticket_id: int | None = None, status: str | None = None) -> dict:
    """List payment requests agents have prepared, optionally filtered by ticket_id and/or status (pending | approved | rejected)."""
    sql, params = "SELECT * FROM payment_requests WHERE 1=1", []
    if ticket_id is not None:
        sql += " AND ticket_id = ?"
        params.append(ticket_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    rows = _query(sql + " ORDER BY id", tuple(params))
    return {"count": len(rows), "requests": rows}


# ------------------------------------------------- write tools (no cash moves)


def _create_request(ticket_id: int, kind: str, ref_id: int, payee: str, amount: float,
                    description: str, reason: str, requested_by: str) -> dict:
    if not _query("SELECT id FROM tickets WHERE id = ?", (ticket_id,)):
        return {"created": False, "message": f"No ticket {ticket_id}."}
    dup = _query(
        "SELECT id FROM payment_requests WHERE kind = ? AND ref_id = ? AND status = 'pending'",
        (kind, ref_id),
    )
    if dup and kind != "purchase_order":
        return {"created": False, "message": f"A pending {kind} request already exists (request {dup[0]['id']})."}
    balance = _checking_balance() or 0.0
    pending = _pending_total()
    with _db(write=True) as conn:
        cur = conn.execute(
            """INSERT INTO payment_requests
               (ticket_id, kind, ref_id, payee, amount, description, reason, requested_by, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (ticket_id, kind, ref_id, payee, round(amount, 2), description, reason, requested_by, _shop_date()),
        )
        req_id = cur.lastrowid
    return {
        "created": True,
        "request_id": req_id,
        "status": "pending",
        "kind": kind,
        "payee": payee,
        "amount": round(amount, 2),
        "description": description,
        "checking_balance": balance,
        "pending_before_this": pending,
        "covered_by_cash": balance - pending >= amount,
        "balance_after_all_pending": round(balance - pending - amount, 2),
        "note": "No money has moved. A human must approve this request.",
    }


@mcp.tool
def request_invoice_payment(ticket_id: int, invoice_id: int, reason: str, requested_by: str) -> dict:
    """Prepare (do NOT pay) a payment of an open vendor invoice, for a human to approve.

    The amount and payee are read from invoices/vendors; the caller cannot set them.
    Returns the request id, amount, and whether current cash covers it.
    """
    rows = _query(
        "SELECT i.id, i.amount, i.status, i.description, v.name AS vendor FROM invoices i "
        "LEFT JOIN vendors v ON v.id = i.vendor_id WHERE i.id = ?",
        (invoice_id,),
    )
    if not rows:
        return {"created": False, "message": f"No invoice {invoice_id}."}
    inv = rows[0]
    if inv["status"] != "open":
        return {"created": False, "message": f"Invoice {invoice_id} is '{inv['status']}', not open."}
    return _create_request(ticket_id, "invoice", invoice_id, inv["vendor"], inv["amount"],
                           f"Invoice {invoice_id}: {inv['description']}", reason, requested_by)


@mcp.tool
def request_rent_payment(ticket_id: int, lease_id: int, reason: str, requested_by: str) -> dict:
    """Prepare (do NOT pay) one month's rent for a lease, for a human to approve.

    Amount (monthly_rent) and payee (landlord) are read from the leases table.
    """
    rows = _query("SELECT id, space_name, landlord, monthly_rent, next_due FROM leases WHERE id = ?", (lease_id,))
    if not rows:
        return {"created": False, "message": f"No lease {lease_id}."}
    l = rows[0]
    return _create_request(ticket_id, "rent", lease_id, l["landlord"], l["monthly_rent"],
                           f"Rent for {l['space_name']} due {l['next_due']}", reason, requested_by)


@mcp.tool
def request_restock_purchase(ticket_id: int, vendor_id: int, sku: str, size: str, qty: int,
                             reason: str, requested_by: str) -> dict:
    """Prepare (do NOT pay) a purchase order of `qty` units of sku/size from a vendor, for a human to approve.

    Cost = qty x pricing.unit_cost, computed here. Returns the expected
    arrival date (shop date + vendor lead_days) along with the request.
    """
    if qty <= 0:
        return {"created": False, "message": "qty must be positive."}
    v = _query("SELECT id, name, lead_days FROM vendors WHERE id = ?", (vendor_id,))
    p = _query("SELECT unit_cost FROM pricing WHERE sku = ?", (sku,))
    if not v or not p:
        return {"created": False, "message": "Unknown vendor or SKU."}
    if not _query("SELECT 1 FROM inventory WHERE sku = ? AND size = ?", (sku, size)):
        return {"created": False, "message": f"{sku} has no size {size}."}
    amount = qty * p[0]["unit_cost"]
    # Spending order: rent and bills already waiting for approval come first, so
    # a new purchase must fit in what is left after them.
    available = round((_checking_balance() or 0.0) - _pending_total(), 2)
    if amount > available:
        return {"created": False, "amount_needed": round(amount, 2), "available_after_pending": available,
                "shortfall": round(amount - available, 2),
                "message": "Not enough checking after pending rent/invoice requests; purchase not requested."}
    arrival = _query("SELECT date(?, ?) AS d", (_shop_date(), f"+{v[0]['lead_days']} days"))[0]["d"]
    out = _create_request(ticket_id, "purchase_order", vendor_id, v[0]["name"], amount,
                          f"PO {qty} x {sku} {size} @ ${p[0]['unit_cost']:.2f}, arrives ~{arrival}",
                          reason, requested_by)
    out["expected_arrival"] = arrival
    return out


@mcp.tool
def add_ticket_note(ticket_id: int, agent: str, note: str) -> dict:
    """Append a dated note to a ticket's notes (e.g. the customer reply draft, a finding). Does not change status."""
    rows = _query("SELECT notes FROM tickets WHERE id = ?", (ticket_id,))
    if not rows:
        return {"updated": False, "message": f"No ticket {ticket_id}."}
    line = f"[{_shop_date()} {agent}] {note.strip()}"
    with _db(write=True) as conn:
        conn.execute("UPDATE tickets SET notes = COALESCE(notes, '') || char(10) || ? WHERE id = ?", (line, ticket_id))
    return {"updated": True, "ticket_id": ticket_id, "appended": line}


@mcp.tool
def update_ticket_status(ticket_id: int, status: str, resolution_note: str, agent: str) -> dict:
    """Set a ticket's status to 'open', 'awaiting_approval', or 'resolved' and append a resolution note.

    'resolved' is refused while the ticket still has pending payment
    requests; use 'awaiting_approval' and the Approve step will resolve it.
    """
    if status not in ("open", "awaiting_approval", "resolved"):
        return {"updated": False, "message": "status must be open, awaiting_approval, or resolved."}
    if not _query("SELECT id FROM tickets WHERE id = ?", (ticket_id,)):
        return {"updated": False, "message": f"No ticket {ticket_id}."}
    pending = _query("SELECT id FROM payment_requests WHERE ticket_id = ? AND status = 'pending'", (ticket_id,))
    if status == "resolved" and pending:
        return {"updated": False, "message": f"Ticket {ticket_id} has pending payment requests "
                f"{[r['id'] for r in pending]}; set 'awaiting_approval' instead."}
    line = f"[{_shop_date()} {agent}] status -> {status}: {resolution_note.strip()}"
    with _db(write=True) as conn:
        conn.execute(
            "UPDATE tickets SET status = ?, notes = COALESCE(notes, '') || char(10) || ? WHERE id = ?",
            (status, line, ticket_id),
        )
    return {"updated": True, "ticket_id": ticket_id, "status": status}


# -------------------------- human-only tools (hidden from agents by backend)


@mcp.tool
def execute_approved_payment(request_id: int, approved_by: str) -> dict:
    """HUMAN ONLY. Execute a pending payment request after a person clicked Approve.

    Writes a payments row, subtracts the amount from checking, and applies
    the side effect (invoice -> paid, lease next_due +1 month). Refuses if
    checking cannot cover it. Resolves the ticket when nothing else is pending.
    """
    if not approved_by or approved_by.strip().lower() in ("", "agent", "ai", "boss"):
        return {"executed": False, "message": "approved_by must name the human approver."}
    with _db(write=True) as conn:
        req = conn.execute("SELECT * FROM payment_requests WHERE id = ?", (request_id,)).fetchone()
        if req is None:
            return {"executed": False, "message": f"No payment request {request_id}."}
        if req["status"] != "pending":
            return {"executed": False, "message": f"Request {request_id} is already {req['status']}."}
        bal = conn.execute("SELECT balance FROM cash_accounts WHERE name = 'checking'").fetchone()["balance"]
        if bal < req["amount"]:
            return {"executed": False, "message": f"Checking ${bal:.2f} cannot cover ${req['amount']:.2f}."}
        today = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()["date_today"]
        if req["kind"] == "invoice":
            inv = conn.execute("SELECT status FROM invoices WHERE id = ?", (req["ref_id"],)).fetchone()
            if inv is None or inv["status"] != "open":
                return {"executed": False, "message": f"Invoice {req['ref_id']} is no longer open."}
            conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (req["ref_id"],))
        elif req["kind"] == "rent":
            conn.execute("UPDATE leases SET next_due = date(next_due, '+1 month') WHERE id = ?", (req["ref_id"],))
        conn.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, 'checking', ?, ?)",
            (req["kind"], req["ref_id"], req["amount"], today, approved_by.strip()),
        )
        new_bal = round(bal - req["amount"], 2)
        conn.execute("UPDATE cash_accounts SET balance = ?, date = ? WHERE name = 'checking'", (new_bal, today))
        conn.execute(
            "UPDATE payment_requests SET status = 'approved', decided_by = ?, decided_at = ? WHERE id = ?",
            (approved_by.strip(), today, request_id),
        )
        still = conn.execute(
            "SELECT COUNT(*) AS n FROM payment_requests WHERE ticket_id = ? AND status = 'pending'",
            (req["ticket_id"],),
        ).fetchone()["n"]
        ticket_resolved = False
        if still == 0:
            cur = conn.execute(
                "UPDATE tickets SET status = 'resolved', notes = COALESCE(notes, '') || char(10) || ? "
                "WHERE id = ? AND status = 'awaiting_approval'",
                (f"[{today} {approved_by.strip()}] approved request {request_id}; status -> resolved", req["ticket_id"]),
            )
            ticket_resolved = cur.rowcount > 0
    return {
        "executed": True,
        "request_id": request_id,
        "ticket_id": req["ticket_id"],
        "kind": req["kind"],
        "payee": req["payee"],
        "amount": req["amount"],
        "balance_before": bal,
        "balance_after": new_bal,
        "approved_by": approved_by.strip(),
        "ticket_resolved": ticket_resolved,
    }


@mcp.tool
def reject_payment_request(request_id: int, decided_by: str, note: str = "") -> dict:
    """HUMAN ONLY. Reject a pending payment request. No money moves; the ticket goes back to 'open'."""
    with _db(write=True) as conn:
        req = conn.execute("SELECT * FROM payment_requests WHERE id = ?", (request_id,)).fetchone()
        if req is None or req["status"] != "pending":
            return {"rejected": False, "message": f"Request {request_id} is not pending."}
        today = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()["date_today"]
        conn.execute(
            "UPDATE payment_requests SET status = 'rejected', decided_by = ?, decided_at = ?, decision_note = ? WHERE id = ?",
            (decided_by, today, note, request_id),
        )
        conn.execute("UPDATE tickets SET status = 'open' WHERE id = ? AND status = 'awaiting_approval'", (req["ticket_id"],))
    return {"rejected": True, "request_id": request_id, "ticket_id": req["ticket_id"]}


_ensure_tables()

if __name__ == "__main__":
    mcp.run(show_banner=False)
