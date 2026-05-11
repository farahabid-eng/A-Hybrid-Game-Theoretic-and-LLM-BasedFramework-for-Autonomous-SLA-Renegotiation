from sla_renegotiation.domain.models import ZOPA, Proposal


def validate_proposal(proposal: Proposal, zopa: ZOPA) -> Proposal:
    if not proposal.structured_adjustments:
        return proposal
    clamped: dict[str, float] = {}
    for metric, value in proposal.structured_adjustments.items():
        if metric in zopa.feasible_range_per_metric:
            lo, hi = zopa.feasible_range_per_metric[metric]
            clamped[metric] = max(lo, min(value, hi))
        else:
            clamped[metric] = value
    return proposal.model_copy(update={"structured_adjustments": clamped})
