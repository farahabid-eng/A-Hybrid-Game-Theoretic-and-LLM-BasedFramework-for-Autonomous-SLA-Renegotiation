from sla_renegotiation.zopa.calculator import compute_zopa
from tests.conftest import sample_client_profile, sample_provider_profile  # noqa: F401


def test_zopa_has_overlapping_metrics(sample_client_profile, sample_provider_profile):  # noqa: F811
    zopa = compute_zopa(sample_client_profile, sample_provider_profile)
    assert len(zopa.feasible_range_per_metric) > 0


def test_zopa_no_overlap():
    from sla_renegotiation.domain.models import StakeholderProfile

    client = StakeholderProfile(
        role="client",
        objectives=[],
        priorities={},
        flexibility_margins={"latency": -0.5},
        constraints=[],
        batna=None,
        context_description="",
    )
    provider = StakeholderProfile(
        role="provider",
        objectives=[],
        priorities={},
        flexibility_margins={"latency": 0.1},
        constraints=[],
        batna=None,
        context_description="",
    )
    zopa = compute_zopa(client, provider)
    assert len(zopa.feasible_range_per_metric) == 0
