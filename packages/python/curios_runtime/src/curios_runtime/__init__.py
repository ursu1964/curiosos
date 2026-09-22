"""M0 runtime boundaries for event/evidence storage and work repositories."""

from curios_runtime.event_evidence_store import (
    EventEvidenceRuntimeStore,
    RuntimeStoreError,
    RuntimeStoreErrorCode,
)
from curios_runtime.work_repository import (
    EXECUTION_TRANSITIONS,
    WORK_ITEM_TRANSITIONS,
    M0WorkRepository,
    RepositoryError,
    RepositoryErrorCode,
    StoredExecutionRecord,
    StoredWorkItem,
    transition_execution_record,
    transition_work_item,
)

__version__ = "0.0.0"

__all__ = (
    "EXECUTION_TRANSITIONS",
    "WORK_ITEM_TRANSITIONS",
    "EventEvidenceRuntimeStore",
    "M0WorkRepository",
    "RepositoryError",
    "RepositoryErrorCode",
    "RuntimeStoreError",
    "RuntimeStoreErrorCode",
    "StoredExecutionRecord",
    "StoredWorkItem",
    "__version__",
    "transition_execution_record",
    "transition_work_item",
)
