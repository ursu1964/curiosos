"""M0 PostgreSQL persistence boundary.

The boundary stores canonical Curios runtime records as typed IDs plus
JSON-compatible payloads. It intentionally does not implement work lifecycle
rules, event/evidence store semantics, or application repositories.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any, NoReturn, Self

from alembic import command
from alembic.config import Config
from curios_contracts import (
    ArtifactReference,
    EventEnvelope,
    EvidenceReference,
    ExecutionRecord,
    PolicyDecision,
    VerificationReference,
    WorkItem,
    to_json_compatible,
)
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError, SQLAlchemyError

from curios_persistence.kinds import PersistenceRecordKind
from curios_persistence.schema import TABLES_BY_RECORD_KIND, m0_persistence_metadata

_MIGRATIONS_PATH = Path(__file__).resolve().parent / "migrations"


class PersistenceErrorCode(StrEnum):
    """Stable persistence failure categories for deterministic translation."""

    CONFIGURATION = "CONFIGURATION"
    CONNECTIVITY = "CONNECTIVITY"
    CONFLICT = "CONFLICT"
    INTEGRITY = "INTEGRITY"
    SCHEMA = "SCHEMA"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PersistenceConfig:
    """Configuration for the M0 PostgreSQL persistence boundary."""

    sqlalchemy_url: str = field(repr=False)
    schema: str | None = None
    echo_sql: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.sqlalchemy_url, str):
            msg = "sqlalchemy_url must be a string"
            raise TypeError(msg)
        parsed = make_url(self.sqlalchemy_url)
        if parsed.get_backend_name() != "postgresql":
            msg = "sqlalchemy_url must target PostgreSQL"
            raise ValueError(msg)
        if self.schema is not None:
            _validate_schema_name(self.schema)


@dataclass(frozen=True, slots=True)
class PersistenceRecord:
    """A canonical record translated into persistence-owned primitive form."""

    kind: PersistenceRecordKind
    record_id: str
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", PersistenceRecordKind(self.kind))
        if not isinstance(self.record_id, str) or not self.record_id:
            msg = "record_id must be a non-empty string"
            raise ValueError(msg)
        if not isinstance(self.payload, Mapping):
            msg = "payload must be a JSON-compatible object"
            raise TypeError(msg)
        object.__setattr__(self, "payload", _json_mapping(self.payload))


class PersistenceError(RuntimeError):
    """Deterministic persistence failure independent of SQLAlchemy classes."""

    def __init__(
        self,
        code: PersistenceErrorCode,
        message: str,
        *,
        retryable: bool,
        operation: str,
        cause_type: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = PersistenceErrorCode(code)
        self.retryable = retryable
        self.operation = operation
        self.cause_type = cause_type

    def to_json_compatible(self) -> dict[str, object]:
        """Return a non-secret JSON-compatible failure summary."""
        return {
            "code": self.code.value,
            "message": str(self),
            "retryable": self.retryable,
            "operation": self.operation,
            "cause_type": self.cause_type,
        }


class PersistenceStore:
    """Transaction-scoped storage primitive for M0 runtime records."""

    def __init__(self, config: PersistenceConfig) -> None:
        if not isinstance(config, PersistenceConfig):
            msg = "config must be a PersistenceConfig"
            raise TypeError(msg)
        self._config = config
        self._engine = _create_engine(config)

    @classmethod
    def from_sqlalchemy_url(cls, sqlalchemy_url: str, *, schema: str | None = None) -> Self:
        """Create a persistence store from an implementation-local SQLAlchemy URL."""
        return cls(PersistenceConfig(sqlalchemy_url=sqlalchemy_url, schema=schema))

    def initialize(self) -> None:
        """Apply the in-package Alembic migrations for this store."""
        apply_schema_migrations(self._config)

    @contextmanager
    def transaction(self) -> Iterator[PersistenceTransaction]:
        """Open a database transaction for primitive persistence operations."""
        error: PersistenceError | None = None
        try:
            with self._engine.connect() as raw_connection:
                connection = _with_schema(raw_connection, self._config.schema)
                with connection.begin():
                    yield PersistenceTransaction(connection)
        except SQLAlchemyError as exc:
            error = _translate_error(exc, operation="transaction")
        if error is not None:
            _raise_persistence_error(error)

    def check_readiness(self) -> dict[str, object]:
        """Return a bounded readiness summary for connectivity and schema presence."""
        try:
            with self._engine.connect() as raw_connection:
                connection = _with_schema(raw_connection, self._config.schema)
                inspector = inspect(connection)
                expected = {table.name for table in m0_persistence_metadata.sorted_tables}
                existing = set(inspector.get_table_names(schema=self._config.schema))
        except SQLAlchemyError as exc:
            error = _translate_error(exc, operation="readiness")
        else:
            return {
                "database": "postgresql",
                "schema": self._config.schema,
                "ready": expected.issubset(existing),
                "tables": tuple(sorted(expected & existing)),
            }
        _raise_persistence_error(error)

    def dispose(self) -> None:
        """Release database resources owned by this store."""
        self._engine.dispose()


class PersistenceTransaction:
    """Primitive record operations bound to one database transaction."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def insert_record(self, record: PersistenceRecord) -> None:
        """Insert one translated canonical record without repository semantics."""
        table = TABLES_BY_RECORD_KIND[record.kind]
        payload = dict(record.payload)
        statement = table.insert().values(
            canonical_id=record.record_id,
            payload=payload,
            payload_sha256=_payload_sha256(payload),
        )
        try:
            self._connection.execute(statement)
        except SQLAlchemyError as exc:
            error = _translate_error(exc, operation=f"insert_{record.kind.value}")
        else:
            return
        _raise_persistence_error(error)

    def read_record(
        self,
        kind: PersistenceRecordKind,
        record_id: str,
    ) -> PersistenceRecord | None:
        """Read one primitive record by kind and canonical ID."""
        kind = PersistenceRecordKind(kind)
        table = TABLES_BY_RECORD_KIND[kind]
        statement = select(table.c.canonical_id, table.c.payload, table.c.payload_sha256).where(
            table.c.canonical_id == record_id
        )
        try:
            row = self._connection.execute(statement).mappings().one_or_none()
        except SQLAlchemyError as exc:
            error = _translate_error(exc, operation=f"read_{kind.value}")
        else:
            if row is None:
                return None
            payload = _require_mapping(row["payload"], "payload")
            _verify_payload_hash(
                payload=payload,
                payload_sha256=_require_str(row["payload_sha256"], "payload_sha256"),
                operation=f"read_{kind.value}",
            )
            return PersistenceRecord(
                kind=kind,
                record_id=_require_str(row["canonical_id"], "canonical_id"),
                payload=payload,
            )
        _raise_persistence_error(error)

    def list_records(
        self,
        kind: PersistenceRecordKind,
        *,
        limit: int,
    ) -> tuple[PersistenceRecord, ...]:
        """List primitive records deterministically within a bounded limit."""
        kind = PersistenceRecordKind(kind)
        if not isinstance(limit, int):
            msg = "limit must be an int"
            raise TypeError(msg)
        if limit < 1 or limit > 1000:
            msg = "limit must be between 1 and 1000"
            raise ValueError(msg)
        table = TABLES_BY_RECORD_KIND[kind]
        statement = (
            select(table.c.canonical_id, table.c.payload, table.c.payload_sha256)
            .order_by(table.c.append_ordinal.asc())
            .limit(limit)
        )
        try:
            rows = tuple(self._connection.execute(statement).mappings())
        except SQLAlchemyError as exc:
            error = _translate_error(exc, operation=f"list_{kind.value}")
        else:
            records: list[PersistenceRecord] = []
            for row in rows:
                payload = _require_mapping(row["payload"], "payload")
                _verify_payload_hash(
                    payload=payload,
                    payload_sha256=_require_str(row["payload_sha256"], "payload_sha256"),
                    operation=f"list_{kind.value}",
                )
                records.append(
                    PersistenceRecord(
                        kind=kind,
                        record_id=_require_str(row["canonical_id"], "canonical_id"),
                        payload=payload,
                    )
                )
            return tuple(records)
        _raise_persistence_error(error)

    def replace_record(self, record: PersistenceRecord, *, expected_payload_sha256: str) -> None:
        """Replace one primitive record when its stored payload hash still matches.

        The payload hash is a persistence-local version token. Repositories use
        it for optimistic concurrency without exposing database-native details.
        """
        if not _is_payload_sha256(expected_payload_sha256):
            msg = "expected_payload_sha256 must be a SHA-256 hex digest"
            raise ValueError(msg)
        table = TABLES_BY_RECORD_KIND[record.kind]
        payload = dict(record.payload)
        statement = (
            table.update()
            .where(table.c.canonical_id == record.record_id)
            .where(table.c.payload_sha256 == expected_payload_sha256)
            .values(
                payload=payload,
                payload_sha256=_payload_sha256(payload),
                updated_at=func.now(),
            )
        )
        try:
            result = self._connection.execute(statement)
        except SQLAlchemyError as exc:
            error = _translate_error(exc, operation=f"replace_{record.kind.value}")
        else:
            if result.rowcount == 1:
                return
            error = PersistenceError(
                PersistenceErrorCode.CONFLICT,
                "Persistence record version conflicts with existing state.",
                retryable=False,
                operation=f"replace_{record.kind.value}",
                cause_type=None,
            )
        _raise_persistence_error(error)

    def count_records(self, kind: PersistenceRecordKind) -> int:
        """Count stored records for one primitive kind."""
        kind = PersistenceRecordKind(kind)
        table = TABLES_BY_RECORD_KIND[kind]
        try:
            count = len(tuple(self._connection.execute(select(table.c.canonical_id))))
        except SQLAlchemyError as exc:
            error = _translate_error(exc, operation=f"count_{kind.value}")
        else:
            return count
        _raise_persistence_error(error)


