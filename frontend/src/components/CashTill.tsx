import { useEffect, useRef, useState } from "react";
import type { Cash, Payment } from "../types";
import { money } from "../agents";

// The till: the balance counts down when an approved payment lands, and the
// receipt underneath lists every payment with who approved it.
export function CashTill({ cash, payments }: { cash: Cash | null; payments: Payment[] }) {
  const [shown, setShown] = useState<number | null>(cash?.balance ?? null);
  const [delta, setDelta] = useState<number | null>(null);
  const prev = useRef<number | null>(null);

  useEffect(() => {
    if (!cash) return;
    const from = prev.current;
    const to = cash.balance;
    prev.current = to;
    if (from == null || from === to || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setShown(to);
      if (from != null && from !== to) setDelta(to - from);
      return;
    }
    setDelta(to - from);
    const start = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / 900);
      const eased = 1 - Math.pow(1 - p, 3);
      setShown(from + (to - from) * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [cash]);

  return (
    <section className="till" aria-label="Checking balance">
      <div className="till-top">
        <span className="till-label">Checking</span>
        <span className="till-asof">as of {cash?.as_of ?? "—"}</span>
      </div>
      <output className="till-amount">{money(shown)}</output>
      {delta != null && delta !== 0 && (
        <span key={cash?.balance} className={`till-delta ${delta < 0 ? "down" : "up"}`}>
          {delta < 0 ? "▼ " : "▲ "}
          {money(Math.abs(delta))}
        </span>
      )}
      {cash && cash.pending_requests_total > 0 && (
        <p className="till-pending">
          {money(cash.pending_requests_total)} waiting for approval · {money(cash.balance_after_pending)} after
        </p>
      )}
      <div className="receipt">
        {payments.length === 0 ? (
          <p className="receipt-empty">No money has left the shop yet.</p>
        ) : (
          <table>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id}>
                  <td>
                    {p.kind === "purchase_order" ? "Purchase order" : p.kind === "rent" ? "Rent" : "Invoice"} {p.kind === "invoice" ? p.ref_id : ""}
                    <small>approved by {p.approved_by}</small>
                  </td>
                  <td className="num">−{money(p.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
