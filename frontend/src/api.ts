import type { AgentEvent, Cash, Payment, PaymentRequest, RunStatus, Ticket, TicketDetail } from "./types";

export const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch { /* keep status text */ }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

export const api = {
  tickets: () => call<{ tickets: Ticket[] }>("/api/tickets").then((r) => r.tickets),
  ticket: (id: number) => call<TicketDetail>(`/api/tickets/${id}`),
  run: (id: number) => call<RunStatus>(`/api/tickets/${id}/run`, { method: "POST" }),
  runStatus: (runId: string) => call<RunStatus>(`/api/runs/${encodeURIComponent(runId)}`),
  events: (since: number) => call<{ last_seq: number; events: AgentEvent[] }>(`/api/events?since=${since}&limit=500`),
  requests: () => call<{ requests: PaymentRequest[] }>("/api/payment-requests").then((r) => r.requests),
  approve: (id: number, name: string) =>
    call<{ amount: number; balance_after: number; payee: string; ticket_resolved: boolean }>(
      `/api/payment-requests/${id}/approve`,
      { method: "POST", body: JSON.stringify({ approved_by: name }) },
    ),
  reject: (id: number, name: string, note: string) =>
    call(`/api/payment-requests/${id}/reject`, { method: "POST", body: JSON.stringify({ approved_by: name, note }) }),
  cash: () => call<Cash>("/api/cash"),
  payments: () => call<{ payments: Payment[] }>("/api/payments").then((r) => r.payments),
  reset: () => call<{ checking_balance: number }>("/api/reset", { method: "POST" }),
};