def canonical_to_record(value: object) -> PersistenceRecord:
    """Translate a canonical Curios object to a persistence primitive record."""
    match value:
        case WorkItem():
            return _record(
                PersistenceRecordKind.WORK, str(value.work_id), value.to_json_compatible()
            )
        case ExecutionRecord():
            return _record(
                PersistenceRecordKind.EXECUTION,
                str(value.execution_id),
                value.to_json_compatible(),
            )
        case EventEnvelope():
            return _record(PersistenceRecordKind.EVENT, str(value.event_id), value.to_json())
        case EvidenceReference():
            return _record(
                PersistenceRecordKind.EVIDENCE,
                str(value.evidence_id),
                value.to_json_compatible(),
            )
        case ArtifactReference():
            return _record(
                PersistenceRecordKind.ARTIFACT,
                str(value.artifact_id),
                value.to_json_compatible(),
            )
        case PolicyDecision():
            if value.decision_id is None:
                msg = "PolicyDecision persistence requires decision_id"
                raise ValueError(msg)
            return _record(
                PersistenceRecordKind.POLICY_DECISION,
                value.decision_id,
                value.to_json_compatible(),
            )
        case VerificationReference():
            return _record(
                PersistenceRecordKind.VERIFICATION,
                str(value.verification_id),
                value.to_json_compatible(),
            )
        case _:
            msg = f"unsupported canonical record type {type(value).__name__}"
            raise TypeError(msg)


