# curios_core

`curios_core` is the Curios-owned application/domain foundation above the
frozen canonical contract layer.

## Dependency Direction

The package may depend inward on `curios_contracts`. Provider, framework, API,
persistence, telemetry, and model implementation packages must depend inward on
contracts and core instead of core depending outward on them.

```text
curios_contracts
       ^
   curios_core
       ^
future provider/service composition
```

## What Belongs Here

- Curios-owned application/service boundaries.
- Provider-facing ports that invert dependencies toward replaceable outer
  implementations.
- Core context composition that uses frozen contract objects.
- Boundary operation results expressed with frozen `Result` and
  `ContractError` semantics.

## What Does Not Belong Here

- Schedulers, DAG engines, capability resolvers, model routers, agent
  executors, policy engines, event buses, repositories, provider SDK calls,
  FastAPI routes, telemetry exporters, cognitive graphs, memory, patterns,
  learning, workflows, or application generation.
- Duplicate canonical contract objects already owned by `curios_contracts`.
- Provider/framework dependencies such as FastAPI, SQLAlchemy, PostgreSQL,
  Ollama, OpenTelemetry, HTTP clients, or model SDKs.

## Current M0 Foundation

The current foundation intentionally contains only:

- `CoreContext`, composed from `ObservabilityContext` and optional `Authority`.
- `ProviderCatalog`, a read-only provider descriptor port whose boundary type is
  `Result[tuple[ProviderDescriptor, ...]]`.
- `CoreServices`, a minimal service boundary that can list declared provider
  descriptors through the port when an outer implementation is wired.

This does not select, route, invoke, schedule, authorize, persist, observe, or
execute providers. Those behaviors remain deferred to later authorized tasks.
