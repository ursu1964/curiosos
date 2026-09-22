"""SQLAlchemy-backed PostgreSQL provider boundary.

This module keeps PostgreSQL and SQLAlchemy objects inside the provider
package. It exposes frozen Curios contract objects at the core-facing boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self

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
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import SQLAlchemyError

POSTGRES_PROVIDER_ID = ProviderId("prv_00000000000000000000000019")
POSTGRES_PROVIDER_DESCRIPTOR = ProviderDescriptor(
    provider_id=POSTGRES_PROVIDER_ID,
    provider_type=ProviderType.DATABASE,
    version=SchemaVersion(0, 1, 0),
    declared_capability_ids=(),
    status=ProviderStatus.UNKNOWN,
    implementation_metadata={
        "database": "postgresql",
        "driver": "psycopg",
        "sqlalchemy": "2.x",
    },
)

_READINESS_SQL = text(
    """
    select
      current_database() as database_name,
      current_user as database_user,
      current_setting('server_version') as server_version,
      not pg_is_in_recovery() as accepts_writes
    """
)


@dataclass(frozen=True, slots=True)
class PostgresProviderConfig:
    """Implementation-local SQLAlchemy connection configuration."""

    sqlalchemy_url: str = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.sqlalchemy_url, str):
            msg = "sqlalchemy_url must be a string"
            raise TypeError(msg)
        parsed = make_url(self.sqlalchemy_url)
        if parsed.get_backend_name() != "postgresql":
            msg = "sqlalchemy_url must target PostgreSQL"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PostgresReadiness:
    """Implementation-local readiness fact returned by the provider boundary."""

    database_name: str
    database_user: str
    server_version: str
    accepts_writes: bool

    @classmethod
    def from_row_mapping(cls, row: Any) -> Self:
        """Create readiness facts from a SQLAlchemy row mapping."""
        return cls(
            database_name=_require_str(row["database_name"], "database_name"),
            database_user=_require_str(row["database_user"], "database_user"),
            server_version=_require_str(row["server_version"], "server_version"),
            accepts_writes=_require_bool(row["accepts_writes"], "accepts_writes"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return a non-secret JSON-compatible provider readiness summary."""
        return {
            "database_name": self.database_name,
            "database_user": self.database_user,
            "server_version": self.server_version,
            "accepts_writes": self.accepts_writes,
        }


class PostgresProvider:
    """PostgreSQL implementation of the core provider catalog boundary."""

    def __init__(
        self,
        config: PostgresProviderConfig | None = None,
        *,
        engine: Engine | None = None,
        descriptor: ProviderDescriptor = POSTGRES_PROVIDER_DESCRIPTOR,
    ) -> None:
        if config is not None and engine is not None:
            msg = "provide config or engine, not both"
            raise ValueError(msg)
        if not isinstance(descriptor, ProviderDescriptor):
            msg = "descriptor must be a ProviderDescriptor"
            raise TypeError(msg)
        self._descriptor = descriptor
        self._engine = engine if engine is not None else _create_engine(config)

    @classmethod
    def from_sqlalchemy_url(cls, sqlalchemy_url: str) -> Self:
        """Create a provider from an implementation-local SQLAlchemy URL."""
        return cls(PostgresProviderConfig(sqlalchemy_url=sqlalchemy_url))

    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        """Return the PostgreSQL provider descriptor without selecting work."""
        _require_context(context)
        return Result.success((self._descriptor,))

    def check_readiness(self, context: CoreContext) -> Result[PostgresReadiness]:
        """Verify basic PostgreSQL connectivity through SQLAlchemy."""
        _require_context(context)
        if self._engine is None:
            return Result.failure(
                (
                    _contract_error(
                        code="POSTGRES_PROVIDER_NOT_CONFIGURED",
                        message="PostgreSQL provider is not configured.",
                        retryable=False,
                        context=context,
                    ),
                )
            )

        try:
            with self._engine.connect() as connection:
                row = connection.execute(_READINESS_SQL).mappings().one()
        except SQLAlchemyError as exc:
            return Result.failure(
                (
                    _contract_error(
                        code="POSTGRES_PROVIDER_UNAVAILABLE",
                        message="PostgreSQL readiness check failed.",
                        retryable=True,
                        context=context,
                        exception=exc,
                    ),
                )
            )

        return Result.success(PostgresReadiness.from_row_mapping(row))

    def dispose(self) -> None:
        """Release provider-owned SQLAlchemy connection resources."""
        if self._engine is not None:
            self._engine.dispose()


def _create_engine(config: PostgresProviderConfig | None) -> Engine | None:
    if config is None:
        return None
    return create_engine(config.sqlalchemy_url, future=True, pool_pre_ping=True)


def _contract_error(
    *,
    code: str,
    message: str,
    retryable: bool,
    context: CoreContext,
    exception: SQLAlchemyError | None = None,
) -> ContractError:
    details: dict[str, object] = {"operation": "postgres_readiness"}
    if exception is not None:
        details["exception_type"] = type(exception).__name__
    return ContractError(
        error_code=ErrorCode(code),
        message=message,
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.ERROR,
        retryable=retryable,
        trace_id=context.observability.trace_id,
        details=details,
    )


def _require_context(context: CoreContext) -> None:
    if not isinstance(context, CoreContext):
        msg = "context must be a CoreContext"
        raise TypeError(msg)


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a bool"
        raise TypeError(msg)
    return value
