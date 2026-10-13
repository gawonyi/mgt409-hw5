import { useEffect, useRef, useState } from "react";
import type { AgentEvent } from "../types";
import { actorMeta, AGENTS, money } from "../agents";

const HIDDEN_TOOLS = new Set(["final_result", "delegate"]);

function argText(args: Record<string, unknown>) {
  return Object.entries(args)
    .filter(([k]) => !["reason", "resolution_note", "note", "requested_by", "agent"].includes(k))
    .map(([k, v]) => `${k}: ${typeof v === "string" ? v : JSON.stringify(v)}`)
    .join(", ");
}

function Row({ e, showResults }: { e: AgentEvent; showResults: boolean }) {
  const m = actorMeta(e.agent);
  const style = { ["--agent" as string]: m.color, ["--depth" as string]: e.depth } as React.CSSProperties;
  const who = (
    <span className="who">
      <span className="badge sm" aria-hidden>{m.mark}</span>
      {m.label}
    </span>
  );

  switch (e.step) {
    case "run_start":
      return <li className="row sys" style={style}>Run started for ticket #{e.ticket_id}</li>;
    case "delegate": {
      const to = e.to ? AGENTS[e.to] : null;
      return (
        <li className="row handoff" style={style}>
          {who}
          <span className="handoff-arrow" aria-label="hands off to">⟶</span>
          {to && (
            <span className="who" style={{ ["--agent" as string]: to.color } as React.CSSProperties}>
              <span className="badge sm" aria-hidden>{to.mark}</span>
              {to.label}
            </span>
          )}
          <p className="task">{e.task}</p>
        </li>
      );
    }
    case "delegate_refused":
      return (
        <li className="row warn" style={style}>
          {who} tried to hand off to {e.to}; refused: {e.reason}
        </li>
      );
    case "model_response": {
      const tools = (e.tools ?? []).filter((t) => !HIDDEN_TOOLS.has(t.name));
      if (!e.said && tools.length === 0) return null;
      return (
        <li className="row speech" style={style}>
          {who}
          {e.said && <p className="said">{e.said}</p>}
          {tools.length > 0 && (
            <ul className="tool-list">
              {tools.map((t, i) => (
                <li key={i} className={`tool${t.name.startsWith("request_") || t.name.startsWith("update_") || t.name.startsWith("add_") ? " write" : ""}`}>
                  <code>{t.name}</code>
                  <span className="args">{argText(t.args)}</span>
                </li>
              ))}
            </ul>
          )}
        </li>
      );
    }
    case "model_request": {
      const results = (e.tool_results ?? []).filter((r) => !HIDDEN_TOOLS.has(r.name));
      if (!showResults || results.length === 0) return null;
      return (
        <li className="row result" style={style}>
          {results.map((r, i) => (
            <details key={i}>
              <summary><code>{r.name}</code> returned</summary>
              <pre>{typeof r.content === "string" ? r.content : JSON.stringify(r.content, null, 2)}</pre>
            </details>
          ))}
        </li>
      );
    }
    case "agent_end": {
      const out = e.output ?? {};
      const line =
        (out.outcome as string) ??
        ((out.findings as string[]) ?? []).slice(0, 2).join(" ") ??
        "";
      return (
        <li className="row done" style={style}>
          {who} <span className="done-tag">reported back</span>
          {line && <p className="said">{line}</p>}
        </li>
      );
    }
    case "human_approval": {
      const d = e.detail ?? {};
      return (
        <li className="row human" style={style}>
          {who} approved {money(d.amount as number)} to {String(d.payee)}. Checking now {money(d.balance_after as number)}.
        </li>
      );
    }
    case "human_rejection":
      return <li className="row human" style={style}>{who} rejected request {String(e.detail?.request_id)}.</li>;
    case "run_end": {
      const u = (e.detail?.usage ?? {}) as Record<string, number>;
      const err = e.detail?.error as string | null;
      return (
        <li className={`row sys${err ? " err" : ""}`} style={style}>
          {err ? `Run stopped: ${err}` : `Run finished · ${u.requests ?? 0} model calls · ${u.delegations ?? 0} hand-offs · ${(u.input_tokens ?? 0) + (u.output_tokens ?? 0)} tokens`}
        </li>
      );
    }
    case "error":
      return <li className="row sys err" style={style}>{String(e.detail?.error ?? "Error")}</li>;
    default:
      return null;
  }
}

export function ActivityFeed({ events, running }: { events: AgentEvent[]; running: boolean }) {
  const [showResults, setShowResults] = useState(false);
  const list = useRef<HTMLOListElement>(null);
  useEffect(() => {
    // While agents work, keep the newest step in view inside the feed.
    if (running && list.current) list.current.scrollTop = list.current.scrollHeight;
  }, [events.length, running]);

  return (
    <section className="feed" aria-label="Agent activity" aria-live="polite">
      <div className="feed-head">
        <h3>Activity</h3>
        <label className="toggle">
          <input type="checkbox" checked={showResults} onChange={(e) => setShowResults(e.target.checked)} />
          Show tool results
        </label>
      </div>
      {events.length === 0 ? (
        <p className="empty">No activity yet. Run the agent team to watch them work this ticket.</p>
      ) : (
        <ol className="rows" ref={list}>
          {events.map((e) => <Row key={e.seq} e={e} showResults={showResults} />)}
        </ol>
      )}
    </section>
  );
}
