import type { AgentEvent, AgentName } from "../types";
import { AGENTS, AGENT_ORDER } from "../agents";

// Five stations. The one that holds the baton (last agent to act while running)
// glows; stations that took part show how many tools they used.
export function RelayStrip({ events, running }: { events: AgentEvent[]; running: boolean }) {
  const stats = new Map<AgentName, { tools: number; done: boolean }>();
  let baton: AgentName | null = null;
  for (const e of events) {
    if (e.agent === "human" || e.agent === "system") continue;
    const s = stats.get(e.agent) ?? { tools: 0, done: false };
    if (e.step === "model_response") {
      s.tools += (e.tools ?? []).filter((t) => t.name !== "final_result" && t.name !== "delegate").length;
    }
    if (e.step === "agent_end") s.done = true;
    if (e.step === "user_prompt") s.done = false;
    stats.set(e.agent, s);
    if (e.step === "agent_end") {
      baton = null;
    } else if (e.step !== "run_end") {
      baton = e.agent;
    }
  }
  // When a delegated agent ends, the caller holds the baton again.
  if (running && baton == null) {
    const last = [...events].reverse().find((e) => e.step === "agent_end");
    if (last) {
      const parent = [...events].reverse().find((e) => e.step === "delegate" && e.to === last.agent);
      baton = (parent?.agent as AgentName) ?? null;
    }
  }

  return (
    <ol className="relay" aria-label="Agent stations">
      {AGENT_ORDER.map((name) => {
        const a = AGENTS[name];
        const s = stats.get(name);
        const state = running && baton === name ? "live" : s ? "took-part" : "idle";
        return (
          <li key={name} className={`station ${state}`} style={{ ["--agent" as string]: a.color }}>
            <span className="badge" aria-hidden>{a.mark}</span>
            <span className="station-name">{a.label}</span>
            <span className="station-note">
              {state === "live" ? "Working now" : s ? `${s.tools} tool call${s.tools === 1 ? "" : "s"}` : "Not called"}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
