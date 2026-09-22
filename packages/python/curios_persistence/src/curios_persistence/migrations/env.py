"""Alembic environment for in-package M0 persistence migrations."""

from __future__ import annotations

from alembic import context
from curios_persistence.schema import m0_persistence_metadata
from sqlalchemy.schema import CreateSchema


def run_migrations_online() -> None:
    connection = context.config.attributes.get("connection")
    if connection is None:
        msg = "curios_persistence migrations require a supplied SQLAlchemy connection"
        raise RuntimeError(msg)

    schema = context.config.attributes.get("schema")
    if schema is not None:
        connection.execute(CreateSchema(schema, if_not_exists=True))

    context.configure(
        connection=connection,
        target_metadata=m0_persistence_metadata,
        version_table_schema=schema,
        include_schemas=schema is not None,
    )

    with context.begin_transaction():
        context.run_migrations()


run_migrations_online()
