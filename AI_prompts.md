# AI Prompts Log — HW5: Campus Customs Multi-Agent Operations

Author: Gawon Yi
Vibe coder: Claude (the Claude app, working directly in this project folder on my Mac); Problem 4's MCP tools were also called from Claude Code with the server connected through `.mcp.json`.

This file logs the prompts I gave my AI coding assistant, one section per problem. I typed my prompts in Korean, my working language; this log gives them in English. For each problem, my first prompt restated that problem's requirements in my own words; the follow-up prompts are the ones I wrote when something went wrong.

---

## Problem 1 — Vibe Coder Prompts

**Prompt 1 (my own words, translated from Korean):**
> Problem 1 is about documenting how I work with an AI coding tool. Create `AI_prompts.md` at the start of the project and keep adding the prompts I give you as we go. Make a separate section for each problem. Each section needs the problem number and title, at least one prompt I wrote myself, any follow-up prompt I needed, and one sentence on what was missing from your first response. When I explain the requirements to you, I should use my own words.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; the first response created the file with the structure I asked for.

---

## Problem 2 — Study the Campus Customs Database

**Prompt 1 (my own words, translated from Korean):**
> For Problem 2, I need to understand the database the agents will use and the real work tickets in it. Open `data/campus_customs.db` and look at every table and column. Copy the original to `data/campus_customs_new.db`; from now on, any database changes happen in the copy, not the original. Look into the three open tickets and figure out which other tables each one connects to. Then create `output/harness.md` that lists every table's columns with one line on why that table matters for the agents' work. The page mentions `desk`, `tickets`, `inventory`, `pricing`, `vendors`, `leases`, `cash_accounts`, `payments`, and `invoices`, but verify every field against the actual database instead of making up column names. `harness.md` will keep growing in later problems.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; the first response checked the real schema, made the copy, and traced all three tickets.

---

## Problem 3 — Build the MCP Server

**Prompt 1 (my own words, translated from Korean):**
> Problem 3 is about building the shared data-access server that every agent will use. Write a FastMCP server in `mcp_server/` that uses `data/campus_customs_new.db`. We don't need to run it or connect it to the coding tool yet. Start with three MCP tools that are needed to handle the three tickets in the database, and give them names that make their job obvious. Everything a tool returns has to come from the real database; never make up data. We'll add more tools to the same server later. In `output/harness.md`, for each of the three tools, record the tool name, which table it reads, which ticket (101, 102, or 103) it helps with, and the specific reason that ticket needs it. Don't just say "reads inventory"; explain what information the ticket needs and why the tool fits. Also create `mcp_server/README.md` explaining the server's purpose, the database it uses, and the three tools.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; the first response delivered the server, README, and ticket-specific harness rows.

---

## Problem 4 — Connect and Test the MCP Server

**Prompt 1 (my own words, translated from Korean):**
> Problem 4 is about proving the MCP server actually works inside an AI coding tool. Connect the server to the vibe coder I use (Claude Code, Codex, Cursor, etc.) by creating `.mcp.json` at the project root, or by saving it the way my tool stores local MCP settings. Then actually call each of the three Problem 3 tools and save the evidence in `output/mcp_smoke.json`. For each tool, the evidence must include the prompt I typed, the name of the tool that was called, and the output it really returned. The outputs have to match the values in `data/campus_customs_new.db`; a made-up run doesn't count.

**Follow-up prompt (translated from Korean):**
> I don't understand what I'm supposed to do. How do I connect this to a coding tool? I'd like the deliverables to run on my Portkey API.

**What was missing from the first response:** It handed me manual setup steps for an outside coding tool instead of a test I could run with one command on the Portkey gateway my workspace already uses.

**Follow-up prompt 2 (translated from Korean):**
> (Pasted the terminal output: every call failed with a 400 error saying gpt-6-luna does not support function tools with reasoning_effort on /v1/chat/completions.)

**What was missing:** The test script did not set `reasoning_effort` to `none`, which gpt-6-luna on Portkey requires before it will call tools.


**Follow-up prompt 3 (later, during the review), typed into Claude Code with the MCP server connected:**
> Use the campus-customs MCP server tools directly (do not start the server yourself or run any script). Call check_stock_by_sku_size for CC-TEE-WHITE size S, get_lease_rent_due for lease 1, and get_sku_pricing for CC-HOOD-NAVY, one at a time, and show each tool name and raw output.

**What was missing:** The Portkey script proved the server works, but the assignment asks for the tools to be called from a vibe coder. My first try in Claude Code failed because `.mcp.json` started the server with the system `python3` (no `fastmcp`), so I asked "this is what step 2 returned, what do I do?"; `.mcp.json` was changed to `.venv/bin/python`, and in a new session Claude Code called all three tools directly. That run is the main evidence in `output/mcp_smoke.json` (screenshot: `output/mcp_smoke_claude_code.png`).
---

