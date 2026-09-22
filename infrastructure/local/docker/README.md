---
id: TASK-BOOT-006-LOCAL-DOCKER-POSTGRESQL
title: LOCAL_DOCKER PostgreSQL Baseline
lifecycle: IMPLEMENTED
artifact_type: infrastructure_note
authority: implementation
---

# LOCAL_DOCKER PostgreSQL Baseline

This directory defines the initial `LOCAL_DOCKER` development infrastructure baseline for `TASK-BOOT-006`.

## Scope

- PostgreSQL 18.x only.
- Ollama remains host-managed.
- No API, web, observability, queue, cache, or model-provider containers are defined.
- PostgreSQL is a replaceable infrastructure provider and does not define CuriosOS domain semantics.

## Local Configuration

Use the explicit local-development placeholders in `.env.example`, or provide equivalent `CURIOS_*` environment variables:

```bash
docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config
```

The placeholder password is non-production development configuration. Do not commit real credentials.

## Operations

Start PostgreSQL:

```bash
docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml up -d
```

Check readiness:

```bash
docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml ps
```

Restart safely:

```bash
docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml restart postgres
```

Stop explicitly:

```bash
docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml stop postgres
```

Ordinary startup and shutdown preserve the named development volume. Avoid destructive reset commands such as `docker compose down -v` unless intentionally discarding local development data.