def record_to_canonical(record: PersistenceRecord) -> object:
    """Translate a persistence primitive record back to its canonical object."""
    match record.kind:
        case PersistenceRecordKind.WORK:
            return WorkItem.from_json_compatible(record.payload)
        case PersistenceRecordKind.EXECUTION:
            return ExecutionRecord.from_json_compatible(record.payload)
        case PersistenceRecordKind.EVENT:
            return EventEnvelope.from_json(record.payload)
        case PersistenceRecordKind.EVIDENCE:
            return EvidenceReference.from_json_compatible(record.payload)
        case PersistenceRecordKind.ARTIFACT:
            return ArtifactReference.from_json_compatible(record.payload)
        case PersistenceRecordKind.POLICY_DECISION:
            return PolicyDecision.from_json_compatible(record.payload)
        case PersistenceRecordKind.VERIFICATION:
            return VerificationReference.from_json_compatible(record.payload)
        case PersistenceRecordKind.WORK_DAG:
            msg = "work_dag records are decoded by the M1 DAG package"
            raise TypeError(msg)


def apply_schema_migrations(config: PersistenceConfig, *, revision: str = "head") -> None:
    """Apply the in-package Alembic schema migrations.

    This is the M0 local-runtime migration hook, not a production migration
    platform. The optional schema is intended for isolated local test state.
    """
    if not isinstance(config, PersistenceConfig):
        msg = "config must be a PersistenceConfig"
        raise TypeError(msg)
    engine: Engine | None = None
    error: PersistenceError | None = None
    try:
        engine = _create_engine(config)
        with engine.begin() as raw_connection:
            connection = _with_schema(raw_connection, config.schema)
            alembic_config = Config()
            alembic_config.set_main_option("script_location", _MIGRATIONS_PATH.as_posix())
            alembic_config.attributes["connection"] = connection
            alembic_config.attributes["schema"] = config.schema
            if revision == "base" or revision.startswith("-"):
                command.downgrade(alembic_config, revision)
            else:
                command.upgrade(alembic_config, revision)
    except SQLAlchemyError as exc:
        error = _translate_error(exc, operation="schema_migration")
    finally:
        if engine is not None:
            engine.dispose()
    if error is not None:
        _raise_persistence_error(error)


