from fastapi import Depends

from sla_renegotiation.services.workflow import WorkflowService
from sla_renegotiation.storage.in_memory import WorkflowStore

_store: WorkflowStore | None = None
_service: WorkflowService | None = None


def get_store() -> WorkflowStore:
    global _store
    if _store is None:
        _store = WorkflowStore()
    return _store


def get_workflow_service(store: WorkflowStore = Depends(get_store)) -> WorkflowService:
    global _service
    if _service is None:
        _service = WorkflowService(store)
    return _service
