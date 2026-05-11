from langchain_core.tools import tool


@tool
def clamp_value(proposed_multiplier: float, lower_bound: float, upper_bound: float) -> float:
    """Clamp a proposed multiplier to stay within [lower_bound, upper_bound].

    Call this tool before finalizing your proposal to ensure the value is valid.
    """
    return max(lower_bound, min(proposed_multiplier, upper_bound))
