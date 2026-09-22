from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest
from curios_contracts import (
    ErrorCategory,
    ProviderStatus,
    ProviderType,
    ResultStatus,
)
from curios_core import CoreContext, ProviderCatalog
from curios_ollama import OllamaModelSummary, OllamaProviderCatalog
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
