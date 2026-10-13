# Campus Customs Harness

The complete harness for the Campus Customs agent team: what data it works with, the tools it can call, the five agents, the API, the dashboard, the safety rules, and how the final run went.

**Contents:** 1 Tables · 2 Open tickets · 3 Initial MCP tools · 4 Agent team · 5 All MCP tools · 6 Safety guardrails · 7 Token limits · 8 API routes · 9 Dashboard · 10 Final run and lessons

**How to run:** `cp data/campus_customs.db data/campus_customs_new.db` → backend from `backend/`: `uvicorn main:app --reload --port 8000` (the API starts the MCP server from `.mcp.json`) → board from `frontend/`: `npm install && npm run dev` → open `http://localhost:5173`, click **Reset data**, run tickets 101, 102, 103 and approve payments.

- **Original database:** `data/campus_customs.db` (never modified)
- **Working database:** `data/campus_customs_new.db` (all updates happen here)
- **Shop date (`desk.date_today`):** 2026-08-31

---

## 1. Tables

| Table | Fields | Why it matters for the agents |
|---|---|---|
| `desk` | `date_today`, `notes` | Gives every agent the shop's "today" (2026-08-31), so they can tell what is overdue or due soon. |
| `tickets` | `id`, `type`, `requester`, `subject`, `sku`, `size`, `qty`, `lease_id`, `invoice_id`, `status`, `notes`, `created_at` | The work queue. The Boss reads a ticket and uses its `type` and linked keys (`sku`/`size`, `lease_id`, `invoice_id`) to decide which specialist to call. |
| `inventory` | `sku`, `name`, `size`, `qty`, `location` (PK `sku`+`size`) | Inventory agent checks whether a SKU and size is in stock, and where it sits, before anyone promises a customer an item. |
| `pricing` | `sku`, `unit_cost`, `list_price` | Lets the agents quote list price and check margin when a customer asks for a discount. |
| `vendors` | `id`, `name`, `specialty`, `lead_days` | Tells Inventory/Accounting who can restock an item and how many days it will take, which sets the delivery date a customer can be told. |
| `leases` | `id`, `space_name`, `landlord`, `monthly_rent`, `next_due`, `notes` | Facilities agent uses this to confirm a rent notice is real: right landlord, right amount, right due date. |
| `cash_accounts` | `name`, `balance`, `date` | The checking balance ($3,400.00 as of 2026-08-31). Accounting checks it before preparing any payment so the shop does not overspend. |
| `payments` | `id`, `kind`, `ref_id`, `amount`, `account`, `paid_at`, `approved_by` | Ledger of money that actually left the shop. Empty at start; a row is written only after a human approves, and `approved_by` records who. |
| `invoices` | `id`, `vendor_id`, `amount`, `due_date`, `status`, `description` | Bills the shop owes vendors. Accounting checks status and due date before paying, and links each invoice back to its vendor. |

Foreign keys declared in the schema: `tickets.lease_id → leases.id`, `tickets.invoice_id → invoices.id`, `invoices.vendor_id → vendors.id`. The `sku` link between `tickets`, `inventory`, and `pricing` is by value, not a declared foreign key. `payments.ref_id` points to whatever record was paid (an invoice id or a lease id, depending on `kind`).

---

## 2. Open tickets and how they connect

All three tickets have `status = 'open'`.

### Ticket 101 — customer_order (Tauhid Zaman, "Bulldog tee")
- **Ask:** 1 × `CC-TEE-WHITE`, size S ("Needs a tee in size S.").
- **inventory:** `CC-TEE-WHITE` / S has `qty = 0` (Aisle B), so it is out of stock. M = 5, L = 3, XL = 2.
- **pricing:** `CC-TEE-WHITE` unit cost $8.00, list price $28.00.
- **invoices:** ticket links `invoice_id = 501`, which is Bulldog Print Co's "Rush reprint CC-TEE-WHITE S", $840.00, due 2026-08-28, status `open`. It is already past due on the shop date of 2026-08-31.
- **vendors:** invoice 501 → vendor 1, Bulldog Print Co (apparel reprint, 5 lead days).
- **cash_accounts:** paying invoice 501 would come out of checking ($3,400.00).
- **Agents involved:** Customer Service (customer reply), Inventory (stock and restock), Accounting (overdue invoice).

