from sla_renegotiation.domain.models import Proposal
from sla_renegotiation.negotiation.agreement import check_agreement


def _proposal(content: str) -> Proposal:
    return Proposal(round_number=1, role="client", content=content)


def test_i_accept_triggers():
    assert check_agreement(_proposal("I accept your proposal"), _proposal("ok"))
    assert check_agreement(_proposal("ok"), _proposal("I accept the terms"))


def test_agreed_triggers():
    assert check_agreement(_proposal("Agreed"), _proposal("ok"))
    assert check_agreement(_proposal("ok"), _proposal("Agreed. Let's proceed"))


def test_acceptable_triggers():
    assert check_agreement(_proposal("Your proposal is acceptable"), _proposal("ok"))
    assert check_agreement(_proposal("ok"), _proposal("That is acceptable to us"))


def test_no_agreement():
    assert not check_agreement(_proposal("Propose reducing latency to 110ms"), _proposal("Propose 120ms latency with 5% cost increase"))
    assert not check_agreement(_proposal("Need better terms"), _proposal("Cannot accept that"))


def test_negation_does_not_trigger():
    assert not check_agreement(_proposal("I cannot accept these terms"), _proposal("ok"))
    assert not check_agreement(_proposal("This is not acceptable"), _proposal("ok"))
    assert not check_agreement(_proposal("I don't agree"), _proposal("ok"))
