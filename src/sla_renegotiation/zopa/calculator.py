from sla_renegotiation.domain.models import StakeholderProfile, ZOPA


def compute_zopa(
    client_profile: StakeholderProfile,
    provider_profile: StakeholderProfile,
    violated_metric: str | None = None,
    agreed_value: float | None = None,
) -> ZOPA:
    feasible_range: dict[str, tuple[float, float]] = {}
    all_metrics = set(client_profile.flexibility_margins) | set(provider_profile.flexibility_margins)

    for metric in all_metrics:
        client_margin = client_profile.flexibility_margins.get(metric, 0.0)
        provider_margin = provider_profile.flexibility_margins.get(metric, 0.0)

        lower = max(1.0 - client_margin, 1.0 - provider_margin)
        upper = min(1.0 + client_margin, 1.0 + provider_margin)

        if metric == violated_metric and agreed_value:
            if client_profile.batna is not None:
                upper = min(upper, client_profile.batna / agreed_value)
            if provider_profile.batna is not None:
                upper = min(upper, provider_profile.batna / agreed_value)

        if lower <= upper:
            feasible_range[metric] = (round(lower, 4), round(upper, 4))

    description = (
        f"ZOPA identified across {len(feasible_range)} metrics. "
        f"{'Agreement possible.' if feasible_range else 'No overlap found — negotiation unlikely to succeed.'}"
    )

    return ZOPA(feasible_range_per_metric=feasible_range, description=description)
