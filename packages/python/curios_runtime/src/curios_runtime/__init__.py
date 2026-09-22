"""M0 runtime repository boundaries."""

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
    "M0WorkRepository",
    "RepositoryError",
    "RepositoryErrorCode",
    "StoredExecutionRecord",
    "StoredWorkItem",
    "__version__",
    "transition_execution_record",
    "transition_work_item",
)
