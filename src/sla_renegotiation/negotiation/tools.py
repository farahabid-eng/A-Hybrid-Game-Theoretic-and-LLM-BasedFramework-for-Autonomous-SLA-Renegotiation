from langchain_core.tools import BaseTool, tool

from sla_renegotiation.domain.models import ZOPA


def _propose_adjustment(
    role: str,
    metric: str,
    desired_value: float,
    zopa: ZOPA,
) -> float:
    """Core logic: clamp to ZOPA bounds and enforce strategic direction.

    Client + low_is_better  → pushes toward lo  (wants lower values)
    Client + high_is_better → pushes toward hi  (wants higher values)
    Provider + low_is_better  → pushes toward hi (wants higher values)
    Provider + high_is_better → pushes toward lo (wants lower values)
    """
    lo, hi = zopa.feasible_range_per_metric[metric]
    is_low = zopa.low_is_better.get(metric, True)
    clamped = max(lo, min(desired_value, hi))
    mid = (lo + hi) / 2

    if role == "client":
        return max(lo, min(clamped, mid)) if is_low else max(mid, min(clamped, hi))
    return max(mid, min(clamped, hi)) if is_low else max(lo, min(clamped, mid))


def make_propose_adjustment(zopa: ZOPA) -> BaseTool:
    @tool
    def propose_adjustment(role: str, metric: str, desired_value: float) -> float:
        """Propose a value for a metric during SLA renegotiation.

        Call this tool for each metric you want to adjust. The tool ensures
        the value stays within the feasible ZOPA range and aligns with your
        strategic direction based on your role.

        Args:
            role: Your role ("client" or "provider").
            metric: The metric name (e.g. latency, availability, cost, throughput, error_rate).
            desired_value: The value you intend to propose for this metric.
        """
        return _propose_adjustment(role, metric, desired_value, zopa)

    return propose_adjustment
