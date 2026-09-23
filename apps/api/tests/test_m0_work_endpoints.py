from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256

from contract_fixtures import fixed_id, human_principal, ref_for
from curios_api import create_api_composition, create_application, create_m0_work_api_composition
from curios_contracts import (
    ContractError,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    ProviderDescriptor,
    ProviderId,
    ProviderStatus,
    ProviderType,
    Result,
    SchemaVersion,
)
from curios_core import CoreContext
from curios_persistence import (
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
    PersistenceStore,
)
from fastapi.testclient import TestClient


def test_provider_inventory_work_flow_crosses_http_runtime_and_observation_boundaries() -> None:
    descriptor = _descriptor()
    app = _app(_MemoryPersistenceStore(), _Catalog(Result.success((descriptor,))))

    with TestClient(app) as client:
        create_response = client.post(
            "/work/provider-inventory",
            json={"title": "Inventory providers", "objective": "Collect provider descriptors."},
        )
        work_id = create_response.json()["work"]["work_id"]
        run_response = client.post(f"/work/{work_id}/run")
        execution_id = run_response.json()["execution"]["execution_id"]
        work_response = client.get(f"/work/{work_id}")
        execution_response = client.get(f"/work/{work_id}/executions/{execution_id}")
        events_response = client.get(f"/work/{work_id}/events")
        evidence_response = client.get(f"/work/{work_id}/evidence")

    assert create_response.status_code == 201
    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["status"] == "COMPLETED"
    assert run_payload["work"]["state"] == "COMPLETED"
    assert run_payload["executor_result"]["value"] == {
        "work_type": "provider_inventory",
        "provider_count": 1,
        "providers": [descriptor.to_json_compatible()],
    }
    assert work_response.json()["work"]["state"] == "COMPLETED"
    assert execution_response.json()["execution"]["state"] == "SUCCEEDED"
    assert [event["event_type"] for event in events_response.json()["events"]] == [
        "policy.evaluated",
        "execution.started",
        "evidence.produced",
        "execution.completed",
    ]
    assert evidence_response.json()["evidence"][0]["kind"] == "provider_report"


def test_policy_unknown_blocks_work_without_executor_invocation() -> None:
    catalog = _Catalog(Result.success((_descriptor(),)))
    app = _app(_MemoryPersistenceStore(), catalog)

    with TestClient(app) as client:
        work_id = client.post("/work/provider-inventory").json()["work"]["work_id"]
        response = client.post(f"/work/{work_id}/run", json={"policy_state_known": False})

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["status"] == "BLOCKED"
    assert detail["policy_decision"]["outcome"] == "UNKNOWN"
    assert catalog.calls == 0


def test_unsupported_and_malformed_effect_requests_do_not_authorize_execution() -> None:
    app = _app(_MemoryPersistenceStore(), _Catalog(Result.success((_descriptor(),))))

    with TestClient(app) as client:
        work_id = client.post("/work/provider-inventory").json()["work"]["work_id"]
        unsupported = client.post(
            f"/work/{work_id}/run",
            json={"requested_effects": ["EXTERNAL_READ"]},
        )
        mixed = client.post(
            f"/work/{work_id}/run",
            json={"requested_effects": ["READ_ONLY", "EXTERNAL_READ"]},
        )
        malformed = client.post(
            f"/work/{work_id}/run",
            json={"requested_effects": ["NOT_A_FROZEN_EFFECT"]},
        )

    assert unsupported.status_code == 403
    assert unsupported.json()["detail"]["policy_decision"]["outcome"] == "DENY"
    assert mixed.status_code == 403
    assert mixed.json()["detail"]["policy_decision"]["outcome"] == "DENY"
    assert malformed.status_code == 400
    assert malformed.json()["detail"]["error_code"] == "M0_API_MALFORMED_REQUEST"


def test_unsupported_work_creation_is_rejected_at_http_boundary() -> None:
    app = _app(_MemoryPersistenceStore(), _Catalog(Result.success((_descriptor(),))))

    with TestClient(app) as client:
        response = client.post("/work/provider-inventory", json={"work_type": "model_generation"})

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "M0_API_UNSUPPORTED_WORK_TYPE"


def test_executor_failure_translates_to_bounded_http_detail_without_native_leakage() -> None:
    app = _app(_MemoryPersistenceStore(), _Catalog(Result.failure((_contract_error(),))))

    with TestClient(app) as client:
        work_id = client.post("/work/provider-inventory").json()["work"]["work_id"]
        response = client.post(f"/work/{work_id}/run")

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["status"] == "FAILED"
    assert detail["executor_result"]["status"] == "failure"
    assert detail["executor_result"]["errors"][0]["error_code"] == (
        "PROVIDER_INVENTORY_CATALOG_FAILURE"
    )
    assert "sqlalchemy" not in json.dumps(detail).lower()
    assert "traceback" not in json.dumps(detail).lower()


