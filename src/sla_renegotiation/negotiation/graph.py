from langgraph.graph import END, StateGraph

from sla_renegotiation.domain.enums import RenegotiationStatus
from sla_renegotiation.domain.models import Proposal
from sla_renegotiation.negotiation.state import NegotiationState

from .agents import client_agent, provider_agent


def client_node(state: NegotiationState) -> dict:
    proposal = client_agent.invoke(
        profile=state["client_profile"],
        zopa=state["zopa"],
        history=_format_history(state["proposals"]),
        current_round=state["current_round"] + 1,
        max_rounds=state["max_rounds"],
    )
    return {
        "proposals": [proposal],
        "current_round": state["current_round"] + 1,
        "next_role": "provider",
    }


def provider_node(state: NegotiationState) -> dict:
    proposal = provider_agent.invoke(
        profile=state["provider_profile"],
        zopa=state["zopa"],
        history=_format_history(state["proposals"]),
        current_round=state["current_round"],
        max_rounds=state["max_rounds"],
    )
    return {
        "proposals": [proposal],
        "next_role": "client",
    }


def should_continue(state: NegotiationState) -> str:
    if state["current_round"] >= state["max_rounds"]:
        return "end_max_rounds"
    if state["agreement_reached"]:
        return "end_agreed"
    return "continue"


def build_negotiation_graph() -> StateGraph:
    graph = StateGraph(NegotiationState)

    graph.add_node("client", client_node)
    graph.add_node("provider", provider_node)

    graph.set_entry_point("client")
    graph.add_edge("client", "provider")
    graph.add_conditional_edges(
        "provider",
        should_continue,
        {
            "continue": "client",
            "end_max_rounds": END,
            "end_agreed": END,
        },
    )

    return graph.compile()


def _format_history(proposals: list[Proposal]) -> str:
    if not proposals:
        return "No prior proposals."
    lines: list[str] = []
    for p in proposals:
        lines.append(f"Round {p.round_number} [{p.role}]: {p.content}")
    return "\n".join(lines)
