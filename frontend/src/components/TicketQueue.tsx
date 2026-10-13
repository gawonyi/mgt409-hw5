import type { Ticket } from "../types";
import { TICKET_KIND } from "../agents";

const STATUS_TEXT = { open: "Open", awaiting_approval: "Needs your approval", resolved: "Resolved" } as const;

export function TicketQueue({ tickets, selected, onSelect }: {
  tickets: Ticket[];
  selected: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <section className="queue" aria-label="Ticket queue">
      <h2 className="pane-title">Queue</h2>
      <ul>
        {tickets.map((t) => (
          <li key={t.id}>
            <button
              className={`ticket status-${t.status}${selected === t.id ? " is-selected" : ""}`}
              onClick={() => onSelect(t.id)}
              aria-pressed={selected === t.id}
            >
              <span className="ticket-no">#{t.id}</span>
              <span className="ticket-subject">{t.subject}</span>
              <span className="ticket-from">{t.requester}</span>
              <span className="ticket-foot">
                <span className="kind">{TICKET_KIND[t.type] ?? t.type}</span>
                {t.running ? (
                  <span className="pill pill-run"><span className="dot" />Agents working</span>
                ) : t.status !== "resolved" ? (
                  <span className={`pill pill-${t.status}`}>{STATUS_TEXT[t.status]}</span>
                ) : null}
              </span>
              {t.status === "resolved" && <span className="stamp" aria-label="Resolved">Resolved</span>}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