### Ticket 102 — rent_notice (Elm City Properties, "Rent due")
- **Ask:** "Email: shop rent due in 2 days."
- **leases:** ticket links `lease_id = 1`, the Chapel Street shop. Landlord Elm City Properties, rent $2,400.00, next due 2026-09-02. That is two days after the shop date, so the email matches the lease.
- **cash_accounts:** rent would come out of checking ($3,400.00).
- **payments:** no rent payment recorded yet (table is empty).
- **Agents involved:** Facilities (verify lease), Accounting (cash check, prepare payment for human approval).

### Ticket 103 — price_override (Yale AI Club, "Bulk hoodie discount")
- **Ask:** 20 × `CC-HOOD-NAVY`, size M, with a bulk discount.
- **inventory:** `CC-HOOD-NAVY` / M has `qty = 8` (Aisle A), which is 12 short of 20. Other sizes: S = 4, L = 14, XL = 6.
- **pricing:** unit cost $22.00, list price $58.00. That is $1,160.00 at list for 20 units, with a $36.00 per-unit margin to work with on any discount.
- **vendors:** Bulldog Print Co (apparel reprint, 5 lead days) is the vendor that could make the missing units.
- **Agents involved:** Inventory (stock shortfall), Accounting (discount and margin), Customer Service (reply to the club).

### Cash pressure across tickets
Checking starts at $3,400.00. Invoice 501 ($840.00) plus rent ($2,400.00) totals $3,240.00, which would leave $160.00. Any restock purchase for Ticket 101 or 103 competes with these two bills, so Accounting should check the balance before preparing each payment, and every payment needs human approval.

---

## 3. MCP tools (initial set, Problem 3)

Server: `mcp_server/server.py` (FastMCP on `data/campus_customs_new.db`). These first three tools are read-only; write tools are added in section 5.

| Tool | Table(s) read | Ticket | Why this tool fits the ticket |
|---|---|---|---|
| `check_stock_by_sku_size(sku, size)` | `inventory` | 101 | Tauhid wants one `CC-TEE-WHITE` in size S, so the first thing the team must know is that S shows `qty = 0` while M/L/XL are on the shelf, which tells Customer Service it cannot promise the tee today and points Inventory to a restock or a different size. |
| `get_lease_rent_due(lease_id)` | `leases`, `desk` | 102 | The rent email only says "due in 2 days," so Facilities needs lease 1's landlord (Elm City Properties), amount ($2,400), and due date (2026-09-02, 2 days after the 2026-08-31 shop date) to confirm the notice is genuine before Accounting prepares any payment. |
| `get_sku_pricing(sku)` | `pricing` | 103 | The Yale AI Club is asking for a bulk discount on 20 `CC-HOOD-NAVY`, and the only way to judge a discount is the $22 unit cost against the $58 list price, a $36 margin per hoodie that sets the floor Accounting cannot go below. |


**Connection and test (Problem 4).** `.mcp.json` registers the server as `campus-customs` (stdio, `.venv/bin/python mcp_server/server.py`). Claude Code loaded it and called all three tools directly; prompt, tool names, raw outputs, and a database check for each are in `output/mcp_smoke.json` (`vibe_coder_test`), with a screenshot in `output/mcp_smoke_claude_code.png`. An automated Portkey check of the same tools is kept as `supporting_portkey_test`.
---

## 4. Agent team (Problem 5)

Framework: PydanticAI. Model: **`gpt-6-luna` for every agent**, via Portkey (`PORTKEY_API_KEY`, OpenAI-compatible endpoint, `reasoning_effort="none"` because the gateway requires it for tool calls). Code: `backend/agents.py`, settings `backend/config.py`, types `backend/models.py`, prompts `backend/prompts/<agent>.md`.

| Agent | Prompt | Owns | Output type | MCP tools it can see |
|---|---|---|---|---|
| Boss | `boss.md` | Routes each ticket to the one specialist that owns the first blocker, enforces shop rules, sets the final status | `TicketOutcome` | get_shop_date, get_ticket, list_tickets, get_cash_balance, list_payment_requests, update_ticket_status |
| Inventory | `inventory.md` | Shelf stock, shortfalls, vendor lead times, restock orders; holds orders tied to unpaid vendor invoices | `SpecialistReport` | common + check_stock_by_sku_size, list_vendors, list_open_invoices, get_sku_pricing, request_restock_purchase, add_ticket_note |
| Accounting | `accounting.md` | Cash, vendor invoices, rent payment requests, spending order, discount policy | `SpecialistReport` | common + get_cash_balance, get_invoice, list_open_invoices, list_payments, list_payment_requests, get_sku_pricing, quote_bulk_discount, get_lease_rent_due, list_leases, list_vendors, request_invoice_payment, request_rent_payment, request_restock_purchase, add_ticket_note |
| Facilities | `facilities.md` | Verifies rent notices against the lease (fraud check), prevents double rent, hands payment to Accounting | `SpecialistReport` | common + get_lease_rent_due, list_leases, list_payments, list_payment_requests, add_ticket_note |
| Customer Service | `customer_service.md` | Writes the requester's reply from tool facts only; never shares internal finances | `SpecialistReport` | common + check_stock_by_sku_size, get_sku_pricing, quote_bulk_discount, list_vendors, add_ticket_note |

