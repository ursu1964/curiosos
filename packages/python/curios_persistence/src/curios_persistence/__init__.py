"""PostgreSQL-backed M0 persistence primitives.

SQLAlchemy, Alembic, driver objects, and database rows are implementation
details of this package. Public functions accept configuration and canonical
contract objects, then return persistence-local value objects.
"""

from curios_persistence.boundary import (
    PersistenceConfig,
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceStore,
    apply_schema_migrations,
    canonical_to_record,
    record_to_canonical,
)
from curios_persistence.kinds import PersistenceRecordKind

__version__ = "0.0.0"

__all__ = (
    "PersistenceConfig",
    "PersistenceError",
    "PersistenceErrorCode",
    "PersistenceRecord",
    "PersistenceRecordKind",
    "PersistenceStore",
    "__version__",
    "apply_schema_migrations",
    "canonical_to_record",
    "record_to_canonical",
)
