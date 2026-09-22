---
id: TASK-M0-005-VALIDATION-EVIDENCE
title: TASK-M0-005 Independent Revalidation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M0-005
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-005 Independent Revalidation Evidence

## Decision

TASK-M0-005 REVALIDATION: PASS

Validated candidate:

`ac96aca82742146dd31c258dfaace3c40ae33fc0`

Implementation commit:

`595f9d868136df78c81d946b729463ec87073441`

Corrective commit:

`ac96aca82742146dd31c258dfaace3c40ae33fc0`

## Previous Defect Revalidation

Previous validation failed because corrupt persisted canonical payloads could
escape `M0WorkRepository` read and transition paths as raw canonical parser
exceptions, including `KeyError`.

Revalidation adversarially exercised corrupt persisted `WORK` and `EXECUTION`
records through:

- `read_work`;
- `transition_work`;
- `read_execution`;
- `transition_execution`.

Representative corruptions included missing required canonical fields, invalid
state enum values, malformed canonical structures, invalid timestamps, and
invalid sequence/reference shapes.

All public paths produced bounded `RepositoryError(PERSISTENCE_FAILURE)` values.
No raw `KeyError`, `ValueError`, contract parser object, `PersistenceError`,
SQLAlchemy exception, psycopg exception, persisted payload, SQL, URL,
credential, or native traceback/detail was exposed through the repository
public API.

For corrupt-payload translations, revalidation confirmed:

- `__cause__ is None`;
- `__context__ is None`;
- `__suppress_context__ is True`;
- operation metadata remains bounded as `read_work`, `transition_work`,
  `read_execution`, or `transition_execution`.

## Repository API

Revalidation accepted:

- `create_work`;
- `read_work`;
- `transition_work`;
- `create_execution`;
- `read_execution`;
- `transition_execution`.

Canonical `WorkItem` and `ExecutionRecord` objects remain authoritative.
Persistence records, payload hashes, SQLAlchemy rows, and PostgreSQL details
remain internal implementation details.

## State Transition Model

Work transitions:

| Source | Allowed target states |
| --- | --- |
| `CREATED` | `READY`, `CANCELLED` |
| `READY` | `RUNNING`, `CANCELLED` |
| `RUNNING` | `WAITING`, `COMPLETED`, `FAILED`, `CANCELLED` |
| `WAITING` | `RUNNING`, `FAILED`, `CANCELLED` |
| `COMPLETED` | none |
| `FAILED` | none |
| `CANCELLED` | none |

Execution transitions:

| Source | Allowed target states |
| --- | --- |
| `CREATED` | `RUNNING`, `CANCELLED` |
| `RUNNING` | `WAITING`, `SUCCEEDED`, `FAILED`, `CANCELLED` |
| `WAITING` | `RUNNING`, `FAILED`, `CANCELLED` |
| `SUCCEEDED` | none |
| `FAILED` | none |
| `CANCELLED` | none |

No missing legal transition or extra unauthorized transition was found.
Terminal states have no outgoing transitions. Same-state transitions are
deterministic and idempotent.

## Concurrency And Persistence

Revalidation accepted use of the persistence payload SHA-256 as the
expected-version token.

Verified behavior:

- stale expected versions produce `RepositoryError(CONFLICT)`;
- replacement is optimistic and version-checked;
- lost updates are blocked;
- same-state transitions return the current stored record and do not replace;
- missing transition targets produce `RepositoryError(NOT_FOUND)`;
- wrong canonical record kinds and corrupt payloads produce bounded
  `RepositoryError(PERSISTENCE_FAILURE)`;
- repository reconstruction against PostgreSQL preserves final canonical
  work/execution state without hidden in-memory authority.

`PersistenceTransaction.replace_record(...)` remains classified as a compatible
generic persistence primitive: it is generic over `PersistenceRecordKind`, has
no work/execution state knowledge, preserves payload hash behavior, translates
database failures into bounded `PersistenceError`, and does not redesign frozen
TASK-M0-002 schema.

## Separation And Topology

Revalidation found no:

- TASK-M0-004 event/evidence runtime store;
- event emission;
- policy evaluation;
- runtime orchestration;
- executor;
- scheduler, DAG, or retry engine;
- API or web behavior;
- M1+ behavior.

TASK-M0-004 remains the independent PG-M0-02B sibling. TASK-M0-006 through
TASK-M0-014 remain blocked.

## Mechanical Verification

| Check | Result |
| --- | --- |
| TOML validation | PASS: 11 `pyproject.toml` files parsed. |
| `uv lock --check` | PASS: resolved 46 packages. |
| `uv sync --locked --all-groups --all-packages` | PASS: checked 43 packages. |
| Docker Compose config | PASS. |
| Ruff | PASS. |
| Ruff format | PASS: 164 files already formatted. |
| Authoritative mypy | PASS: `uv run mypy apps/api/src packages/python/*/src`; 49 source files. |
| Independent adversarial corrupt-payload/concurrency probe | PASS. |
| TASK-M0-005 unit tests | PASS: 47 passed. |
| TASK-M0-005 PostgreSQL integration | PASS: 1 passed serially. |
| Persistence/policy regressions | PASS: 39 passed. |
| Contracts/core regressions | PASS: 138 passed. |
| Architecture/security | PASS: 50 passed. |
| API integration | PASS: 6 passed, 2 known dependency warnings. |
| PostgreSQL persistence integration | PASS: 1 passed serially. |
| PostgreSQL provider integration | PASS: 1 passed serially. |
| BOOT acceptance | PASS: 6 passed, 2 known dependency warnings. |
| Full pytest | PASS: 327 passed, 2 known dependency warnings. |
| Frontend frozen install | PASS. |
| Frontend repository check | PASS. |
| Web tests | PASS: 1 test file, 2 tests. |
| Web typecheck | PASS. |
| Web production build | PASS: 18 modules transformed. |
| `git diff --check` | PASS. |

The warnings are the existing Starlette/TestClient `httpx` deprecation and
anyio `BlockingPortal` alias deprecation warnings.

PostgreSQL-dependent verification was run serially. The named volume was
preserved; `docker compose down -v` was not used.

## Lifecycle Transition

TASK-M0-005 is `VALIDATED, FROZEN`.

TASK-M0-004 remains unchanged. TASK-M0-006 is not ready until frozen TASK-M0-004
is integrated with frozen TASK-M0-005.