def _create_engine(config: PersistenceConfig) -> Engine:
    return create_engine(
        config.sqlalchemy_url, future=True, pool_pre_ping=True, echo=config.echo_sql
    )


def _with_schema(connection: Connection, schema: str | None) -> Connection:
    if schema is None:
        return connection
    return connection.execution_options(schema_translate_map={None: schema})


def _record(
    kind: PersistenceRecordKind,
    record_id: str,
    payload: Mapping[str, object],
) -> PersistenceRecord:
    return PersistenceRecord(kind=kind, record_id=record_id, payload=payload)


def _json_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    compatible = to_json_compatible(value)
    if not isinstance(compatible, dict):
        msg = "payload must serialize to a JSON object"
        raise TypeError(msg)
    json.dumps(compatible, allow_nan=False, sort_keys=True)
    return compatible


def _payload_sha256(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    return sha256(encoded).hexdigest()


def _verify_payload_hash(
    *,
    payload: Mapping[str, object],
    payload_sha256: str,
    operation: str,
) -> None:
    if _payload_sha256(payload) == payload_sha256:
        return
    error = PersistenceError(
        PersistenceErrorCode.INTEGRITY,
        "Persistence record payload hash does not match stored payload.",
        retryable=False,
        operation=operation,
    )
    _raise_persistence_error(error)


def _is_payload_sha256(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _translate_error(exc: SQLAlchemyError, *, operation: str) -> PersistenceError:
    if isinstance(exc, IntegrityError):
        return PersistenceError(
            PersistenceErrorCode.CONFLICT,
            "Persistence record conflicts with existing state.",
            retryable=False,
            operation=operation,
            cause_type=type(exc).__name__,
        )
    if isinstance(exc, OperationalError):
        return PersistenceError(
            PersistenceErrorCode.CONNECTIVITY,
            "PostgreSQL persistence operation failed due to connectivity.",
            retryable=True,
            operation=operation,
            cause_type=type(exc).__name__,
        )
    if isinstance(exc, ProgrammingError):
        return PersistenceError(
            PersistenceErrorCode.SCHEMA,
            "PostgreSQL persistence schema is not initialized or is incompatible.",
            retryable=False,
            operation=operation,
            cause_type=type(exc).__name__,
        )
    return PersistenceError(
        PersistenceErrorCode.UNKNOWN,
        "PostgreSQL persistence operation failed.",
        retryable=False,
        operation=operation,
        cause_type=type(exc).__name__,
    )


def _raise_persistence_error(error: PersistenceError) -> NoReturn:
    raise error


def _validate_schema_name(schema: str) -> None:
    if not schema or not schema.replace("_", "").isalnum() or schema[0].isdigit():
        msg = "schema must be a simple PostgreSQL identifier"
        raise ValueError(msg)


def _require_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        msg = f"{field_name} must be an object"
        raise TypeError(msg)
    return value


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value
