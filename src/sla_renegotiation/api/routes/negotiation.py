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
from sla_renegotiation.domain.enums import NegotiationRole, RenegotiationStatus
from sla_renegotiation.domain.models import ProposalEvaluation
from sla_renegotiation.negotiation.agents import client_agent, provider_agent
from sla_renegotiation.negotiation.agreement import check_agreement
from sla_renegotiation.negotiation.graph import _format_history
from sla_renegotiation.negotiation.scoring import compute_utility_score
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

                client_proposal = workflow.proposals[-1] if workflow.proposals else None

                client_utility_score = 1.0
                client_threshold_met = True
                if client_proposal and client_proposal.structured_adjustments:
                    client_utility_score = compute_utility_score(
                        client_proposal,
                        workflow.provider_profile,
                        workflow.zopa,
                        NegotiationRole.PROVIDER,
                    )
                    client_threshold_met = (
                        client_utility_score >= workflow.provider_profile.acceptance_threshold
                    )

                await websocket.send_json(
                    {
                        "type": "negotiation.utility",
                        "role": "client",
                        "round": round_num,
                        "utility_score": round(client_utility_score, 4),
                        "threshold": workflow.provider_profile.acceptance_threshold,
                        "threshold_met": client_threshold_met,
                    }
                )

                provider_history = _format_history(workflow.proposals)
                if client_proposal and client_proposal.structured_adjustments:
                    provider_history += (
                        f"\n\nUtility Evaluation: The client's proposal scored "
                        f"{client_utility_score:.4f} (your acceptance threshold: "
                        f"{workflow.provider_profile.acceptance_threshold}). "
                    )
                    if client_threshold_met:
                        provider_history += (
                            "This meets the threshold — proceed with qualitative assessment."
                        )
                    else:
                        provider_history += (
                            "This is BELOW the threshold — reject without qualitative review "
                            "and generate a counter-offer."
                        )

                await websocket.send_json(
                    {
                        "type": "profiling.progress",
                        "status": f"Provider agent is generating proposal (round {round_num})...",
                    }
                )

                async for token, proposal in provider_agent.stream_content(
                    profile=workflow.provider_profile,
                    zopa=round_zopa,
                    history=provider_history,
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

                provider_proposal = workflow.proposals[-1] if workflow.proposals else None

                provider_utility_score = 1.0
                provider_threshold_met = True
                if provider_proposal and provider_proposal.structured_adjustments:
                    provider_utility_score = compute_utility_score(
                        provider_proposal,
                        workflow.client_profile,
                        workflow.zopa,
                        NegotiationRole.CLIENT,
                    )
                    provider_threshold_met = (
                        provider_utility_score >= workflow.client_profile.acceptance_threshold
                    )

                await websocket.send_json(
                    {
                        "type": "negotiation.utility",
                        "role": "provider",
                        "round": round_num,
                        "utility_score": round(provider_utility_score, 4),
                        "threshold": workflow.client_profile.acceptance_threshold,
                        "threshold_met": provider_threshold_met,
                    }
                )

                # Store evaluations
                workflow.evaluations.append(
                    ProposalEvaluation(
                        proposal_round=round_num,
                        evaluator_role=NegotiationRole.PROVIDER,
                        utility_score=round(client_utility_score, 4),
                        threshold_met=client_threshold_met,
                        accepted=False,
                    )
                )
                workflow.evaluations.append(
                    ProposalEvaluation(
                        proposal_round=round_num,
                        evaluator_role=NegotiationRole.CLIENT,
                        utility_score=round(provider_utility_score, 4),
                        threshold_met=provider_threshold_met,
                        accepted=False,
                    )
                )

                proposals = (
                    workflow.proposals[-2:] if len(workflow.proposals) >= 2 else workflow.proposals
                )

                agreement_reached = len(workflow.proposals) >= 2 and check_agreement(
                    workflow.proposals[-2], workflow.proposals[-1]
                )
                if agreement_reached:
                    workflow.status = RenegotiationStatus.AGREED
                    for eval_ in workflow.evaluations:
                        if eval_.proposal_round == round_num:
                            eval_.accepted = True
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
                        "evaluations": [
                            e.model_dump()
                            for e in workflow.evaluations
                            if e.proposal_round == round_num
                        ],
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
