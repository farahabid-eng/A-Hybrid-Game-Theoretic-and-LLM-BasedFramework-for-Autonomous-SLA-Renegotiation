from langchain_core.prompts import ChatPromptTemplate

from sla_renegotiation.domain.models import (
    ZOPA,
    Proposal,
    RenegotiationClause,
    RenegotiationEvaluationResult,
    SLATemplate,
    SLOConfig,
    StakeholderProfile,
    Violation,
)
from sla_renegotiation.llm.factory import build_model
from sla_renegotiation.llm.prompts import RENEGOTIATION_EVALUATION_JUDGE_SYSTEM
from sla_renegotiation.negotiation.graph import _format_history
from sla_renegotiation.profiles.builder import _format_sla_context


def evaluate_renegotiation(
    *,
    sla: SLATemplate | None,
    slo_configs: list[SLOConfig],
    violation: Violation,
    zopa: ZOPA,
    client_profile: StakeholderProfile,
    provider_profile: StakeholderProfile,
    proposals: list[Proposal],
    rc: RenegotiationClause | None = None,
) -> RenegotiationEvaluationResult:
    sla_section = _format_sla_context(sla, slo_configs)
    history = _format_history(proposals)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RENEGOTIATION_EVALUATION_JUDGE_SYSTEM),
            (
                "human",
                "Please evaluate the following SLA renegotiation:\n\n"
                "SLA Context:\n{sla_context}\n\n"
                "Violation:\n{violation_json}\n\n"
                "ZOPA:\n{zopa_json}\n\n"
                "Client Profile:\n{client_profile_json}\n\n"
                "Provider Profile:\n{provider_profile_json}\n\n"
                "Negotiation History:\n{history}\n\n"
                "Renegotiation Clause:\n{rc_text}",
            ),
        ]
    )

    model = build_model("judge", temperature=0.0)
    chain = prompt | model.with_structured_output(RenegotiationEvaluationResult)

    result = chain.invoke(
        {
            "sla_context": sla_section,
            "violation_json": violation.model_dump_json(indent=2),
            "zopa_json": zopa.model_dump_json(indent=2),
            "client_profile_json": client_profile.model_dump_json(indent=2),
            "provider_profile_json": provider_profile.model_dump_json(indent=2),
            "history": history,
            "rc_text": rc.clause_text if rc else "Not yet generated",
        }
    )
    assert isinstance(result, RenegotiationEvaluationResult)
    return result
