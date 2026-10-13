export type AgentName = "boss" | "inventory" | "accounting" | "facilities" | "customer_service";
export type Actor = AgentName | "human" | "system";
export type TicketStatus = "open" | "awaiting_approval" | "resolved";

export interface Ticket {
  id: number;
  type: string;
  requester: string;
  subject: string;
  status: TicketStatus;
  created_at: string;
  pending_request_ids: number[];
  latest_run_id: string | null;
  running: boolean;
}

export interface TicketDetail {
  ticket: Ticket & { notes: string | null; sku: string | null; size: string | null; qty: number | null };
  payment_requests: PaymentRequest[];
  latest_run: RunStatus | null;
}

export interface PaymentRequest {
  id: number;
  ticket_id: number;
  kind: "invoice" | "rent" | "purchase_order";
  ref_id: number;
  payee: string;
  amount: number;
  description: string;
  reason: string;
  requested_by: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
  decided_by: string | null;
}

export interface Contribution { agent: AgentName; summary: string }

export interface TicketOutcome {
  ticket_id: number;
  final_status: TicketStatus;
  outcome: string;
  first_agent_called: AgentName | null;
  delegations: string[];
  agent_contributions: Contribution[];
  payment_request_ids: number[];
  human_approvals_needed: string[];
  customer_reply: string | null;
}

export interface RunStatus {
  run_id: string;
  ticket_id: number;
  state: "running" | "done" | "error";
  result: { outcome: TicketOutcome | null; error: string | null; usage: Record<string, number> } | null;
}

export interface Cash {
  balance: number;
  as_of: string;
  pending_requests_total: number;
  balance_after_pending: number;
}

export interface Payment {
  id: number;
  kind: string;
  ref_id: number;
  amount: number;
  paid_at: string;
  approved_by: string;
}

export interface AgentEvent {
  seq: number;
  ts: string;
  run_id: string;
  ticket_id: number;
  agent: Actor;
  depth: number;
  step: string;
  said?: string | null;
  tools?: { name: string; args: Record<string, unknown> }[];
  tool_results?: { name: string; content: unknown }[];
  to?: AgentName;
  task?: string;
  reason?: string | null;
  output?: Record<string, unknown>;
  detail?: Record<string, unknown>;
}
