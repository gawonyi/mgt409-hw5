# Campus Customs Multi-Agent Operations (MGT 409 HW5)

A five-agent team (Boss, Inventory, Accounting, Facilities, Customer Service) that works the support tickets of Campus Customs, a small Yale merch shop. The agents read and write shop data only through an MCP server over a SQLite database, run on `gpt-6-luna` through Portkey, and can prepare payments but never move money: a human approves every payment on a React dashboard.

Author: Gawon Yi

```
React board (frontend/, :5173)  →  FastAPI (backend/main.py, :8000)  →  PydanticAI agents (backend/agents.py)
                                                     ↓                               ↓
                                         campus-customs MCP server (mcp_server/server.py, started from .mcp.json)
                                                                     ↓
                                                    data/campus_customs_new.db (working copy)
```

## Requirements

- Python 3.11+ and Node.js 18+
- A Portkey API key with access to `gpt-6-luna`

## 1. Set up

```bash
git clone https://github.com/gawonyi/mgt409-hw5.git
cd mgt409-hw5

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

cp .env.example .env        # then put your key in PORTKEY_API_KEY
```

The backend finds `.env` in the project folder or any parent folder. Never commit it.

## 2. Copy the original database to the working copy

`data/campus_customs.db` is the original and is never written. Everything runs on `data/campus_customs_new.db`:

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

## 3. MCP server

`.mcp.json` registers the server as `campus-customs` (stdio, run with the project's `.venv/bin/python` from step 1, so a coding agent can start it without an activated venv). The backend starts it automatically from this file, so you normally don't run it by hand. To run it on its own, or to check it:

```bash
python3 mcp_server/server.py      # stdio MCP server (waits for a client; Ctrl+C to stop)
python3 mcp_smoke_test.py         # a Portkey model calls three tools; writes output/mcp_smoke.json
```

In Claude Code (or Cursor), open this folder after step 1 and the `campus-customs` tools are available from `.mcp.json`; `output/mcp_smoke.json` records such a run.

`mcp_smoke_test.py` opens the database itself only to double-check the tool outputs (read-only); the agents and the API never touch the database except through the MCP server.

Tools and the tables they use: `mcp_server/README.md`. Claude Code and Cursor can load the same `.mcp.json`.

## 4. FastAPI backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API at http://localhost:8000 (route list at http://localhost:8000/docs). Leave this terminal running. You can also run one ticket from the command line: `python3 backend/agents.py 101`.

## 5. React dashboard

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## 6. Full three-ticket test

1. **Reset the database first**: click **Reset data** on the board (or `curl -X POST http://localhost:8000/api/reset`, or repeat step 2 with the backend stopped). Checking goes back to $3,400.00 and all tickets to Open. The audit trail is kept; it only grows.
2. Type your name under **Approving as**.
3. Select **#101**, click **Run agent team**, wait for the agents, then **Approve → Confirm payment** for the $840.00 invoice.
4. Do the same for **#102** (approve the $2,400.00 rent).
5. Run **#103** (a discount quote; no payment expected).

The tickets can be run in any order; the submitted final run used 103 → 102 → 101. Either way the expected end state is all three tickets resolved and checking $160.00 in `cash_accounts` ($3,400.00 − $2,400.00 rent − $840.00 invoice).

## Project layout

| Path | What it is |
|---|---|
| `AI_prompts.md` | Prompts I gave my AI coding assistant, per problem |
| `.mcp.json` | MCP server registration (campus-customs, stdio) |
| `mcp_server/server.py` | FastMCP server: all reads/writes of shop data; payment execution is human-only |
| `backend/agents.py` | The five PydanticAI agents, delegation tool, audited agent loop |
| `backend/prompts/*.md` | One prompt per agent with its shop rules |
| `backend/models.py` | Pydantic data types (reports, outcomes, audit events) |
| `backend/main.py` | FastAPI routes for the board |
| `backend/config.py`, `audit.py`, `mcp_client.py` | Model/limits settings, append-only audit log, MCP connection and per-role tool filters |
| `frontend/` | React + Vite + TypeScript dashboard |
| `output/harness.md` | Full harness: tables, MCP tools, agents, routes, dashboard, safety rules, token limits, final run |
| `output/desk_tickets.html` | Expected vs. actual per ticket, Cash reconciliation, Reflection |
| `output/resolved_tickets.json`, `resolved_board.html` | Results and board screenshots of the final run |
| `output/audit_trail.json` | Every agent-loop step of every run (append-only) |
| `output/mcp_smoke.json`, `mcp_smoke_claude_code.png` | Problem 4: the three MCP tools called from Claude Code (plus an automated Portkey check) |
| `output/design.md`, `github_url.txt` | Dashboard design notes, repo URL |
