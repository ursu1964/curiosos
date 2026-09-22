---
id: BOOT-000-ARCHITECTURE-BASELINE
title: BOOT-000 Architecture Baseline
lifecycle: FROZEN
artifact_type: architecture_baseline
authority: authoritative
---

# BOOT-000 Architecture Baseline

This artifact captures the architecture constraints that implementation tasks must preserve during BOOT-000.

## Canonical Semantics

CuriosOS owns canonical semantics. Frameworks, databases, model providers, UI frameworks, telemetry systems, and orchestration tools are implementations or providers.

Forbidden dependency patterns include:

```text
Curios domain -> FastAPI
Curios domain -> SQLAlchemy
Curios domain -> Ollama
Curios domain -> PostgreSQL-specific semantics
Curios domain -> React
```

Provider and framework code may depend inward on Curios contracts. Curios contracts must not depend outward on provider implementations.

## Initial Technology Baseline

The initial implementation baseline is:

- Python 3.14.x.
- uv with committed `uv.lock`.
- FastAPI as API framework provider.
- Pydantic v2 as replaceable Python schema implementation.
- React, TypeScript, Vite, Node 24 LTS, and pnpm for frontend implementation.
- PostgreSQL 18.x through SQLAlchemy 2.x and Alembic.
- Docker/Compose for `LOCAL_DOCKER`.
- Ollama as the first local model provider.
- pytest, Vitest, Playwright, Ruff, mypy, ESLint, Prettier.
- OpenTelemetry-compatible telemetry provider boundary.

These technologies do not define CuriosOS domain semantics.

## Initial Monorepo Boundary

The frozen conceptual topology is:

```text
docs/
apps/
services/
packages/
providers/
tests/
infrastructure/
tooling/
generated/
```

`TASK-BOOT-001` creates only the initial `docs/**` Build Pack foundation. Other top-level implementation directories are created only by later authorized tasks.

## Runtime Truth

Runtime visualizations must reflect recorded runtime truth. CuriosOS must not invent agent activity, pattern reuse, verification, provider execution, test success, or evidence.

## Security and Effects

Canonical M0 effects are:

```text
READ_ONLY
LOCAL_WRITE
EXTERNAL_READ
EXTERNAL_WRITE
DESTRUCTIVE
SECRET_ACCESS
NETWORK_ACCESS
EXECUTION
```

Approval is a policy outcome, not an effect. `PolicyDecision.UNKNOWN` must be preserved as `UNKNOWN`; for governed effects it prevents execution.
