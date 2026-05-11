from collections.abc import AsyncIterator

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from sla_renegotiation.domain.enums import NegotiationRole
from sla_renegotiation.domain.models import ZOPA, Proposal, StakeholderProfile
from sla_renegotiation.llm.factory import build_model
from sla_renegotiation.llm.prompts import NEGOTIATION_AGENT_SYSTEM, NEGOTIATION_STREAM_SYSTEM
from sla_renegotiation.negotiation.tools import clamp_value
from sla_renegotiation.negotiation.validation import validate_proposal


class NegotiationAgent:
    def __init__(self, role: str) -> None:
        self.role = role
        self._chain: Runnable | None = None
        self._stream_chain: Runnable | None = None

    def _build_chain(self) -> Runnable:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", NEGOTIATION_AGENT_SYSTEM),
                (
                    "human",
                    "History:\n{history}\n\nGenerate your proposal based on the above context.",
                ),
            ]
        )
        model = build_model(self.role, temperature=0.7)
        return prompt | model.bind_tools([clamp_value]).with_structured_output(Proposal)

    def _build_stream_chain(self) -> Runnable:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", NEGOTIATION_STREAM_SYSTEM),
                (
                    "human",
                    "History:\n{history}\n\nGenerate your proposal based on the above context.",
                ),
            ]
        )
        model = build_model(self.role, temperature=0.7)
        return prompt | model

    @property
    def chain(self) -> Runnable:
        if self._chain is None:
            self._chain = self._build_chain()
        return self._chain

    @property
    def stream_chain(self) -> Runnable:
        if self._stream_chain is None:
            self._stream_chain = self._build_stream_chain()
        return self._stream_chain

    def invoke(
        self,
        profile: StakeholderProfile,
        zopa: ZOPA,
        history: str,
        current_round: int,
        max_rounds: int,
    ) -> Proposal:
        raw = self.chain.invoke(
            {
                "role": self.role,
                "profile": profile.model_dump_json(indent=2),
                "zopa": zopa.model_dump_json(indent=2),
                "current_round": current_round,
                "max_rounds": max_rounds,
                "history": history or "No prior proposals.",
            }
        )
        return validate_proposal(raw, zopa)

    async def stream_content(
        self,
        profile: StakeholderProfile,
        zopa: ZOPA,
        history: str,
        current_round: int,
        max_rounds: int,
    ) -> AsyncIterator[tuple[str, Proposal | None]]:
        full_text = ""
        async for chunk in self.stream_chain.astream(
            {
                "role": self.role,
                "profile": profile.model_dump_json(indent=2),
                "zopa": zopa.model_dump_json(indent=2),
                "current_round": current_round,
                "max_rounds": max_rounds,
                "history": history or "No prior proposals.",
            }
        ):
            if chunk.content:
                full_text += chunk.content
                yield (chunk.content, None)

        proposal = Proposal(
            round_number=current_round,
            role=NegotiationRole(self.role),
            content=full_text.strip(),
        )
        yield ("", proposal)


client_agent = NegotiationAgent("client")
provider_agent = NegotiationAgent("provider")
