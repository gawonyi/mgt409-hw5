import type { AgentEvent, AgentName, TicketOutcome } from "../types";
import { AGENTS, AGENT_ORDER } from "../agents";

// One line per agent that touched the ticket: the Boss's contribution list when the
// run is done, otherwise the latest report each agent sent back.
export function AgentSummary({ outcome, events }: { outcome: TicketOutcome | null; events: AgentEvent[] }) {
  const fromRun = new Map<AgentName, string>();
  for (const c of outcome?.agent_contributions ?? []) fromRun.set(c.agent, c.summary);
  if (fromRun.size === 0) {
    for (const e of events) {
      if (e.step !== "agent_end" || e.agent === "human" || e.agent === "system") continue;
      const o = e.output ?? {};
      const s = (o.outcome as string) ?? ((o.findings as string[]) ?? []).slice(0, 2).join(" ");
      if (s) fromRun.set(e.agent, s);
    }
  }
  const agents = AGENT_ORDER.filter((a) => fromRun.has(a));

  return (
    <section className="summary" aria-label="What each agent did">
      <h3>What each agent did</h3>
      {agents.length === 0 ? (
        <p className="empty">Summaries appear here after the run.</p>
      ) : (
        <ul>
          {agents.map((a) => (
            <li key={a} style={{ ["--agent" as string]: AGENTS[a].color } as React.CSSProperties}>
              <span className="badge sm" aria-hidden>{AGENTS[a].mark}</span>
              <div>
                <b>{AGENTS[a].label}</b>
                <p>{fromRun.get(a)}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
      {outcome?.customer_reply && (
        <blockquote className="reply">
          <span>Reply to requester</span>
          {outcome.customer_reply}
        </blockquote>
      )}
    </section>
  );
}
