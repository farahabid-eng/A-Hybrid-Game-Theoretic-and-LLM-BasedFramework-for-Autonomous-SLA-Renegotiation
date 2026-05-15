from sla_renegotiation.domain.enums import EventType, NegotiationRole
from sla_renegotiation.domain.models import ZOPA, Proposal, SLODefinition, StakeholderProfile


def compute_zopa(
    client_profile: StakeholderProfile,
    provider_profile: StakeholderProfile,
    violated_event_type: EventType | None = None,
    agreed_value: float | None = None,
    slo_definitions: dict[str, SLODefinition] | None = None,
) -> ZOPA:
    violated_metric = (
        violated_event_type.value.removesuffix("_violation") if violated_event_type else None
    )
    if not violated_metric:
        return ZOPA(feasible_range_per_metric={}, description="No violation specified")

    client_batna = client_profile.batna
    provider_batna = provider_profile.batna
    if client_batna is None or provider_batna is None:
        return ZOPA(
            feasible_range_per_metric={},
            description=f"Both BATNAs required for ZOPA on {violated_metric}",
        )

    is_low_better = violated_event_type.is_low_better if violated_event_type else True

    if is_low_better:
        lo, hi = provider_batna, client_batna
    else:
        lo, hi = client_batna, provider_batna

    if lo > hi:
        return ZOPA(
            feasible_range_per_metric={},
            description="BATNAs do not overlap — no agreement possible",
        )

    feasible_range = {violated_metric: (round(lo, 4), round(hi, 4))}
    current_targets = {}
    units = {}
    if agreed_value is not None:
        current_targets[violated_metric] = agreed_value
    if slo_definitions and violated_metric in slo_definitions:
        units[violated_metric] = slo_definitions[violated_metric].unit

    return ZOPA(
        feasible_range_per_metric=feasible_range,
        units=units,
        current_targets=current_targets,
        low_is_better={violated_metric: is_low_better},
        description=f"BATNA-based ZOPA for {violated_metric}: {lo} – {hi}",
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
