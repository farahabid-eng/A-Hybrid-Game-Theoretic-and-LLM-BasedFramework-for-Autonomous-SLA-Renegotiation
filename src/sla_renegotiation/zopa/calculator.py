from sla_renegotiation.domain.enums import EventType, NegotiationRole
from sla_renegotiation.domain.models import ZOPA, Proposal, SLODefinition, StakeholderProfile


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
    low_is_better: dict[str, bool] = {}
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
            if metric == violated_metric and violated_event_type is not None:
                low_is_better[metric] = violated_event_type.is_low_better
            elif slo_definitions and metric in slo_definitions:
                low_is_better[metric] = slo_definitions[metric].event_type.is_low_better
            else:
                low_is_better[metric] = True

    description = (
        f"ZOPA identified across {len(feasible_range)} metrics. "
        f"{'Agreement possible.' if feasible_range else 'No overlap found — negotiation unlikely to succeed.'}"
    )

    return ZOPA(
        feasible_range_per_metric=feasible_range,
        units=units,
        current_targets=current_targets,
        low_is_better=low_is_better,
        description=description,
    )


def _narrow_one_side(
    orig_lo: float,
    orig_hi: float,
    proposed_value: float,
    role: NegotiationRole,
    metric_is_low_better: bool,
) -> tuple[float, float]:
    clamped = max(orig_lo, min(proposed_value, orig_hi))
    if metric_is_low_better:
        if role == NegotiationRole.CLIENT:
            return orig_lo, min(orig_hi, clamped)
        return max(orig_lo, clamped), orig_hi
    if role == NegotiationRole.CLIENT:
        return max(orig_lo, clamped), orig_hi
    return orig_lo, min(orig_hi, clamped)


def narrow_zopa(
    zopa: ZOPA,
    last_proposal: Proposal,
) -> ZOPA:
    """Narrow ZOPA feasible ranges based on a single proposal.

    Each side's proposal constrains the range: the proposing party signals
    they want *at least* their proposed value (or better), so the range
    contracts from the appropriate direction using the metric's
    low-is-better / high-is-better flag.
    """
    narrowed: dict[str, tuple[float, float]] = {}
    adjustments = last_proposal.structured_adjustments or {}

    for metric, (lo, hi) in zopa.feasible_range_per_metric.items():
        if metric in adjustments:
            metric_low_better = zopa.low_is_better.get(metric, True)
            new_lo, new_hi = _narrow_one_side(
                lo,
                hi,
                adjustments[metric],
                last_proposal.role,
                metric_low_better,
            )
            if new_lo <= new_hi:
                narrowed[metric] = (round(new_lo, 4), round(new_hi, 4))
            else:
                narrowed[metric] = (lo, hi)
        else:
            narrowed[metric] = (lo, hi)

    return ZOPA(
        feasible_range_per_metric=narrowed,
        units=zopa.units,
        current_targets=zopa.current_targets,
        low_is_better=zopa.low_is_better,
        description=zopa.description,
    )
