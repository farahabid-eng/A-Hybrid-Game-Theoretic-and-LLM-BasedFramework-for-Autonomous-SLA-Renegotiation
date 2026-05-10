from fastapi import APIRouter, Depends

from sla_renegotiation.api.dependencies import get_workflow_service
from sla_renegotiation.api.schemas import CreateWorkflowRequest, WorkflowResponse
from sla_renegotiation.domain.enums import EventType
from sla_renegotiation.domain.models import Violation
from sla_renegotiation.services.workflow import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", response_model=WorkflowResponse)
def create_workflow(body: CreateWorkflowRequest, svc: WorkflowService = Depends(get_workflow_service)) -> WorkflowResponse:
    violation = Violation(
        event_type=EventType(body.event_type),
        observed_value=body.observed_value,
        agreed_value=body.agreed_value,
        unit=body.unit,
        time_to_repair_seconds=body.time_to_repair_seconds,
        description=body.description,
    )
    workflow = svc.create_workflow(violation, max_rounds=body.max_rounds)
    return _to_response(workflow)


@router.get("", response_model=list[WorkflowResponse])
def list_workflows(svc: WorkflowService = Depends(get_workflow_service)) -> list[WorkflowResponse]:
    return [_to_response(w) for w in svc._store.list_all()]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: str, svc: WorkflowService = Depends(get_workflow_service)) -> WorkflowResponse:
    workflow = svc.get_workflow(workflow_id)
    if not workflow:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _to_response(workflow)


def _to_response(w: object) -> WorkflowResponse:
    return WorkflowResponse(
        id=w.id,
        status=w.status.value,
        current_round=w.current_round,
        max_rounds=w.max_rounds,
        proposals=[p.model_dump() for p in w.proposals],
        rc=w.rc.model_dump() if w.rc else None,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )
