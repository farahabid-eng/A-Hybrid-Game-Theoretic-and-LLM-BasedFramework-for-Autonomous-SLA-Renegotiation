from fastapi import APIRouter, Depends, HTTPException

from sla_renegotiation.api.dependencies import get_workflow_service
from sla_renegotiation.api.schemas import (
    SubmitClientFormRequest,
    SubmitProviderFormRequest,
    WorkflowResponse,
)
from sla_renegotiation.context_gathering.forms import ClientForm, ProviderForm
from sla_renegotiation.services.workflow import WorkflowService

router = APIRouter(prefix="/workflows/{workflow_id}/context", tags=["context"])


@router.post("/client", response_model=WorkflowResponse)
def submit_client_context(
    workflow_id: str,
    body: SubmitClientFormRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    form = ClientForm(**body.model_dump())
    workflow = svc.submit_client_form(workflow_id, form)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _to_response(workflow)


@router.post("/provider", response_model=WorkflowResponse)
def submit_provider_context(
    workflow_id: str,
    body: SubmitProviderFormRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    form = ProviderForm(**body.model_dump())
    workflow = svc.submit_provider_form(workflow_id, form)
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
