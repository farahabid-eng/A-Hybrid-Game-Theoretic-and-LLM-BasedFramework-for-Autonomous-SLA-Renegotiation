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


def _format_clause_text(metric: str, agreed_target: str, stop_condition: str) -> str:
    return (
        f"Upon occurrence of a **{metric}** violation, "
        f"**corrective adjustment** is activated to maintain **{agreed_target}**. "
        f"This condition remains in effect until **{stop_condition}**, "
        f"after which normal SLA conditions resume and the clause is deactivated."
    )


def generate_rc(workflow: Workflow) -> RenegotiationClause:
    violation = workflow.violation
    if not violation:
        return RenegotiationClause(clause_text="")

    metric = violation.metric
    value = _get_agreed_value(workflow)
    unit = violation.unit
    is_low_better = violation.event_type.is_low_better
    ttr = _get_ttr(workflow)

    op = "<=" if is_low_better else ">="
    agreed_target = f"{metric} {op} {value}{unit}"

    stop_condition = "the time to repair (TTR) is over or the value of the violated SLO is restored"

    clause_text = _format_clause_text(metric, agreed_target, stop_condition)

    return RenegotiationClause(clause_text=clause_text)
