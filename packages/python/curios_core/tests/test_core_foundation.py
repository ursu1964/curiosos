from __future__ import annotations

import ast
from pathlib import Path

import pytest
from curios_contracts import (
    Authority,
    ContractError,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    ObservabilityContext,
    ProviderDescriptor,
    ProviderId,
    ProviderStatus,
    ProviderType,
    Result,
    ResultStatus,
    SchemaVersion,
)
from curios_core import CoreContext, CoreServices, ProviderCatalog

SOURCE_ROOT = Path(__file__).parents[1] / "src" / "curios_core"
PACKAGE_ROOT = Path(__file__).parents[1]
PYPROJECT = PACKAGE_ROOT / "pyproject.toml"

FORBIDDEN_IMPORT_ROOTS = {
    "anthropic",
    "boto3",
    "fastapi",
    "httpx",
    "langchain",
    "llama_index",
    "ollama",
    "openai",
    "opentelemetry",
    "psycopg",
    "pydantic",
    "requests",
    "sqlalchemy",
}

FORBIDDEN_DUPLICATE_CONTRACT_NAMES = {
    "AgentDefinition",
    "AgentInstance",
    "ArtifactReference",
    "Authority",
    "Capability",
    "CapabilityRequirement",
    "ContractError",
    "EventEnvelope",
    "ExecutionRecord",
    "EvidenceReference",
    "ObjectReference",
    "ObservabilityContext",
    "PolicyDecision",
    "ProviderDescriptor",
    "Result",
    "SecretReference",
    "VerificationReference",
    "WorkItem",
}

FORBIDDEN_CORE_BEHAVIOR_NAMES = {
    "AgentExecutor",
    "CapabilityResolver",
    "DagEngine",
    "EventBus",
    "Memory",
    "ModelRouter",
    "PolicyEngine",
    "Repository",
    "Scheduler",
    "Workflow",
}


class DescriptorCatalog:
    def __init__(self, descriptors: tuple[ProviderDescriptor, ...]) -> None:
        self.descriptors = descriptors

    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        assert isinstance(context.observability, ObservabilityContext)
        return Result.success(self.descriptors)


class FailingCatalog:
    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        assert isinstance(context, CoreContext)
        return Result.failure(
            (
                ContractError(
                    error_code=ErrorCode("CORE_PORT_FAILURE"),
                    message="provider catalog failed with translated contract error",
                    category=ErrorCategory.DEPENDENCY,
                    severity=ErrorSeverity.ERROR,
                    retryable=False,
                ),
            )
        )


def _source_trees() -> list[ast.AST]:
    return [
        ast.parse(source_path.read_text(encoding="utf-8"))
        for source_path in SOURCE_ROOT.rglob("*.py")
    ]


def _declared_class_names() -> set[str]:
    names: set[str] = set()
    for tree in _source_trees():
        names.update(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    return names


def _import_roots() -> set[str]:
    roots: set[str] = set()
    for tree in _source_trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                roots.add(node.module.split(".")[0])
    return roots


def test_core_context_composes_frozen_contract_contexts() -> None:
    observability = ObservabilityContext(trace_id=None)
    context = CoreContext(observability=observability)

    assert context.observability is observability
    assert context.authority is None

    with pytest.raises(TypeError, match="observability must be an ObservabilityContext"):
        CoreContext(observability=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="authority must be an Authority"):
        CoreContext(authority=object())  # type: ignore[arg-type]


def test_core_context_uses_contract_authority_without_redefining_it() -> None:
    assert "Authority" not in _declared_class_names()
    assert Authority.__module__ == "curios_contracts.security"


def test_core_service_lists_provider_descriptors_through_contract_facing_port() -> None:
    descriptor = ProviderDescriptor(
        provider_id=ProviderId.generate(),
        provider_type=ProviderType.MODEL,
        version=SchemaVersion(1, 0, 0),
        declared_capability_ids=(),
        status=ProviderStatus.AVAILABLE,
    )
    services = CoreServices(provider_catalog=DescriptorCatalog((descriptor,)))
    result = services.list_provider_descriptors(CoreContext())

    assert isinstance(services.provider_catalog, ProviderCatalog)
    assert result.status is ResultStatus.SUCCESS
    assert result.value == (descriptor,)


def test_core_service_without_provider_catalog_returns_empty_contract_result() -> None:
    result = CoreServices().list_provider_descriptors(CoreContext())

    assert result == Result.success(())


def test_provider_catalog_port_preserves_contract_error_result_boundary() -> None:
    result = CoreServices(provider_catalog=FailingCatalog()).list_provider_descriptors(
        CoreContext()
    )

    assert result.status is ResultStatus.FAILURE
    assert result.errors[0].error_code == "CORE_PORT_FAILURE"
    assert result.errors[0].category is ErrorCategory.DEPENDENCY


def test_core_source_has_no_provider_or_framework_imports() -> None:
    assert _import_roots().isdisjoint(FORBIDDEN_IMPORT_ROOTS)


def test_core_package_declares_only_contract_runtime_dependency() -> None:
    pyproject = PYPROJECT.read_text(encoding="utf-8")

    assert '"curios-contracts"' in pyproject
    for dependency in FORBIDDEN_IMPORT_ROOTS:
        assert dependency not in pyproject


def test_core_does_not_duplicate_canonical_contracts() -> None:
    assert _declared_class_names().isdisjoint(FORBIDDEN_DUPLICATE_CONTRACT_NAMES)


def test_core_does_not_introduce_deferred_runtime_behaviors() -> None:
    assert _declared_class_names().isdisjoint(FORBIDDEN_CORE_BEHAVIOR_NAMES)
