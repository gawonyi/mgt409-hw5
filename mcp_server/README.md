# Campus Customs MCP Server

**Purpose.** The one shared data-access server for the Campus Customs agent team. Agents get every shop fact by calling these tools, never by querying the database themselves, so each answer traces back to a real record.

**Database.** `data/campus_customs_new.db`, the working copy of `data/campus_customs.db` (the original is never touched). Read tools open the file read-only. The server adds one table, `payment_requests`, to hold payments waiting for a human.

**Code.** `mcp_server/server.py` (FastMCP). `.mcp.json` registers it as `campus-customs` (stdio, `.venv/bin/python mcp_server/server.py`); Claude Code and Cursor read the same format.

## Tools

### Read
| Tool | Reads | Returns |
|---|---|---|
| `get_shop_date()` | desk | Shop date and desk notes |
| `list_tickets()` | tickets | All tickets with status |
| `get_ticket(ticket_id)` | tickets | Full ticket row and linked keys |
| `check_stock_by_sku_size(sku, size)` | inventory | Qty on hand, aisle, in-stock flag, other sizes |
| `get_lease_rent_due(lease_id)` | leases, desk | Landlord, rent, next due, days until due |
| `list_leases()` | leases, desk, payment_requests | All leases with days until due, and rent due within 7 days that is not yet requested |
| `get_sku_pricing(sku)` | pricing | Unit cost, list price, unit margin |
| `quote_bulk_discount(sku, qty, discount_pct)` | pricing | Quoted unit price and total, savings, margin, and `policy` (ok / needs_manager_approval / list_price_only under 10 units / not_allowed) |
| `list_vendors()` | vendors | Vendors with specialty and lead days |
| `get_invoice(invoice_id)` | invoices, vendors, desk | Invoice, vendor, days overdue |
| `list_open_invoices(sku=None)` | invoices, vendors | Open invoices, optionally for one SKU |
| `get_cash_balance()` | cash_accounts, payment_requests | Checking balance, pending total, balance after pending |
| `list_payments()` | payments | Money that actually left |
| `list_payment_requests(ticket_id=None, status=None)` | payment_requests | Prepared requests and their status |

### Write (no money moves)
| Tool | Writes | Notes |
|---|---|---|
| `request_invoice_payment(ticket_id, invoice_id, reason, requested_by)` | payment_requests | Amount/payee from invoices; open invoices only; no duplicates; refused if it would leave rent due within 7 days uncovered |
| `request_rent_payment(ticket_id, lease_id, reason, requested_by)` | payment_requests | Amount/payee from leases; no duplicates |
| `request_restock_purchase(ticket_id, vendor_id, sku, size, qty, reason, requested_by)` | payment_requests | Cost = qty × unit_cost; refused if it does not fit after pending requests and rent due within 7 days |
| `add_ticket_note(ticket_id, agent, note)` | tickets.notes | Dated note, e.g. customer reply |
| `update_ticket_status(ticket_id, status, resolution_note, agent)` | tickets | `resolved` refused while requests are pending; customer orders and price overrides need a `Customer reply:` note first |

### Human only (hidden from every agent; called by the Approve/Reject route)
| Tool | Writes | Notes |
|---|---|---|
| `execute_approved_payment(request_id, approved_by)` | payments, cash_accounts, invoices / leases, payment_requests, tickets | Needs a named human; refuses if cash is short |
| `reject_payment_request(request_id, decided_by, note)` | payment_requests, tickets | No money moves |

## Smoke test (Problem 4)
- **Vibe coder:** Claude Code loaded `.mcp.json` and called the three original tools directly; prompt, tool names, and outputs are in `output/mcp_smoke.json` (`vibe_coder_test`), screenshot `output/mcp_smoke_claude_code.png`.
- **Automated:** `python3 mcp_smoke_test.py` lets a Portkey model call the same three tools and checks each output against the database (`supporting_portkey_test`).
