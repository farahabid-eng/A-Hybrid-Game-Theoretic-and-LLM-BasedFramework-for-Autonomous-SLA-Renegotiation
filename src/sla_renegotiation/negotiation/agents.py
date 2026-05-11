from collections.abc import AsyncIterator

from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk

from sla_renegotiation.domain.enums import NegotiationRole
from sla_renegotiation.domain.models import ZOPA, Proposal, StakeholderProfile
from sla_renegotiation.llm.factory import build_model
from sla_renegotiation.llm.prompts import NEGOTIATION_STREAM_SYSTEM
from sla_renegotiation.negotiation.tools import validate_metric_adjustment

_SAFE_TOOL_NAMES = {"validate_metric_adjustment"}


class NegotiationAgent:
    def __init__(self, role: str) -> None:
        self.role = role

    async def stream_content(
        self,
        profile: StakeholderProfile,
        zopa: ZOPA,
        history: str,
        current_round: int,
        max_rounds: int,
    ) -> AsyncIterator[tuple[str, Proposal | None]]:
        model = build_model(self.role, temperature=0.7)

        zopa_lines = []
        for metric, (lo, hi) in zopa.feasible_range_per_metric.items():
            unit = zopa.units.get(metric, "")
            target = zopa.current_targets.get(metric)
            current = f" (current: {target}{unit})" if target is not None else ""
            zopa_lines.append(f"- {metric}: {lo}{unit} – {hi}{unit}{current}")
        zopa_str = "\n".join(zopa_lines)

        system_prompt = NEGOTIATION_STREAM_SYSTEM.format(
            role=self.role,
            profile=profile.model_dump_json(indent=2),
            zopa=zopa_str,
            current_round=current_round,
            max_rounds=max_rounds,
        )

        agent = create_agent(
            model=model,
            tools=[validate_metric_adjustment],
            system_prompt=system_prompt,
            name=self.role,
        )

        user_content = (
            f"History:\n{history or 'No prior proposals.'}\n\n"
            "Generate your proposal based on the above context."
        )
        full_text = ""
        accumulated_message: AIMessageChunk | None = None
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": user_content}]},
            stream_mode=["messages"],
            version="v2",
        ):
            if chunk["type"] != "messages":
                continue
            token, _ = chunk["data"]
            if not isinstance(token, AIMessageChunk):
                continue
            accumulated_message = (accumulated_message + token) if accumulated_message else token
            text = token.content
            if not isinstance(text, str) or not text:
                continue
            full_text += text
            yield (text, None)

        adjustments: dict[str, float] = {}
        if accumulated_message is not None:
            for tc in accumulated_message.tool_calls:
                if tc.get("name") in _SAFE_TOOL_NAMES:
                    args = tc.get("args", {})
                    if "metric" in args and "proposed_value" in args:
                        adjustments[args["metric"]] = args["proposed_value"]

        proposal = Proposal(
            round_number=current_round,
            role=NegotiationRole(self.role),
            content=full_text.strip(),
            structured_adjustments=adjustments or None,
        )
        yield ("", proposal)


client_agent = NegotiationAgent("client")
provider_agent = NegotiationAgent("provider")