## Problem 5 — Build the Agent Team and Grow the MCP Tools

**Prompt 1 (my own words, translated from Korean):**
> Problem 5 is about building five agents with different expertise and wiring them so they can hand work to each other. Build it in PydanticAI with Boss (splits up the work and delegates), Inventory, Accounting, Facilities, and Customer Service. The diagram shows Boss in the middle, but the real system has to let agents delegate to each other too, with a run loop that handles those hand-offs. Put one prompt file per agent in `backend/prompts/`, the data types in `backend/models.py`, and the agent code under `backend/`. Every agent uses `PORTKEY_API_KEY` and only `gpt-6-luna`. The prompts need real shop rules and scope for each role, for example deadlines, holding orders that have an unpaid invoice, and payments that need a human to approve, given to the right agent; specific beats generic. Add the tools the agents need to the existing MCP server. Agents must get data from `data/campus_customs_new.db` through MCP only, with no separate shop-tools layer that goes around it, and every shop fact has to come from the database. Write `output/audit_trail.json` with every agent-loop step, enough to review later who did what; append on every run and never delete or overwrite old entries. Add to `output/harness.md` the agent list, every MCP tool with the tables it uses, guardrails for a business that handles real customers and real money, and how token use is limited. Finally, update `mcp_server/README.md` so it lists every tool.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing I had to ask for, though testing showed the restock tool would let a purchase order go through when cash was short, so it got a server-side check.

---

## Problem 6 — Plan the Three Tickets

**Prompt 1 (my own words, translated from Korean):**
> Problem 6 is about planning how the agents should handle the three tickets before we actually run them. Create `output/desk_tickets.html` as a page I can double-click to open in a browser, with a tab for each of Ticket 101, 102, and 103, plus Cash and Reflection tabs for later problems (those two can be empty or have a short note for now). On each ticket tab, fill in only the Expected section and leave space for an Actual section we'll fill after the run. Expected needs: which agent the Boss calls first and why, every delegation we expect between agents and in what order, and which MCP tools we expect the run to use. Don't plan for the Boss to call every specialist; pick only the agents each ticket needs and spell out the hand-offs between specialists.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; the plans named only the agents each ticket needs and the specialist-to-specialist hand-offs.

---

## Problem 7 — Backend Routes

**Prompt 1 (my own words, translated from Korean):**
> Problem 7 is about building a FastAPI backend so the React dashboard can run the agents and get results back. In `backend/main.py`, add API routes that: list tickets 101, 102, and 103 with their status (open/resolved); take a ticket ID and run the agent team on it; return recent agent events, including what each agent said and which tools it used; process a payment or purchase only after a human clicks approve; return the current checking balance from `cash_accounts`; and reset the database to its original state for testing. Agents can prepare payments, but the cash balance may only change after a person approves. The server runs from `backend/` with `uvicorn main:app --reload --port 8000` at http://localhost:8000, and the next problem's frontend will call it. Also add one line per route to `output/harness.md` with its URL and what it does; the exact endpoint paths are up to us.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; all six functions were covered and the approve route was tested to be the only thing that changes cash.

---

## Problem 8 — Agent Dashboard

**Prompt 1 (my own words, translated from Korean):**
> Problem 8 is about building a dashboard where we can see the tickets and the agents' work in real time, and where a person can approve payments. Build it in `frontend/` with React + Vite + TypeScript, calling the Problem 7 API at http://localhost:8000, and allow the Vite dev server origin (usually http://localhost:5173) in the backend's CORS. The dashboard must show all three tickets, let me pick one and start the agent team, show what each agent is saying or doing while it runs, change the ticket to resolved when it's done, give a short summary of what each agent did, let a human approve a payment or purchase, show the current checking balance, and make it visible that the cash balance actually drops after an approved payment. Design is graded too: think about layout and usability, make each agent's activity easy to tell apart, make it feel like an operations dashboard a real employee would use, and go beyond the default Vite template with creative design choices. It starts with `npm run dev`. Also write `output/design.md` explaining why I chose the layout, how each agent's information is shown differently, how resolved tickets and the cash balance are shown, and the creative choices for usability and polish and why.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing I had to ask for; screenshot testing caught a slow refresh after approval and a sideways scroll on phones, which were fixed before handing it over.

---

## Problem 9 — Resolve the Tickets

