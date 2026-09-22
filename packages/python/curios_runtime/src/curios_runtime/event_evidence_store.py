"""TASK-M0-004 event/evidence runtime store.

This module owns runtime-store semantics above ``curios_persistence``. It
persists and rereads canonical contracts while keeping persistence records,
database rows, and SQLAlchemy/PostgreSQL details behind the persistence
boundary.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from enum import StrEnum
from typing import NoReturn, Protocol

from curios_contracts import (
    EventEnvelope,
    EventId,
    EvidenceId,
    EvidenceReference,
    VerificationId,
    VerificationReference,
)
from curios_persistence import (
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
    canonical_to_record,
    record_to_canonical,
)

_DEFAULT_LIST_LIMIT = 100
_MAX_LIST_LIMIT = 1000


class RuntimeStoreErrorCode(StrEnum):
    """Stable TASK-M0-004 runtime-store failure categories."""

    CONFLICT = "CONFLICT"
    CORRUPT_RECORD = "CORRUPT_RECORD"
    NOT_FOUND = "NOT_FOUND"
    PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE"


class RuntimeStoreError(RuntimeError):
    """Curios-owned runtime-store failure without persistence-native leakage."""

    def __init__(
        self,
        code: RuntimeStoreErrorCode,
        message: str,
        *,
        operation: str,
        retryable: bool = False,
        detail: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = RuntimeStoreErrorCode(code)
        self.operation = operation
        self.retryable = retryable
        self.detail = dict(detail or {})

    def to_json_compatible(self) -> dict[str, object]:
        """Return bounded, non-native runtime-store error details."""
        serialized: dict[str, object] = {
            "code": self.code.value,
            "message": str(self),
            "operation": self.operation,
            "retryable": self.retryable,
        }
        if self.detail:
            serialized["detail"] = dict(self.detail)
        return serialized


@dataclass(frozen=True, slots=True)
class EventEvidenceRuntimeStore:
    """Runtime-facing event/evidence store backed by persistence primitives."""

    persistence_store: _PersistenceStore

    def append_event(self, event: EventEnvelope) -> EventEnvelope:
        """Persist one canonical event and return the accepted canonical value."""
        if not isinstance(event, EventEnvelope):
            msg = "event must be an EventEnvelope"
            raise TypeError(msg)
        self._insert(event, operation="append_event")
        return event

    def get_event(self, event_id: EventId) -> EventEnvelope | None:
        """Read one canonical event by identity, returning ``None`` when absent."""
        _require_id(event_id, EventId, "event_id")
        record = self._read(PersistenceRecordKind.EVENT, str(event_id), operation="get_event")
        if record is None:
            return None
        event = _event_from_record(record, operation="get_event")
        if event.event_id != event_id:
            _raise_corrupt("get_event", "event record identity does not match requested ID")
        return event

    def require_event(self, event_id: EventId) -> EventEnvelope:
        """Read one event and raise a Curios-owned not-found error when absent."""
        event = self.get_event(event_id)
        if event is None:
            _raise_not_found("require_event", "event", str(event_id))
        return event

    def list_events(self, *, limit: int = _DEFAULT_LIST_LIMIT) -> tuple[EventEnvelope, ...]:
        """List stored events in deterministic persistence append order."""
        return tuple(
            _event_from_record(record, operation="list_events")
            for record in self._list(
                PersistenceRecordKind.EVENT,
                limit=limit,
                operation="list_events",
            )
        )

    def append_evidence(self, evidence: EvidenceReference) -> EvidenceReference:
        """Persist one canonical evidence reference."""
        if not isinstance(evidence, EvidenceReference):
            msg = "evidence must be an EvidenceReference"
            raise TypeError(msg)
        self._insert(evidence, operation="append_evidence")
        return evidence

    def get_evidence(self, evidence_id: EvidenceId) -> EvidenceReference | None:
        """Read one canonical evidence reference by identity."""
        _require_id(evidence_id, EvidenceId, "evidence_id")
        record = self._read(
            PersistenceRecordKind.EVIDENCE,
            str(evidence_id),
            operation="get_evidence",
        )
        if record is None:
            return None
        evidence = _evidence_from_record(record, operation="get_evidence")
        if evidence.evidence_id != evidence_id:
            _raise_corrupt("get_evidence", "evidence record identity does not match requested ID")
        return evidence

    def require_evidence(self, evidence_id: EvidenceId) -> EvidenceReference:
        """Read one evidence reference and raise when absent."""
        evidence = self.get_evidence(evidence_id)
        if evidence is None:
            _raise_not_found("require_evidence", "evidence", str(evidence_id))
        return evidence

    def list_evidence(
        self,
        *,
        limit: int = _DEFAULT_LIST_LIMIT,
    ) -> tuple[EvidenceReference, ...]:
        """List stored evidence references in deterministic persistence append order."""
        return tuple(
            _evidence_from_record(record, operation="list_evidence")
            for record in self._list(
                PersistenceRecordKind.EVIDENCE,
                limit=limit,
                operation="list_evidence",
            )
        )

    def append_verification(
        self,
        verification: VerificationReference,
    ) -> VerificationReference:
        """Persist one canonical verification reference without evaluating it."""
        if not isinstance(verification, VerificationReference):
            msg = "verification must be a VerificationReference"
            raise TypeError(msg)
        self._insert(verification, operation="append_verification")
        return verification

    def get_verification(self, verification_id: VerificationId) -> VerificationReference | None:
        """Read one canonical verification reference by identity."""
        _require_id(verification_id, VerificationId, "verification_id")
        record = self._read(
            PersistenceRecordKind.VERIFICATION,
            str(verification_id),
            operation="get_verification",
        )
        if record is None:
            return None
        verification = _verification_from_record(record, operation="get_verification")
        if verification.verification_id != verification_id:
            _raise_corrupt(
                "get_verification",
                "verification record identity does not match requested ID",
            )
        return verification

    def require_verification(self, verification_id: VerificationId) -> VerificationReference:
        """Read one verification reference and raise when absent."""
        verification = self.get_verification(verification_id)
        if verification is None:
            _raise_not_found("require_verification", "verification", str(verification_id))
        return verification

    def list_verifications(
        self,
        *,
        limit: int = _DEFAULT_LIST_LIMIT,
    ) -> tuple[VerificationReference, ...]:
        """List stored verification references in deterministic persistence append order."""
        return tuple(
            _verification_from_record(record, operation="list_verifications")
            for record in self._list(
                PersistenceRecordKind.VERIFICATION,
                limit=limit,
                operation="list_verifications",
            )
        )

    def _insert(self, canonical: object, *, operation: str) -> None:
        record = canonical_to_record(canonical)
        error: RuntimeStoreError | None = None
        try:
            with self.persistence_store.transaction() as transaction:
                transaction.insert_record(record)
        except PersistenceError as exc:
            error = _runtime_error_from_persistence(exc, operation=operation)
        if error is not None:
            raise error

    def _read(
        self,
        kind: PersistenceRecordKind,
        record_id: str,
        *,
        operation: str,
    ) -> PersistenceRecord | None:
        error: RuntimeStoreError | None = None
        try:
            with self.persistence_store.transaction() as transaction:
                return transaction.read_record(kind, record_id)
        except PersistenceError as exc:
            error = _runtime_error_from_persistence(exc, operation=operation)
        if error is not None:
            raise error

    def _list(
        self,
        kind: PersistenceRecordKind,
        *,
        limit: int,
        operation: str,
    ) -> tuple[PersistenceRecord, ...]:
        _validate_limit(limit)
        error: RuntimeStoreError | None = None
        try:
            with self.persistence_store.transaction() as transaction:
                return transaction.list_records(kind, limit=limit)
        except PersistenceError as exc:
            error = _runtime_error_from_persistence(exc, operation=operation)
        if error is not None:
            raise error


class _PersistenceTransaction(Protocol):
    def insert_record(self, record: PersistenceRecord) -> None: ...

    def read_record(
        self,
        kind: PersistenceRecordKind,
        record_id: str,
    ) -> PersistenceRecord | None: ...

    def list_records(
        self,
        kind: PersistenceRecordKind,
        *,
        limit: int,
    ) -> tuple[PersistenceRecord, ...]: ...


class _PersistenceStore(Protocol):
    def transaction(self) -> AbstractContextManager[_PersistenceTransaction]: ...


def _event_from_record(record: PersistenceRecord, *, operation: str) -> EventEnvelope:
    value = _canonical_from_record(record, PersistenceRecordKind.EVENT, operation=operation)
    if not isinstance(value, EventEnvelope):
        _raise_corrupt(operation, "event record did not decode to EventEnvelope")
    return value


def _evidence_from_record(record: PersistenceRecord, *, operation: str) -> EvidenceReference:
    value = _canonical_from_record(record, PersistenceRecordKind.EVIDENCE, operation=operation)
    if not isinstance(value, EvidenceReference):
        _raise_corrupt(operation, "evidence record did not decode to EvidenceReference")
    return value


def _verification_from_record(
    record: PersistenceRecord,
    *,
    operation: str,
) -> VerificationReference:
    value = _canonical_from_record(record, PersistenceRecordKind.VERIFICATION, operation=operation)
    if not isinstance(value, VerificationReference):
        _raise_corrupt(operation, "verification record did not decode to VerificationReference")
    return value


def _canonical_from_record(
    record: PersistenceRecord,
    expected_kind: PersistenceRecordKind,
    *,
    operation: str,
) -> object:
    if record.kind is not expected_kind:
        _raise_corrupt(operation, "persistence record kind did not match runtime-store request")
    value: object | None = None
    corrupt = False
    try:
        value = record_to_canonical(record)
    except KeyError, TypeError, ValueError:
        corrupt = True
    if corrupt:
        _raise_corrupt(operation, "persistence record payload is not canonical")
    return value


def _runtime_error_from_persistence(
    exc: PersistenceError,
    *,
    operation: str,
) -> RuntimeStoreError:
    if exc.code is PersistenceErrorCode.CONFLICT:
        return RuntimeStoreError(
            RuntimeStoreErrorCode.CONFLICT,
            "Runtime store record already exists.",
            operation=operation,
            retryable=False,
            detail={"persistence_code": exc.code.value},
        )
    if exc.code is PersistenceErrorCode.INTEGRITY:
        return RuntimeStoreError(
            RuntimeStoreErrorCode.CORRUPT_RECORD,
            "persistence record integrity check failed",
            operation=operation,
            retryable=False,
        )
    return RuntimeStoreError(
        RuntimeStoreErrorCode.PERSISTENCE_FAILURE,
        "Runtime store persistence operation failed.",
        operation=operation,
        retryable=exc.retryable,
        detail={"persistence_code": exc.code.value},
    )


def _raise_not_found(operation: str, record_kind: str, record_id: str) -> NoReturn:
    raise RuntimeStoreError(
        RuntimeStoreErrorCode.NOT_FOUND,
        f"Runtime store {record_kind} record was not found.",
        operation=operation,
        detail={"record_id": record_id, "record_kind": record_kind},
    )


def _raise_corrupt(operation: str, message: str) -> NoReturn:
    raise RuntimeStoreError(
        RuntimeStoreErrorCode.CORRUPT_RECORD,
        message,
        operation=operation,
        retryable=False,
    ) from None


def _validate_limit(limit: int) -> None:
    if not isinstance(limit, int):
        msg = "limit must be an int"
        raise TypeError(msg)
    if limit < 1 or limit > _MAX_LIST_LIMIT:
        msg = "limit must be between 1 and 1000"
        raise ValueError(msg)


def _require_id[IdT](value: object, expected_type: type[IdT], field_name: str) -> None:
    if not isinstance(value, expected_type):
        msg = f"{field_name} must be {expected_type.__name__}"
        raise TypeError(msg)