def test_work_truth_is_observable_after_api_reconstruction() -> None:
    store = _MemoryPersistenceStore()
    descriptor = _descriptor()
    app = _app(store, _Catalog(Result.success((descriptor,))))

    with TestClient(app) as client:
        work_id = client.post("/work/provider-inventory").json()["work"]["work_id"]
        client.post(f"/work/{work_id}/run")

    reconstructed = _app(store, _Catalog(Result.success((descriptor,))))
    with TestClient(reconstructed) as client:
        work_response = client.get(f"/work/{work_id}")
        events_response = client.get(f"/work/{work_id}/events")
        evidence_response = client.get(f"/work/{work_id}/evidence")

    assert work_response.status_code == 200
    assert work_response.json()["work"]["state"] == "COMPLETED"
    assert len(events_response.json()["events"]) == 4
    assert len(evidence_response.json()["evidence"]) == 1


def test_m0_work_routes_fail_closed_when_runtime_is_not_composed() -> None:
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post("/work/provider-inventory")

    assert response.status_code == 503
    assert response.json()["detail"]["error_code"] == "M0_API_RUNTIME_UNAVAILABLE"


def _app(store: PersistenceStore, catalog: _Catalog):
    provider_ref = ref_for(ProviderId)
    m0_work = create_m0_work_api_composition(
        persistence_store=store,
        provider_catalog=catalog,
        principal=human_principal(),
        producer_ref=provider_ref,
        executor_ref=provider_ref,
        resource_refs=(provider_ref,),
    )
    return create_application(create_api_composition(provider_catalog=catalog, m0_work=m0_work))


def _descriptor() -> ProviderDescriptor:
    return ProviderDescriptor(
        provider_id=fixed_id(ProviderId),
        provider_type=ProviderType.MODEL,
        version=SchemaVersion(1, 0, 0),
        declared_capability_ids=(),
        status=ProviderStatus.AVAILABLE,
    )


def _contract_error() -> ContractError:
    return ContractError(
        error_code=ErrorCode("TEST_PROVIDER_FAILURE"),
        message="provider catalog failure",
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.ERROR,
        retryable=True,
    )


class _Catalog:
    def __init__(self, result: Result[tuple[ProviderDescriptor, ...]]) -> None:
        self._result = result
        self.calls = 0

    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        assert isinstance(context, CoreContext)
        self.calls += 1
        return self._result


class _MemoryPersistenceStore(PersistenceStore):
    def __init__(self) -> None:
        self._records: dict[tuple[PersistenceRecordKind, str], PersistenceRecord] = {}
        self._order: list[tuple[PersistenceRecordKind, str]] = []

    @contextmanager
    def transaction(self) -> Iterator[_MemoryTransaction]:  # type: ignore[override]
        yield _MemoryTransaction(self)


class _MemoryTransaction:
    def __init__(self, store: _MemoryPersistenceStore) -> None:
        self._store = store

    def insert_record(self, record: PersistenceRecord) -> None:
        key = (record.kind, record.record_id)
        if key in self._store._records:
            raise PersistenceError(
                PersistenceErrorCode.CONFLICT,
                "duplicate",
                retryable=False,
                operation=f"insert_{record.kind.value}",
            )
        self._store._records[key] = record
        self._store._order.append(key)

    def read_record(
        self,
        kind: PersistenceRecordKind,
        record_id: str,
    ) -> PersistenceRecord | None:
        return self._store._records.get((PersistenceRecordKind(kind), record_id))

    def list_records(
        self,
        kind: PersistenceRecordKind,
        *,
        limit: int,
    ) -> tuple[PersistenceRecord, ...]:
        normalized_kind = PersistenceRecordKind(kind)
        records = (
            self._store._records[key] for key in self._store._order if key[0] is normalized_kind
        )
        return tuple(_take(records, limit=limit))

    def replace_record(self, record: PersistenceRecord, *, expected_payload_sha256: str) -> None:
        key = (record.kind, record.record_id)
        current = self._store._records.get(key)
        if current is None or _record_version(current) != expected_payload_sha256:
            raise PersistenceError(
                PersistenceErrorCode.CONFLICT,
                "version conflict",
                retryable=False,
                operation=f"replace_{record.kind.value}",
            )
        self._store._records[key] = record


def _take(values: Iterator[PersistenceRecord], *, limit: int) -> list[PersistenceRecord]:
    output: list[PersistenceRecord] = []
    for value in values:
        if len(output) == limit:
            break
        output.append(value)
    return output


def _record_version(record: PersistenceRecord) -> str:
    encoded = json.dumps(
        record.payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
