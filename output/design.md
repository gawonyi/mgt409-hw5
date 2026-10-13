# Campus Customs Desk: dashboard design

The board is the shift lead's screen at a small campus merch shop. Someone standing at the counter should be able to answer four questions in a glance: what is in the queue, which agent is doing what right now, is money waiting on me, and how much is in checking. Everything on the page serves one of those.

Stack: React 18 + Vite + TypeScript in `frontend/`, calling the FastAPI backend at `http://localhost:8000` (CORS allows `http://localhost:5173`). Start with `npm install` then `npm run dev`.

## 1. Layout and why

```
┌ Campus Customs Desk ───────────────────────────────────────── Reset data ┐
│ Queue          │ Selected ticket                       │ Checking        │
│ ┌ #101 ──────┐ │ Customer order · #101                 │ $3,400.00       │
│ │ Bulldog tee│ │ Bulldog tee          [Run agent team] │ ▼ $840.00       │
│ └────────────┘ │ (Bo)──(In)──(Ac)──(Fa)──(CS)  relay   │ receipt …       │
│ ┌ #102 ──────┐ │ Activity feed (indented by hand-off)  ├─────────────────┤
│ └────────────┘ │ What each agent did + customer reply  │ Waiting for you │
│ ┌ #103 ──────┐ │                                       │ [Approve][Reject│
└────────────────┴───────────────────────────────────────┴─────────────────┘
```

- **Three columns that match how the work flows: pick, watch, decide.** The queue sits on the left because that is where the eye starts. The selected ticket takes the wide middle column because the agents' conversation is the longest content. The right column holds the two things only a human controls: cash and approvals.
- **Approvals sit directly under the balance,** so the person approving a payment always sees what it will do to checking before clicking (the till also shows "waiting for approval" and "balance after").
- **One ticket at a time in the middle** keeps the feed readable and mirrors the backend rule that only one ticket runs at a time (they share one cash account).
- Responsive: at ≤1180px the cash and approvals drop below as two columns; at phone width everything stacks with no sideways scroll.

## 2. How each agent looks different

- **Each agent gets its own color, two-letter mark, and name,** always used together so color never carries meaning alone: Boss purple (Bo), Inventory mint (In), Accounting amber (Ac, the money color), Facilities blue (Fa), Customer Service pink (CS). The five colors are a fixed palette defined once in `frontend/src/agents.ts`, so an agent always looks the same everywhere on the board.
- **Relay strip.** The five agents sit on one line like stations on a relay. The agent currently holding the baton glows in its own color and says "Working now"; agents that took part show how many tools they used; agents that were not needed stay grey and say "Not called." This makes the key design idea of HW5 visible: the Boss does *not* call every specialist.
- **Activity feed.** Every row has a left stripe in the speaker's color and is indented by delegation depth, so a hand-off from Inventory to Accounting visibly steps inward and comes back out when Accounting reports back. Row types look different:
  - speech (what the agent said) in a solid row,
  - hand-offs as dashed rows with "Boss ⟶ Inventory" and the task text,
  - tool calls as chips with their arguments: mint for reads, amber for writes (requests, notes, status), matching the till and approval colors,
  - "reported back" rows when a specialist finishes, and a quiet system line with model calls, hand-offs, and tokens at the end of a run.
  - "Show tool results" reveals the raw MCP output under each call for anyone auditing the numbers.
- **What each agent did** lists one line per agent that worked the ticket (from the Boss's outcome), then the exact reply sent to the requester.

## 3. Resolved tickets and cash

- **Resolved tickets are stamped.** A resolved ticket gets a tilted mint "Resolved" rubber stamp on its queue card and its text dims, like a paper slip that has been dealt with. Open tickets show "Open"; tickets waiting on money show an amber "Needs your approval"; a running ticket shows a pulsing "Agents working". The Run button reads "Resolved" or "Waiting for your approval" and is disabled when there is nothing for agents to do.
- **Cash is a till, not a stat tile.** Checking is shown large in a monospaced, tabular font. When an approved payment lands, the number counts down to the new balance and a rose "▼ $840.00" appears, so the drop is something you see happen, not just a changed digit. Pending requests show in amber as "$X waiting for approval · $Y after".
- **The receipt** under the till lists every payment that actually left the shop, with who approved it, on a paper-slip edge. Before any approval it says "No money has left the shop yet."

## 4. Creative choices for usability and polish

- **The baton.** The only continuous animation on the page is the glow on whichever agent is working, so motion always means "look here." The stamp and the till countdown are one-off responses to an action. All motion turns off under `prefers-reduced-motion`.
- **Approval is a two-step human act.** You type your name once ("Approving as", remembered in this browser), click Approve, then confirm "Send $840.00 from checking?". The backend rejects approvals without a real name, so the name on the receipt is the person who clicked.
- **Words written for a shop employee, not a developer.** "Waiting for you", "Run agent team", "No money has left the shop yet", "Paid $840.00 to Bulldog Print Co. Ticket #101 resolved." Errors say what to do: if the backend is down, the banner shows the exact `uvicorn` command.
- **Theme.** A dark purple-and-mint system (the standard dashboard theme I use for this course), with fixed meanings: purple means you and the app (selection, primary buttons), mint means the machine working (live agents, read tools, good news), amber means money waiting, rose means money leaving. Numbers use a monospaced font and line up.
- **Live without a refresh button.** The board polls agent events every second during a run (every 4 seconds otherwise) and asks only for events after the last one it has, so it stays light. The backend keeps one open MCP connection for these reads.
- **Accessible basics:** visible purple focus rings, real buttons, `aria-live` on the activity feed, and labels on every control.
