import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, API } from "./api";
import type { AgentEvent, Cash, Payment, PaymentRequest, Ticket, TicketDetail } from "./types";
import { TICKET_KIND, money } from "./agents";
import { TicketQueue } from "./components/TicketQueue";
import { RelayStrip } from "./components/RelayStrip";
import { ActivityFeed } from "./components/ActivityFeed";
import { ApprovalTray } from "./components/ApprovalTray";
import { CashTill } from "./components/CashTill";
import { AgentSummary } from "./components/AgentSummary";

function loadName(): string {
  try { return localStorage.getItem("cc-approver") ?? ""; } catch { return ""; }
}

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [detail, setDetail] = useState<TicketDetail | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const lastSeq = useRef(0);
  const [cash, setCash] = useState<Cash | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [requests, setRequests] = useState<PaymentRequest[]>([]);
  const [runId, setRunId] = useState<string | null>(null);
  const [approver, setApproverState] = useState(loadName);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [notice, setNotice] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [offline, setOffline] = useState(false);

  const setApprover = (s: string) => {
    setApproverState(s);
    try { localStorage.setItem("cc-approver", s); } catch { /* storage blocked; keep in memory */ }
  };

  const refreshShop = useCallback(async () => {
    try {
      const [t, c, p, r] = await Promise.all([api.tickets(), api.cash(), api.payments(), api.requests()]);
      setTickets(t); setCash(c); setPayments(p); setRequests(r); setOffline(false);
      setSelected((cur) => cur ?? t[0]?.id ?? null);
    } catch {
      setOffline(true);
    }
  }, []);

  const refreshDetail = useCallback(async (id: number | null) => {
    if (id == null) return;
    try { setDetail(await api.ticket(id)); } catch { /* shown via offline banner */ }
  }, []);

  const pulling = useRef(false);
  const pullEvents = useCallback(async () => {
    if (pulling.current) return;          // one request at a time, so no event is added twice
    pulling.current = true;
    try {
      const r = await api.events(lastSeq.current);
      if (r.last_seq < lastSeq.current) {   // backend restarted: start over
        lastSeq.current = 0;
        setEvents([]);
        return;
      }
      const fresh = r.events.filter((e) => e.seq > lastSeq.current);
      if (fresh.length) {
        lastSeq.current = fresh[fresh.length - 1].seq;
        setEvents((prev) => [...prev, ...fresh]);
      }
    } catch { /* offline banner covers it */ } finally {
      pulling.current = false;
    }
  }, []);

  useEffect(() => { refreshShop(); pullEvents(); }, [refreshShop, pullEvents]);
  useEffect(() => { refreshDetail(selected); }, [selected, refreshDetail]);

  // Live loop: events every second while a run is going, every 4s otherwise.
  const running = runId != null;
  useEffect(() => {
    const id = setInterval(pullEvents, running ? 1000 : 4000);
    return () => clearInterval(id);
  }, [running, pullEvents]);

  useEffect(() => {
    if (!runId) return;
    const id = setInterval(async () => {
      try {
        const s = await api.runStatus(runId);
        if (s.state !== "running") {
          setRunId(null);
          await pullEvents();
          await refreshShop();
          await refreshDetail(s.ticket_id);
          setNotice(s.state === "done"
            ? { kind: "ok", text: `Ticket #${s.ticket_id}: ${s.result?.outcome?.final_status === "awaiting_approval" ? "agents finished, payment waiting for you" : "agents finished"}` }
            : { kind: "err", text: `Ticket #${s.ticket_id} stopped: ${s.result?.error ?? "unknown error"}` });
        }
      } catch { /* keep polling */ }
    }, 1500);
    return () => clearInterval(id);
  }, [runId, pullEvents, refreshShop, refreshDetail]);

  const current = tickets.find((t) => t.id === selected) ?? null;
  const ticketEvents = useMemo(() => events.filter((e) => e.ticket_id === selected), [events, selected]);
  const lastRunEvents = useMemo(() => {
    const starts = ticketEvents.filter((e) => e.step === "run_start");
    const last = starts[starts.length - 1];
    return last ? ticketEvents.filter((e) => e.seq >= last.seq) : ticketEvents;
  }, [ticketEvents]);
  const outcome = detail?.ticket.id === selected ? detail?.latest_run?.result?.outcome ?? null : null;
  const anyRunning = running || tickets.some((t) => t.running);

  async function startRun() {
    if (!current) return;
    setNotice(null);
    try {
      const s = await api.run(current.id);
      setRunId(s.run_id);
      setTickets((ts) => ts.map((t) => (t.id === current.id ? { ...t, running: true } : t)));
    } catch (e) {
      setNotice({ kind: "err", text: (e as Error).message });
    }
  }

  async function approve(r: PaymentRequest) {
    setBusyId(r.id);
    try {
      const res = await api.approve(r.id, approver.trim());
      setNotice({ kind: "ok", text: `Paid ${money(res.amount)} to ${res.payee}.${res.ticket_resolved ? ` Ticket #${r.ticket_id} resolved.` : ""}` });
      await refreshShop(); await refreshDetail(selected); await pullEvents();
    } catch (e) {
      setNotice({ kind: "err", text: `Not paid: ${(e as Error).message}` });
    } finally { setBusyId(null); }
  }

  async function reject(r: PaymentRequest) {
    setBusyId(r.id);
    try {
      await api.reject(r.id, approver.trim(), "Rejected from the desk board");
      setNotice({ kind: "ok", text: `Rejected request ${r.id}. No money moved.` });
      await refreshShop(); await refreshDetail(selected); await pullEvents();
    } catch (e) {
      setNotice({ kind: "err", text: (e as Error).message });
    } finally { setBusyId(null); }
  }

  async function reset() {
    if (!window.confirm("Reset the working database to the original data? Pending requests and payments are cleared. The audit trail is kept.")) return;
    try {
      await api.reset();
      setNotice({ kind: "ok", text: "Database reset. Checking is back to the starting balance." });
      await refreshShop(); await refreshDetail(selected);
    } catch (e) {
      setNotice({ kind: "err", text: (e as Error).message });
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden>CC</span>
          <div>
            <h1>Campus Customs Desk</h1>
            <p>Chapel Street shop · five agents on shift</p>
          </div>
        </div>
        <button className="btn ghost small" onClick={reset} disabled={anyRunning}>Reset data</button>
      </header>

      {offline && (
        <div className="banner err">Can't reach the backend at {API}. Start it from backend/ with <code>uvicorn main:app --reload --port 8000</code>.</div>
      )}
      {notice && (
        <div className={`banner ${notice.kind}`} role="status">
          {notice.text}
          <button className="banner-x" onClick={() => setNotice(null)} aria-label="Dismiss">×</button>
        </div>
      )}

      <main className="layout">
        <TicketQueue tickets={tickets} selected={selected} onSelect={setSelected} />

        <section className="desk" aria-label="Selected ticket">
          {current ? (
            <>
              <div className="desk-head">
                <div>
                  <p className="desk-kind">{TICKET_KIND[current.type] ?? current.type} · #{current.id}</p>
                  <h2>{current.subject}</h2>
                  <p className="desk-from">From {current.requester}</p>
                  {detail?.ticket.id === current.id && detail.ticket.sku && (
                    <p className="desk-ask">{detail.ticket.qty} × {detail.ticket.sku} · size {detail.ticket.size}</p>
                  )}
                </div>
                <button className="btn primary run" onClick={startRun}
                  disabled={anyRunning || current.status !== "open"}>
                  {current.running || (running && current.id === selected) ? "Agents working…"
                    : current.status === "resolved" ? "Resolved"
                    : current.status === "awaiting_approval" ? "Waiting for your approval" : "Run agent team"}
                </button>
              </div>
              <RelayStrip events={lastRunEvents} running={current.running || running} />
              <ActivityFeed events={ticketEvents} running={current.running || running} />
              <AgentSummary outcome={outcome} events={lastRunEvents} />
            </>
          ) : (
            <p className="empty">Loading tickets…</p>
          )}
        </section>

        <aside className="side">
          <CashTill cash={cash} payments={payments} />
          <ApprovalTray requests={requests} approver={approver} setApprover={setApprover}
            onApprove={approve} onReject={reject} busyId={busyId} />
        </aside>
      </main>
    </div>
  );
}
