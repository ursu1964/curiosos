from __future__ import annotations

import json

import curios_api.service as service
import pytest
from curios_api import create_api_composition, create_application
from fastapi.testclient import TestClient
from test_m1_cognitive_loop_endpoints import (
    _attempt,
    _executed_runner_result,
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


@pytest.mark.parametrize(
    "path",
    M1_PATHS,
)
@pytest.mark.parametrize(
    "body",
    (
        "token=super-secret",
        "password=hunter2",
        "api_key=secret-value",
        "Authorization: Bearer secret-token",
        "credential=private",
        "secret=hidden",
    ),
)
def test_m1_endpoints_bound_non_object_json_without_echoing_raw_body(
    path: str,
    body: str,
) -> None:
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(path, json=body)

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "error_code": "M1_API_MALFORMED_REQUEST",
        "message": "M1 API request is not canonical.",
        "details": {},
    }
    response_text = json.dumps(response.json()).lower()
    assert body.lower() not in response_text
    assert "token=super-secret" not in response_text
    assert "password=hunter2" not in response_text
    assert "api_key=secret-value" not in response_text
    assert "authorization: bearer secret-token" not in response_text
    assert "credential=private" not in response_text
    assert "secret=hidden" not in response_text


@pytest.mark.parametrize("path", M1_PATHS)
@pytest.mark.parametrize(
    "body",
    (
        {},
        "",
        0,
        1.5,
        True,
        False,
        [],
        [["token=super-secret"]],
        None,
    ),
)
def test_m1_endpoints_bound_body_shape_matrix(path: str, body: object) -> None:
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(path, json=body)

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "M1_API_MALFORMED_REQUEST"
    assert "token=super-secret" not in json.dumps(response.json()).lower()


@pytest.mark.parametrize("path", M1_PATHS)
def test_m1_endpoints_bound_malformed_json_syntax(path: str) -> None:
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(
            path,
            content="{invalid-json",
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "error_code": "M1_API_MALFORMED_REQUEST",
        "message": "M1 API request is not canonical.",
        "details": {},
    }
    assert "invalid-json" not in json.dumps(response.json()).lower()


def test_m1_endpoint_rejects_json_payload_outside_declared_json_media_type() -> None:
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        text_plain = client.post(
            "/m1/intents/decompose",
            content='{"objective":"Implement a bounded change"}',
            headers={"content-type": "text/plain"},
        )
        missing = client.post(
            "/m1/intents/decompose",
            content='{"objective":"Implement a bounded change"}',
        )

    _assert_bounded_m1_error(text_plain)
    _assert_bounded_m1_error(missing)


@pytest.mark.parametrize("path", M1_PATHS)
@pytest.mark.parametrize(
    ("content_type", "accepted"),
    (
        ("application/json", True),
        ("application/json;charset=utf-8", True),
        ("application/json; charset=UTF-8", True),
        ("Application/JSON ; charset=utf-8", True),
        ("text/plain", False),
        ("application/octet-stream", False),
        ("application/x-www-form-urlencoded", False),
        ("multipart/form-data", False),
        ("application/merge-patch+json", False),
        ("", False),
        ("application/json token=super-secret", False),
        ("text/plain; token=super-secret", False),
        ("application/x-invalid; password=hunter2", False),
    ),
)
def test_m1_endpoints_enforce_declared_json_media_type(
    path: str,
    content_type: str,
    accepted: bool,
) -> None:
    app = create_application(create_api_composition())
    payload = _valid_payload_for_path(path)

    with TestClient(app) as client:
        response = client.post(
            path,
            content=json.dumps(payload),
            headers={"content-type": content_type},
        )

    if accepted:
        assert response.status_code in {200, 201}
    else:
        _assert_bounded_m1_error(response)
        response_text = json.dumps(response.json()).lower()
        assert "token=super-secret" not in response_text
        assert "password=hunter2" not in response_text


@pytest.mark.parametrize("path", M1_PATHS)
def test_m1_endpoints_reject_missing_content_type_before_domain_processing(path: str) -> None:
    app = create_application(create_api_composition())
    payload = _valid_payload_for_path(path)

    with TestClient(app) as client:
        response = client.post(path, content=json.dumps(payload))

    _assert_bounded_m1_error(response)


def test_rejected_media_does_not_invoke_decomposition(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def fail_if_called(*_args: object, **_kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("decomposition must not be called for invalid media")

    monkeypatch.setattr(service, "decompose_intent", fail_if_called)
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(
            "/m1/intents/decompose",
            content=json.dumps(_valid_payload_for_path("/m1/intents/decompose")),
            headers={"content-type": "text/plain; token=super-secret"},
        )

    _assert_bounded_m1_error(response)
    assert calls == 0


def test_rejected_media_does_not_invoke_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingRunner:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("runner must not be constructed for invalid media")

    monkeypatch.setattr(service, "BoundedM1DagRunner", FailingRunner)
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(
            "/m1/dag/run-once",
            content=json.dumps(_valid_payload_for_path("/m1/dag/run-once")),
            headers={"content-type": "application/octet-stream"},
        )

    _assert_bounded_m1_error(response)


def test_rejected_media_does_not_invoke_verification_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingVerificationLoop:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("verification loop must not be constructed for invalid media")

    monkeypatch.setattr(service, "BoundedM1VerificationLoop", FailingVerificationLoop)
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(
            "/m1/verification/complete",
            content=json.dumps(_valid_payload_for_path("/m1/verification/complete")),
            headers={"content-type": "application/x-invalid; password=hunter2"},
        )

    _assert_bounded_m1_error(response)


def _valid_payload_for_path(path: str) -> dict[str, object]:
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


def _assert_bounded_m1_error(response) -> None:
    assert response.status_code == 400
    assert response.json()["detail"] == {
        "error_code": "M1_API_MALFORMED_REQUEST",
        "message": "M1 API request is not canonical.",
        "details": {},
    }
