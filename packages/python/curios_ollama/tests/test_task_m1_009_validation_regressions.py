from __future__ import annotations

import pytest
from curios_contracts import ErrorCategory, ResultStatus
from curios_core import CoreContext
from curios_ollama import OllamaModelProfileDiscovery, OllamaModelSummary

SAFE_INVALID_INVENTORY_MESSAGE = (
    "Ollama model profile discovery received invalid local inventory metadata."
)


class _MalformedInventoryClient:
    def __init__(self, message: str) -> None:
        self.message = message

    def list_models(self) -> tuple[object, ...]:
        raise ValueError(self.message)


class _UnavailableInventoryClient:
    def list_models(self) -> tuple[OllamaModelSummary, ...]:
        raise OSError("password=hunter2")


class _InventoryClientWithGenerationMethods:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def list_models(self) -> tuple[OllamaModelSummary, ...]:
        self.calls.append("list_models")
        return (OllamaModelSummary(name="local-only:latest"),)

    def generate(self) -> None:
        raise AssertionError("generate must not be called by profile discovery")

    def chat(self) -> None:
        raise AssertionError("chat must not be called by profile discovery")


def _assert_no_public_leak(result: object, leaked_text: str) -> None:
    serialized = result.to_json_compatible()  # type: ignore[attr-defined]
    assert leaked_text not in result.errors[0].message  # type: ignore[attr-defined]
    assert leaked_text not in str(result.errors[0].details)  # type: ignore[attr-defined]
    assert leaked_text not in str(result.errors[0].to_json_compatible())  # type: ignore[attr-defined]
    assert leaked_text not in str(serialized)
    assert leaked_text not in repr(result)
    assert leaked_text not in repr(result.errors[0])  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "provider_message",
    (
        "token=super-secret",
        "password=hunter2",
        "api_key=secret-value",
        "Authorization: Bearer secret-token",
        "token=secret",
        "credential=private",
        "secret=hidden",
        "provider returned malformed model entry",
    ),
)
def test_malformed_inventory_failure_does_not_leak_provider_exception_text(
    provider_message: str,
) -> None:
    result = OllamaModelProfileDiscovery(
        client=_MalformedInventoryClient(provider_message),  # type: ignore[arg-type]
    ).discover_model_profiles(CoreContext())

    assert result.status is ResultStatus.FAILURE
    assert result.value is None
    assert result.errors[0].error_code == "OLLAMA_MODEL_PROFILE_INVALID"
    assert result.errors[0].message == SAFE_INVALID_INVENTORY_MESSAGE
    assert result.errors[0].retryable is False
    assert result.errors[0].details is None
    _assert_no_public_leak(result, provider_message)


def test_unavailable_provider_failure_does_not_leak_raw_client_exception_text() -> None:
    result = OllamaModelProfileDiscovery(
        client=_UnavailableInventoryClient(),
    ).discover_model_profiles(CoreContext())

    assert result.status is ResultStatus.FAILURE
    assert result.value is None
    assert result.errors[0].error_code == "OLLAMA_MODEL_PROFILE_DISCOVERY_UNAVAILABLE"
    assert result.errors[0].category is ErrorCategory.DEPENDENCY
    assert result.errors[0].retryable is True
    _assert_no_public_leak(result, "password=hunter2")


def test_profile_discovery_uses_inventory_only_not_generation_methods() -> None:
    client = _InventoryClientWithGenerationMethods()

    result = OllamaModelProfileDiscovery(client=client).discover_model_profiles(CoreContext())

    assert result.status is ResultStatus.SUCCESS
    assert result.value is not None
    assert tuple(profile.model_name for profile in result.value) == ("local-only:latest",)
    assert client.calls == ["list_models"]
