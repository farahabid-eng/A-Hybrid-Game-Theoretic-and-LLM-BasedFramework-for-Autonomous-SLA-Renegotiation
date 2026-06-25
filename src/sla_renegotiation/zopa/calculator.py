from sla_renegotiation.domain.enums import EventType, NegotiationRole
from sla_renegotiation.domain.models import ZOPA, Proposal, SLOConfig, SLODefinition


def compute_zopa(
    client_batna: float | None = None,
    provider_batna: float | None = None,
    violated_event_type: EventType | None = None,
    agreed_value: float | None = None,
    slo_definitions: dict[str, SLODefinition] | None = None,
) -> ZOPA:
    violated_metric = (
        violated_event_type.value.removesuffix("_violation") if violated_event_type else None
    )
    if not violated_metric:
        return ZOPA(feasible_range_per_metric={}, description="No violation specified")

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


def compute_multi_metric_zopa(
    slo_configs: list[SLOConfig],
    violated_metric: str | None = None,
) -> ZOPA:
    feasible_ranges: dict[str, tuple[float, float]] = {}
    units: dict[str, str] = {}
    current_targets: dict[str, float] = {}
    low_is_better: dict[str, bool] = {}

    for slo in slo_configs:
        if slo.client_batna is None or slo.provider_batna is None:
            continue

        is_low = slo.event_type.is_low_better
        lo, hi = (
            (slo.provider_batna, slo.client_batna)
            if is_low
            else (slo.client_batna, slo.provider_batna)
        )

        if round(lo, 4) > round(hi, 4):
            continue

        feasible_ranges[slo.metric] = (round(lo, 4), round(hi, 4))
        current_targets[slo.metric] = slo.agreed_value
        units[slo.metric] = slo.unit
        low_is_better[slo.metric] = is_low

    if not feasible_ranges:
        return ZOPA(
            feasible_range_per_metric={},
            description="No overlapping BATNAs — no agreement possible",
        )

    violated_info = ""
    if violated_metric and violated_metric in feasible_ranges:
        vr = feasible_ranges[violated_metric]
        violated_info = f" (violated: {violated_metric} {vr[0]}–{vr[1]})"

    return ZOPA(
        feasible_range_per_metric=feasible_ranges,
        units=units,
        current_targets=current_targets,
        low_is_better=low_is_better,
        description=f"Multi-metric ZOPA{violated_info}",
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