"common" = get_shop_date, get_ticket, list_tickets.

**Delegation.** Every agent has a `delegate(to_agent, task)` tool that can call any other agent, so the graph is fully connected (Boss is the usual entry point, but e.g. Inventory → Accounting or Facilities → Accounting happen directly). Each delegated agent runs its own loop (`Agent.iter`) and returns its structured report to the caller. One `RunUsage` object is shared by all agents in a ticket run.

**Agent loop.** `run_agent_loop()` steps through PydanticAI's graph node by node (user prompt → model request → model response / tool calls → … → end) and writes every node to the audit trail.

## 5. MCP tools (full list)

Server: `mcp_server/server.py`. The backend reaches the database **only** through this server (`backend/mcp_client.py` starts it from `.mcp.json`); there is no separate shop-tools layer.

| Tool | Table(s) | Kind | Used by |
|---|---|---|---|
| `get_shop_date` | desk | read | all |
| `list_tickets` | tickets | read | all |
| `get_ticket` | tickets | read | all |
| `check_stock_by_sku_size` | inventory | read | Inventory, Customer Service |
| `get_lease_rent_due` | leases, desk | read | Facilities, Accounting |
| `list_leases` | leases, desk, payment_requests | read (rent due within 7 days and not yet requested) | Accounting, Facilities |
| `get_sku_pricing` | pricing | read | Inventory, Accounting, Customer Service |
| `quote_bulk_discount` | pricing | read (math in Python) | Accounting, Customer Service |
| `list_vendors` | vendors | read | Inventory, Accounting, Customer Service |
| `get_invoice` | invoices, vendors, desk | read | Accounting |
| `list_open_invoices` | invoices, vendors | read | Inventory, Accounting |
| `get_cash_balance` | cash_accounts, payment_requests | read | Boss, Accounting |
| `list_payments` | payments | read | Accounting, Facilities |
| `list_payment_requests` | payment_requests | read | Boss, Accounting, Facilities |
| `request_invoice_payment` | invoices, vendors → payment_requests | write (pending only) | Accounting |
| `request_rent_payment` | leases → payment_requests | write (pending only) | Accounting |
| `request_restock_purchase` | vendors, pricing, inventory → payment_requests | write (pending only) | Inventory, Accounting |
| `add_ticket_note` | tickets | write (notes) | Inventory, Accounting, Facilities, Customer Service |
| `update_ticket_status` | tickets, payment_requests | write (status) | Boss |
| `execute_approved_payment` | payment_requests, payments, cash_accounts, invoices, leases, tickets | **human only** | Approve route (Problem 7) |
| `reject_payment_request` | payment_requests, tickets | **human only** | Reject route (Problem 7) |

`payment_requests` is a table the server adds to the working DB (`CREATE TABLE IF NOT EXISTS`) to hold requests waiting for a human. It disappears on reset and is recreated when the server starts.

## 6. Safety guardrails (real customers, real money)

