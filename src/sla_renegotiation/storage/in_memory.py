from sla_renegotiation.domain.models import Workflow


class WorkflowStore:
    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}

    def save(self, workflow: Workflow) -> None:
        self._workflows[workflow.id] = workflow

    def get(self, workflow_id: str) -> Workflow | None:
        return self._workflows.get(workflow_id)

    def list_all(self) -> list[Workflow]:
        return list(self._workflows.values())

    def delete(self, workflow_id: str) -> None:
        self._workflows.pop(workflow_id, None)
