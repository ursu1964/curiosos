from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest
from curios_contracts import (
    CapabilityId,
    ErrorCategory,
    ObjectReference,
    ProviderId,
    ProviderStatus,
    ProviderType,
    ReferenceKind,
    ResultStatus,
)
from curios_core import CoreContext, ProviderCatalog
from curios_ollama import (
    LocalModelProfile,
    ModelProfileStatus,
    OllamaModelProfileDiscovery,
    OllamaModelSummary,
    OllamaProviderCatalog,
)
from curios_ollama.client import OllamaModelClient, parse_tags_response

PACKAGE_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = PACKAGE_ROOT / "src" / "curios_ollama"
PYPROJECT = PACKAGE_ROOT / "pyproject.toml"

FORBIDDEN_BEHAVIOR_NAMES = {
    "AgentRuntime",
    "Chat",
    "Completion",
    "Generate",
    "ModelRouter",
    "Orchestrator",
    "PolicyEngine",
    "Repository",
}
FORBIDDEN_PROFILE_CALL_NAMES = {
    "chat",
    "complete",
    "completion",
    "generate",
    "invoke",
    "prompt",
    "route",
}
PROVIDER_ID = ProviderId("prv_00000000000000000000000001")
OTHER_PROVIDER_ID = ProviderId("prv_00000000000000000000000002")


class FakeModelClient:
    def __init__(
        self,
        models: tuple[OllamaModelSummary, ...] = (),
        error: Exception | None = None,
    ) -> None:
        self.models = models
        self.error = error
        self.calls = 0

    def list_models(self) -> tuple[OllamaModelSummary, ...]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.models


def _source_trees() -> tuple[ast.AST, ...]:
    return tuple(
        ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
        for path in SOURCE_ROOT.rglob("*.py")
    )


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
                roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots.add(node.module.split(".", maxsplit=1)[0])
    return roots


def test_catalog_is_core_provider_catalog_with_deterministic_fake_client() -> None:
    fake_client = FakeModelClient((OllamaModelSummary(name="llama-local:latest", size_bytes=10),))
    catalog = OllamaProviderCatalog(client=fake_client)

    assert isinstance(catalog, ProviderCatalog)
    result = catalog.list_provider_descriptors(CoreContext())

    assert fake_client.calls == 1
    assert result.status is ResultStatus.SUCCESS
    assert result.value is not None
    assert len(result.value) == 1
    descriptor = result.value[0]
    assert descriptor.provider_type is ProviderType.MODEL
    assert descriptor.status is ProviderStatus.AVAILABLE
    assert descriptor.implementation_metadata == {
        "model_count": 1,
        "provider_family": "ollama",
    }


def test_catalog_does_not_require_downloaded_models_for_availability() -> None:
    result = OllamaProviderCatalog(client=FakeModelClient()).list_provider_descriptors(
        CoreContext()
    )

    assert result.status is ResultStatus.SUCCESS
    assert result.value is not None
    assert result.value[0].status is ProviderStatus.AVAILABLE
    assert result.value[0].implementation_metadata == {
        "model_count": 0,
        "provider_family": "ollama",
    }


def test_catalog_translates_provider_failures_to_contract_errors() -> None:
    result = OllamaProviderCatalog(
        client=FakeModelClient(error=OSError("offline"))
    ).list_provider_descriptors(CoreContext())

    assert result.status is ResultStatus.FAILURE
    assert result.errors[0].error_code == "OLLAMA_PROVIDER_UNAVAILABLE"
    assert result.errors[0].category is ErrorCategory.DEPENDENCY
    assert result.errors[0].retryable is True


def test_catalog_translates_provider_timeouts_to_timeout_category() -> None:
    result = OllamaProviderCatalog(
        client=FakeModelClient(error=TimeoutError())
    ).list_provider_descriptors(CoreContext())

    assert result.status is ResultStatus.FAILURE
    assert result.errors[0].category is ErrorCategory.TIMEOUT


