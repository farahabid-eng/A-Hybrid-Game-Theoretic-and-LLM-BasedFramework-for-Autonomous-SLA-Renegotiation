from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from sla_renegotiation.domain.enums import NegotiationRole
from sla_renegotiation.domain.models import SLATemplate, SLOConfig, StakeholderProfile
from sla_renegotiation.llm.factory import build_model
from sla_renegotiation.llm.prompts import PROFILE_BUILDER_SYSTEM


def _format_sla_context(
    sla: SLATemplate | None,
    slo_configs: list[SLOConfig] | None,
) -> str:
    parts: list[str] = []

    if sla:
        parts.append("## Selected SLA")
        parts.append(f"Name: {sla.name}")
        parts.append(f"Description: {sla.description}")
        parts.append("")

    if slo_configs:
        parts.append("## Service Level Objectives")
        header = f"{'Metric':<20} {'Target':<12} {'Unit':<10} {'Description'}"
        sep = "-" * len(header)
        parts.append(header)
        parts.append(sep)
        for c in slo_configs:
            parts.append(f"{c.metric:<20} {c.agreed_value:<12} {c.unit:<10} {c.description}")
        parts.append("")

        parts.append("## Configured BATNAs (Walk-away Thresholds)")
        batna_header = f"{'Metric':<20} {'Client BATNA':<16} {'Provider BATNA':<16}"
        batna_sep = "-" * len(batna_header)
        parts.append(batna_header)
        parts.append(batna_sep)
        for c in slo_configs:
            client = str(c.client_batna) if c.client_batna is not None else "not set"
            provider = str(c.provider_batna) if c.provider_batna is not None else "not set"
            parts.append(f"{c.metric:<20} {client:<16} {provider:<16}")
        parts.append("")

    return "\n".join(parts)


def build_profile_chain() -> Runnable:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", PROFILE_BUILDER_SYSTEM),
            (
                "human",
                "Analyze the following stakeholder context and construct a structured profile:\n\n{input}",
            ),
        ]
    )
    model = build_model("profiling", temperature=0)
    return prompt | model.with_structured_output(StakeholderProfile)


def build_profile(
    context: str,
    role: NegotiationRole,
    sla: SLATemplate | None = None,
    slo_configs: list[SLOConfig] | None = None,
) -> StakeholderProfile:
    sla_section = _format_sla_context(sla, slo_configs)
    chain = build_profile_chain()

    input_parts = [f"Role: {role.value}"]
    if sla_section:
        input_parts.append(sla_section)
    input_parts.append(f"Stakeholder context:\n{context}")

    return chain.invoke({"input": "\n\n".join(input_parts)})
