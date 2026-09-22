---
id: BOOT-000-TASK-PACK
title: BOOT-000 Atomic Task Pack
lifecycle: FROZEN
artifact_type: task_pack
authority: authoritative
---

# BOOT-000 Atomic Task Pack

This artifact summarizes file ownership, effects, verification, and rollback boundaries for `TASK-BOOT-001` through `TASK-BOOT-028`.

## Common Rules

- Each task must stay within its allowed scope.
- No task may expand frozen scope without an approved change.
- No task may mark itself `VALIDATED`.
- Implementation-agent self-report is not sufficient for validation.
- Rollback uses task-owned diffs or isolated branch/worktree practices, not destructive reset of the repository.

## Task Ownership Matrix

| Task | Allowed Ownership | Effects | Verification |
| --- | --- | --- | --- |
| TASK-BOOT-001 | `docs/**` Build Pack foundation only | LOCAL_WRITE | scope review, diff review, documentation consistency |
| TASK-BOOT-002 | repository metadata conventions | LOCAL_WRITE | scope review, metadata checks |
| TASK-BOOT-003 | Python uv workspace files | LOCAL_WRITE, EXTERNAL_READ, EXECUTION | uv checks, Ruff, mypy, pytest bootstrap |
| TASK-BOOT-004 | pnpm/TypeScript workspace files | LOCAL_WRITE, EXTERNAL_READ, EXECUTION | pnpm checks, TypeScript, ESLint, Prettier |
| TASK-BOOT-005 | developer command surface | LOCAL_WRITE, EXECUTION | command dry checks where possible |
| TASK-BOOT-006 | `LOCAL_DOCKER` PostgreSQL infrastructure | LOCAL_WRITE, EXTERNAL_READ, EXECUTION | Compose validation and isolated PostgreSQL check |
| TASK-BOOT-007 | Python package skeletons | LOCAL_WRITE | workspace integrity and import-boundary checks |
| TASK-BOOT-008 | TypeScript package skeletons | LOCAL_WRITE | workspace integrity checks |
| TASK-BOOT-009 | primitive contracts | LOCAL_WRITE | schema, contract, unit, architecture checks |
| TASK-BOOT-010 | result, error, artifact/evidence refs | LOCAL_WRITE | schema, contract, unit, architecture checks |
| TASK-BOOT-011 | work, execution, capability, provider, agent contracts | LOCAL_WRITE | schema, contract, unit, architecture checks |
| TASK-BOOT-012 | event and observability contracts | LOCAL_WRITE | schema, contract, unit, architecture checks |
| TASK-BOOT-013 | config, security, effect, policy contracts | LOCAL_WRITE | schema, contract, unit, architecture/security checks |
| TASK-BOOT-014 | contract/schema test foundation | LOCAL_WRITE, EXECUTION | independent contract-test review |
| TASK-BOOT-015 | architecture conformance checks | LOCAL_WRITE, EXECUTION | independent architecture verification |
| TASK-BOOT-016 | security baseline tests | LOCAL_WRITE, EXECUTION | independent security verification |
| TASK-BOOT-017 | core package foundation | LOCAL_WRITE | unit, contract, architecture checks |
| TASK-BOOT-018 | configuration provider | LOCAL_WRITE | provider conformance and security checks |
| TASK-BOOT-019 | PostgreSQL provider boundary | LOCAL_WRITE, EXECUTION | provider conformance and integration checks |
| TASK-BOOT-020 | Ollama provider boundary with deterministic tests | LOCAL_WRITE | deterministic provider conformance checks |
| TASK-BOOT-021 | telemetry provider boundary | LOCAL_WRITE | observability conformance checks |
| TASK-BOOT-022 | FastAPI service composition | LOCAL_WRITE, EXECUTION | API contract and integration checks |
| TASK-BOOT-023 | API integration tests | LOCAL_WRITE, EXECUTION | integration test evidence |
| TASK-BOOT-024 | web bootstrap | LOCAL_WRITE, EXECUTION | frontend checks and build |
| TASK-BOOT-025 | CI quality gates | LOCAL_WRITE, EXECUTION | CI syntax/dry validation where possible |
| TASK-BOOT-026 | BOOT acceptance suite | LOCAL_WRITE, EXECUTION | acceptance evidence |
| TASK-BOOT-027 | independent verification record | READ_ONLY, LOCAL_WRITE evidence | independent verifier record |
| TASK-BOOT-028 | BOOT freeze/status ledger update | LOCAL_WRITE | human or designated acceptance review |

## First Task Scope

`TASK-BOOT-001` is the first authorized modifying task. It may create only Build Pack documentation under `docs/**`. It must not modify `README.md`, `.gitignore`, `1.txt`, source code, manifests, Docker files, CI files, tests, packages, services, providers, infrastructure, tooling, or generated artifacts.

## TASK-BOOT-002 Scope

`TASK-BOOT-002` establishes repository-level metadata and conventions before workspace bootstrap tasks begin.

Allowed ownership:

- `.gitignore`
- `.editorconfig`
- `docs/program/status-ledger/**` for lifecycle/status evidence
- `docs/tasks/**` for task-scope evidence

Forbidden ownership:

- `README.md`
- `1.txt`
- application, service, package, provider, test, infrastructure, tooling, generated, CI, manifest, dependency, Docker, database, or source-code files

Acceptance evidence:

- metadata files are minimal and technology-neutral where possible;
- future local build outputs, caches, virtual environments, dependencies, logs, secrets, and generated outputs are ignored without ignoring lockfiles;
- `README.md`, `.gitignore` beyond authorized edits, and `1.txt` scope rules are respected;
- no implementation topology is created.

## Deferred Scope

The following are deferred beyond BOOT-000:

- DataLab.
- Full cognitive graph runtime.
- Multi-agent orchestration runtime.
- Application intelligence.
- Coding-agent orchestration.
- Learning and self-improvement.
- Multi-project execution.
- Production IAM.
- Full policy language.
- Cloud infrastructure provisioning.
- External event brokers.
- Live LLM quality gates.
- Production observability stack.
- Repository branch protection administration.
