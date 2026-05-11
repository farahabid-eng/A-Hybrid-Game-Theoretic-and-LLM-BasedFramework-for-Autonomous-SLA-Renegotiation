from langchain_core.tools import tool


@tool
def validate_metric_adjustment(
    proposed_value: float, lower_bound: float, upper_bound: float
) -> float:
    """Clamp a proposed metric value to stay within the feasible range.

    Call this tool before finalizing your proposal to ensure the value is valid.
    """
    return max(lower_bound, min(proposed_value, upper_bound))
