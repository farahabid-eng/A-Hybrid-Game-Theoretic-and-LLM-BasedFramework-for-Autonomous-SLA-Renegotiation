from sla_renegotiation.domain.enums import EventType, RenegotiationStatus
from sla_renegotiation.domain.models import RenegotiationClause, Workflow


def _get_agreed_value(workflow: Workflow) -> float:
    if not workflow.violation:
        return 0.0
    metric = workflow.violation.metric
    for proposal in reversed(workflow.proposals):
        if proposal.structured_adjustments and metric in proposal.structured_adjustments:
            return proposal.structured_adjustments[metric]
    if workflow.zopa and metric in workflow.zopa.feasible_range_per_metric:
        lo, hi = workflow.zopa.feasible_range_per_metric[metric]
        return (lo + hi) / 2
    return workflow.violation.observed_value


def _get_ttr(workflow: Workflow) -> int | None:
    if workflow.violation and workflow.violation.time_to_repair is not None:
        return workflow.violation.time_to_repair
    if workflow.sla_id and workflow.violation:
        from sla_renegotiation.storage.sla_seeds import get_sla
        sla = get_sla(workflow.sla_id)
        if sla:
            for slo in sla.slos:
                if slo.metric == workflow.violation.metric:
                    return slo.time_to_repair
    return None


def _format_action(
    metric: str, value: float, unit: str, is_low_better: bool
) -> str:
    op = "<=" if is_low_better else ">="
    return f"adjust({metric}, {op}, {value}{unit})"


def _format_stop_condition(
    metric: str, value: float, unit: str, ttr: int | None, is_low_better: bool
) -> str:
    op = ">" if is_low_better else "<"
    ttr_part = f"TTR={ttr}min" if ttr is not None else "TTR"
    return f"(t >= {ttr_part}) OR ({metric} {op} {value}{unit})"


def generate_rc(workflow: Workflow) -> RenegotiationClause:
    violation = workflow.violation
    if not violation:
        return RenegotiationClause(
            event=EventType.LATENCY_VIOLATION,
            action="",
            stop_condition="",
            status=RenegotiationStatus.ACTIVATED,
        )

    metric = violation.metric
    value = _get_agreed_value(workflow)
    unit = violation.unit
    is_low_better = violation.event_type.is_low_better
    ttr = _get_ttr(workflow)

    return RenegotiationClause(
        event=violation.event_type,
        action=_format_action(metric, value, unit, is_low_better),
        stop_condition=_format_stop_condition(metric, value, unit, ttr, is_low_better),
        status=RenegotiationStatus.ACTIVATED,
    )
