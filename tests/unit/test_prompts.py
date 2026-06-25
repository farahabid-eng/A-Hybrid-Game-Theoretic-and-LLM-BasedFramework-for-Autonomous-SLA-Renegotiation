from sla_renegotiation.llm.prompts import (
    NEGOTIATION_AGENT_SYSTEM,
    PROFILE_BUILDER_SYSTEM,
    RC_GENERATOR_SYSTEM,
)


def test_profile_builder_system_not_empty():
    assert len(PROFILE_BUILDER_SYSTEM) > 50


def test_negotiation_agent_system_has_template_vars():
    assert "{role}" in NEGOTIATION_AGENT_SYSTEM
    assert "{profile}" in NEGOTIATION_AGENT_SYSTEM
    assert "{zopa}" in NEGOTIATION_AGENT_SYSTEM
    assert "{current_round}" in NEGOTIATION_AGENT_SYSTEM
    assert "{max_rounds}" in NEGOTIATION_AGENT_SYSTEM


def test_rc_generator_system_not_empty():
    assert len(RC_GENERATOR_SYSTEM) > 50
