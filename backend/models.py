"""Data types shared by the agents, the audit trail, and (later) the API routes."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
AGENT_NAMES: tuple[str, ...] = ("boss", "inventory", "accounting", "facilities", "customer_service")
TicketStatus = Literal["open", "awaiting_approval", "resolved"]


class SpecialistReport(BaseModel):
    """What a specialist hands back to whoever delegated to it."""

    agent: AgentName
    ticket_id: int
    findings: list[str] = Field(description="Facts found, each citing the MCP tool and the value it returned.")
    actions_taken: list[str] = Field(default_factory=list, description="Writes made through MCP (notes, requests).")
    payment_request_ids: list[int] = Field(default_factory=list, description="Ids from request_* tools, if any.")
    needs_human_approval: bool = False
    blockers: list[str] = Field(default_factory=list, description="Rules or missing data that stop progress.")
    reply_to_requester: str | None = Field(None, description="Customer-facing text, Customer Service only.")


class AgentContribution(BaseModel):
    agent: AgentName
    summary: str


class TicketOutcome(BaseModel):
    """The Boss's final answer for one ticket."""

    ticket_id: int
    final_status: TicketStatus
    outcome: str = Field(description="Two or three sentences: what was decided and why.")
    first_agent_called: AgentName | None = None
    delegations: list[str] = Field(default_factory=list, description="e.g. 'boss -> inventory: check S stock'")
    agent_contributions: list[AgentContribution] = Field(default_factory=list)
    payment_request_ids: list[int] = Field(default_factory=list)
    human_approvals_needed: list[str] = Field(default_factory=list)
    customer_reply: str | None = None


class AuditEvent(BaseModel):
    """One line in output/audit_trail.json: a single step of one agent's loop."""

    ts: str
    run_id: str
    ticket_id: int
    agent: AgentName | Literal["human", "system"]
    depth: int
    chain: list[str]
    step: Literal[
        "run_start", "user_prompt", "model_request", "model_response",
        "tool_call", "tool_result", "delegate", "delegate_refused", "agent_end", "run_end", "error",
        "human_approval", "human_rejection", "db_reset",
    ]
    detail: dict[str, Any] = Field(default_factory=dict)


class TicketRunResult(BaseModel):
    run_id: str
    ticket_id: int
    outcome: TicketOutcome | None = None
    error: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    """Body of the Approve / Reject buttons. A person must type their name."""

    approved_by: str = Field(min_length=2, description="Name of the human clicking Approve.")
    note: str = ""


class RunStatus(BaseModel):
    run_id: str
    ticket_id: int
    state: Literal["running", "done", "error"]
    result: TicketRunResult | None = None
