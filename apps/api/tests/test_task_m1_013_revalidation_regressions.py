from __future__ import annotations

import copy
import json

import curios_api.service as service
import pytest
from curios_api import create_api_composition, create_application
from fastapi.testclient import TestClient
from test_m1_cognitive_loop_endpoints import (
    _attempt,
    _executed_runner_result,
    _incompatible_selected_decision,
    _no_route_decision,
    _runner_payload,
    _selected_decision,
    _verification_payload,
    _work,
)

M1_PATHS = (
    "/m1/intents/decompose",
    "/m1/dag/run-once",
    "/m1/verification/complete",
)

SAFE_ERROR = {
    "error_code": "M1_API_MALFORMED_REQUEST",
    "message": "M1 API request is not canonical.",
    "details": {},
}


@pytest.mark.parametrize(
    ("content_type", "accepted"),
    (
        ("application/json", True),
        ("application/json; charset=utf-8", True),
        ("Application/JSON ; charset=UTF-8", True),
        ("text/plain", False),
        ("application/octet-stream", False),
        ("application/x-www-form-urlencoded", False),
        ("multipart/form-data", False),
        ("application/merge-patch+json", False),
        ("application/json token=super-secret", False),
        ("text/plain; token=super-secret", False),
    ),
)
@pytest.mark.parametrize("path", M1_PATHS)
def test_revalidation_media_type_matrix_for_every_m1_endpoint(
    path: str,
    content_type: str,
    accepted: bool,
) -> None:
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(
            path,
            content=json.dumps(_valid_payload(path)),
            headers={"content-type": content_type},
        )

    if accepted:
        assert response.status_code in {200, 201}
        return

    _assert_safe_malformed(response)
    body = _response_text(response)
    assert "token=super-secret" not in body


