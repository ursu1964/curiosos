from __future__ import annotations

import pytest
from curios_contracts import (
    ErrorCategory,
    ProviderDescriptor,
    ProviderStatus,
    ProviderType,
    ResultStatus,
)
from curios_core import CoreContext, ProviderCatalog
from curios_postgres_provider import (
    POSTGRES_PROVIDER_DESCRIPTOR,
    POSTGRES_PROVIDER_ID,
    PostgresProvider,
    PostgresProviderConfig,
    PostgresReadiness,
)


def test_postgres_provider_is_a_core_provider_catalog() -> None:
    provider = PostgresProvider()

    result = provider.list_provider_descriptors(CoreContext())

    assert isinstance(provider, ProviderCatalog)
    assert result.status is ResultStatus.SUCCESS
    assert result.value is not None
    assert result.value == (POSTGRES_PROVIDER_DESCRIPTOR,)
    assert result.value[0].provider_id == POSTGRES_PROVIDER_ID
    assert result.value[0].provider_type is ProviderType.DATABASE
    assert result.value[0].status is ProviderStatus.UNKNOWN
    assert result.value[0].declared_capability_ids == ()


def test_postgres_provider_does_not_configure_database_until_given_engine_or_config() -> None:
    result = PostgresProvider().check_readiness(CoreContext())

    assert result.status is ResultStatus.FAILURE
    assert result.errors[0].error_code == "POSTGRES_PROVIDER_NOT_CONFIGURED"
    assert result.errors[0].category is ErrorCategory.DEPENDENCY
    assert result.errors[0].details == {"operation": "postgres_readiness"}


def test_postgres_provider_requires_core_context() -> None:
    provider = PostgresProvider()

    with pytest.raises(TypeError, match="context must be a CoreContext"):
        provider.list_provider_descriptors(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="context must be a CoreContext"):
        provider.check_readiness(object())  # type: ignore[arg-type]


def test_postgres_provider_config_accepts_only_postgresql_sqlalchemy_urls() -> None:
    config = PostgresProviderConfig(
        sqlalchemy_url="postgresql+psycopg://curios@127.0.0.1:5432/curios_dev"
    )

    assert "curios_dev" in config.sqlalchemy_url
    with pytest.raises(ValueError, match="must target PostgreSQL"):
        PostgresProviderConfig(sqlalchemy_url="sqlite+pysqlite:///:memory:")


def test_postgres_readiness_is_non_secret_json_compatible_summary() -> None:
    readiness = PostgresReadiness(
        database_name="curios_dev",
        database_user="curios_dev",
        server_version="18.0",
        accepts_writes=True,
    )

    assert readiness.to_json_compatible() == {
        "database_name": "curios_dev",
        "database_user": "curios_dev",
        "server_version": "18.0",
        "accepts_writes": True,
    }


def test_postgres_descriptor_remains_canonical_contract_object() -> None:
    assert isinstance(POSTGRES_PROVIDER_DESCRIPTOR, ProviderDescriptor)
    assert POSTGRES_PROVIDER_DESCRIPTOR.implementation_metadata == {
        "database": "postgresql",
        "driver": "psycopg",
        "sqlalchemy": "2.x",
    }
