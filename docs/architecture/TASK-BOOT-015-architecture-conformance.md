---
id: TASK-BOOT-015-ARCHITECTURE-CONFORMANCE
title: Curios Architecture Conformance Checks
lifecycle: FROZEN
artifact_type: architecture_conformance
authority: implementation_agent
task: TASK-BOOT-015
---

# Curios Architecture Conformance Checks

TASK-BOOT-015 makes the frozen CuriosOS architecture boundaries
machine-checkable without introducing a third-party architecture framework.

## Failure Mapping

Every conformance violation emitted by the TASK-BOOT-015 suite maps to:

```text
ARCHITECTURE_FAILURE
```

Failure messages identify the violated rule, source file, forbidden dependency,
and line number when the violation is source-backed.

## Implemented Rules

- `curios_contracts` source and runtime package metadata must not depend on
  FastAPI/Starlette, SQLAlchemy/Alembic/SQLModel, PostgreSQL drivers,
  Ollama/provider SDKs, OpenTelemetry implementation packages, Docker tooling,
  React/TypeScript runtime concerns, repository tooling/infrastructure, provider
  implementation imports, or `curios_core`.
- `curios_core` source and runtime package metadata must not depend on
  FastAPI/Starlette, SQLAlchemy/Alembic/SQLModel, PostgreSQL drivers,
  Ollama/provider SDKs, OpenTelemetry implementation packages, Docker tooling,
  repository tooling/infrastructure, or provider implementation imports.
- Provider implementation packages may be absent. When provider packages or a
  top-level `providers/**` tree appear, contracts/core outward imports are
  still blocked by import-root patterns.
- Canonical contract classes must not become SQLAlchemy ORM models through ORM
  bases, ORM decorators, or ORM mapping attributes.
- FastAPI request/response classes must not become canonical authority through
  FastAPI bases or decorators in `curios_contracts`.
- Provider-native model/type annotations must not appear in canonical contract
  annotations when they originate from forbidden provider/framework imports.
- `ObjectReference` must remain the single generic object-reference abstraction.
  Specific references such as artifact, evidence, verification, or secret
  pointers remain allowed when they do not duplicate the generic `kind/ref_id`
  shape.
- The TypeScript workspace must remain structurally downstream/separate from
  canonical Python contracts. The check inspects `pyproject.toml` and
  `pnpm-workspace.yaml`; it does not pretend to prove semantic authorship from
  TypeScript source text.
- Canonical domain packages must not import repository tooling or
  Docker/Compose infrastructure concerns.

## Inspection Mechanism

- Python AST import analysis for source-level dependency direction.
- Python AST class/base/decorator/field inspection for forbidden ORM and FastAPI
  authority markers.
- Python AST annotation inspection with import-alias resolution for
  provider-native canonical field/type leakage.
- `pyproject.toml` metadata inspection for runtime dependency contamination,
  using normalized Python distribution names for dotted import families such as
  `google.genai` and `opentelemetry.exporter`.
- Repository source-path and workspace-configuration checks for Python/Node
  boundary direction.

## Limits

- The suite intentionally avoids brittle text heuristics for semantic authority.
  It can prove dependency/path/configuration boundaries, not subjective
  authorship of copied prose or duplicated business meaning.
- Annotation checks catch provider-native types imported from forbidden packages
  or referenced by forbidden qualified names. A locally defined type with a
  provider-like name but no provider import is not classified as provider-native
  by this deterministic strategy.
- Provider implementation discovery is path/import-root based until concrete
  provider packages exist. Future provider package names should preserve a clear
  `provider` import root or live under `providers/**` to stay automatically
  covered.