def test_tags_response_parser_normalizes_provider_json_inside_adapter() -> None:
    models = parse_tags_response(
        {
            "models": [
                {
                    "name": "llama-local:latest",
                    "modified_at": "2026-09-22T10:00:00Z",
                    "size": 42,
                    "digest": "sha256:abc",
                    "details": {"format": "gguf"},
                }
            ]
        }
    )

    assert models == (
        OllamaModelSummary(
            name="llama-local:latest",
            modified_at="2026-09-22T10:00:00Z",
            size_bytes=42,
            digest="sha256:abc",
        ),
    )


@pytest.mark.parametrize(
    "payload",
    (
        None,
        {"models": "not-a-list"},
        {"models": [None]},
        {"models": [{"name": ""}]},
        {"models": [{"name": "llama-local", "size": "large"}]},
    ),
)
def test_tags_response_parser_rejects_invalid_provider_json(payload: object) -> None:
    with pytest.raises(ValueError):
        parse_tags_response(payload)


def test_ollama_package_does_not_add_sdk_or_routing_dependencies() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    assert pyproject["project"]["dependencies"] == ["curios-contracts", "curios-core"]
    assert "ollama" not in _import_roots()
    assert "openai" not in _import_roots()


def test_ollama_boundary_does_not_implement_deferred_runtime_behaviors() -> None:
    assert _declared_class_names().isdisjoint(FORBIDDEN_BEHAVIOR_NAMES)


def test_client_protocol_is_fakeable_without_live_ollama() -> None:
    fake_client = FakeModelClient((OllamaModelSummary(name="deterministic"),))

    assert isinstance(fake_client, OllamaModelClient)
    assert fake_client.list_models() == (OllamaModelSummary(name="deterministic"),)


def test_local_model_profile_is_bounded_provider_record() -> None:
    profile = LocalModelProfile(
        provider_ref=ObjectReference.from_id(PROVIDER_ID),
        model_name=" llama-local:latest ",
        context_window_tokens=4096,
        metadata={"provider_family": "ollama", "size_bytes": 10},
    )

    assert profile.provider_ref == ObjectReference.from_id(PROVIDER_ID)
    assert profile.model_name == "llama-local:latest"
    assert profile.status is ModelProfileStatus.AVAILABLE
    assert profile.to_json_compatible() == {
        "provider_ref": {"kind": "provider", "ref_id": str(PROVIDER_ID)},
        "model_name": "llama-local:latest",
        "schema_version": "0.0.0",
        "status": "available",
        "context_window_tokens": 4096,
        "metadata": {"provider_family": "ollama", "size_bytes": 10},
    }
    assert LocalModelProfile.from_json_compatible(profile.to_json_compatible()) == profile


