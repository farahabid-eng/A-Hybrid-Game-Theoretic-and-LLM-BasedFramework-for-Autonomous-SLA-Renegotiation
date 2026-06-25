from fastapi import APIRouter, Depends, HTTPException

from sla_renegotiation.api.dependencies import get_workflow_service
from sla_renegotiation.api.schemas import (
    CreateWorkflowRequest,
    GenerateProfileRequest,
    SetProfileRequest,
    SimulateViolationRequest,
    SLOConfigResponse,
    WorkflowResponse,
)
from sla_renegotiation.domain.enums import NegotiationRole
from sla_renegotiation.services.workflow import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", response_model=WorkflowResponse)
def create_workflow(
    body: CreateWorkflowRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    try:
        workflow = svc.create_workflow(
            sla_id=body.sla_id,
            max_rounds=body.max_rounds,
            metric_weights=body.metric_weights,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _to_response(workflow, svc)


@router.get("", response_model=list[WorkflowResponse])
def list_workflows(
    svc: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowResponse]:
    return [_to_response(w, svc) for w in svc._store.list_all()]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: str,
    svc: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    workflow = svc.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _to_response(workflow, svc)


@router.get("/{workflow_id}/slos", response_model=list[SLOConfigResponse])
def get_workflow_slos(
    workflow_id: str,
    svc: WorkflowService = Depends(get_workflow_service),
) -> list[SLOConfigResponse]:
    svc.get_workflow(workflow_id)  # ensure exists
    configs = svc.get_slo_configs(workflow_id)
    if not configs:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return [
        SLOConfigResponse(
            metric=c.metric,
            unit=c.unit,
            agreed_value=c.agreed_value,
            description=c.description,
            event_type=c.event_type.value if hasattr(c.event_type, "value") else c.event_type,
            time_to_repair=c.time_to_repair,
        )
        for c in configs
    ]


@router.post("/{workflow_id}/profiles/client", response_model=WorkflowResponse)
def set_client_profile(
    workflow_id: str,
    body: SetProfileRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    try:
        workflow = svc.set_profile(
            workflow_id,
            NegotiationRole.CLIENT,
            objectives=body.objectives,
            priorities=body.priorities,
            flexibility_margins=body.flexibility_margins,
            context_description=body.context_description,
            tone=body.tone,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _to_response(workflow, svc)


@router.post("/{workflow_id}/profiles/provider", response_model=WorkflowResponse)
def set_provider_profile(
    workflow_id: str,
    body: SetProfileRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    try:
        workflow = svc.set_profile(
            workflow_id,
            NegotiationRole.PROVIDER,
            objectives=body.objectives,
            priorities=body.priorities,
            flexibility_margins=body.flexibility_margins,
            context_description=body.context_description,
            tone=body.tone,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _to_response(workflow, svc)


@router.post("/{workflow_id}/profiles/client/generate")
def generate_client_profile(
    workflow_id: str,
    body: GenerateProfileRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> dict[str, object]:
    profile = svc.generate_profile(workflow_id, NegotiationRole.CLIENT, body.context)
    return profile.model_dump()


@router.post("/{workflow_id}/profiles/provider/generate")
def generate_provider_profile(
    workflow_id: str,
    body: GenerateProfileRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> dict[str, object]:
    profile = svc.generate_profile(workflow_id, NegotiationRole.PROVIDER, body.context)
    return profile.model_dump()


@router.post("/{workflow_id}/violation", response_model=WorkflowResponse)
def simulate_violation(
    workflow_id: str,
    body: SimulateViolationRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    try:
        workflow = svc.simulate_violation(workflow_id, body.event_type, body.observed_value)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _to_response(workflow, svc)


from sla_renegotiation.domain.models import Workflow as WorkflowModel


def _to_response(w: WorkflowModel, _svc: WorkflowService | None = None) -> WorkflowResponse:
    return WorkflowResponse(
        id=w.id,
        status=w.status.value,
        sla_id=w.sla_id,
        current_round=w.current_round,
        max_rounds=w.max_rounds,
        proposals=[p.model_dump() for p in w.proposals],
        rc=w.rc.model_dump() if w.rc else None,
        client_profile=w.client_profile.model_dump() if w.client_profile else None,
        provider_profile=w.provider_profile.model_dump() if w.provider_profile else None,
        zopa=w.zopa.model_dump() if w.zopa else None,
        violation=w.violation.model_dump() if w.violation else None,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )
