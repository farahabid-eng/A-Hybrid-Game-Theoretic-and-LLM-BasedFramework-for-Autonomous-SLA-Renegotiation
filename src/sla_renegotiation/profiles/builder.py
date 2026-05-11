from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from sla_renegotiation.context_gathering.forms import ClientForm, ProviderForm
from sla_renegotiation.domain.enums import NegotiationRole
from sla_renegotiation.domain.models import StakeholderProfile
from sla_renegotiation.llm.prompts import PROFILE_BUILDER_SYSTEM
from sla_renegotiation.llm.factory import build_model


def build_profile_chain(role: NegotiationRole) -> Runnable:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", PROFILE_BUILDER_SYSTEM),
            (
                "human",
                "Analyze the following stakeholder input and construct a structured profile:\n\n{input}",
            ),
        ]
    )
    model = build_model("profiling", temperature=0)
    return prompt | model.with_structured_output(StakeholderProfile)


def build_profile(form: ClientForm | ProviderForm, role: NegotiationRole) -> StakeholderProfile:
    chain = build_profile_chain(role)
    return chain.invoke({"input": form.model_dump_json(indent=2)})
