"""PostgreSQL provider implementation boundary."""

from curios_postgres_provider.boundary import (
    POSTGRES_PROVIDER_DESCRIPTOR,
    POSTGRES_PROVIDER_ID,
    PostgresProvider,
    PostgresProviderConfig,
    PostgresReadiness,
)

__version__ = "0.0.0"

__all__ = (
    "POSTGRES_PROVIDER_DESCRIPTOR",
    "POSTGRES_PROVIDER_ID",
    "PostgresProvider",
    "PostgresProviderConfig",
    "PostgresReadiness",
    "__version__",
)
