from langchain_core.tools import tool


@tool
def validate_metric_adjustment(
    metric: str, proposed_value: float, lower_bound: float, upper_bound: float
) -> float:
    """Clamp a proposed value for a specific metric to stay within the feasible range.

    Call this tool for each metric you adjust in your proposal to ensure the value is valid.

    Args:
        metric: The metric name (e.g. latency, availability, cost, throughput).
        proposed_value: The value you intend to propose for this metric.
        lower_bound: The lower end of the feasible range for this metric.
        upper_bound: The upper end of the feasible range for this metric.
    """
    return max(lower_bound, min(proposed_value, upper_bound))
