---
id: BOOT-000-DECISION-BASELINE
title: BOOT-000 Decision Baseline
lifecycle: FROZEN
artifact_type: decision_baseline
authority: authoritative
---

# BOOT-000 Decision Baseline

This record preserves the frozen conclusions of BOOT-000A through BOOT-000K in concise form. It is not a transcript archive and does not replace the individual approved planning decisions.

## BOOT-000A - Repository Discovery

- Lifecycle/status: VALIDATED.
- Principal decisions: repository is a pre-implementation shell with tracked `README.md` and `.gitignore`, plus untracked `1.txt`.
- Constraints: no existing CuriosOS implementation requires migration.
- Relationship: established the baseline for all later planning and prevented blind restructuring.

## BOOT-000B - Architecture & Technology Decision Freeze

- Lifecycle/status: FROZEN.
- Principal decisions: Python 3.14.x, uv, FastAPI, React/TypeScript/Vite, Node 24 LTS, pnpm, PostgreSQL 18.x, SQLAlchemy, Alembic, Docker/Compose for `LOCAL_DOCKER`, Ollama as local model provider, pytest, Vitest, Playwright, Ruff, mypy, ESLint, Prettier, OpenTelemetry-compatible telemetry.
- Constraints: technologies are replaceable providers or engineering tooling; they do not become CuriosOS domain semantics.
- Relationship: supplies the implementation technology baseline for topology, environment, CI, and task planning.

## BOOT-000C - Enterprise Build Pack

- Lifecycle/status: FROZEN.
- Principal decisions: authoritative artifacts use Markdown with YAML front matter, stable IDs, lifecycle metadata, traceability, one canonical program status ledger, explicit change control, and generated-document separation.
- Constraints: historical source material is context, not direct runtime/build authority.
- Relationship: defines the documentation/control authority that `TASK-BOOT-001` creates.

## BOOT-000D - Repository Topology & Package Boundary Freeze

- Lifecycle/status: FROZEN.
- Principal decisions: monorepo with `docs`, `apps`, `services`, `packages`, `providers`, `tests`, `infrastructure`, `tooling`, and optional non-authoritative `generated` boundary.
- Constraints: one modular backend service first; no premature microservices; provider/framework code depends inward on Curios contracts.
- Relationship: governs future file ownership and dependency-direction checks.

## BOOT-000E - Development Environment Specification

- Lifecycle/status: FROZEN.
- Principal decisions: host-first development; one uv workspace and one root `.venv`; one pnpm workspace; `LOCAL_DOCKER` uses PostgreSQL first; Ollama is host-managed initially.
- Constraints: all Curios environment variables use the `CURIOS_` prefix. Compose base/full/observability variants are tooling profiles beneath `LOCAL_DOCKER`, not semantic Curios environment profiles.
- Relationship: governs workspace, local infrastructure, and command-surface implementation tasks.

## BOOT-000F - Core Contracts & Conventions

- Lifecycle/status: FROZEN.
- Principal decisions: canonical contracts are Curios-owned; Python/Pydantic, JSON Schema, OpenAPI, TypeScript, database schemas, and providers are representations or implementations.
- Constraints: engineering/build lifecycle is distinct from runtime state machines. Artifact references use provider-neutral locator semantics. Correlation contracts include contextual IDs where applicable.
- Relationship: governs M0 contracts and downstream provider/API/frontend boundary work.

## BOOT-000G - Testing & Independent Verification

- Lifecycle/status: FROZEN.
- Principal decisions: test taxonomy, M0 contract test matrix, contract conformance, provider testing, architecture tests, isolation, determinism, evidence, verification, acceptance gates, and failure taxonomy are frozen.
- Constraints: implementation-agent success is not validation. Generic evidence does not imply secret scanning unless that verification was performed.
- Relationship: governs test foundation, acceptance suite, and verification assignments.

## BOOT-000H - Security, Configuration & Effect Governance

- Lifecycle/status: FROZEN.
- Principal decisions: minimum M0 security concepts include identity, principal, authority, permission, policy, effect, approval, secret, resource, scope, and security evidence.
- Constraints: canonical M0 effects are `READ_ONLY`, `LOCAL_WRITE`, `EXTERNAL_READ`, `EXTERNAL_WRITE`, `DESTRUCTIVE`, `SECRET_ACCESS`, `NETWORK_ACCESS`, and `EXECUTION`. Approval is a policy/control outcome, not an effect. `PolicyDecision` outcomes are `ALLOW`, `DENY`, `REQUIRES_APPROVAL`, and `UNKNOWN`. Governed effects cannot proceed on `UNKNOWN`.
- Relationship: governs security contracts, policy checks, provider authority, and task effect classification.

## BOOT-000I - Observability, Evidence, Provenance & Runtime Truth

- Lifecycle/status: FROZEN.
- Principal decisions: observability distinguishes events, logs, traces, spans, metrics, evidence, provenance, audit records, verification records, runtime state, and visualization projections.
- Constraints: OpenTelemetry is a provider, not semantic authority. `trace_id` is required for runtime-derived evidence; non-runtime evidence may omit runtime trace identifiers when it preserves sufficient provenance and criteria references.
- Relationship: governs event/observability contracts, telemetry provider boundaries, evidence, and acceptance records.

## BOOT-000J - CI, Quality Gates & Merge Eligibility

- Lifecycle/status: FROZEN.
- Principal decisions: CI enforces deterministic quality gates, locked dependencies, contract compatibility, architecture conformance, security baseline, and evidence production. GitHub Actions is the initial implementation assumption, not semantic authority.
- Constraints: ordinary CI must not depend on live Ollama, GPU, or nondeterministic model behavior. GitHub branch protection is not required during initial M0 implementation.
- Relationship: governs CI implementation, merge eligibility, and evidence mapping.

## BOOT-000K - Implementation DAG & Atomic Task Pack

- Lifecycle/status: FROZEN.
- Principal decisions: BOOT-000 is decomposed into `TASK-BOOT-001` through `TASK-BOOT-028`, with explicit workstreams, dependency DAG, parallel groups, ownership, verification, and acceptance gates.
- Constraints: `PG-07` is corrected into `PG-07A` and `PG-07B`; `TASK-BOOT-016` depends on `TASK-BOOT-013` and `TASK-BOOT-015`. Do not create empty documentation directories. Do not proceed beyond the authorized task.
- Relationship: supplies the implementation control plan beginning with `TASK-BOOT-001`.
