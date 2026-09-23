---
id: TASK-M1-001-EVIDENCE
title: TASK-M1-001 M1 Topology and Guardrail Transition Evidence
lifecycle: TESTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M1-001
milestone_id: M1
date: 2026-09-23
---

# TASK-M1-001 Evidence

## Objective

Establish the M1 topology and guardrail transition required before M1
implementation begins.

TASK-M1-001 does not implement cognitive contracts, deterministic
decomposition, DAG records/runtime, capability resolution, agent persistence,
executor seams, model/profile discovery, routing records, bounded runner,
verification loop, API routes, web UI, integration tests, acceptance tests, CI,
or M2+ behavior.

## Starting Baseline

`97e52872e8e087cd0da4dea72d2ac1a8e90868c1`

M1 planning is `VALIDATED, FROZEN`. TASK-M1-001 is the first authorized M1
execution unit from that baseline.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Reconstruct current frozen topology | PASS | Current topology remains frozen BOOT+M0; no production package/app/runtime/API/web surface was added. |
| Represent planned M1 surfaces | PASS | Security tests include a planned M1 surface registry by owning task while keeping only TASK-M1-001 currently authorized. |
| Enforce planned is not authorized | PASS | Adversarial tests reject premature M1 package, contract, runtime, API, web, integration, and acceptance surfaces. |
| Preserve BOOT/M0 security | PASS | Existing secret scanning, `.github`, provider, API/web, integration, acceptance, policy, and authority tests remain active. |
| Preserve architecture direction | PASS | Architecture tests block contracts/core from depending on representative M1 implementation roots. |
| Protect canonical authority | PASS | Frozen `curios_contracts` declaration, schema/vocabulary-member, and package-export inventories reject premature authority inside already-authorized files as well as new contract files. |
| Keep agent/execution separate | PASS | TASK-M1-001 adds no agent semantics; architecture/security tests reject premature agent runtime/lifecycle surfaces. |
| Keep model scope bounded | PASS | Model generation, inference, router optimization, and live quality gates remain blocked by topology examples and workflow checks. |
| Keep DAG scheduler separate | PASS | M1 bounded DAG surfaces remain planned only; production scheduler/orchestration examples remain blocked. |
| Preserve API/web exactness | PASS | M1 API/web examples are rejected until TASK-M1-013 and TASK-M1-014 authorize exact files. |
| Preserve test-surface exactness | PASS | M1 integration and acceptance examples are rejected until TASK-M1-015 and TASK-M1-017. |
| Preserve CI exactness | PASS | `.github/workflows/quality-gates.yml` remains the only authorized GitHub path; workflow content unchanged. |
| Update lifecycle truthfully | PASS | TASK-M1-001 is recorded as `IMPLEMENTED, TESTED`; TASK-M1-002 through TASK-M1-019 remain `BLOCKED`. |

## Files Changed

- `tests/security/test_security_baseline.py`
- `tests/architecture/test_architecture_conformance.py`
- `docs/security/TASK-M1-001-topology-guardrails.md`
- `docs/architecture/TASK-M1-001-topology-guardrails.md`
- `docs/program/status-ledger/M1-status-ledger.md`
- `docs/tasks/TASK-M1-001-evidence.md`

## Topology Model

M1 surfaces are represented as planned task-owned categories. They are not
currently authorized implementation files.

Current authorization remains frozen BOOT+M0 plus TASK-M1-001 guardrail docs,
security tests, architecture tests, task evidence, and ledger updates.

## Independent Validation Failure And Correction

Independent validation of candidate
`3525d4f7f65ef2dd35322be46dd22f2f147db53f` failed because TASK-M1-001 blocked
new premature contract files but did not protect canonical authority inside an
already-authorized `curios_contracts` file.

The confirmed bypass added an exported `Intent` dataclass directly to
`packages/python/curios_contracts/src/curios_contracts/work.py` and re-exported
it from `curios_contracts/__init__.py`; the previous security and architecture
suites stayed green.

The correction freezes the current contract authority inventory explicitly:

- public top-level declarations for every existing `curios_contracts` source
  module;
- representative frozen class fields and enum/vocabulary members;
- public package imports/re-exports in `curios_contracts/__init__.py`;
- the exact package `__all__` export set.

The replayed bypass now fails the canonical declaration inventory and package
export inventory checks.

## Second Independent Validation Failure And Correction

Independent revalidation of corrected candidate
`21c4b690397a470eee4fc3ca9ae6c65ff80f8e61` found a narrower package-export
bypass. Prepending the following import to `curios_contracts/__init__.py`
created a new public package name while the guard stayed green:

```python
from curios_contracts.work import WorkItem as Intent
```

`from curios_contracts import Intent` then succeeded with `Intent is WorkItem`.

The root cause was information loss in the package export inventory:
`_contract_init_authority` keyed imports by source module, so a later legitimate
frozen import from `curios_contracts.work` overwrote the earlier unauthorized
alias import.

The second correction represents package-initializer import authority as an
ordered sequence of import statements:

- every import statement is preserved;
- duplicate source-module imports are preserved;
- imported names and aliases are preserved;
- statement order is preserved;
- plain `import ... as ...` statements are represented and rejected unless
  explicitly frozen.

The confirmed alias bypass now fails the package export inventory check.

## Third Independent Validation Failure And Correction

