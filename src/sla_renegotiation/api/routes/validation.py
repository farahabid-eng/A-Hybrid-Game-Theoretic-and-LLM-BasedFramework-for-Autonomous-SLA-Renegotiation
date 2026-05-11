from fastapi import APIRouter, Depends, HTTPException

from sla_renegotiation.api.dependencies import get_workflow_service
from sla_renegotiation.api.schemas import ValidateRCRequest, WorkflowResponse
from sla_renegotiation.services.workflow import WorkflowService

router = APIRouter(prefix="/workflows/{workflow_id}/rc", tags=["validation"])


@router.post("/accept", response_model=WorkflowResponse)
def accept_rc(
    workflow_id: str,
    _body: ValidateRCRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    workflow = svc.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _to_response(workflow)


@router.post("/reject", response_model=WorkflowResponse)
def reject_rc(
    workflow_id: str,
    _body: ValidateRCRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    workflow = svc.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _to_response(workflow)


def _to_response(w: object) -> WorkflowResponse:
    from sla_renegotiation.api.schemas import WorkflowResponse as WR

    return WR(
        id=w.id,
        status=w.status.value,
        current_round=w.current_round,
        max_rounds=w.max_rounds,
        proposals=[p.model_dump() for p in w.proposals],
        rc=w.rc.model_dump() if w.rc else None,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )
