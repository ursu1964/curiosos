"""M0 runtime boundaries for event/evidence storage, work repositories, and steps."""

from curios_runtime.agent_repository import (
    AgentRepositoryError,
    AgentRepositoryErrorCode,
    M1AgentRepository,
    StoredAgentDefinition,
    StoredAgentInstance,
)
from curios_runtime.event_evidence_store import (
    EventEvidenceRuntimeStore,
    RuntimeStoreError,
    RuntimeStoreErrorCode,
)
from curios_runtime.provider_inventory_executor import ProviderInventoryExecutor
from curios_runtime.single_step_runtime import (
    SingleStepExecutionOutcome,
    SingleStepExecutionRequest,
    SingleStepExecutor,
    SingleStepRuntimeError,
    SingleStepRuntimeErrorCode,
    SingleStepRuntimeRequest,
    SingleStepRuntimeResult,
    SingleStepRuntimeService,
    SingleStepRuntimeStatus,
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
    "AgentRepositoryError",
    "AgentRepositoryErrorCode",
    "EventEvidenceRuntimeStore",
    "M0WorkRepository",
    "M1AgentRepository",
    "ProviderInventoryExecutor",
    "RepositoryError",
    "RepositoryErrorCode",
    "RuntimeStoreError",
    "RuntimeStoreErrorCode",
    "SingleStepExecutionOutcome",
    "SingleStepExecutionRequest",
    "SingleStepExecutor",
    "SingleStepRuntimeError",
    "SingleStepRuntimeErrorCode",
    "SingleStepRuntimeRequest",
    "SingleStepRuntimeResult",
    "SingleStepRuntimeService",
    "SingleStepRuntimeStatus",
    "StoredAgentDefinition",
    "StoredAgentInstance",
    "StoredExecutionRecord",
    "StoredWorkItem",
    "__version__",
    "transition_execution_record",
    "transition_work_item",
)