**Prompt 1 (my own words, translated from Korean):**
> Problem 9 is about running the finished multi-agent system on the real data, resolving all three tickets, and checking the results. Reset `data/campus_customs_new.db` to the original data, record the starting checking balance, run tickets 101, 102, and 103 from the dashboard, and keep going until all three are resolved. Then reopen `output/desk_tickets.html` and fill in each ticket's Actual section with the agents that actually took part, the real delegations between them, and the MCP tools they actually used, keeping the Expected plans so the two can be compared. The Cash tab needs the starting balance after reset, how cash changed for each ticket and why (which payment or purchase, how much), and the ending balance, which must equal `cash_accounts` in the database. Save `output/resolved_tickets.json` with each ticket's ID, final status, a short outcome, each agent's contribution, and any human payment approvals, and `output/resolved_board.html` as a double-clickable page with screenshots of the React board showing 101, 102, and 103 resolved. Keep appending real runs to `output/audit_trail.json` and finish `output/harness.md` so it covers the tables, MCP tools, five agents, API routes, dashboard, and safety rules.

**Follow-up prompt (translated from Korean):**
> I ran them, but tickets 2 and 3 ended up like this. (Pasted screenshots: 102 and 103 finished but stayed Open.)

**What was missing from the first response:** The agent prompts were too strict for the real tickets: Facilities required the rent email's amount to match even though the email has no amount, and the Boss would not resolve a price quote while waiting on the customer, so both rules had to be clarified before a clean rerun.

---

## Problem 10 — Reflection

**Prompt 1 (my own words, translated from Korean):**
> Problem 10 is about judging how well the multi-agent system actually worked and whether the way we split up and delegated the work made sense. Don't make a separate document; finish the Reflection tab in `output/desk_tickets.html`. Answer five questions: how well the agents performed on each ticket and what that judgment is based on; how the real delegation and results differed from the plan for tickets 101, 102, and 103; what would have been simpler with a single agent using tools instead of several agents, and why; three new problems Campus Customs might face that the current agents and tools can already solve; and three it can't solve, with the new tools and agents that would be needed. Tie everything to the Campus Customs app we actually built, use the real results of the three runs and the Expected/Actual and Cash tabs as evidence, name specific ticket numbers and situations, and avoid a generic essay about AI pros and cons.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; every answer cites ticket numbers, run ids, tool counts, and the Cash tab.

---

## Problem 11 — Submit to GitHub

**Prompt 1 (my own words, translated from Korean):**
> Problem 11 is about packaging the project so a grader can download it and reproduce it. Upload the code to a public GitHub repository, and I'll submit the URL on Canvas; also write the same URL in `output/github_url.txt`. Don't upload the `.env` with my real API key; include `.env.example` instead. Include both `data/campus_customs.db` (original) and `data/campus_customs_new.db` (working copy). Follow the required layout: `AI_prompts.md`, `requirements.txt`, `.env.example`, `.gitignore`, `.mcp.json`, `README.md` at the root, plus `data/`, `mcp_server/` (`server.py`, `README.md`), `frontend/`, `backend/` (`main.py`, `models.py`, `prompts/` with the five agent prompts), and `output/` with all the deliverables. The root README has to explain how to copy the original DB to the working copy, run the MCP server, run the FastAPI backend, run the React dashboard, and reset the DB before a full three-ticket test.

**Follow-up prompt:** None needed.

**What was missing from the first response:** Nothing; it also checked that no file contains the real API key before uploading.

---

## Review and Revision (after the first GitHub upload)

**Prompt 1 (translated from Korean):**
> Grade this assignment from the professor's point of view and evaluate whether it meets every requirement.

**Prompt 2 (translated from Korean):**
> Before fixing anything, here is more feedback. Check whether it is worth applying and list everything that needs to be fixed. (Attached another reviewer's feedback.)

**Prompt 3 (translated from Korean):**
> Update all of it!

**Prompt 4 (translated from Korean):**
> Keep the record of the rule violation, but fix it so the final output is confirmed to work correctly. Fix everything.

**What the review found and what changed:** Ticket 101 had been resolved without a reply to the customer, the rent-first rule had only held by luck, the Problem 4 evidence did not come from a vibe coder, and (found after the third run) the ticket 103 reply priced 8 hoodies at the bulk rate although bulk pricing needs 10+ units. Fixes: server-side guards (a customer order needs a saved reply before it can wait for approval or resolve; rent due within 7 days is held back before any other payment), a new `list_leases` tool, sharper Boss and Accounting prompts, Problem 4 tools called from Claude Code, the discount policy enforced inside `quote_bulk_discount`, and clean reruns of all three tickets; the fourth run is the final one and every fix is verified there (Problem 9 and 10 outputs updated, earlier runs kept in the run history).
