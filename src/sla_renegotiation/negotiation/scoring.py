from sla_renegotiation.domain.enums import NegotiationRole
from sla_renegotiation.domain.models import ZOPA, Proposal, StakeholderProfile


def compute_utility_score(
    proposal: Proposal,
    evaluator_profile: StakeholderProfile,
    zopa: ZOPA,
    evaluator_role: NegotiationRole,
) -> float:
    adjustments = proposal.structured_adjustments
    if not adjustments:
        return 1.0

    weighted_sum = 0.0
    total_weight = 0.0

    for metric, proposed_value in adjustments.items():
        weight = evaluator_profile.priorities.get(metric, 0.0)
        if weight <= 0:
            continue

        feasible_range = zopa.feasible_range_per_metric.get(metric)
        if not feasible_range:
            continue

        lo, hi = feasible_range
        if hi == lo:
            score = 1.0
        else:
            low_is_better = zopa.low_is_better.get(metric, True)
            if evaluator_role == NegotiationRole.CLIENT:
                ideal = lo if low_is_better else hi
            else:
                ideal = hi if low_is_better else lo

            clamped = max(lo, min(proposed_value, hi))
            distance = abs(clamped - ideal)
            score = 1.0 - (distance / abs(hi - lo))
            score = max(0.0, min(1.0, score))

        weighted_sum += score * weight
        total_weight += weight

    if total_weight == 0:
        return 1.0

    return weighted_sum / total_weight
