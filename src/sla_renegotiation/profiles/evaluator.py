from langchain_core.prompts import ChatPromptTemplate

from sla_renegotiation.domain.enums import NegotiationRole
from sla_renegotiation.domain.models import (
    ProfileEvaluationResult,
    SLATemplate,
    SLOConfig,
    StakeholderProfile,
)
from sla_renegotiation.llm.factory import build_model
from sla_renegotiation.llm.prompts import PROFILE_EVALUATION_JUDGE_SYSTEM


def evaluate_profile(
    context: str,
    role: NegotiationRole,
    profile: StakeholderProfile,
    sla: SLATemplate | None = None,
    slo_configs: list[SLOConfig] | None = None,
) -> ProfileEvaluationResult:
    """Evaluate a generated stakeholder profile using LLM-as-a-judge."""
    from sla_renegotiation.profiles.builder import _format_sla_context

    sla_section = _format_sla_context(sla, slo_configs)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", PROFILE_EVALUATION_JUDGE_SYSTEM),
            (
                "human",
                "Please evaluate the following profile generation:\n\n"
                "Role: {role}\n\n"
                "SLA Context:\n{sla_context}\n\n"
                "Raw Stakeholder Context (Input):\n{context}\n\n"
                "Generated Profile:\n{profile_json}",
            ),
        ]
    )

    model = build_model("profiling", temperature=0.0)
    chain = prompt | model.with_structured_output(ProfileEvaluationResult)

    result = chain.invoke(
        {
            "role": role.value,
            "sla_context": sla_section,
            "context": context,
            "profile_json": profile.model_dump_json(indent=2),
        }
    )
    assert isinstance(result, ProfileEvaluationResult)
    return result
