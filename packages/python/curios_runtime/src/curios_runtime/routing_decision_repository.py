"""M1 routing decision records over executor and local profile candidates."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from types import MappingProxyType
from typing import NoReturn, Self

from curios_contracts import (
    DecisionId,
    ObjectReference,
    ObservabilityContext,
    ReferenceKind,
    SchemaVersion,
    UtcTimestamp,
    WorkId,
    WorkItem,
    to_json_compatible,
)
from curios_persistence import (
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
    PersistenceStore,
)

_SCHEMA_VERSION = SchemaVersion.parse("1.0.0")
_MAX_CANDIDATES = 32
_MAX_WORK_TYPES = 16
_MAX_STRING_LENGTH = 256
_MAX_CONSTRAINT_KEYS = 16
_MAX_CONSTRAINT_SEQUENCE_ITEMS = 16
_MAX_CONSTRAINT_DEPTH = 3
_SAFE_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_SAFE_VALUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@+-]{0,255}$")
_SAFE_MESSAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,;:/@+-]{0,255}$")
_SECRET_TOKEN_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|credential|password|private[_-]?key|secret|token)"
)
_SECRET_VALUE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|credential|password|secret|token)\s*[:=]"
)
_NO_MODEL_CANDIDATE_KEY = "no_model"
_CONSTRAINT_REQUIRED_ROUTE_KIND = "required_route_kind"
_CONSTRAINT_REQUIRED_PROVIDER_REF = "required_provider_ref"
_CONSTRAINT_LOCAL_ONLY = "local_only"
_ALLOWED_CONSTRAINT_KEYS = frozenset(
    {
        _CONSTRAINT_REQUIRED_ROUTE_KIND,
        _CONSTRAINT_REQUIRED_PROVIDER_REF,
        _CONSTRAINT_LOCAL_ONLY,
    }
)


class RouteCandidateKind(StrEnum):
    """Stable M1 route candidate classes without execution authority."""

    DETERMINISTIC_EXECUTOR = "deterministic_executor"
    MODEL_PROFILE = "model_profile"
    NO_MODEL = "no_model"


class RoutingDecisionStatus(StrEnum):
    """Stable routing decision outcomes."""

    SELECTED = "SELECTED"
    NO_ROUTE = "NO_ROUTE"


class RoutingRationaleCode(StrEnum):
    """Bounded reason codes for deterministic M1 routing."""

    SELECTED_SINGLE_VALID_ROUTE = "SELECTED_SINGLE_VALID_ROUTE"
    NO_VALID_ROUTE = "NO_VALID_ROUTE"
    AMBIGUOUS_ROUTE = "AMBIGUOUS_ROUTE"


class RoutingDecisionErrorCode(StrEnum):
    """Stable bounded failure categories for routing decision records."""

    CONFLICT = "CONFLICT"
    CORRUPT_RECORD = "CORRUPT_RECORD"
    INVALID_CANDIDATE = "INVALID_CANDIDATE"
    INVALID_CONSTRAINT = "INVALID_CONSTRAINT"
    INVALID_REQUEST = "INVALID_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE"


class RoutingDecisionError(RuntimeError):
    """Bounded routing decision failure without provider/persistence leakage."""

    def __init__(
        self,
        code: RoutingDecisionErrorCode,
        message: str,
        *,
        retryable: bool,
        operation: str,
    ) -> None:
        super().__init__(message)
        self.code = RoutingDecisionErrorCode(code)
        self.retryable = retryable
        self.operation = operation

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "message": str(self),
            "retryable": self.retryable,
            "operation": self.operation,
        }


@dataclass(frozen=True, slots=True)
class RoutingCandidate:
    """One inert route candidate for a specific work item."""

    candidate_key: str
    kind: RouteCandidateKind
    work_ref: ObjectReference
    provider_ref: ObjectReference | None = None
    model_name: str | None = None
    model_status: str | None = None
    executor_name: str | None = None
    supported_work_types: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        kind = RouteCandidateKind(self.kind)
        work_ref = _require_ref_kind(self.work_ref, ReferenceKind.WORK, "work_ref")
        candidate_key = _safe_token(self.candidate_key, "candidate_key")
        if kind is RouteCandidateKind.NO_MODEL and candidate_key != _NO_MODEL_CANDIDATE_KEY:
            _raise_routing_error(
                RoutingDecisionError(
                    RoutingDecisionErrorCode.INVALID_CANDIDATE,
                    "No-model route candidates must use the canonical no_model key.",
                    retryable=False,
                    operation="construct_candidate",
                )
            )
        provider_ref = self.provider_ref
        if provider_ref is not None:
            provider_ref = _require_ref_kind(provider_ref, ReferenceKind.PROVIDER, "provider_ref")
        model_name = self.model_name
        if model_name is not None:
            model_name = _safe_text(model_name, "model_name")
        model_status = self.model_status
        if model_status is not None:
            model_status = _safe_token(model_status, "model_status")
        executor_name = self.executor_name
        if executor_name is not None:
            executor_name = _safe_token(executor_name, "executor_name")
        supported_work_types = tuple(
            _safe_token(work_type, "supported_work_type") for work_type in self.supported_work_types
        )

        if kind is RouteCandidateKind.DETERMINISTIC_EXECUTOR:
            if executor_name is None or not supported_work_types:
                _invalid_candidate("Deterministic executor candidates require executor metadata.")
            if provider_ref is not None or model_name is not None or model_status is not None:
                _invalid_candidate("Deterministic executor candidates cannot include model fields.")
        elif kind is RouteCandidateKind.MODEL_PROFILE:
            if provider_ref is None or model_name is None or model_status is None:
                _invalid_candidate("Model profile candidates require provider, model, and status.")
            if executor_name is not None or supported_work_types:
                _invalid_candidate("Model profile candidates cannot include executor fields.")
        elif (
            provider_ref is not None
            or model_name is not None
            or model_status is not None
            or executor_name is not None
            or supported_work_types
        ):
            _invalid_candidate("No-model candidates cannot include execution or profile fields.")

        object.__setattr__(self, "candidate_key", candidate_key)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "work_ref", work_ref)
        object.__setattr__(self, "provider_ref", provider_ref)
        object.__setattr__(self, "model_name", model_name)
        object.__setattr__(self, "model_status", model_status)
        object.__setattr__(self, "executor_name", executor_name)
        object.__setattr__(self, "supported_work_types", tuple(sorted(set(supported_work_types))))

    @classmethod
    def deterministic_executor(
        cls,
        *,
        work_id: WorkId,
        executor_name: str,
        supported_work_types: tuple[str, ...],
    ) -> Self:
        return cls(
            candidate_key=f"executor_{_safe_token(executor_name, 'executor_name')}",
            kind=RouteCandidateKind.DETERMINISTIC_EXECUTOR,
            work_ref=ObjectReference.from_id(work_id),
            executor_name=executor_name,
            supported_work_types=supported_work_types,
        )

    @classmethod
    def model_profile(cls, *, work_id: WorkId, profile: object) -> Self:
        provider_ref = getattr(profile, "provider_ref", None)
        model_name = getattr(profile, "model_name", None)
        status = getattr(profile, "status", None)
        status_value = getattr(status, "value", status)
        if not isinstance(provider_ref, ObjectReference):
            _invalid_candidate("Model profile candidates require a canonical provider reference.")
        if not isinstance(model_name, str) or not isinstance(status_value, str):
            _invalid_candidate("Model profile candidates require string model status metadata.")
        candidate_model = _safe_text(model_name, "model_name").lower()
        provider_token = str(provider_ref.ref_id).replace("_", "").lower()
        return cls(
            candidate_key=f"model_profile_{provider_token}_{_candidate_token(candidate_model)}",
            kind=RouteCandidateKind.MODEL_PROFILE,
            work_ref=ObjectReference.from_id(work_id),
            provider_ref=provider_ref,
            model_name=model_name,
            model_status=status_value,
        )

    @classmethod
    def no_model(cls, *, work_id: WorkId) -> Self:
        return cls(
            candidate_key=_NO_MODEL_CANDIDATE_KEY,
            kind=RouteCandidateKind.NO_MODEL,
            work_ref=ObjectReference.from_id(work_id),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        if not isinstance(value, dict):
            msg = "routing candidate JSON must be an object"
            raise TypeError(msg)
        return cls(
            candidate_key=_require_str(value["candidate_key"], "candidate_key"),
            kind=RouteCandidateKind(_require_str(value["kind"], "kind")),
            work_ref=ObjectReference.from_json_compatible(value["work_ref"]),
            provider_ref=(
                ObjectReference.from_json_compatible(value["provider_ref"])
                if value.get("provider_ref") is not None
                else None
            ),
            model_name=_optional_str(value.get("model_name"), "model_name"),
            model_status=_optional_str(value.get("model_status"), "model_status"),
            executor_name=_optional_str(value.get("executor_name"), "executor_name"),
            supported_work_types=tuple(
                _require_str(item, "supported_work_type")
                for item in _optional_sequence(value.get("supported_work_types"))
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "candidate_key": self.candidate_key,
            "kind": self.kind.value,
            "work_ref": to_json_compatible(self.work_ref),
            "provider_ref": to_json_compatible(self.provider_ref),
            "model_name": self.model_name,
            "model_status": self.model_status,
            "executor_name": self.executor_name,
            "supported_work_types": to_json_compatible(self.supported_work_types),
        }


@dataclass(frozen=True, slots=True)
class RoutingDecisionRationale:
    """Structured bounded rationale without raw provider text."""

    code: RoutingRationaleCode
    message: str
    details: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", RoutingRationaleCode(self.code))
        object.__setattr__(self, "message", _safe_message(self.message, "message"))
        object.__setattr__(self, "details", _normalize_constraints(self.details))

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        if not isinstance(value, dict):
            msg = "routing rationale JSON must be an object"
            raise TypeError(msg)
        return cls(
            code=RoutingRationaleCode(_require_str(value["code"], "code")),
            message=_require_str(value["message"], "message"),
            details=_optional_mapping(value.get("details"), "details"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "message": self.message,
            "details": to_json_compatible(self.details),
        }


@dataclass(frozen=True, slots=True)
class RoutingDecisionRequest:
    """Input to deterministic route selection over already discovered candidates."""

    decision_id: DecisionId
    work: WorkItem
    candidates: tuple[RoutingCandidate, ...]
    requested_at: UtcTimestamp
    producer_ref: ObjectReference
    observability_context: ObservabilityContext
    resource_constraints: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.decision_id, DecisionId):
            msg = "decision_id must be a DecisionId"
            raise TypeError(msg)
        if not isinstance(self.work, WorkItem):
            msg = "work must be a WorkItem"
            raise TypeError(msg)
        candidates = _normalize_candidates(self.candidates, self.work.work_id)
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "requested_at", UtcTimestamp(self.requested_at))
        if not isinstance(self.producer_ref, ObjectReference):
            msg = "producer_ref must be an ObjectReference"
            raise TypeError(msg)
        if not isinstance(self.observability_context, ObservabilityContext):
            msg = "observability_context must be an ObservabilityContext"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "resource_constraints",
            _normalize_resource_constraints(self.resource_constraints),
        )


@dataclass(frozen=True, slots=True)
class RoutingDecisionRecord:
    """Persistable M1 route decision without execution side effects."""

    decision_id: DecisionId
    work_ref: ObjectReference
    status: RoutingDecisionStatus
    candidates: tuple[RoutingCandidate, ...]
    selected_route: RoutingCandidate | None
    rationale: RoutingDecisionRationale
    resource_constraints: Mapping[str, object] | None
    decided_at: UtcTimestamp
    producer_ref: ObjectReference
    observability_context: ObservabilityContext
    schema_version: SchemaVersion = field(default=_SCHEMA_VERSION)

    def __post_init__(self) -> None:
        if not isinstance(self.decision_id, DecisionId):
            msg = "decision_id must be a DecisionId"
            raise TypeError(msg)
        work_ref = _require_ref_kind(self.work_ref, ReferenceKind.WORK, "work_ref")
        status = RoutingDecisionStatus(self.status)
        candidates = _normalize_candidates(self.candidates, _work_id(work_ref))
        selected_route = self.selected_route
        if selected_route is not None:
            if not isinstance(selected_route, RoutingCandidate):
                msg = "selected_route must be a RoutingCandidate when provided"
                raise TypeError(msg)
            if selected_route.work_ref != work_ref:
                _invalid_request("Selected route must reference the routed work item.")
        if status is RoutingDecisionStatus.SELECTED and selected_route is None:
            _invalid_request("Selected routing decisions require a selected route.")
        if status is RoutingDecisionStatus.NO_ROUTE and selected_route is not None:
            _invalid_request("No-route routing decisions cannot include a selected route.")
        if not isinstance(self.rationale, RoutingDecisionRationale):
            msg = "rationale must be a RoutingDecisionRationale"
            raise TypeError(msg)
        if not isinstance(self.producer_ref, ObjectReference):
            msg = "producer_ref must be an ObjectReference"
            raise TypeError(msg)
        if not isinstance(self.observability_context, ObservabilityContext):
            msg = "observability_context must be an ObservabilityContext"
            raise TypeError(msg)
        if not isinstance(self.schema_version, SchemaVersion):
            msg = "schema_version must be a SchemaVersion"
            raise TypeError(msg)
        object.__setattr__(self, "work_ref", work_ref)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "decided_at", UtcTimestamp(self.decided_at))
        object.__setattr__(
            self,
            "resource_constraints",
            _normalize_resource_constraints(self.resource_constraints),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        if not isinstance(value, dict):
            msg = "routing decision JSON must be an object"
            raise TypeError(msg)
        selected = value.get("selected_route")
        return cls(
            decision_id=DecisionId(_require_str(value["decision_id"], "decision_id")),
            work_ref=ObjectReference.from_json_compatible(value["work_ref"]),
            status=RoutingDecisionStatus(_require_str(value["status"], "status")),
            candidates=tuple(
                RoutingCandidate.from_json_compatible(item)
                for item in _required_sequence(value["candidates"], "candidates")
            ),
            selected_route=(
                RoutingCandidate.from_json_compatible(selected) if selected is not None else None
            ),
            rationale=RoutingDecisionRationale.from_json_compatible(value["rationale"]),
            resource_constraints=_optional_mapping(
                value.get("resource_constraints"),
                "resource_constraints",
            ),
            decided_at=UtcTimestamp(_require_str(value["decided_at"], "decided_at")),
            producer_ref=ObjectReference.from_json_compatible(value["producer_ref"]),
            observability_context=ObservabilityContext.from_json(value["observability_context"]),
            schema_version=SchemaVersion.parse(
                _require_str(value["schema_version"], "schema_version")
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "decision_id": str(self.decision_id),
            "work_ref": to_json_compatible(self.work_ref),
            "status": self.status.value,
            "candidates": to_json_compatible(self.candidates),
            "selected_route": to_json_compatible(self.selected_route),
            "rationale": self.rationale.to_json_compatible(),
            "resource_constraints": to_json_compatible(self.resource_constraints),
            "decided_at": to_json_compatible(self.decided_at),
            "producer_ref": to_json_compatible(self.producer_ref),
            "observability_context": to_json_compatible(self.observability_context),
            "schema_version": to_json_compatible(self.schema_version),
        }


@dataclass(frozen=True, slots=True)
class StoredRoutingDecision:
    """A persisted routing decision plus its optimistic concurrency version."""

    decision: RoutingDecisionRecord
    version: str


class M1RoutingDecisionRepository:
    """Repository boundary for deterministic M1 routing decision records."""

    def __init__(self, store: PersistenceStore) -> None:
        if not isinstance(store, PersistenceStore):
            msg = "store must be a PersistenceStore"
            raise TypeError(msg)
        self._store = store

    def create_decision(self, decision: RoutingDecisionRecord) -> StoredRoutingDecision:
        """Persist a routing decision without scheduling or invoking a model."""
        if not isinstance(decision, RoutingDecisionRecord):
            msg = "decision must be a RoutingDecisionRecord"
            raise TypeError(msg)
        record = _decision_to_record(decision)
        try:
            with self._store.transaction() as transaction:
                transaction.insert_record(record)
        except PersistenceError as exc:
            _raise_routing_error(_translate_persistence_error(exc, operation="create_decision"))
        return StoredRoutingDecision(decision=decision, version=_record_version(record))

    def read_decision(self, decision_id: DecisionId) -> StoredRoutingDecision | None:
        """Read a persisted routing decision by canonical decision ID."""
        if not isinstance(decision_id, DecisionId):
            msg = "decision_id must be a DecisionId"
            raise TypeError(msg)
        error: RoutingDecisionError | None = None
        try:
            with self._store.transaction() as transaction:
                record = transaction.read_record(
                    PersistenceRecordKind.ROUTING_DECISION,
                    str(decision_id),
                )
        except PersistenceError as exc:
            error = _translate_persistence_error(exc, operation="read_decision")
        if error is not None:
            _raise_routing_error(error)
        if record is None:
            return None
        decision = _record_to_decision(record, operation="read_decision")
        return StoredRoutingDecision(decision=decision, version=_record_version(record))

    def list_decisions(self, *, limit: int) -> tuple[StoredRoutingDecision, ...]:
        """List persisted routing decisions in deterministic append order."""
        try:
            with self._store.transaction() as transaction:
                records = transaction.list_records(
                    PersistenceRecordKind.ROUTING_DECISION,
                    limit=limit,
                )
        except PersistenceError as exc:
            _raise_routing_error(_translate_persistence_error(exc, operation="list_decisions"))
        return tuple(
            StoredRoutingDecision(
                decision=_record_to_decision(record, operation="list_decisions"),
                version=_record_version(record),
            )
            for record in records
        )


def select_m1_route(request: RoutingDecisionRequest) -> RoutingDecisionRecord:
    """Return a deterministic routing decision without execution side effects."""
    if not isinstance(request, RoutingDecisionRequest):
        msg = "request must be a RoutingDecisionRequest"
        raise TypeError(msg)

    valid = tuple(
        candidate for candidate in request.candidates if _candidate_is_valid(candidate, request)
    )
    if len(valid) == 1:
        selected = valid[0]
        return RoutingDecisionRecord(
            decision_id=request.decision_id,
            work_ref=ObjectReference.from_id(request.work.work_id),
            status=RoutingDecisionStatus.SELECTED,
            candidates=request.candidates,
            selected_route=selected,
            rationale=RoutingDecisionRationale(
                code=RoutingRationaleCode.SELECTED_SINGLE_VALID_ROUTE,
                message="Selected the only valid M1 route candidate.",
                details={
                    "selected_candidate_key": selected.candidate_key,
                    "selected_kind": selected.kind.value,
                    "valid_candidate_count": 1,
                },
            ),
            resource_constraints=request.resource_constraints,
            decided_at=request.requested_at,
            producer_ref=request.producer_ref,
            observability_context=request.observability_context,
        )

    rationale_code = (
        RoutingRationaleCode.NO_VALID_ROUTE if not valid else RoutingRationaleCode.AMBIGUOUS_ROUTE
    )
    return RoutingDecisionRecord(
        decision_id=request.decision_id,
        work_ref=ObjectReference.from_id(request.work.work_id),
        status=RoutingDecisionStatus.NO_ROUTE,
        candidates=request.candidates,
        selected_route=None,
        rationale=RoutingDecisionRationale(
            code=rationale_code,
            message=(
                "No M1 route candidate satisfied the routing constraints."
                if not valid
                else "Multiple M1 route candidates satisfied the routing constraints."
            ),
            details={
                "valid_candidate_count": len(valid),
                "candidate_count": len(request.candidates),
            },
        ),
        resource_constraints=request.resource_constraints,
        decided_at=request.requested_at,
        producer_ref=request.producer_ref,
        observability_context=request.observability_context,
    )


def _candidate_is_valid(candidate: RoutingCandidate, request: RoutingDecisionRequest) -> bool:
    if candidate.kind is RouteCandidateKind.NO_MODEL:
        return False
    constraints = request.resource_constraints or {}
    required_kind = constraints.get(_CONSTRAINT_REQUIRED_ROUTE_KIND)
    if required_kind is not None and candidate.kind.value != required_kind:
        return False
    required_provider_ref = constraints.get(_CONSTRAINT_REQUIRED_PROVIDER_REF)
    if required_provider_ref is not None:
        if candidate.provider_ref is None:
            return False
        if candidate.provider_ref.to_json_compatible() != required_provider_ref:
            return False
    if candidate.kind is RouteCandidateKind.DETERMINISTIC_EXECUTOR:
        return request.work.work_type in candidate.supported_work_types
    if candidate.kind is RouteCandidateKind.MODEL_PROFILE:
        return candidate.model_status == "available"
    return False


def _normalize_candidates(
    candidates: tuple[RoutingCandidate, ...],
    work_id: WorkId,
) -> tuple[RoutingCandidate, ...]:
    normalized = tuple(candidates)
    if len(normalized) > _MAX_CANDIDATES:
        _invalid_request("Routing decisions cannot contain more than 32 candidates.")
    keys: set[str] = set()
    work_ref = ObjectReference.from_id(work_id)
    for candidate in normalized:
        if not isinstance(candidate, RoutingCandidate):
            msg = "candidates must contain RoutingCandidate values"
            raise TypeError(msg)
        if candidate.work_ref != work_ref:
            _invalid_request("Routing candidates must reference the requested work item.")
        if candidate.candidate_key in keys:
            _raise_routing_error(
                RoutingDecisionError(
                    RoutingDecisionErrorCode.INVALID_CANDIDATE,
                    "Routing candidate keys must be distinct.",
                    retryable=False,
                    operation="construct_request",
                )
            )
        keys.add(candidate.candidate_key)
        if len(candidate.supported_work_types) > _MAX_WORK_TYPES:
            _invalid_candidate("Routing candidate work type list exceeds the bounded M1 limit.")
    return tuple(sorted(normalized, key=lambda candidate: candidate.candidate_key))


def _normalize_resource_constraints(
    constraints: Mapping[str, object] | None,
) -> Mapping[str, object] | None:
    normalized = _normalize_constraints(constraints)
    if normalized is None:
        return None
    unknown = set(normalized) - _ALLOWED_CONSTRAINT_KEYS
    if unknown:
        _raise_routing_error(
            RoutingDecisionError(
                RoutingDecisionErrorCode.INVALID_CONSTRAINT,
                "Routing constraints contain unsupported keys.",
                retryable=False,
                operation="construct_request",
            )
        )
    if _CONSTRAINT_REQUIRED_ROUTE_KIND in normalized:
        try:
            RouteCandidateKind(
                _require_str(
                    normalized[_CONSTRAINT_REQUIRED_ROUTE_KIND],
                    _CONSTRAINT_REQUIRED_ROUTE_KIND,
                )
            )
        except ValueError:
            _raise_routing_error(
                RoutingDecisionError(
                    RoutingDecisionErrorCode.INVALID_CONSTRAINT,
                    "Routing constraints require a supported route kind.",
                    retryable=False,
                    operation="construct_request",
                )
            )
    if normalized.get(_CONSTRAINT_LOCAL_ONLY) not in {None, True}:
        _raise_routing_error(
            RoutingDecisionError(
                RoutingDecisionErrorCode.INVALID_CONSTRAINT,
                "M1 routing constraints support only local routes.",
                retryable=False,
                operation="construct_request",
            )
        )
    if _CONSTRAINT_REQUIRED_PROVIDER_REF in normalized:
        try:
            provider_ref = ObjectReference.from_json_compatible(
                normalized[_CONSTRAINT_REQUIRED_PROVIDER_REF]
            )
        except KeyError, TypeError, ValueError:
            _invalid_constraint("Routing constraints require a canonical provider reference.")
        if provider_ref.kind is not ReferenceKind.PROVIDER:
            _invalid_constraint("Routing constraints require a canonical provider reference.")
    return normalized


def _normalize_constraints(constraints: Mapping[str, object] | None) -> Mapping[str, object] | None:
    if constraints is None:
        return None
    if not isinstance(constraints, Mapping):
        msg = "constraints must be a mapping when provided"
        raise TypeError(msg)
    if len(constraints) > _MAX_CONSTRAINT_KEYS:
        _invalid_request("Routing constraints exceed the bounded M1 key limit.")
    return MappingProxyType(
        {
            _safe_token(key, "constraint key"): _normalize_constraint_value(
                value,
                depth=_MAX_CONSTRAINT_DEPTH,
            )
            for key, value in constraints.items()
        }
    )


def _normalize_constraint_value(value: object, *, depth: int) -> object:
    if depth < 0:
        _invalid_request("Routing constraint nesting is too deep.")
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int | float):
        if isinstance(value, bool):
            _invalid_request("Routing constraint numeric values cannot be bools.")
        return value
    if isinstance(value, str):
        return _safe_text(value, "constraint value")
    if isinstance(value, Mapping):
        if len(value) > _MAX_CONSTRAINT_KEYS:
            _invalid_request("Routing nested constraints exceed the bounded M1 key limit.")
        return {
            _safe_token(key, "constraint key"): _normalize_constraint_value(
                nested,
                depth=depth - 1,
            )
            for key, nested in value.items()
        }
    if isinstance(value, list | tuple):
        if len(value) > _MAX_CONSTRAINT_SEQUENCE_ITEMS:
            _invalid_request("Routing constraint sequence exceeds the bounded M1 item limit.")
        return tuple(_normalize_constraint_value(item, depth=depth - 1) for item in value)
    _invalid_request("Routing constraints contain unsupported value types.")


def _decision_to_record(decision: RoutingDecisionRecord) -> PersistenceRecord:
    return PersistenceRecord(
        PersistenceRecordKind.ROUTING_DECISION,
        str(decision.decision_id),
        decision.to_json_compatible(),
    )


def _record_to_decision(record: PersistenceRecord, *, operation: str) -> RoutingDecisionRecord:
    if record.kind is not PersistenceRecordKind.ROUTING_DECISION:
        _raise_routing_error(_corrupt_record(operation))
    try:
        return RoutingDecisionRecord.from_json_compatible(record.payload)
    except Exception:
        _raise_routing_error(_corrupt_record(operation))


def _record_version(record: PersistenceRecord) -> str:
    encoded = json.dumps(
        record.payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _translate_persistence_error(
    exc: PersistenceError,
    *,
    operation: str,
) -> RoutingDecisionError:
    if exc.code is PersistenceErrorCode.CONFLICT:
        return RoutingDecisionError(
            RoutingDecisionErrorCode.CONFLICT,
            "Routing decision record conflicts with existing state.",
            retryable=False,
            operation=operation,
        )
    return RoutingDecisionError(
        RoutingDecisionErrorCode.PERSISTENCE_FAILURE,
        "Routing decision persistence operation failed.",
        retryable=exc.retryable,
        operation=operation,
    )


def _corrupt_record(operation: str) -> RoutingDecisionError:
    return RoutingDecisionError(
        RoutingDecisionErrorCode.CORRUPT_RECORD,
        "Persisted routing decision record did not decode as RoutingDecisionRecord.",
        retryable=False,
        operation=operation,
    )


def _invalid_candidate(message: str) -> NoReturn:
    _raise_routing_error(
        RoutingDecisionError(
            RoutingDecisionErrorCode.INVALID_CANDIDATE,
            message,
            retryable=False,
            operation="construct_candidate",
        )
    )


def _invalid_request(message: str) -> NoReturn:
    _raise_routing_error(
        RoutingDecisionError(
            RoutingDecisionErrorCode.INVALID_REQUEST,
            message,
            retryable=False,
            operation="construct_request",
        )
    )


def _invalid_constraint(message: str) -> NoReturn:
    _raise_routing_error(
        RoutingDecisionError(
            RoutingDecisionErrorCode.INVALID_CONSTRAINT,
            message,
            retryable=False,
            operation="construct_request",
        )
    )


def _require_ref_kind(
    reference: ObjectReference,
    kind: ReferenceKind,
    field_name: str,
) -> ObjectReference:
    if not isinstance(reference, ObjectReference):
        msg = f"{field_name} must be an ObjectReference"
        raise TypeError(msg)
    if reference.kind is not kind:
        msg = f"{field_name} must reference {kind.value} objects"
        raise TypeError(msg)
    return reference


def _work_id(reference: ObjectReference) -> WorkId:
    _require_ref_kind(reference, ReferenceKind.WORK, "work_ref")
    if not isinstance(reference.ref_id, WorkId):
        msg = "work references must contain WorkId values"
        raise TypeError(msg)
    return reference.ref_id


def _safe_token(value: object, field_name: str) -> str:
    text = _require_str(value, field_name).strip()
    if not _SAFE_TOKEN_RE.fullmatch(text):
        msg = f"{field_name} must be a bounded snake_case token"
        raise ValueError(msg)
    _reject_secret_text(text, field_name)
    return text


def _safe_text(value: object, field_name: str) -> str:
    text = _require_str(value, field_name).strip()
    _reject_secret_text(text, field_name)
    if not text or len(text) > _MAX_STRING_LENGTH or not _SAFE_VALUE_RE.fullmatch(text):
        msg = f"{field_name} must be bounded safe text"
        raise ValueError(msg)
    return text


def _safe_message(value: object, field_name: str) -> str:
    text = _require_str(value, field_name).strip()
    _reject_secret_text(text, field_name)
    if not text or len(text) > _MAX_STRING_LENGTH or not _SAFE_MESSAGE_RE.fullmatch(text):
        msg = f"{field_name} must be bounded safe text"
        raise ValueError(msg)
    return text


def _candidate_token(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not normalized:
        _invalid_candidate("Model profile candidate keys require a safe model identity.")
    return normalized[:64]


def _reject_secret_text(value: str, field_name: str) -> None:
    if (
        _SECRET_TOKEN_RE.search(field_name)
        or _SECRET_TOKEN_RE.search(value)
        or _SECRET_VALUE_RE.search(value)
    ):
        _raise_routing_error(
            RoutingDecisionError(
                RoutingDecisionErrorCode.INVALID_REQUEST,
                "Routing decisions cannot contain sensitive text.",
                retryable=False,
                operation="construct_request",
            )
        )


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value


def _optional_str(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_str(value, field_name)


def _required_sequence(value: object, field_name: str) -> tuple[object, ...]:
    if not isinstance(value, list | tuple):
        msg = f"{field_name} must be a list"
        raise TypeError(msg)
    return tuple(value)


def _optional_sequence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if not isinstance(value, list | tuple):
        msg = "optional sequence must be a list"
        raise TypeError(msg)
    return tuple(value)


def _optional_mapping(value: object, field_name: str) -> Mapping[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        msg = f"{field_name} must be an object when provided"
        raise TypeError(msg)
    return value


def _raise_routing_error(error: RoutingDecisionError) -> NoReturn:
    raise error from None
