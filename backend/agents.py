"""Campus Customs agent team (PydanticAI): Boss, Inventory, Accounting, Facilities, Customer Service.

* Each agent has its own prompt file (backend/prompts/<name>.md), the same
  gpt-6-luna model settings, and its own agent loop (Agent.iter), so every
  loop step is written to output/audit_trail.json.
* Every agent has a `delegate` tool that can hand a sub-task to ANY other
  agent. Guardrails: no self-delegation, no cycles, max depth, max hand-offs.
* Shop facts come only from the MCP server (role-filtered toolsets).

CLI:  python3 backend/agents.py 101
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from dataclasses import dataclass, field, replace
from typing import Any

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart, UserPromptPart,
)
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

import audit
from config import (
    MAX_DELEGATION_DEPTH, MAX_DELEGATIONS_PER_TICKET, MODEL_SETTINGS, PROMPTS_DIR,
    TICKET_USAGE_LIMITS, get_model,
)
from mcp_client import role_toolset, shared_toolset
from models import AGENT_NAMES, AgentName, SpecialistReport, TicketOutcome, TicketRunResult

DELEGATION_RULES = f"""

## How to work with the team (system rules, all agents)
- You are the `{{name}}` agent. Other agents: {", ".join(AGENT_NAMES)}.
- Use the `delegate` tool to hand a specific sub-task to another agent when the fact or action
  belongs to their role. Say exactly what you need back. Do not delegate what your own tools can do.
- Delegation limits: no delegating to yourself or to an agent already upstream in the chain,
  at most {MAX_DELEGATION_DEPTH} levels deep, at most {MAX_DELEGATIONS_PER_TICKET} hand-offs per ticket.
  If a delegation is refused, finish with what you have and list the gap as a blocker.
- Every shop fact (stock, prices, dates, balances, amounts) must come from an MCP tool result in
  this run. If a tool did not return it, say you do not know. Never invent ids, amounts, or dates.
- Do all arithmetic with tools (quote_bulk_discount, get_cash_balance, request_* results), not in your head.
- You can never move money. request_* tools only create pending requests for a human to approve.
"""


@dataclass
class Deps:
    ticket_id: int
    run_id: str
    agent: str
    depth: int = 0
    chain: list[str] = field(default_factory=list)
    budget: dict[str, int] = field(default_factory=lambda: {"delegations": 0})


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8") + DELEGATION_RULES.replace("{name}", name)


def build_team(base_toolset, model: Model | None = None) -> dict[str, Agent]:
    model = model or get_model()
    team: dict[str, Agent] = {}
    for name in AGENT_NAMES:
        agent: Agent[Deps, Any] = Agent(
            model,
            name=name,
            deps_type=Deps,
            output_type=TicketOutcome if name == "boss" else SpecialistReport,
            instructions=load_prompt(name),
            toolsets=[role_toolset(base_toolset, name)],
            model_settings=MODEL_SETTINGS,
            retries=2,
        )
        agent.tool(_make_delegate(team))
        team[name] = agent
    return team


def _make_delegate(team: dict[str, Agent]):
    async def delegate(ctx: RunContext[Deps], to_agent: AgentName, task: str) -> str:
        """Hand a specific sub-task to another Campus Customs agent and return its report (JSON).

        to_agent: one of boss, inventory, accounting, facilities, customer_service.
        task: what you need from them, including the ticket facts they need to start.
        """
        d = ctx.deps
        refusal = None
        if to_agent == d.agent:
            refusal = "cannot delegate to yourself"
        elif to_agent in d.chain:
            refusal = f"{to_agent} is already upstream in this chain ({' -> '.join(d.chain)})"
        elif d.depth + 1 > MAX_DELEGATION_DEPTH:
            refusal = f"max delegation depth {MAX_DELEGATION_DEPTH} reached"
        elif d.budget["delegations"] >= MAX_DELEGATIONS_PER_TICKET:
            refusal = f"ticket already used {MAX_DELEGATIONS_PER_TICKET} delegations"
        if refusal:
            audit.log(run_id=d.run_id, ticket_id=d.ticket_id, agent=d.agent, depth=d.depth, chain=d.chain,
                      step="delegate_refused", detail={"to": to_agent, "task": task, "reason": refusal})
            return json.dumps({"refused": True, "reason": refusal})

        d.budget["delegations"] += 1
        audit.log(run_id=d.run_id, ticket_id=d.ticket_id, agent=d.agent, depth=d.depth, chain=d.chain,
                  step="delegate", detail={"to": to_agent, "task": task, "delegation_no": d.budget["delegations"]})
        child = replace(d, agent=to_agent, depth=d.depth + 1, chain=[*d.chain, to_agent])
        prompt = (f"[Delegated by {d.agent} | ticket {d.ticket_id} | chain {' -> '.join(child.chain)}]\n{task}")
        output = await run_agent_loop(team, to_agent, prompt, child, usage=ctx.usage)
        return output.model_dump_json()

    return delegate


def _log_node(node: Any, deps: Deps) -> None:
    """Turn one PydanticAI graph node into audit events."""
    base = dict(run_id=deps.run_id, ticket_id=deps.ticket_id, agent=deps.agent, depth=deps.depth, chain=deps.chain)
    if Agent.is_user_prompt_node(node):
        audit.log(**base, step="user_prompt", detail={"prompt": audit.clip(node.user_prompt)})
    elif Agent.is_model_request_node(node):
        parts = []
        for p in node.request.parts:
            if isinstance(p, ToolReturnPart):
                parts.append({"tool_result": p.tool_name, "tool_call_id": p.tool_call_id,
                              "content": audit.truncate_tool_result(p.content)})
            elif isinstance(p, RetryPromptPart):
                parts.append({"retry": audit.clip(p.model_response(), 500)})
            elif isinstance(p, UserPromptPart):
                parts.append({"user_prompt": audit.clip(p.content, 500)})
        audit.log(**base, step="model_request", detail={"parts": parts})
    elif Agent.is_call_tools_node(node):
        resp = node.model_response
        calls = [{"tool": p.tool_name, "args": p.args_as_dict(), "tool_call_id": p.tool_call_id}
                 for p in resp.parts if isinstance(p, ToolCallPart)]
        text = " ".join(p.content for p in resp.parts if isinstance(p, TextPart)).strip()
        audit.log(**base, step="model_response", detail={
            "model": resp.model_name, "text": audit.clip(text, 1_000), "tool_calls": calls,
            "usage": {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens},
        })
    elif Agent.is_end_node(node):
        out = node.data.output
        audit.log(**base, step="agent_end",
                  detail={"output": out.model_dump() if hasattr(out, "model_dump") else audit.clip(out)})


async def run_agent_loop(team: dict[str, Agent], name: str, prompt: str, deps: Deps,
                         usage: RunUsage | None = None):
    """One agent's loop, stepped node by node so each step is audited."""
    agent = team[name]
    async with agent.iter(prompt, deps=deps, usage=usage, usage_limits=TICKET_USAGE_LIMITS) as run:
        async for node in run:
            _log_node(node, deps)
    return run.result.output


