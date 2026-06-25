from sla_renegotiation.domain.enums import EventType, NegotiationRole
from sla_renegotiation.domain.models import ZOPA, Proposal, SLOConfig, SLODefinition


def compute_zopa(
    violated_event_type: EventType | None = None,
    agreed_value: float | None = None,
    slo_definitions: dict[str, SLODefinition] | None = None,
) -> ZOPA:
    violated_metric = (
        violated_event_type.value.removesuffix("_violation") if violated_event_type else None
    )
    if not violated_metric or agreed_value is None:
        return ZOPA(
            feasible_range_per_metric={}, description="No violation or agreed value specified"
        )

    is_low_better = violated_event_type.is_low_better if violated_event_type else True
    lo = round(agreed_value * 0.8, 4)
    hi = round(agreed_value * 1.2, 4)
    if violated_metric.endswith("%") or (
        slo_definitions
        and violated_metric in slo_definitions
        and slo_definitions[violated_metric].unit == "%"
    ):
        lo = max(0.0, lo)
        hi = min(100.0, hi)

    feasible_range = {violated_metric: (lo, hi)}
    current_targets = {violated_metric: agreed_value}
    units = {}
    if slo_definitions and violated_metric in slo_definitions:
        units[violated_metric] = slo_definitions[violated_metric].unit

    return ZOPA(
        feasible_range_per_metric=feasible_range,
        units=units,
        current_targets=current_targets,
        low_is_better={violated_metric: is_low_better},
        description=f"ZOPA for {violated_metric}: {lo} – {hi}",
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
        is_low = slo.event_type.is_low_better

        # Default range: ±20% of agreed value
        val = slo.agreed_value
        lo = round(val * 0.8, 4)
        hi = round(val * 1.2, 4)

        # Clamp percentages to valid bounds
        if slo.unit == "%":
            lo = max(0.0, lo)
            hi = min(100.0, hi)
            if not is_low:  # e.g., availability
                # Keep the lower bound reasonable (at least 90.0)
                lo = max(90.0, lo)

        feasible_ranges[slo.metric] = (lo, hi)
        current_targets[slo.metric] = slo.agreed_value
        units[slo.metric] = slo.unit
        low_is_better[slo.metric] = is_low

    violated_info = f" (violated: {violated_metric})" if violated_metric else ""
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
