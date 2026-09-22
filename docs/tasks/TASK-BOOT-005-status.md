---
id: TASK-BOOT-005-STATUS
title: TASK-BOOT-005 Developer Command Surface Status
lifecycle: TESTED
artifact_type: task_status
authority: evidence
task: TASK-BOOT-005
---

# TASK-BOOT-005 Developer Command Surface Status

## Status

`TASK-BOOT-005` is implemented and locally tested. It is not self-declared `VALIDATED` or `FROZEN`.

## Mechanism

The command surface uses a dependency-free Bash router at `tooling/curios`.

This keeps the command layer provider-neutral and avoids modifying Python or Node manifests owned by other boot tasks. No root command-entry file was added because `tooling/curios` is directly executable from the repository root.

## Command Behavior

Supported inspection commands:

- `tooling/curios help`
- `tooling/curios commands`
- `tooling/curios status`

Required command intentions are present:

- `setup`
- `dev`
- `dev-api`
- `dev-web`
- `db-up`
- `db-down`
- `db-migrate`
- `format`
- `lint`
- `typecheck`
- `test`
- `test-unit`
- `test-contract`
- `test-integration`
- `test-e2e`
- `verify`

At this repository stage, the required command intentions report `not bootstrapped` and exit `78`. This is intentional because Python, Node, database, application, provider, and test implementations are outside `TASK-BOOT-005` scope.

Unknown commands exit `2`.

## Checks

Local checks performed:

- `bash -n tooling/curios`
- `tooling/curios help`
- `tooling/curios commands`
- `tooling/curios status`
- every required command intention was invoked and verified to exit `78`
- an unknown command was invoked and verified to exit `2`
- `git diff --check`
- complete diff and changed-file scope inspected

## Limitations

The command layer does not start services, install dependencies, manage databases, run formatters, run linters, run typecheckers, run tests, or perform aggregate verification yet. Those capabilities require later boot tasks to create the relevant workspaces, infrastructure, application code, and test suites.
