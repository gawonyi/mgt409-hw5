import type { Actor, AgentName } from "./types";

// One color + mark per agent, fixed order (AGENTS.md SERIES). Color is never the
// only cue: every agent also has a two-letter mark and a name.
export const AGENTS: Record<AgentName, { label: string; mark: string; role: string; color: string }> = {
  boss: { label: "Boss", mark: "Bo", role: "Routes the ticket, closes it out", color: "#a06bff" },
  inventory: { label: "Inventory", mark: "In", role: "Shelf stock and reorders", color: "#4ef0c4" },
  accounting: { label: "Accounting", mark: "Ac", role: "Cash, bills, discounts", color: "#ffd76e" },
  facilities: { label: "Facilities", mark: "Fa", role: "Lease and building", color: "#7aa2ff" },
  customer_service: { label: "Customer Service", mark: "CS", role: "Replies to requesters", color: "#ffb3f2" },
};
export const AGENT_ORDER: AgentName[] = ["boss", "inventory", "accounting", "facilities", "customer_service"];

export function actorMeta(a: Actor) {
  if (a === "human") return { label: "You", mark: "✓", role: "Human approver", color: "#ece9f5" };
  if (a === "system") return { label: "Desk", mark: "⟲", role: "System", color: "#7d7597" };
  return AGENTS[a];
}

export const money = (n: number | null | undefined) =>
  n == null ? "—" : n.toLocaleString("en-US", { style: "currency", currency: "USD" });

export const TICKET_KIND: Record<string, string> = {
  customer_order: "Customer order",
  rent_notice: "Rent notice",
  price_override: "Price override",
};
