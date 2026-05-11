from sla_renegotiation.domain.enums import EventType
from sla_renegotiation.domain.models import ZOPA, StakeholderProfile


def compute_zopa(
    client_profile: StakeholderProfile,
    provider_profile: StakeholderProfile,
    violated_event_type: EventType | None = None,
    agreed_value: float | None = None,
) -> ZOPA:
    feasible_range: dict[str, tuple[float, float]] = {}
    all_metrics = set(client_profile.flexibility_margins) | set(
        provider_profile.flexibility_margins
    )

    violated_metric = (
        violated_event_type.value.removesuffix("_violation") if violated_event_type else None
    )

    for metric in all_metrics:
        client_margin = client_profile.flexibility_margins.get(metric, 0.0)
        provider_margin = provider_profile.flexibility_margins.get(metric, 0.0)

        lower = max(1.0 - client_margin, 1.0 - provider_margin)
        upper = min(1.0 + client_margin, 1.0 + provider_margin)

        if metric == violated_metric and agreed_value:
            if client_profile.batna is not None and provider_profile.batna is not None:
                if violated_event_type and violated_event_type.is_low_better:
                    lower = provider_profile.batna / agreed_value
                    upper = client_profile.batna / agreed_value
                else:
                    lower = client_profile.batna / agreed_value
                    upper = provider_profile.batna / agreed_value
            elif client_profile.batna is not None:
                ratio = client_profile.batna / agreed_value
                if violated_event_type and violated_event_type.is_low_better:
                    upper = min(upper, ratio)
                else:
                    lower = max(lower, ratio)
            elif provider_profile.batna is not None:
                ratio = provider_profile.batna / agreed_value
                if violated_event_type and violated_event_type.is_low_better:
                    lower = max(lower, ratio)
                else:
                    upper = min(upper, ratio)

        if lower <= upper:
            feasible_range[metric] = (round(lower, 4), round(upper, 4))

    description = (
        f"ZOPA identified across {len(feasible_range)} metrics. "
        f"{'Agreement possible.' if feasible_range else 'No overlap found — negotiation unlikely to succeed.'}"
    )

    return ZOPA(feasible_range_per_metric=feasible_range, description=description)
