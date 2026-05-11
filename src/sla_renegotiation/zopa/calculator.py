from sla_renegotiation.domain.enums import EventType
from sla_renegotiation.domain.models import ZOPA, SLODefinition, StakeholderProfile


def _get_target(
    metric: str,
    violated_metric: str | None,
    agreed_value: float | None,
    slo_definitions: dict[str, SLODefinition] | None,
) -> float | None:
    if metric == violated_metric and agreed_value is not None:
        return agreed_value
    if slo_definitions and metric in slo_definitions:
        return slo_definitions[metric].target_value
    return None


def compute_zopa(
    client_profile: StakeholderProfile,
    provider_profile: StakeholderProfile,
    violated_event_type: EventType | None = None,
    agreed_value: float | None = None,
    slo_definitions: dict[str, SLODefinition] | None = None,
) -> ZOPA:
    feasible_range: dict[str, tuple[float, float]] = {}
    units: dict[str, str] = {}
    current_targets: dict[str, float] = {}
    all_metrics = set(client_profile.flexibility_margins) | set(
        provider_profile.flexibility_margins
    )

    violated_metric = (
        violated_event_type.value.removesuffix("_violation") if violated_event_type else None
    )

    for metric in all_metrics:
        target = _get_target(metric, violated_metric, agreed_value, slo_definitions)
        if target is None:
            continue

        client_margin = client_profile.flexibility_margins.get(metric, 0.0)
        provider_margin = provider_profile.flexibility_margins.get(metric, 0.0)

        lower = target * max(1.0 - client_margin, 1.0 - provider_margin)
        upper = target * min(1.0 + client_margin, 1.0 + provider_margin)

        if metric == violated_metric:
            if client_profile.batna is not None and provider_profile.batna is not None:
                if violated_event_type and violated_event_type.is_low_better:
                    lower = provider_profile.batna
                    upper = client_profile.batna
                else:
                    lower = client_profile.batna
                    upper = provider_profile.batna
            elif client_profile.batna is not None:
                if violated_event_type and violated_event_type.is_low_better:
                    upper = min(upper, client_profile.batna)
                else:
                    lower = max(lower, client_profile.batna)
            elif provider_profile.batna is not None:
                if violated_event_type and violated_event_type.is_low_better:
                    lower = max(lower, provider_profile.batna)
                else:
                    upper = min(upper, provider_profile.batna)

        if lower <= upper:
            feasible_range[metric] = (round(lower, 4), round(upper, 4))
            current_targets[metric] = target
            if slo_definitions and metric in slo_definitions:
                units[metric] = slo_definitions[metric].unit

    description = (
        f"ZOPA identified across {len(feasible_range)} metrics. "
        f"{'Agreement possible.' if feasible_range else 'No overlap found — negotiation unlikely to succeed.'}"
    )

    return ZOPA(
        feasible_range_per_metric=feasible_range,
        units=units,
        current_targets=current_targets,
        description=description,
    )