BOSS_KICKOFF = """Work ticket {ticket_id}.
1. Read it with get_ticket (and get_shop_date).
2. Decide which ONE specialist owns the first blocking question and delegate to them first.
   Only bring in more specialists if a report shows you need them.
3. Set the ticket status with update_ticket_status ('awaiting_approval' if any payment request
   is pending, 'resolved' if nothing is left to do).
4. Return the TicketOutcome."""


async def run_ticket(ticket_id: int, model: Model | None = None) -> TicketRunResult:
    run_id = f"t{ticket_id}-{uuid.uuid4().hex[:8]}"
    deps = Deps(ticket_id=ticket_id, run_id=run_id, agent="boss", chain=["boss"])
    usage = RunUsage()
    audit.log(run_id=run_id, ticket_id=ticket_id, agent="boss", depth=0, chain=["boss"], step="run_start",
              detail={"model": "gpt-6-luna" if model is None else getattr(model, "model_name", str(model))})
    outcome, error = None, None
    try:
        base = shared_toolset()
        async with base:  # one MCP server process for the whole ticket
            team = build_team(base, model)
            outcome = await run_agent_loop(team, "boss", BOSS_KICKOFF.format(ticket_id=ticket_id), deps, usage)
    except Exception as exc:  # show the real error; never invent an outcome
        error = f"{type(exc).__name__}: {exc}"
        audit.log(run_id=run_id, ticket_id=ticket_id, agent="boss", depth=0, chain=["boss"], step="error",
                  detail={"error": audit.clip(error)})
    usage_d = {"requests": usage.requests, "tool_calls": usage.tool_calls,
               "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
               "delegations": deps.budget["delegations"]}
    audit.log(run_id=run_id, ticket_id=ticket_id, agent="boss", depth=0, chain=["boss"], step="run_end",
              detail={"error": error, "usage": usage_d,
                      "final_status": outcome.final_status if outcome else None})
    return TicketRunResult(run_id=run_id, ticket_id=ticket_id, outcome=outcome, error=error, usage=usage_d)


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        sys.exit("usage: python3 backend/agents.py <ticket_id>   e.g. 101")
    result = asyncio.run(run_ticket(int(sys.argv[1])))
    print(result.model_dump_json(indent=2))
    print("\nNext step: check output/audit_trail.json, then approve any pending request from the board (Problem 7/8).")


if __name__ == "__main__":
    main()
