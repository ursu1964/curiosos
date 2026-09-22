---
id: TASK-BOOT-016-SECURITY-BASELINE
title: TASK-BOOT-016 Security Baseline Tests
lifecycle: IMPLEMENTED
artifact_type: security_baseline
authority: implementation_agent
task: TASK-BOOT-016
---

# TASK-BOOT-016 Security Baseline Tests

TASK-BOOT-016 establishes deterministic M0 security baseline checks for the
frozen TASK-BOOT-013 security contracts and TASK-BOOT-015 architecture
conformance boundary.

The baseline is a test/check foundation only. It does not implement IAM,
policy evaluation, secret resolution, approval workflow, provider adapters,
runtime security engines, or PG-08 provider work.

## Acceptance Mapping

| Requirement | Implemented Check |
| --- | --- |
| Canonical effects, risks, policy outcomes, approvals, and configuration profiles remain frozen. | `test_security_vocabularies_are_exact_and_do_not_collapse_controls` |
| `PolicyDecision.UNKNOWN` remains distinct from `DENY` and does not authorize governed effects. | `test_unknown_policy_for_governed_effects_is_not_authorizing_or_rewritten` |
| Security records do not serialize secret values or prohibited credential-bearing fields. | `test_security_records_do_not_serialize_secret_values_or_credential_fields` |
| Tracked authoritative source/config/documentation surfaces do not contain committed secret-shaped literals. | `test_tracked_security_surfaces_do_not_contain_secret_shaped_literals` |
| Repository secret scanning distinguishes prohibited literals from approved local placeholders. | `test_secret_scanner_rejects_secret_literals_and_allows_documented_placeholders` |
| Secret/principal/authority-related contracts reject obvious secret-shaped input. | `test_secret_principal_and_authority_contracts_reject_secret_value_shapes` |
| Security contract dataclasses do not grow secret-value fields. | `test_security_contract_dataclass_fields_do_not_add_secret_value_slots` |
| Secret-value field detection rejects semantic variants rather than a few fixed examples. | `test_secret_field_detector_rejects_semantic_secret_value_variants` |
| Security contracts remain provider/framework/runtime independent. | `test_security_contract_source_has_no_runtime_security_imports` |
| Local development configuration examples stay CURIOS-prefixed and placeholder-oriented. | `test_local_docker_configuration_examples_remain_placeholder_and_curios_prefixed` |
| `CoreContext` and `CoreServices` do not become authority, policy, or secret-resolution engines. | `test_core_context_and_services_do_not_implement_security_authority_engines` |
| PG-08 provider/runtime surfaces remain absent. | `test_later_task_security_provider_runtime_surfaces_remain_absent` |

## Failure Class

TASK-BOOT-016 security baseline violations report:

```text
SECURITY_FAILURE
```

## Boundaries

- No production or developer secrets are required.
- No live provider, database, Docker, Ollama, network, or external security
  service is invoked.
- No new dependency is introduced.
- Existing TASK-BOOT-015 architecture tests remain responsible for broad
  architecture dependency-direction enforcement.
- TASK-BOOT-016 adds security-specific static and contract checks without
  duplicating the full architecture conformance suite.
- Repository secret scanning is deterministic and scoped to tracked
  source/configuration/documentation surfaces relevant to the current bootstrap
  baseline. It excludes generated, cache, dependency, VCS, and untracked
  historical material.
