from __future__ import annotations

import json

import pytest
from curios_api import create_api_composition, create_application
from fastapi.testclient import TestClient

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
