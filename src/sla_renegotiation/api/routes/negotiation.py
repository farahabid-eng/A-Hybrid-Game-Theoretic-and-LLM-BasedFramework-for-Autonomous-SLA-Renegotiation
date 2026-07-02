import asyncio
import contextlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from sla_renegotiation.api.dependencies import get_workflow_service
from sla_renegotiation.api.schemas import (
    EvaluateRenegotiationRequest,
    RenegotiationEvaluationResponse,
    WorkflowResponse,
)
from sla_renegotiation.domain.enums import RenegotiationStatus
from sla_renegotiation.negotiation.agents import client_agent, provider_agent
from sla_renegotiation.negotiation.agreement import check_agreement
from sla_renegotiation.negotiation.graph import _format_history
from sla_renegotiation.services.workflow import WorkflowService

router = APIRouter(prefix="/workflows/{workflow_id}/negotiation", tags=["negotiation"])


@router.post("/profile", response_model=WorkflowResponse)
def run_profiling(
    workflow_id: str,
    svc: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    workflow = svc.run_profiling(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _to_response(workflow)


@router.post("/round", response_model=WorkflowResponse)
async def run_round(
    workflow_id: str,
    svc: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    workflow = await svc.run_negotiation_round(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _to_response(workflow)


@router.post("/evaluate", response_model=RenegotiationEvaluationResponse)
def evaluate_negotiation(
    workflow_id: str,
    body: EvaluateRenegotiationRequest,
    svc: WorkflowService = Depends(get_workflow_service),
) -> RenegotiationEvaluationResponse:
    try:
        result = svc.evaluate_renegotiation(
            workflow_id,
            human_realism_score=body.human_realism_score,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RenegotiationEvaluationResponse(
        sla_constraint_compliance_score=result.sla_constraint_compliance_score,
        sla_constraint_compliance_reasoning=result.sla_constraint_compliance_reasoning,
        zopa_compliance_score=result.zopa_compliance_score,
        zopa_compliance_reasoning=result.zopa_compliance_reasoning,
        stakeholder_profile_alignment_score=result.stakeholder_profile_alignment_score,
        stakeholder_profile_alignment_reasoning=result.stakeholder_profile_alignment_reasoning,
        concession_strategy_coherence_score=result.concession_strategy_coherence_score,
        concession_strategy_coherence_reasoning=result.concession_strategy_coherence_reasoning,
        utility_consistency_score=result.utility_consistency_score,
        utility_consistency_reasoning=result.utility_consistency_reasoning,
        negotiation_realism_score=result.negotiation_realism_score,
        negotiation_realism_reasoning=result.negotiation_realism_reasoning,
        overall_score=result.overall_score,
    )


@router.websocket("/ws")
async def negotiate_ws(websocket: WebSocket, workflow_id: str) -> None:
    from sla_renegotiation.api.dependencies import get_store

    await websocket.accept()
    store = get_store()
    service = WorkflowService(store)

    workflow = service.get_workflow(workflow_id)
    if not workflow:
        await websocket.send_json({"type": "error", "detail": "Workflow not found"})
        await websocket.close()
        return

    try:
        data = await websocket.receive_json()
        if data.get("type") != "start":
            return

        lock = await store.get_lock(workflow_id)
        async with lock:
            workflow = service.get_workflow(workflow_id)
            if workflow.status in (
                RenegotiationStatus.AGREED,
                RenegotiationStatus.FAILED,
                RenegotiationStatus.MAX_ROUNDS_REACHED,
                RenegotiationStatus.DEADLOCK,
                RenegotiationStatus.REJECTED,
            ):
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": f"Negotiation already in state: {workflow.status.value}",
                    }
                )
                await websocket.close()
                return

            is_resume = workflow.zopa is not None and workflow.current_round > 0

            if is_resume:
                await websocket.send_json(
                    {
                        "type": "negotiation.resume",
                        "current_round": workflow.current_round,
                        "status": workflow.status.value,
                    }
                )
            else:
                await websocket.send_json(
                    {"type": "profiling.progress", "status": "Computing ZOPA..."}
                )
                workflow = service.run_profiling(workflow_id)
                if not workflow:
                    await websocket.send_json({"type": "error", "detail": "Profiling failed"})
                    return

                await websocket.send_json(
                    {
                        "type": "profiling.complete",
                        "client_profile": workflow.client_profile.model_dump()
                        if workflow.client_profile
                        else None,
                        "provider_profile": workflow.provider_profile.model_dump()
                        if workflow.provider_profile
                        else None,
                        "zopa": workflow.zopa.model_dump() if workflow.zopa else None,
                    }
                )

                if workflow.zopa and not workflow.zopa.feasible_range_per_metric:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "detail": "ZOPA determination failed — no feasible agreement range. Workflow status: "
                            + workflow.status.value,
                        }
                    )
                    await websocket.close()
                    return

            while workflow.current_round < workflow.max_rounds:
                round_num = workflow.current_round + 1

                await websocket.send_json(
                    {
                        "type": "profiling.progress",
                        "status": f"Client agent is generating proposal (round {round_num})...",
                    }
                )

                violated_metric = workflow.violation.metric if workflow.violation else "unknown"
                history = _format_history(workflow.proposals)
                round_zopa = workflow.zopa

                async for token, proposal in client_agent.stream_content(
                    profile=workflow.client_profile,
                    zopa=round_zopa,
                    history=history,
                    current_round=round_num,
                    max_rounds=workflow.max_rounds,
                    violated_metric=violated_metric,
                ):
                    if token:
                        await websocket.send_json(
                            {
                                "type": "negotiation.token",
                                "role": "client",
                                "token": token,
                                "round": round_num,
                            }
                        )
                    else:
                        assert proposal is not None
                        workflow.proposals.append(proposal)
                        await websocket.send_json(
                            {
                                "type": "negotiation.token.done",
                                "role": "client",
                                "round": round_num,
                                "proposal": proposal.model_dump(),
                            }
                        )

                workflow.current_round = round_num

                await websocket.send_json(
                    {
                        "type": "profiling.progress",
                        "status": f"Provider agent is generating proposal (round {round_num})...",
                    }
                )

                async for token, proposal in provider_agent.stream_content(
                    profile=workflow.provider_profile,
                    zopa=round_zopa,
                    history=_format_history(workflow.proposals),
                    current_round=round_num,
                    max_rounds=workflow.max_rounds,
                    violated_metric=violated_metric,
                ):
                    if token:
                        await websocket.send_json(
                            {
                                "type": "negotiation.token",
                                "role": "provider",
                                "token": token,
                                "round": round_num,
                            }
                        )
                    else:
                        assert proposal is not None
                        workflow.proposals.append(proposal)
                        await websocket.send_json(
                            {
                                "type": "negotiation.token.done",
                                "role": "provider",
                                "round": round_num,
                                "proposal": proposal.model_dump(),
                            }
                        )

                proposals = (
                    workflow.proposals[-2:] if len(workflow.proposals) >= 2 else workflow.proposals
                )

                if len(workflow.proposals) >= 2 and check_agreement(
                    workflow.proposals[-2], workflow.proposals[-1]
                ):
                    workflow.status = RenegotiationStatus.AGREED
                elif round_num >= workflow.max_rounds:
                    workflow.status = RenegotiationStatus.MAX_ROUNDS_REACHED
                else:
                    workflow.status = RenegotiationStatus.NEGOTIATING

                workflow.updated_at = datetime.now().isoformat()
                store.save(workflow)

                await websocket.send_json(
                    {
                        "type": "negotiation.round",
                        "round": round_num,
                        "proposals": [p.model_dump() for p in proposals],
                        "status": workflow.status.value,
                    }
                )

                await asyncio.sleep(0.5)

                if workflow.status in (
                    RenegotiationStatus.MAX_ROUNDS_REACHED,
                    RenegotiationStatus.AGREED,
                    RenegotiationStatus.FAILED,
                    RenegotiationStatus.DEADLOCK,
                ):
                    break

            workflow = await service.finalize(workflow_id)
            if workflow and workflow.rc:
                await websocket.send_json(
                    {
                        "type": "negotiation.complete",
                        "status": workflow.status.value,
                        "rc": workflow.rc.model_dump(),
                    }
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        with contextlib.suppress(BaseException):
            await websocket.send_json({"type": "error", "detail": f"Negotiation failed: {str(e)}"})


def _to_response(w: object) -> WorkflowResponse:
    from sla_renegotiation.api.schemas import WorkflowResponse as WR

    return WR(
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
