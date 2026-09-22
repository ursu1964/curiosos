---
id: BOOT-VERIFY-PG-READINESS-001-EVIDENCE
title: BOOT-VERIFY-PG-READINESS-001 PostgreSQL Readiness Evidence
lifecycle: TESTED
artifact_type: verification_evidence
authority: evidence
subject_id: BOOT-VERIFY-PG-READINESS-001
related_task_id: TASK-BOOT-006
---

# BOOT-VERIFY-PG-READINESS-001 PostgreSQL Readiness Evidence

## Scope

This record covers the corrective verification for the deferred
`TASK-BOOT-006` `LOCAL_DOCKER` PostgreSQL readiness item.

The historical `TASK-BOOT-006` lifecycle status remains `VALIDATED, FROZEN`.
This evidence records a narrow corrective configuration change and live
readiness verification for the previously deferred Docker-daemon-dependent
check.

## Root Cause

The `postgres:18` image did not become healthy when the named volume was mounted
directly at:

```text
/var/lib/postgresql/data
```

Container diagnostics for PostgreSQL 18 indicated that the supported persistent
volume mount point is:

```text
/var/lib/postgresql
```

The existing named volume `curios-local-docker_postgres_data` was inspected
read-only before correction and did not contain visible persisted PostgreSQL
data requiring migration. The volume was not deleted.

## Corrective Change

Changed only the `postgres_data` mount target in
`infrastructure/local/docker/compose.yaml`:

```text
postgres_data:/var/lib/postgresql/data
```

to:

```text
postgres_data:/var/lib/postgresql
```

No PostgreSQL image version, service name, environment variable, port,
healthcheck, or additional service was changed.

## Verification

| Check | Result |
| --- | --- |
| `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet` | Passed. |
| Start only `postgres` with Docker Compose | Passed; container recreated and started. |
| Container health | Passed; `curios-local-docker-postgres-1` reached `healthy`. |
| PostgreSQL readiness | Passed; `pg_isready` reported accepting connections on `127.0.0.1:5432`. |
| Clean stop | Passed; `docker compose ... stop postgres` exited cleanly and container stopped with exit code 0. |
| Persistent named volume | Passed; `curios-local-docker_postgres_data` remained present after stop. |

## Persistence Safety

No destructive volume command was used.

The corrective verification did not run:

- `docker compose down -v`;
- `docker volume rm`;
- any equivalent destructive reset.

## Status Handling

This corrective record closes the previously deferred live PostgreSQL readiness
verification item. It does not rewrite the original `TASK-BOOT-006` history or
advance any later BOOT task.