Enforced in code (cannot be talked around by a prompt):
- **Humans move money, agents do not.** Agents can only create `pending` payment requests. `execute_approved_payment` and `reject_payment_request` are filtered out of every agent's toolset (asserted at import) and are called only by the human Approve/Reject route. `approved_by` must name a person; "agent", "ai", "boss" are refused.
- **Amounts come from the database.** Request tools take ids (invoice, lease, vendor + sku/qty) and read the amount and payee from the DB; the model never types a dollar figure.
- **No overspending, rent first.** Execution refuses if checking cannot cover the amount. A vendor-invoice or purchase request is refused if, after it and everything already pending, checking would not cover rent due within 7 days that has not been requested yet (`_rent_reserve`). Each accepted request records the rent check it passed.
- **No double payments.** A second pending request for the same invoice or lease is refused; an invoice that is no longer open cannot be paid; a request can be approved only once.
- **No premature closing.** `update_ticket_status` refuses `resolved` while the ticket has pending requests, and refuses both `awaiting_approval` and `resolved` on a customer order or price override until Customer Service has saved a `Customer reply:` note. Approval resolves a ticket only if that reply exists.
- **Least privilege.** Each agent sees only its role's MCP tools; the server opens the DB read-only for read tools.
- **Original data is safe.** Everything runs on `campus_customs_new.db`; `campus_customs.db` is never written.
- **Audit everything.** Every agent-loop step, delegation, refusal, and error is appended to `output/audit_trail.json` (atomic write, never truncated; a malformed file stops the run instead of being overwritten).
- **Secrets.** `PORTKEY_API_KEY` is read from a `.env` file in the project folder or a parent folder (template: `.env.example`; `.env` is git-ignored), sent only to Portkey, never logged, and not passed to the MCP server process.

Enforced in prompts:
- Rent before everything else (also enforced in code, see above); overdue vendor invoices before new purchases; Accounting writes its rent check with numbers.
- Orders tied to an unpaid vendor invoice are held until a human approves that payment.
- Rent notices are paid only if the landlord, amount, and "due in N days" match the lease (fraud check).
- Discounts: ≥10 units only; ≤10% Accounting may offer; 10–20% needs a manager's approval; never >20% or below 1.5 × unit cost.
- Customer orders and price overrides always end with a Customer Service reply (also enforced in code); replies use tool facts only, no internal cash figures, no invented dates.
- Delegations ask for the action ("prepare the payment if the rules allow"), not just a status check.
- "If a tool did not return it, say you do not know."

## 7. Token limits

- **Per-ticket budget:** one shared `RunUsage` with `UsageLimits(request_limit=40, tool_calls_limit=60, total_tokens_limit=150_000)` across all five agents; exceeding it stops the run with a logged error instead of looping.
- **Delegation caps:** max depth 3, max 6 hand-offs per ticket, no self-delegation, no cycles (an agent already upstream cannot be called again).
- **Small context:** tool results are compact JSON and are truncated to 12,000 characters before reaching the model; audit entries are clipped too.
- **Role-filtered tools:** each agent's prompt only carries the schemas of its own tools (6–17 of the 19 agent-visible tools; the 2 human-only tools are never sent).
- **Cheap model, no reasoning tokens:** `gpt-6-luna` with `reasoning_effort="none"`; structured outputs keep final answers short.
- **Usage is recorded:** each `model_response` audit entry logs input/output tokens, and `run_end` logs the ticket's totals.

---

## 8. API routes (Problem 7)

FastAPI app in `backend/main.py`. Run from `backend/`: `uvicorn main:app --reload --port 8000` → `http://localhost:8000` (interactive docs at `/docs`). CORS allows the Vite board at `http://localhost:5173`. Every route reads or writes shop data through the campus-customs MCP server.

| Method & URL | What it does |
|---|---|
| `GET /api/health` | Liveness check; says which DB is in use and whether a ticket is running. |
| `GET /api/tickets` | Lists tickets 101–103 with status (open / awaiting_approval / resolved), pending payment request ids, and whether each is running. |
| `GET /api/tickets/{ticket_id}` | One ticket with its notes, its payment requests, and the latest run's outcome (summary per agent). |
| `POST /api/tickets/{ticket_id}/run` | Starts the five-agent team on that ticket in the background and returns a run id (202); refuses if another ticket is running or this one is resolved. |
| `GET /api/runs/{run_id}` | Run state (running / done / error) and, when finished, the Boss's TicketOutcome. |
| `GET /api/events?since=N&ticket_id=T` | Recent agent events after sequence N: what each agent said, delegations, tools called with arguments, and tool results. |
| `GET /api/payment-requests?status=&ticket_id=` | Payment requests the agents prepared, filterable by status and ticket. |
| `POST /api/payment-requests/{id}/approve` | **Human action, the only route that moves cash.** Body `{"approved_by": "<name>"}`; executes the pending payment/purchase, lowers checking, logs a `human_approval` audit event. |
| `POST /api/payment-requests/{id}/reject` | Human action; rejects a pending request (no money moves) and logs a `human_rejection` event. |
| `GET /api/cash` | Current checking balance from `cash_accounts`, plus pending total and balance after pending. |
| `GET /api/payments` | Payments that actually left checking, with who approved each. |
| `POST /api/reset` | Copies `data/campus_customs.db` over `data/campus_customs_new.db` for a fresh run; refused while a ticket runs; the audit trail is kept. |

