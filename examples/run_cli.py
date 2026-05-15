"""CLI-only example of running the SLA renegotiation workflow without the UI.

Requires a valid OPENAI_API_KEY (or other configured LLM provider) in .env.

Usage:
    export OPENAI_API_KEY=sk-...
    uv run python examples/run_cli.py
"""

from sla_renegotiation.context_gathering.forms import ClientForm, ProviderForm
from sla_renegotiation.domain.enums import EventType
from sla_renegotiation.domain.models import Violation
from sla_renegotiation.services.workflow import WorkflowService
from sla_renegotiation.storage.in_memory import WorkflowStore


def main() -> None:
    store = WorkflowStore()
    svc = WorkflowService(store)

    violation = Violation(
        event_type=EventType.LATENCY_VIOLATION,
        observed_value=250.0,
        agreed_value=100.0,
        unit="ms",
        description="Severe latency degradation during peak hours",
    )

    workflow = svc.create_workflow(violation, max_rounds=5)
    print(f"Created workflow: {workflow.id}")
    print(f"Violation: {violation.event_type.value} = {violation.observed_value}{violation.unit} (agreed: {violation.agreed_value}{violation.unit})")
    print()

    client_form = ClientForm(
        business_context="Real-time gaming platform with 50M monthly users",
        objectives=["Restore sub-100ms latency", "Maintain 99.9% uptime"],
        priorities={"latency": 0.5, "availability": 0.3, "cost": 0.2},
        flexibility_margins={"latency": 0.2, "availability": 0.05, "cost": 0.3},
        constraints=["P99 latency cannot exceed 200ms"],
        batna=150.0,
        tone="aggressive",
    )
    svc.submit_client_form(workflow.id, client_form)
    print("Client context submitted.")

    provider_form = ProviderForm(
        resource_limitations=["East coast data center at 85% capacity"],
        operational_constraints=["No hardware upgrades until next quarter"],
        priorities={"latency": 0.2, "availability": 0.2, "cost": 0.6},
        flexibility_margins={"latency": 0.1, "availability": 0.1, "cost": 0.15},
        cost_considerations="Infrastructure costs increased 20% year-over-year",
        batna=80.0,
    )
    svc.submit_provider_form(workflow.id, provider_form)
    print("Provider context submitted.")
    print()

    try:
        svc.run_profiling(workflow.id)
    except Exception as e:
        print(f"Profiling failed (check LLM API keys): {e}")
        return

    workflow = svc.get_workflow(workflow.id)
    print(f"Profiles built: client={workflow.client_profile is not None}, provider={workflow.provider_profile is not None}")
    print(f"ZOPA: {workflow.zopa.description}")
    print()

    print("Starting negotiation...")
    for _ in range(workflow.max_rounds):
        try:
            workflow = svc.run_negotiation_round(workflow.id)
            print(f"  Round {workflow.current_round}: {workflow.proposals[-1].content[:80]}...")
        except Exception as e:
            print(f"  Round failed: {e}")
            break

    print()
    print("Finalizing...")
    workflow = svc.finalize(workflow.id)
    print(f"Status: {workflow.status.value}")
    if workflow.rc:
        print(f"RC action: {workflow.rc.action}")
    print("Done.")


if __name__ == "__main__":
    main()
