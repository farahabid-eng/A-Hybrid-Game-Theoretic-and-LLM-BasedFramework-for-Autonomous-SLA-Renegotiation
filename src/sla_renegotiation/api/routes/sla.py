from fastapi import APIRouter, HTTPException

from sla_renegotiation.api.schemas import (
    SLADetailResponse,
    SLASummaryResponse,
    SLODefinitionResponse,
)
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
            )
            for slo in sla.slos
        ],
    )
