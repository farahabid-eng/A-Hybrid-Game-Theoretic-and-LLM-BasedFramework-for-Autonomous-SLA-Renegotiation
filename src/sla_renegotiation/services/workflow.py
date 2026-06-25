from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate

from sla_renegotiation.domain.enums import NegotiationRole, RenegotiationStatus
from sla_renegotiation.domain.models import (
    RenegotiationClause,
    SLOConfig,
    StakeholderProfile,
    Violation,
    Workflow,
)
from sla_renegotiation.llm.factory import build_model, llm_rate_limiter
from sla_renegotiation.llm.prompts import RC_GENERATOR_SYSTEM
from sla_renegotiation.negotiation.agents import client_agent, provider_agent
from sla_renegotiation.negotiation.agreement import check_agreement
from sla_renegotiation.negotiation.graph import _format_history
from sla_renegotiation.profiles.builder import build_profile
from sla_renegotiation.storage.in_memory import WorkflowStore
from sla_renegotiation.storage.sla_seeds import get_sla
from sla_renegotiation.zopa.calculator import compute_multi_metric_zopa


class WorkflowService:
    def __init__(self, store: WorkflowStore) -> None:
        self._store = store

    def create_workflow(
        self,
        sla_id: str,
        max_rounds: int = 10,
        metric_weights: dict[str, float] | None = None,
    ) -> Workflow:
        sla = get_sla(sla_id)
        if not sla:
            raise ValueError(f"SLA template '{sla_id}' not found")

        workflow = Workflow(
            sla_id=sla_id,
            max_rounds=max_rounds,
            status=RenegotiationStatus.PENDING,
        )

        # Copy SLA-level SLO configs to the workflow
        sla_configs = self._store.get_sla_slo_configs(sla_id)
        if sla_configs:
            workflow_configs = [
                SLOConfig(
                    metric=c.metric,
                    unit=c.unit,
                    agreed_value=c.agreed_value,
                    description=c.description,
                    event_type=c.event_type,
                    time_to_repair=c.time_to_repair,
                )
                for c in sla_configs
            ]
        else:
            workflow_configs = [
                SLOConfig(
                    metric=slo.metric,
                    unit=slo.unit,
                    agreed_value=slo.target_value,
                    description=slo.description,
                    event_type=slo.event_type,
                    time_to_repair=slo.time_to_repair,
                )
                for slo in sla.slos
            ]

        # Determine metric weights
        metrics = [c.metric for c in workflow_configs]
        if not metric_weights:
            n = len(metrics)
            metric_weights = {m: round(1.0 / n, 4) for m in metrics}
        else:
            # Add any missing metrics with weight 0
            for m in metrics:
                if m not in metric_weights:
                    metric_weights[m] = 0.0
            # Validate sum of weights is roughly 1.0
            tot = sum(metric_weights.values())
            if not (0.99 <= tot <= 1.01):
                raise ValueError("The sum of metric weights must be exactly 1.0")

        # Generate default stakeholder profiles based on weights
        workflow.client_profile = StakeholderProfile(
            role=NegotiationRole.CLIENT,
            objectives=[f"Minimize {m} degradation and optimize QoS" for m in metrics],
            priorities=metric_weights,
            flexibility_margins={m: 0.15 for m in metrics},
            context_description="Client seeking optimal service level targets.",
            tone="collaborative",
        )
        workflow.provider_profile = StakeholderProfile(
            role=NegotiationRole.PROVIDER,
            objectives=[f"Maintain operational feasibility for {m}" for m in metrics],
            priorities=metric_weights,
            flexibility_margins={m: 0.15 for m in metrics},
            context_description="Provider delivering stable service level targets.",
            tone="collaborative",
        )

        self._store.save(workflow)
        self._store.save_slo_configs(workflow.id, workflow_configs)
        return workflow

    def set_profile(
        self,
        workflow_id: str,
        role: NegotiationRole,
        objectives: list[str],
        priorities: dict[str, float],
        flexibility_margins: dict[str, float],
        context_description: str,
        tone: str = "neutral",
    ) -> Workflow:
        workflow = self._store.get(workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")

        profile = StakeholderProfile(
            role=role,
            objectives=objectives,
            priorities=priorities,
            flexibility_margins=flexibility_margins,
            context_description=context_description,
            tone=tone,
        )

        if role == NegotiationRole.CLIENT:
            workflow.client_profile = profile
        else:
            workflow.provider_profile = profile

        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        assert workflow is not None
        return workflow

    def generate_profile(
        self, workflow_id: str, role: NegotiationRole, context: str
    ) -> StakeholderProfile:
        slo_configs = self._store.get_slo_configs(workflow_id)
        workflow = self._store.get(workflow_id)
        sla = get_sla(workflow.sla_id) if workflow and workflow.sla_id else None
        return build_profile(context, role, sla=sla, slo_configs=slo_configs)

    def simulate_violation(
        self,
        workflow_id: str,
        event_type: str,
        observed_value: float,
    ) -> Workflow:
        from sla_renegotiation.domain.enums import EventType

        workflow = self._store.get(workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")

        evt = EventType(event_type)
        metric = evt.value.removesuffix("_violation")

        slo_configs = self._store.get_slo_configs(workflow_id)
        matching = [s for s in slo_configs if s.metric == metric]
        if not matching:
            raise ValueError(f"No SLO for metric '{metric}'")

        slo = matching[0]
        violation = Violation(
            event_type=evt,
            observed_value=observed_value,
            agreed_value=slo.agreed_value,
            unit=slo.unit,
        )
        workflow.violation = violation
        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    def run_profiling(self, workflow_id: str) -> Workflow | None:
        workflow = self._store.get(workflow_id)
        if not workflow or not workflow.client_profile or not workflow.provider_profile:
            return None
        if not workflow.violation:
            return None

        workflow.status = RenegotiationStatus.ZOPA_CALCULATION
        self._store.save(workflow)

        slo_configs = self._store.get_slo_configs(workflow_id)

        workflow.zopa = compute_multi_metric_zopa(
            slo_configs,
            violated_metric=workflow.violation.metric,
        )

        # Enforce negotiation for the violated metric to be between the observed value and the original agreed value
        if workflow.violation and workflow.zopa:
            violated_metric = workflow.violation.metric
            observed_value = workflow.violation.observed_value
            agreed_value = workflow.violation.agreed_value
            is_low_better = workflow.zopa.low_is_better.get(violated_metric, True)

            # Enforce "Degraded Regime" for severe violations (>10% deviation) as per NEGOTIATION_AGENT_SYSTEM.
            # If severe, cap the negotiation at a "realistic recovery" level rather than the original target.
            deviation = (
                abs(agreed_value - observed_value) / agreed_value if agreed_value != 0 else 0
            )
            if deviation > 0.10:
                gap = abs(agreed_value - observed_value)
                # Cap recovery at 30% of the gap back toward the target to ensure a realistic range
                recovery_limit = (
                    observed_value + (gap * 0.3)
                    if not is_low_better
                    else observed_value - (gap * 0.3)
                )
                new_lo, new_hi = (
                    (recovery_limit, observed_value)
                    if is_low_better
                    else (observed_value, recovery_limit)
                )
            else:
                # Normal range [observed, agreed] for minor violations
                new_lo, new_hi = (
                    (agreed_value, observed_value)
                    if is_low_better
                    else (observed_value, agreed_value)
                )

            workflow.zopa.feasible_range_per_metric[violated_metric] = (
                min(new_lo, new_hi),
                max(new_lo, new_hi),
            )

        if not workflow.zopa.feasible_range_per_metric:
            workflow.status = RenegotiationStatus.FAILED
        else:
            workflow.status = RenegotiationStatus.NEGOTIATING
        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    async def run_negotiation_round(self, workflow_id: str) -> Workflow | None:
        workflow = self._store.get(workflow_id)
        if (
            not workflow
            or not workflow.client_profile
            or not workflow.provider_profile
            or not workflow.zopa
        ):
            return None

        if workflow.current_round >= workflow.max_rounds:
            workflow.status = RenegotiationStatus.MAX_ROUNDS_REACHED
            self._store.save(workflow)
            return workflow

        history = _format_history(workflow.proposals)

        violated_metric = workflow.violation.metric if workflow.violation else "unknown"
        round_zopa = workflow.zopa

        client_proposal = None
        async for _, proposal in client_agent.stream_content(
            profile=workflow.client_profile,
            zopa=round_zopa,
            history=history,
            current_round=workflow.current_round + 1,
            max_rounds=workflow.max_rounds,
            violated_metric=violated_metric,
        ):
            if proposal:
                client_proposal = proposal
        if client_proposal:
            workflow.proposals.append(client_proposal)
        workflow.current_round += 1

        provider_proposal = None
        async for _, proposal in provider_agent.stream_content(
            profile=workflow.provider_profile,
            zopa=round_zopa,
            history=_format_history(workflow.proposals),
            current_round=workflow.current_round,
            max_rounds=workflow.max_rounds,
            violated_metric=violated_metric,
        ):
            if proposal:
                provider_proposal = proposal
        if provider_proposal:
            workflow.proposals.append(provider_proposal)

        if (
            client_proposal
            and provider_proposal
            and check_agreement(client_proposal, provider_proposal)
        ):
            workflow.status = RenegotiationStatus.AGREED
        elif workflow.current_round >= workflow.max_rounds:
            workflow.status = RenegotiationStatus.MAX_ROUNDS_REACHED
        else:
            workflow.status = RenegotiationStatus.NEGOTIATING

        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    async def finalize(self, workflow_id: str) -> Workflow | None:
        workflow = self._store.get(workflow_id)
        if not workflow or not workflow.violation:
            return None

        # Prepare context for the RC generation prompt
        violated_metric = workflow.violation.metric
        history = _format_history(workflow.proposals)

        # Use the last two proposals as the core of the agreement
        agreement = ""
        if len(workflow.proposals) >= 2:
            agreement = f"Client: {workflow.proposals[-2].content}\nProvider: {workflow.proposals[-1].content}"

        ttr = workflow.violation.time_to_repair or "not specified"
        recovery_params = f"Time-to-Repair (TTR): {ttr} minutes"

        prompt = ChatPromptTemplate.from_template(RC_GENERATOR_SYSTEM)
        model = build_model("rc")
        chain = prompt | model

        async with llm_rate_limiter:
            response = await chain.ainvoke(
                {
                    "violated_metric": violated_metric,
                    "history": history,
                    "agreement": agreement,
                    "recovery_parameters": recovery_params,
                }
            )

        workflow.rc = RenegotiationClause(clause_text=str(response.content))
        workflow.status = RenegotiationStatus.AGREED
        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        return self._store.get(workflow_id)

    def get_slo_configs(self, workflow_id: str) -> list[SLOConfig]:
        return self._store.get_slo_configs(workflow_id)

    # --- SLA-level methods ---

    def get_sla_slo_configs(self, sla_id: str) -> list[SLOConfig]:
        return self._store.get_sla_slo_configs(sla_id)

    def set_sla_profile(
        self,
        sla_id: str,
        role: NegotiationRole,
        objectives: list[str],
        priorities: dict[str, float],
        flexibility_margins: dict[str, float],
        context_description: str,
        tone: str = "neutral",
    ) -> None:
        profile = StakeholderProfile(
            role=role,
            objectives=objectives,
            priorities=priorities,
            flexibility_margins=flexibility_margins,
            context_description=context_description,
            tone=tone,
        )
        self._store.save_sla_profile(sla_id, role.value, profile)

    def get_sla_profile(self, sla_id: str, role: NegotiationRole) -> StakeholderProfile | None:
        return self._store.get_sla_profile(sla_id, role.value)

    def generate_sla_profile(
        self, sla_id: str, role: NegotiationRole, context: str
    ) -> StakeholderProfile:
        slo_configs = self._store.get_sla_slo_configs(sla_id)
        sla = get_sla(sla_id)
        return build_profile(context, role, sla=sla, slo_configs=slo_configs)