@pytest.mark.parametrize(
    "kwargs",
    (
        {
            "provider_ref": ObjectReference(
                kind=ReferenceKind.CAPABILITY, ref_id=CapabilityId("cap_00000000000000000000000001")
            ),
            "model_name": "llama-local",
        },
        {"provider_ref": ObjectReference.from_id(PROVIDER_ID), "model_name": ""},
        {
            "provider_ref": ObjectReference.from_id(PROVIDER_ID),
            "model_name": "token=visible",
        },
        {
            "provider_ref": ObjectReference.from_id(PROVIDER_ID),
            "model_name": "llama-local",
            "context_window_tokens": 0,
        },
        {
            "provider_ref": ObjectReference.from_id(PROVIDER_ID),
            "model_name": "llama-local",
            "metadata": {"api_key": "not-allowed"},
        },
        {
            "provider_ref": ObjectReference.from_id(PROVIDER_ID),
            "model_name": "llama-local",
            "metadata": {"note": "token=not-allowed"},
        },
    ),
)
def test_local_model_profile_rejects_invalid_or_secret_shaped_metadata(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises((TypeError, ValueError)):
        LocalModelProfile(**kwargs)


def test_profile_discovery_returns_deterministic_non_invoked_candidates() -> None:
    fake_client = FakeModelClient(
        (
            OllamaModelSummary(name="zeta:latest", size_bytes=20),
            OllamaModelSummary(
                name="alpha:latest",
                modified_at="2026-09-22T10:00:00Z",
                size_bytes=10,
                digest="sha256:abc",
            ),
        )
    )
    discovery = OllamaModelProfileDiscovery(client=fake_client, provider_id=PROVIDER_ID)

    result = discovery.discover_model_profiles(CoreContext())

    assert fake_client.calls == 1
    assert result.status is ResultStatus.SUCCESS
    assert result.value is not None
    assert tuple(profile.model_name for profile in result.value) == ("alpha:latest", "zeta:latest")
    assert result.value[0].to_json_compatible() == {
        "provider_ref": {"kind": "provider", "ref_id": str(PROVIDER_ID)},
        "model_name": "alpha:latest",
        "schema_version": "0.0.0",
        "status": "available",
        "context_window_tokens": None,
        "metadata": {
            "digest": "sha256:abc",
            "modified_at": "2026-09-22T10:00:00Z",
            "provider_family": "ollama",
            "size_bytes": 10,
        },
    }
    assert result.errors == ()


def test_profile_discovery_allows_empty_candidate_set_without_live_model() -> None:
    fake_client = FakeModelClient()

    result = OllamaModelProfileDiscovery(
        client=fake_client,
        provider_id=OTHER_PROVIDER_ID,
    ).discover_model_profiles(CoreContext())

    assert fake_client.calls == 1
    assert result.status is ResultStatus.SUCCESS
    assert result.value == ()


@pytest.mark.parametrize(
    ("error", "category"),
    ((OSError("offline"), ErrorCategory.DEPENDENCY), (TimeoutError(), ErrorCategory.TIMEOUT)),
)
def test_profile_discovery_reports_unavailable_provider_boundedly(
    error: Exception,
    category: ErrorCategory,
) -> None:
    result = OllamaModelProfileDiscovery(
        client=FakeModelClient(error=error),
        provider_id=PROVIDER_ID,
    ).discover_model_profiles(CoreContext())

    assert result.status is ResultStatus.FAILURE
    assert result.value is None
    assert result.errors[0].error_code == "OLLAMA_MODEL_PROFILE_DISCOVERY_UNAVAILABLE"
    assert result.errors[0].category is category
    assert result.errors[0].retryable is True


def test_profile_discovery_rejects_invalid_provider_payload_without_partial_success() -> None:
    class InvalidModelClient:
        def list_models(self) -> tuple[object, ...]:
            return (object(),)

    result = OllamaModelProfileDiscovery(
        client=InvalidModelClient(),  # type: ignore[arg-type]
        provider_id=PROVIDER_ID,
    ).discover_model_profiles(CoreContext())

    assert result.status is ResultStatus.FAILURE
    assert result.value is None
    assert result.errors[0].error_code == "OLLAMA_MODEL_PROFILE_INVALID"
    assert result.errors[0].retryable is False


def test_profile_discovery_rejects_duplicate_model_candidates() -> None:
    result = OllamaModelProfileDiscovery(
        client=FakeModelClient(
            (
                OllamaModelSummary(name="duplicate:latest"),
                OllamaModelSummary(name="duplicate:latest"),
            )
        ),
        provider_id=PROVIDER_ID,
    ).discover_model_profiles(CoreContext())

    assert result.status is ResultStatus.FAILURE
    assert result.value is None
    assert result.errors[0].error_code == "OLLAMA_MODEL_PROFILE_DUPLICATE"
    assert result.errors[0].retryable is False


def test_profile_discovery_does_not_add_generation_routing_or_persistence_authority() -> None:
    for tree in _source_trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = _call_name(node.func)
                assert call_name not in FORBIDDEN_PROFILE_CALL_NAMES

    assert _import_roots().isdisjoint({"asyncpg", "psycopg", "requests", "sqlalchemy"})


def _call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""
