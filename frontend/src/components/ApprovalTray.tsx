import { useState } from "react";
import type { PaymentRequest } from "../types";
import { AGENTS, money } from "../agents";

const KIND = { invoice: "Vendor invoice", rent: "Rent", purchase_order: "Purchase order" } as const;

export function ApprovalTray({ requests, approver, setApprover, onApprove, onReject, busyId }: {
  requests: PaymentRequest[];
  approver: string;
  setApprover: (s: string) => void;
  onApprove: (r: PaymentRequest) => void;
  onReject: (r: PaymentRequest) => void;
  busyId: number | null;
}) {
  const pending = requests.filter((r) => r.status === "pending");
  const [confirming, setConfirming] = useState<number | null>(null);
  const nameOk = approver.trim().length >= 2;

  return (
    <section className="tray" aria-label="Approvals">
      <h2 className="pane-title">Waiting for you</h2>
      <label className="approver">
        <span>Approving as</span>
        <input value={approver} onChange={(e) => setApprover(e.target.value)} placeholder="Your name" autoComplete="name" />
      </label>
      {pending.length === 0 ? (
        <p className="empty">Nothing to approve. Agents put payments here; money only moves when you approve.</p>
      ) : (
        <ul className="requests">
          {pending.map((r) => {
            const by = AGENTS[r.requested_by as keyof typeof AGENTS];
            return (
              <li key={r.id} className="request">
                <div className="req-top">
                  <span className="req-kind">{KIND[r.kind]} · ticket #{r.ticket_id}</span>
                  <span className="req-amount">{money(r.amount)}</span>
                </div>
                <p className="req-payee">Pay {r.payee}</p>
                <p className="req-desc">{r.description}</p>
                {by && (
                  <p className="req-by" style={{ ["--agent" as string]: by.color } as React.CSSProperties}>
                    Prepared by <b>{by.label}</b>: {r.reason}
                  </p>
                )}
                {confirming === r.id ? (
                  <div className="req-actions confirm">
                    <span>Send {money(r.amount)} from checking?</span>
                    <button className="btn primary" disabled={busyId === r.id} onClick={() => { onApprove(r); setConfirming(null); }}>
                      {busyId === r.id ? "Paying…" : "Confirm payment"}
                    </button>
                    <button className="btn ghost" onClick={() => setConfirming(null)}>Cancel</button>
                  </div>
                ) : (
                  <div className="req-actions">
                    <button className="btn primary" disabled={!nameOk || busyId != null} onClick={() => setConfirming(r.id)}
                      title={nameOk ? "" : "Type your name first"}>
                      Approve
                    </button>
                    <button className="btn ghost" disabled={!nameOk || busyId != null} onClick={() => onReject(r)}>Reject</button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
