---
id: TASK-BOOT-004-EVIDENCE
title: TASK-BOOT-004 Implementation Evidence
lifecycle: TESTED
artifact_type: evidence
authority: implementation_evidence
task: TASK-BOOT-004
date: 2026-09-22
---

# TASK-BOOT-004 Implementation Evidence

## Scope

TASK-BOOT-004 establishes the minimum root Node, TypeScript, and pnpm workspace foundation. It does not create application directories or TypeScript package skeletons.

## Files

- `package.json`
- `pnpm-workspace.yaml`
- `pnpm-lock.yaml`
- `tsconfig.base.json`
- `tsconfig.json`
- `eslint.config.mjs`
- `.prettierignore`
- `prettier.config.mjs`
- `docs/program/status-ledger/BOOT-000-task-ledger.md`
- `docs/tasks/TASK-BOOT-004-evidence.md`

## Policy And Tooling

- Node policy: Node 24 LTS via `engines.node` of `>=24 <25`.
- pnpm package manager metadata: `pnpm@12.5.1`.
- Workspace patterns: `apps/*` and `packages/typescript/*`.
- TypeScript baseline: strict compiler options in `tsconfig.base.json`.
- Frontend tooling baseline: ESLint flat config and Prettier root config.
- Root dev dependencies:
  - `@eslint/js@10.0.1`
  - `eslint@10.11.0`
  - `prettier@3.9.8`
  - `typescript@6.0.3`
  - `typescript-eslint@8.70.0`
- Application dependencies: none.
- React/Vite dependencies: none.

## Checks

| Check | Result |
| --- | --- |
| `git status --short --branch` | Passed; branch `task/boot-004-typescript`. |
| `git rev-parse HEAD` | Passed; base commit `14e714a0fbd4b733e42235cfae39a672f1d6598a`. |
| `git merge-base HEAD 14e714a` | Passed; merge base `14e714a0fbd4b733e42235cfae39a672f1d6598a`. |
| `node --version` | Passed; `v24.18.0`. |
| `pnpm --version` | Passed; `12.5.1`. |
| `pnpm list --depth -1 --recursive` | Passed; workspace resolves to the private root package only. |
| `pnpm install --frozen-lockfile` | Passed; lockfile is consistent. |
| `pnpm check` | Passed; runs TypeScript, ESLint, and Prettier checks. |
| `git ls-files node_modules` | Passed; no committed `node_modules` paths. |
| `git diff --check` | Passed; no whitespace errors. |
| Diff inspection | Passed; complete staged diff inspected before commit. |
| Scope review | Passed; changed paths are limited to TASK-BOOT-004 root workspace/tooling files and TASK-BOOT-004 status/evidence. |