Route guardrails: one ticket run at a time (they share one cash account); approve needs a named person ("agent"/"ai"/"boss" refused) and can succeed only once per request; agent runs cannot reach the approve logic because the cash-moving MCP tools are not in any agent's toolset.

---

## 9. Dashboard (Problem 8)

React + Vite + TypeScript board in `frontend/` (`npm install`, `npm run dev` → `http://localhost:5173`), calling the API at `http://localhost:8000`. Design notes: `output/design.md`.

- Queue of tickets 101–103 with status (Open / Needs your approval / Agents working / Resolved stamp).
- Run agent team button per ticket (`POST /api/tickets/{id}/run`), then live polling of `/api/events?since=N` and `/api/runs/{run_id}`.
- Relay strip of the five agents (working now / tool count / not called) and an activity feed indented by delegation depth with tool chips.
- "What each agent did" summary and the customer reply from the Boss's TicketOutcome.
- Approvals tray: human types their name, Approve → confirm → `POST /api/payment-requests/{id}/approve`; Reject also available.
- Checking till from `/api/cash` with a countdown and "▼ amount" after an approved payment, plus a receipt of `/api/payments`.
- Reset data button (`POST /api/reset`).
- Backend change for the board: API routes now reuse one long-lived MCP connection (restarted after a reset) instead of starting a server process per request.


---

## 10. Final run and lessons (Problem 9)

Final clean run on 2026-10-13: database reset at 1:45 PM ET (checking $3,400.00), then tickets 103 → 102 → 101 from the board. Details: `output/desk_tickets.html` (Actual, Cash, Reflection tabs), `output/resolved_tickets.json`, `output/resolved_board.html`, `output/audit_trail.json`.

| Ticket | Run id | First agent | Hand-offs | Payment (approved by Gawon Yi) | Checking after | Status |
|---|---|---|---|---|---|---|
| 103 | t103-04635cf5 | Accounting | boss→accounting, boss→inventory, boss→customer_service | None (10% quote, $1,044.00 for 20) | $3,400.00 | resolved |
| 102 | t102-4ac81e5f | Facilities | boss→facilities, facilities→accounting | Request 1, rent lease 1, $2,400.00 to Elm City Properties | $1,000.00 | resolved |
| 101 | t101-82446e08 | Inventory | boss→inventory, boss→accounting, boss→customer_service | Request 2, invoice 501, $840.00 to Bulldog Print Co (rent check: nothing due within 7 days) | $160.00 | resolved |

Ending checking $160.00 = `cash_accounts.checking` ($3,400.00 − $2,400.00 − $840.00). Facilities was skipped on 101 and 103, Inventory and Customer Service on 102. Usage: 41 model calls, 57 tool calls, 8 hand-offs, about 105,000 tokens, within the per-ticket limits in section 7.

**How the system changed between runs** (every run is in the audit trail):
- **Before any reset:** `t101-e7bcc25c` was the Problem 5 command-line test of ticket 101 (it left request 1 pending; the first reset cleared it).
- **Run 1** (reset 11:21 AM ET; t101-379f4cf0, t102-802de7c2, t103-8cb082a8): 102 stayed open because the Facilities rule demanded that the email's amount match the lease, but the email has no amount; 103 stayed open because the Boss waited for the club's answer. Fixed in `facilities.md` (check an amount only if the notice states one) and `boss.md` (a price override is resolved once the in-policy quote is saved).
- **Run 2** (reset 1:10 PM ET; t101-0c6826ff, t102-08fbf1ce, t103-3283da3e): all resolved, but 101 closed with no reply to the customer, Accounting needed two hand-offs because it was only asked to "confirm", and it paid the invoice before rent without checking the lease (rent fit, by luck). Fixed with code, not just prompts: `update_ticket_status` refuses `awaiting_approval`/`resolved` on customer orders and price overrides until a `Customer reply:` note exists, approval resolves such tickets only with that reply, and a new `list_leases` tool plus a server-side hold back rent due within 7 days before any invoice or purchase request is accepted. `boss.md` now asks delegates for the action, and `accounting.md` requires the rent check with numbers.
- **Run 3** (reset 1:45 PM ET; table above) is the final run.
