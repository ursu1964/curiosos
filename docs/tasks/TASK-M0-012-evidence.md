---
id: TASK-M0-012-EVIDENCE
title: TASK-M0-012 M0 Acceptance Suite Evidence
lifecycle: FROZEN
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-012
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-012 Evidence

## Objective

Add the authoritative M0 acceptance suite proving that the frozen M0 milestone
delivers the governed local work execution slice without extending production
behavior.

TASK-M0-012 owns milestone-level acceptance tests and evidence only.

## Starting Baseline

`dee41f8829b0fe4ac9a5f2ac0b9c5ba32618c2db`

## Implemented Surface

- `tests/acceptance/test_m0_acceptance.py`
- `tests/acceptance/test_boot_acceptance.py`
- `tests/security/test_security_baseline.py`
- `docs/security/TASK-M0-001-topology-guardrails.md`
- `docs/architecture/TASK-M0-001-topology-guardrails.md`
- `docs/program/status-ledger/M0-status-ledger.md`
- `docs/tasks/TASK-M0-012-evidence.md`

No production code, dependency manifest, lockfile, workflow, runtime behavior,
API route, web feature, policy rule, persistence schema, provider behavior,
scheduler, DAG runtime, agent runtime, model router, DataLab, or M1+ surface
was added.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| M0 objective | PASS | Acceptance composes frozen API, runtime, policy, executor, repository, event/evidence store, and PostgreSQL boundaries to prove governed local work execution. |
| VS-M0-001 success | PASS | Provider-inventory work is created through API, authorized by policy, invokes the executor exactly once per successful work, records deterministic provider descriptors, and reaches `COMPLETED` / `SUCCEEDED`. |
| VS-M0-002 policy safety | PASS | `UNKNOWN` and unsupported effect requests are non-authorizing, return bounded API truth, and do not invoke the executor. |
| VS-M0-003 recovery | PASS | Runtime/application/store objects are disposed and reconstructed against the same PostgreSQL schema; work, execution, events, and evidence are reread from persisted truth. |
| VS-M0-004 API/web observability | PASS | API observation routes expose persisted work/execution/events/evidence, and web source/API-boundary tests prove the console consumes the frozen route set without becoming semantic authority. |
| Cross-work isolation | PASS | Independent work IDs and execution IDs remain distinct; cross-work execution lookup returns 404; event/evidence subjects remain scoped. |
| Runtime consistency | PASS | Successful, blocked, and provider-failure outcomes produce legal persisted work/execution/event/evidence truth. |
| Provider inventory | PASS | Acceptance expects canonical `ProviderDescriptor` JSON, deterministic ordering, no provider-native payloads, and no live Ollama. |
| API safety | PASS | Bounded 403/502 responses are checked; SQLAlchemy, psycopg, and traceback strings do not appear in failure detail. |
| Web safety | PASS | Web source exposes provider-inventory-only controls, manual refresh, stale-response protection, no arbitrary effects, and no polling/WebSocket/SSE framework. |
| Security acceptance | PASS | Security topology authorizes only exact BOOT/M0 acceptance files, exact M0 integration file, exact `.github` workflow surface, and preserves secret scanning. |
| Architecture acceptance | PASS | Architecture tests remain authoritative for contracts/core inward dependency and provider/API/web outer-boundary rules. |
| CI acceptance | PASS | Frozen workflow already runs `uv run pytest tests/acceptance -q`, M0 integration, security, architecture, full pytest, frontend gates, and diff hygiene. No CI edit was required. |
| M1+ exclusion | PASS | Acceptance checks preserve absence/blocking of scheduler, agent, model-router/generation, DataLab, knowledge/memory, full policy/IAM, secret resolver, brokers, cloud, and live LLM gates. |
| Determinism | PASS | Acceptance uses deterministic fake provider catalogs; only PostgreSQL `LOCAL_DOCKER` is live. |

## Scenario Matrix

| Scenario | Vertical Slice | Frozen Tasks Exercised | Evidence |
| --- | --- | --- | --- |
| Successful provider inventory | VS-M0-001 | TASK-M0-002 through TASK-M0-008 | API-created work executes through policy/runtime/executor and persists recorded truth. |
| Policy blocking | VS-M0-002 | TASK-M0-003, TASK-M0-006, TASK-M0-008 | `UNKNOWN` and unsupported effects fail closed before executor invocation. |
| PostgreSQL reconstruction | VS-M0-003 | TASK-M0-002, TASK-M0-004, TASK-M0-005, TASK-M0-008 | Reconstructed app/runtime/store reads the same work/execution/event/evidence truth. |
| API/web observability | VS-M0-004 | TASK-M0-008, TASK-M0-009 | Web API boundary and console source align with the frozen work route set and recorded truth presentation. |
| Guardrail acceptance | M0 exit criteria | TASK-M0-001, TASK-M0-011 | Security, architecture, workflow, and deferred-scope checks remain active. |

## PostgreSQL Lifecycle

The acceptance test uses PostgreSQL 18 `LOCAL_DOCKER`, starts only the
`postgres` service, uses an isolated generated schema, stops the service
cleanly, verifies the named volume remains present, and never uses destructive
volume operations.

## CI Invocation Decision

No workflow edit was made. TASK-M0-011 already froze the workflow gate:

- `uv run pytest tests/acceptance -q`

Because TASK-M0-012 adds its acceptance test under `tests/acceptance`, the
existing frozen gate now invokes the M0 acceptance suite without changing the
CI execution surface.

## Verification

Verification performed during implementation:

- TASK-M0-012 acceptance tests: `2 passed`, `2` known dependency warnings
- Complete acceptance suite: `8 passed`, `2` known dependency warnings
- Security and architecture tests: `208 passed`
- API and M0 integration regression tests: `24 passed`, `2` known dependency
  warnings
- Runtime package tests: `91 passed`
- Policy, persistence boundary, contracts, and core tests: `162 passed`
- Provider package tests: `29 passed`
- Contract, schema, architecture, security, and acceptance tests: `231 passed`,
  `2` known dependency warnings
- PostgreSQL-backed persistence/runtime/provider/integration/acceptance tests:
  `9 passed`, `2` known dependency warnings; PostgreSQL named volume preserved
- Full pytest suite: `540 passed`, `2` known dependency warnings
- TOML validation: `11` files parsed successfully
- `uv lock --check`: passed
- `uv sync --locked --all-groups --all-packages`: passed
- Docker Compose config validation: passed
- Ruff: passed
- Ruff format check: passed
- mypy: passed across `53` source files
- `pnpm install --frozen-lockfile`: passed
- `pnpm check`: passed
- `apps/web` tests: `1` file / `6` tests passed
- `apps/web` typecheck: passed
- `apps/web` production build: passed
- Workflow Prettier check: passed

## Lifecycle

TASK-M0-012 is `VALIDATED, FROZEN`.

Independent validation accepted the implemented acceptance suite without
requiring production corrections. TASK-M0-013 remains blocked until this
complete validation/freeze history is integrated into `main`.
