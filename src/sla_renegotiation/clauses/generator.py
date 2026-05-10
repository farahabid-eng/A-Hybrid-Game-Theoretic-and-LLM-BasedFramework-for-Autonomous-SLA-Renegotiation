from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from sla_renegotiation.domain.models import RenegotiationClause, Workflow
from sla_renegotiation.llm.prompts import RC_GENERATOR_SYSTEM
from sla_renegotiation.llm.factory import build_model


def build_rc_chain() -> Runnable:
    prompt = ChatPromptTemplate.from_messages([
        ("system", RC_GENERATOR_SYSTEM),
        ("human", "Generate a Renegotiation Clause based on the following negotiation outcome:\n\n{input}"),
    ])
    model = build_model("rc", temperature=0)
    return prompt | model.with_structured_output(RenegotiationClause)


def generate_rc(workflow: Workflow) -> RenegotiationClause:
    chain = build_rc_chain()
    return chain.invoke({"input": workflow.model_dump_json(indent=2)})