Independent revalidation of corrected candidate
`0e5e6ddb970cbe3e18bea6f06667e25f44d33016` found that package export authority
could still be expanded through nested executable statements in
`curios_contracts/__init__.py`:

```python
if True:
    from curios_contracts.work import WorkItem as Intent
```

`from curios_contracts import Intent` then succeeded with `Intent is WorkItem`
while the security suite stayed green.

The third correction freezes the package initializer as a bounded AST grammar:

- module docstring;
- exact ordered frozen `ImportFrom` statements;
- exact `__version__ = "0.0.0"` assignment;
- exact literal tuple `__all__` assignment.

Every other top-level statement shape is rejected fail-closed, including
conditional blocks, try/fallback blocks, loops, `with`, `match`, function/class
definitions, dynamic `globals`/`setattr`/`exec`/`eval` exports, `__getattr__`,
`__dir__`, annotated assignments, tuple assignments, plain imports, star
imports, and later `__all__` mutation.

The confirmed conditional import bypass is now rejected by the package
initializer statement-sequence guard.

## Adversarial Coverage

The guardrail tests reject representative premature additions for:

- M1 cognitive contract files;
- M1 cognitive declarations, fields, enum members, type aliases, public
  factories/functions, and constants inside already-authorized contract files;
- M1 package-level exports, aliases, and re-exports from `curios_contracts`;
- duplicate-module import aliases, alias-only exports without `__all__`
  changes, star imports, plain import aliases, and public assignment aliases in
  `curios_contracts/__init__.py`;
- conditional, try/fallback, nested, and dynamic package-initializer exports;
- unexpected package-initializer executable statement shapes and `__all__`
  mutation;
- TypeScript contract files;
- M1 package roots;
- DAG/agent/executor/model/routing/runner/verification runtime modules;
- M1 API source and API tests;
- M1 web source files;
- M1 integration tests;
- M1 acceptance tests;
- M2+ package roots and top-level runtime/service/provider roots.

Private implementation helpers that remain private by name are not treated as
new canonical authority. Re-exporting a private helper through the package
boundary is rejected.

## Future Task Transition

TASK-M1-002 owns future `Intent`, `Objective`, `Problem`, `Assumption`,
`Decision`, and `Plan` canonical contract transitions. TASK-M1-004 owns future
bounded work-DAG records. TASK-M1-009 owns model/profile discovery records.
TASK-M1-010 owns routing decision records.

Those planned concepts remain unauthorized today. The owning future task must
deliberately update the frozen declaration/export inventory when it transitions
authority.

Existing `Capability`, `CapabilityRequirement`, `AgentDefinition`,
`AgentInstance`, `ObjectReference`, and `WorkItem` remain frozen current
contract authority and are not newly authorized by M1 planning.

## Dependency Changes

None.

## Frozen Baseline Integrity

TASK-M1-001 changed only guardrail tests and governance documentation. It did
not change frozen production semantics, package manifests, dependency locks,
CI workflow content, API behavior, web behavior, or runtime implementation.

## Verification

| Check | Result |
| --- | --- |
| Canonical-authority bypass replay | Passed: temporary exported `Intent` probe was rejected by declaration and export inventories. |
| Alias export bypass replay | Passed: temporary `WorkItem as Intent` package import was importable but rejected by lossless export inventory. |
| Conditional initializer bypass replay | Passed: temporary conditional `WorkItem as Intent` import was importable but rejected by statement-sequence guard. |
| Initializer/export adversarial matrix | Passed: `58` passed. |
| Canonical-authority targeted suite | Passed: `76` passed, `237` deselected. |
| Security and architecture focused suite | Passed: `346 passed` (`313` security, `33` architecture). |
| TOML validation | Passed: `11` `pyproject.toml` files parsed. |
| `uv lock --check` | Passed: `47` packages resolved. |
| `uv sync --locked --all-groups --all-packages` | Passed: `47` packages resolved, `44` packages checked. |
| Docker Compose config | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed: `207` files already formatted. |
| mypy strict baseline | Passed: no issues in 53 source files. |
| Package/API/provider tests | Passed: 168 passed, 2 known dependency warnings. |
| M0 runtime, persistence, and policy package tests | Passed: 128 passed, 4 deselected. |
| Contract and schema tests | Passed: 15 passed. |
| Security tests | Passed: 313 passed. |
| Architecture tests | Passed: 33 passed. |
| API integration tests | Passed: 6 passed, 2 known dependency warnings. |
| PostgreSQL provider integration test | Passed: 1 passed. |
| M0 PostgreSQL integration tests | Passed: 4 passed. |
| M0 vertical-slice integration tests | Passed: 2 passed, 2 known dependency warnings. |
| BOOT/M0 acceptance tests | Passed: 8 passed, 2 known dependency warnings. |
| Full pytest suite | Passed: 678 passed, 2 known dependency warnings. |
| Frontend checks | Passed: frozen install, `pnpm check`, apps/web tests (6 passed), typecheck, and production build (`18` modules transformed). |
| Workflow Prettier/static audit | Passed: workflow Prettier check and quality-gate static audit (`127` passed, `186` deselected). |
| `git diff --check` | Passed. |

The warnings are the existing Starlette/TestClient `httpx` deprecation and
anyio `BlockingPortal` alias deprecation warnings previously classified as
non-blocking dependency warnings.

## Lifecycle State

TASK-M1-001 is `IMPLEMENTED, TESTED`.

TASK-M1-002 through TASK-M1-019 remain `BLOCKED`.
