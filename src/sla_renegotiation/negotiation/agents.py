from collections.abc import AsyncIterator

from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk

from sla_renegotiation.domain.enums import NegotiationRole
from sla_renegotiation.domain.models import ZOPA, Proposal, StakeholderProfile
from sla_renegotiation.llm.factory import build_model, llm_rate_limiter
from sla_renegotiation.llm.prompts import NEGOTIATION_AGENT_SYSTEM
from sla_renegotiation.negotiation.tools import _propose_adjustment, make_propose_adjustment
from sla_renegotiation.negotiation.validation import validate_proposal

_SAFE_TOOL_NAMES = {"propose_adjustment"}


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
        violated_metric: str,
    ) -> AsyncIterator[tuple[str, Proposal | None]]:
        model = build_model(self.role, temperature=0.7)

        zopa_lines = []
        for metric, (lo, hi) in zopa.feasible_range_per_metric.items():
            unit = zopa.units.get(metric, "")
            target = zopa.current_targets.get(metric)
            current = f" (current: {target}{unit})" if target is not None else ""
            direction = "higher" if not zopa.low_is_better.get(metric, True) else "lower"
            zopa_lines.append(
                f"- {metric}: {lo}{unit} – {hi}{unit}{current} [{direction} is better]"
            )
        zopa_str = "\n".join(zopa_lines)

        system_prompt = NEGOTIATION_AGENT_SYSTEM.format(
            role=self.role,
            profile=profile.model_dump_json(indent=2),
            zopa=zopa_str,
            current_round=current_round,
            max_rounds=max_rounds,
            violated_metric=violated_metric,
        )

        propose_tool = make_propose_adjustment(zopa)
        agent = create_agent(
            model=model,
            tools=[propose_tool],
            system_prompt=system_prompt,
            name=self.role,
        )

        user_content = (
            f"History:\n{history or 'No prior proposals.'}\n\n"
            "Generate your proposal based on the above context."
        )
        full_text = ""
        accumulated_message: AIMessageChunk | None = None
        async with llm_rate_limiter:
            async for chunk in agent.astream(
                {"messages": [{"role": "user", "content": user_content}]},
                stream_mode="messages",
                version="v2",
            ):
                if chunk["type"] != "messages":
                    continue
                token, _ = chunk["data"]
                if not isinstance(token, AIMessageChunk):
                    continue
                accumulated_message = (
                    (accumulated_message + token) if accumulated_message else token
                )
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
                        if all(k in args for k in ("role", "metric", "desired_value")):
                            adjustments[args["metric"]] = _propose_adjustment(
                                args["role"],
                                args["metric"],
                                args["desired_value"],
                                zopa,
                            )

            proposal = Proposal(
                round_number=current_round,
                role=NegotiationRole(self.role),
                content=full_text.strip(),
                structured_adjustments=adjustments or None,
            )
            proposal = validate_proposal(proposal, zopa)
            yield ("", proposal)


client_agent = NegotiationAgent("client")
provider_agent = NegotiationAgent("provider")