@pytest.mark.parametrize("path", M1_PATHS)
def test_revalidation_missing_and_empty_content_type_never_reaches_domain(
    path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_domain_spy(path, monkeypatch)
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        missing = client.post(path, content=json.dumps(_valid_payload(path)))
        empty = client.post(
            path,
            content=json.dumps(_valid_payload(path)),
            headers={"content-type": ""},
        )

    _assert_safe_malformed(missing)
    _assert_safe_malformed(empty)
    assert calls() == 0


@pytest.mark.parametrize(
    "body",
    (
        "token=super-secret",
        0,
        1.5,
        True,
        False,
        [],
        [["password=hunter2"]],
        None,
    ),
)
@pytest.mark.parametrize("path", M1_PATHS)
def test_revalidation_non_object_json_never_reaches_domain(
    path: str,
    body: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_domain_spy(path, monkeypatch)
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(path, json=body)

    _assert_safe_malformed(response)
    response_text = _response_text(response)
    assert "token=super-secret" not in response_text
    assert "password=hunter2" not in response_text
    assert calls() == 0


@pytest.mark.parametrize("path", M1_PATHS)
def test_revalidation_malformed_json_never_reaches_domain(
    path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_domain_spy(path, monkeypatch)
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(
            path,
            content="{invalid-json",
            headers={"content-type": "application/json; charset=utf-8"},
        )

    _assert_safe_malformed(response)
    assert "invalid-json" not in _response_text(response)
    assert calls() == 0


@pytest.mark.parametrize(
    "objective",
    (
        "Address a philosophical question.",
        "Discuss the statusquo of design terms.",
    ),
)
def test_revalidation_decomposition_near_misses_remain_domain_results(
    objective: str,
) -> None:
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(
            "/m1/intents/decompose",
            json={"objective": objective},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["decomposition"]["status"] == "UNSUPPORTED"
    assert payload["decomposition"]["unsupported_reason"] == "NO_TEMPLATE_MATCH"
    assert payload["dag"] is None


def test_revalidation_runner_domain_outcomes_survive_transport_corrections() -> None:
    work = _work()
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        no_route = client.post(
            "/m1/dag/run-once",
            json=_runner_payload(work, decision=_no_route_decision(work)),
        )
        incompatible = client.post(
            "/m1/dag/run-once",
            json=_runner_payload(work, decision=_incompatible_selected_decision(work)),
        )

    assert no_route.status_code == 200
    assert no_route.json()["runner_result"]["node_results"][0]["reason"] == "NO_ROUTE"
    assert incompatible.status_code == 200
    runner_result = incompatible.json()["runner_result"]
    assert runner_result["node_results"][0]["status"] == "BLOCKED"
    assert runner_result["node_results"][0]["reason"] == "ROUTE_NOT_EXECUTABLE"
    assert runner_result["events"] == []
    assert runner_result["evidence_refs"] == []


def test_revalidation_verification_domain_outcomes_survive_transport_corrections() -> None:
    work = _work()
    runner_result = _executed_runner_result(work)
    executor_outcome = runner_result["executor_outcome"]
    assert isinstance(executor_outcome, dict)
    evidence = executor_outcome["evidence_refs"][0]
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        approved = client.post(
            "/m1/verification/complete",
            json=_verification_payload(
                work, runner_result, attempts=[_attempt("passed", [evidence])]
            ),
        )
        rejected = client.post(
            "/m1/verification/complete",
            json=_verification_payload(
                work, runner_result, attempts=[_attempt("failed", [evidence])]
            ),
        )
        deferred = client.post(
            "/m1/verification/complete",
            json=_verification_payload(
                work, runner_result, attempts=[_attempt("inconclusive", [])]
            ),
        )

    assert approved.status_code == 200
    assert approved.json()["verification_result"]["completion_decision"] == "APPROVED"
    assert rejected.status_code == 200
    assert rejected.json()["verification_result"]["completion_decision"] == "REJECTED"
    assert deferred.status_code == 200
    assert deferred.json()["verification_result"]["completion_decision"] == "DEFERRED"


def test_revalidation_authority_looking_extra_fields_are_ignored_not_authority() -> None:
    work = _work()
    payload = _runner_payload(work, decision=_selected_decision(work))
    mutated = copy.deepcopy(payload)
    mutated.update(
        {
            "execute": True,
            "retry": True,
            "provider_url": "https://example.invalid",
            "model": "not-authorized",
            "persist": True,
            "max_concurrency_override": 0,
        }
    )
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        baseline = client.post("/m1/dag/run-once", json=payload)
        with_extras = client.post("/m1/dag/run-once", json=mutated)

    assert baseline.status_code == 200
    assert with_extras.status_code == 200
    assert (
        with_extras.json()["runner_result"]["node_results"]
        == baseline.json()["runner_result"]["node_results"]
    )


def test_revalidation_openapi_runtime_media_contract_is_consistent() -> None:
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]

    assert set(path for path in paths if path.startswith("/m1/")) == set(M1_PATHS)
    for path in M1_PATHS:
        assert set(paths[path]) == {"post"}
        body = paths[path]["post"]["requestBody"]
        assert body["required"] is True
        assert set(body["content"]) == {"application/json"}
        assert body["content"]["application/json"]["schema"]["type"] == "object"
    assert not any("model" in path and path.startswith("/m1/") for path in paths)
    assert not any("web" in path and path.startswith("/m1/") for path in paths)


def _valid_payload(path: str) -> dict[str, object]:
    if path == "/m1/intents/decompose":
        return {"objective": "Implement a bounded change"}
    work = _work()
    if path == "/m1/dag/run-once":
        return _runner_payload(work, decision=_selected_decision(work))
    if path == "/m1/verification/complete":
        runner_result = _executed_runner_result(work)
        executor_outcome = runner_result["executor_outcome"]
        assert isinstance(executor_outcome, dict)
        evidence = executor_outcome["evidence_refs"][0]
        return _verification_payload(
            work,
            runner_result,
            attempts=[_attempt("passed", [evidence])],
        )
    raise AssertionError(f"unexpected path: {path}")


def _install_domain_spy(path: str, monkeypatch: pytest.MonkeyPatch):
    calls = 0

    def record_call(*_args: object, **_kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("domain seam must not be reached")

    class FailingRunner:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            record_call()

    class FailingVerificationLoop:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            record_call()

    if path == "/m1/intents/decompose":
        monkeypatch.setattr(service, "decompose_intent", record_call)
    elif path == "/m1/dag/run-once":
        monkeypatch.setattr(service, "BoundedM1DagRunner", FailingRunner)
    elif path == "/m1/verification/complete":
        monkeypatch.setattr(service, "BoundedM1VerificationLoop", FailingVerificationLoop)
    else:
        raise AssertionError(f"unexpected path: {path}")

    return lambda: calls


def _assert_safe_malformed(response) -> None:
    assert response.status_code == 400
    assert response.json()["detail"] == SAFE_ERROR


def _response_text(response) -> str:
    return json.dumps(dict(response.headers)) + json.dumps(response.json())
