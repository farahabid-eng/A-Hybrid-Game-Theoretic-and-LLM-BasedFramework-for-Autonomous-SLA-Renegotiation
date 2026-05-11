from datetime import datetime

from sla_renegotiation.clauses.generator import generate_rc
from sla_renegotiation.context_gathering.forms import ClientForm, ProviderForm
from sla_renegotiation.domain.enums import NegotiationRole, RenegotiationStatus
from sla_renegotiation.domain.models import Violation, Workflow
from sla_renegotiation.negotiation.agents import client_agent, provider_agent
from sla_renegotiation.negotiation.agreement import check_agreement
from sla_renegotiation.negotiation.graph import _format_history
from sla_renegotiation.profiles.builder import build_profile
from sla_renegotiation.storage.in_memory import WorkflowStore
from sla_renegotiation.zopa.calculator import compute_zopa


class WorkflowService:
    def __init__(self, store: WorkflowStore) -> None:
        self._store = store

    def create_workflow(
        self, violation: Violation, sla_id: str | None = None, max_rounds: int = 10
    ) -> Workflow:
        workflow = Workflow(
            violation=violation,
            sla_id=sla_id,
            max_rounds=max_rounds,
            status=RenegotiationStatus.CONTEXT_GATHERING,
        )
        self._store.save(workflow)
        return workflow

    def submit_client_form(self, workflow_id: str, form: ClientForm) -> Workflow | None:
        workflow = self._store.get(workflow_id)
        if not workflow:
            return None
        workflow.client_form = form
        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    def submit_provider_form(self, workflow_id: str, form: ProviderForm) -> Workflow | None:
        workflow = self._store.get(workflow_id)
        if not workflow:
            return None
        workflow.provider_form = form
        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    def run_profiling(self, workflow_id: str) -> Workflow | None:
        workflow = self._store.get(workflow_id)
        if not workflow or not workflow.client_form or not workflow.provider_form:
            return None

        workflow.status = RenegotiationStatus.PROFILING
        self._store.save(workflow)

        workflow.client_profile = build_profile(workflow.client_form, NegotiationRole.CLIENT)
        workflow.provider_profile = build_profile(workflow.provider_form, NegotiationRole.PROVIDER)

        workflow.status = RenegotiationStatus.ZOPA_CALCULATION
        workflow.zopa = compute_zopa(
            workflow.client_profile,
            workflow.provider_profile,
            violated_event_type=workflow.violation.event_type if workflow.violation else None,
            agreed_value=workflow.violation.agreed_value if workflow.violation else None,
        )

        workflow.status = RenegotiationStatus.NEGOTIATING
        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    def run_negotiation_round(self, workflow_id: str) -> Workflow | None:
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

        client_proposal = client_agent.invoke(
            profile=workflow.client_profile,
            zopa=workflow.zopa,
            history=history,
            current_round=workflow.current_round + 1,
            max_rounds=workflow.max_rounds,
        )
        workflow.proposals.append(client_proposal)
        workflow.current_round += 1

        provider_proposal = provider_agent.invoke(
            profile=workflow.provider_profile,
            zopa=workflow.zopa,
            history=_format_history(workflow.proposals),
            current_round=workflow.current_round,
            max_rounds=workflow.max_rounds,
        )
        workflow.proposals.append(provider_proposal)

        if check_agreement(client_proposal, provider_proposal):
            workflow.status = RenegotiationStatus.AGREED
        elif workflow.current_round >= workflow.max_rounds:
            workflow.status = RenegotiationStatus.MAX_ROUNDS_REACHED
        else:
            workflow.status = RenegotiationStatus.NEGOTIATING

        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    def finalize(self, workflow_id: str) -> Workflow | None:
        workflow = self._store.get(workflow_id)
        if not workflow:
            return None
        workflow.rc = generate_rc(workflow)
        workflow.status = RenegotiationStatus.AGREED
        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        return self._store.get(workflow_id)
