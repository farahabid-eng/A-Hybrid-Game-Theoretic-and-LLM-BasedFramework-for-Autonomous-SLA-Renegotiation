from fastapi import APIRouter, Depends, HTTPException

from sla_renegotiation.api.dependencies import get_workflow_service
from sla_renegotiation.api.schemas import (
    GenerateProfileRequest,
    SetBATNAsRequest,
    SetProfileRequest,
    SLADetailResponse,
    SLASLOConfigResponse,
    SLASummaryResponse,
    SLODefinitionResponse,
)
from sla_renegotiation.domain.enums import NegotiationRole
from sla_renegotiation.services.workflow import WorkflowService
from sla_renegotiation.storage.sla_seeds import get_all_slas, get_sla

router = APIRouter(prefix="/slas", tags=["slas"])


@router.get("", response_model=list[SLASummaryResponse])
def list_slas() -> list[SLASummaryResponse]:
    return [
        SLASummaryResponse(
            id=sla.id,
            name=sla.name,
            description=sla.description,
            slo_count=len(sla.slos),
        )
        for sla in get_all_slas()
    ]


@router.get("/{sla_id}", response_model=SLADetailResponse)
def get_sla_detail(sla_id: str) -> SLADetailResponse:
    sla = get_sla(sla_id)
    if not sla:
        raise HTTPException(status_code=404, detail="SLA template not found")
    return SLADetailResponse(
        id=sla.id,
        name=sla.name,
        description=sla.description,
        slos=[
            SLODefinitionResponse(
                metric=slo.metric,
                target_value=slo.target_value,
                unit=slo.unit,
                description=slo.description,
                event_type=slo.event_type.value,
                time_to_repair=slo.time_to_repair,
            )
            for slo in sla.slos
        ],
    )


@router.get("/{sla_id}/slos", response_model=list[SLASLOConfigResponse])
def get_sla_slos(
    sla_id: str,
    svc: WorkflowService = Depends(get_workflow_service),
) -> list[SLASLOConfigResponse]:
    sla = get_sla(sla_id)
    if not sla:
        raise HTTPException(status_code=404, detail="SLA template not found")

    configs = svc.get_sla_slo_configs(sla_id)
    if configs:
        return [
            SLASLOConfigResponse(
                metric=c.metric,
                unit=c.unit,
                agreed_value=c.agreed_value,
                description=c.description,
                event_type=c.event_type.value if hasattr(c.event_type, "value") else c.event_type,
                time_to_repair=c.time_to_repair,
                client_batna=c.client_batna,
                provider_batna=c.provider_batna,
            )
            for c in configs
        ]

    return [
        SLASLOConfigResponse(
            metric=slo.metric,
            unit=slo.unit,
            agreed_value=slo.target_value,
            description=slo.description,
            event_type=slo.event_type.value,
            time_to_repair=slo.time_to_repair,
        )
        for slo in sla.slos
    ]


@router.post("/{sla_id}/batnas")
def set_sla_batnas(
    sla_id: str,
    body: SetBATNAsRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> dict[str, str]:
    try:
        svc.set_sla_batnas(sla_id, body.client_batnas, body.provider_batnas)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"status": "ok"}


@router.post("/{sla_id}/profiles/{role}")
def set_sla_profile(
    sla_id: str,
    role: str,
    body: SetProfileRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> dict[str, str]:
    try:
        parsed_role = NegotiationRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    try:
        svc.set_sla_profile(
            sla_id,
            parsed_role,
            objectives=body.objectives,
            priorities=body.priorities,
            flexibility_margins=body.flexibility_margins,
            context_description=body.context_description,
            tone=body.tone,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"status": "ok"}


@router.get("/{sla_id}/profiles/{role}")
def get_sla_profile(
    sla_id: str,
    role: str,
    svc: WorkflowService = Depends(get_workflow_service),
) -> dict[str, object] | None:
    try:
        parsed_role = NegotiationRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    profile = svc.get_sla_profile(sla_id, parsed_role)
    return profile.model_dump() if profile else None


@router.post("/{sla_id}/profiles/{role}/generate")
def generate_sla_profile(
    sla_id: str,
    role: str,
    body: GenerateProfileRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> dict[str, object]:
    try:
        parsed_role = NegotiationRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    profile = svc.generate_sla_profile(sla_id, parsed_role, body.context)
    return profile.model_dump()
