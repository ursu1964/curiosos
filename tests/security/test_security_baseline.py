from __future__ import annotations

import ast
import json
import re
from dataclasses import fields
from pathlib import Path
from typing import get_type_hints

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, human_principal
from curios_contracts import (
    APPROVAL_OUTCOME_VALUES,
    CONFIGURATION_PROFILE_VALUES,
    EFFECT_CLASSIFICATION_VALUES,
    GOVERNED_EFFECT_VALUES,
    POLICY_DECISION_OUTCOME_VALUES,
    RISK_CLASSIFICATION_VALUES,
    Approval,
    ApprovalOutcome,
    ArtifactId,
    Authority,
    ConfigurationProfile,
    ConfigurationProfileName,
    EffectClassification,
    EventId,
    EvidenceId,
    ExecutionId,
    ObjectReference,
    ObservabilityContext,
    Permission,
    PolicyDecision,
    PolicyDecisionOutcome,
    Principal,
    PrincipalType,
    ProjectId,
    ProviderId,
    SecretReference,
    WorkId,
    to_json_compatible,
)
from curios_core import CoreContext, CoreServices

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_SOURCE = REPO_ROOT / "packages/python/curios_contracts/src/curios_contracts"
CORE_SOURCE = REPO_ROOT / "packages/python/curios_core/src/curios_core"
LOCAL_DOCKER_ENV_EXAMPLE = REPO_ROOT / "infrastructure/local/docker/.env.example"

SECURITY_FAILURE = "SECURITY_FAILURE"

SECRET_SHAPED_VALUE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|credential|password|secret|token)\s*[:=]"
)
PROHIBITED_SECRET_VALUE_FIELDS = frozenset(
    {
        "api_key",
        "authorization",
        "cookie",
        "credential",
        "credentials",
        "oauth_token",
        "password",
        "private_key",
        "secret_value",
        "session",
        "token",
    }
)
SECURITY_IMPLEMENTATION_IMPORTS = frozenset(
    {
        "alembic",
        "boto3",
        "docker",
        "fastapi",
        "hvac",
        "keyring",
        "ollama",
        "opentelemetry",
        "pydantic",
        "psycopg",
        "requests",
        "sqlalchemy",
        "starlette",
    }
)
CORE_SECURITY_RUNTIME_NAMES = frozenset(
    {
        "AuthorityGrant",
        "CredentialStore",
        "IamService",
        "PolicyEngine",
        "PolicyEvaluator",
        "SecretResolver",
    }
)
CORE_FORBIDDEN_SECURITY_METHOD_PARTS = frozenset(
    {
        "authorize",
        "evaluate_policy",
        "grant_authority",
        "resolve_secret",
        "revoke_authority",
    }
)
LATER_TASK_PATHS = (
    "apps",
    "services",
    "providers",
    "packages/python/curios_config",
    "packages/python/curios_postgres",
    "packages/python/curios_telemetry",
    "packages/python/curios_ollama",
    "tests/integration",
)


def _provider_ref() -> ObjectReference:
    return ObjectReference.from_id(fixed_id(ProviderId))


def _project_ref() -> ObjectReference:
    return ObjectReference.from_id(fixed_id(ProjectId))


def _security_records() -> tuple[object, ...]:
    principal = Principal(
        principal_type=PrincipalType.HUMAN,
        identity="operator@example.test",
        principal_ref=_project_ref(),
        execution_ref=ObjectReference.from_id(fixed_id(ExecutionId)),
    )
    permission = Permission(
        action="read",
        resource_type="artifact",
        resource_ref=ObjectReference.from_id(fixed_id(ArtifactId)),
        scope="project sandbox",
        permitted_effects=(EffectClassification.READ_ONLY,),
    )
    authority = Authority(
        authority_id="authz-local-read",
        principal=principal,
        permissions=(permission,),
        scope="project sandbox",
        granted_at=UTC_NOW,
        expires_at=UTC_LATER,
        provenance_refs=(fixed_id(EvidenceId),),
        approval_id="approval-local-read",
    )
    policy_decision = PolicyDecision(
        decision_id="decision-unknown",
        subject_ref=ObjectReference.from_id(fixed_id(WorkId)),
        principal=principal,
        requested_effects=(EffectClassification.SECRET_ACCESS,),
        resource_refs=(_provider_ref(),),
        scope="project sandbox",
        outcome=PolicyDecisionOutcome.UNKNOWN,
        reason="policy unavailable",
        policy_refs=(ObjectReference.from_id(fixed_id(EventId)),),
        decided_at=UTC_NOW,
        observability_context=ObservabilityContext(
            trace_id=None,
            principal_ref=ObjectReference.from_id(fixed_id(ProjectId)),
        ),
    )
    approval = Approval(
        approval_id="approval-secret-read",
        requested_by=principal,
        subject_ref=ObjectReference.from_id(fixed_id(WorkId)),
        action="read_secret",
        requested_effects=(EffectClassification.SECRET_ACCESS,),
        scope="project sandbox",
        reason="bounded review fixture",
        outcome=ApprovalOutcome.PENDING,
        requested_at=UTC_NOW,
        expires_at=UTC_LATER,
        evidence_refs=(fixed_id(EvidenceId),),
    )
    secret_reference = SecretReference(
        secret_provider_ref=_provider_ref(),
        name="model_provider_key",
        key="current",
        scope="local docker project",
        purpose="provider lookup",
    )
    configuration = ConfigurationProfile(
        profile=ConfigurationProfileName.LOCAL_DOCKER,
        description="Local Docker development profile identity.",
    )
    return (
        configuration,
        secret_reference,
        principal,
        permission,
        authority,
        policy_decision,
        approval,
    )


def _walk(value: object) -> tuple[object, ...]:
    nodes: list[object] = [value]
    if isinstance(value, dict):
        for key, item in value.items():
            nodes.extend((key, *_walk(item)))
    elif isinstance(value, list | tuple):
        for item in value:
            nodes.extend(_walk(item))
    return tuple(nodes)


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.py") if path.is_file()))


def _parse_python(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())


def _import_roots(source_root: Path) -> set[str]:
    roots: set[str] = set()
    for source_file in _python_files(source_root):
        tree = _parse_python(source_file)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".", maxsplit=1)[0])
    return roots


def _declared_class_names(source_root: Path) -> set[str]:
    names: set[str] = set()
    for source_file in _python_files(source_root):
        tree = _parse_python(source_file)
        names.update(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    return names


def _function_names(source_root: Path) -> set[str]:
    names: set[str] = set()
    for source_file in _python_files(source_root):
        tree = _parse_python(source_file)
        names.update(
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        )
    return names


def _assert_no_security_failure(condition: bool, message: str) -> None:
    assert condition, f"{SECURITY_FAILURE}: {message}"


def test_security_vocabularies_are_exact_and_do_not_collapse_controls() -> None:
    _assert_no_security_failure(
        EFFECT_CLASSIFICATION_VALUES
        == (
            "READ_ONLY",
            "LOCAL_WRITE",
            "EXTERNAL_READ",
            "EXTERNAL_WRITE",
            "DESTRUCTIVE",
            "SECRET_ACCESS",
            "NETWORK_ACCESS",
            "EXECUTION",
        ),
        "effect classification vocabulary changed",
    )
    _assert_no_security_failure(
        "APPROVAL_REQUIRED" not in EFFECT_CLASSIFICATION_VALUES,
        "approval must remain a policy/control outcome, not an effect",
    )
    _assert_no_security_failure(
        RISK_CLASSIFICATION_VALUES == ("LOW", "MODERATE", "HIGH", "CRITICAL"),
        "risk classification vocabulary changed",
    )
    _assert_no_security_failure(
        POLICY_DECISION_OUTCOME_VALUES == ("ALLOW", "DENY", "REQUIRES_APPROVAL", "UNKNOWN"),
        "policy decision outcome vocabulary changed",
    )
    _assert_no_security_failure(
        APPROVAL_OUTCOME_VALUES == ("PENDING", "APPROVED", "REJECTED"),
        "approval outcome vocabulary changed",
    )
    _assert_no_security_failure(
        CONFIGURATION_PROFILE_VALUES == ("LOCAL_DOCKER",),
        "canonical configuration profile vocabulary changed",
    )
    _assert_no_security_failure(
        GOVERNED_EFFECT_VALUES == EFFECT_CLASSIFICATION_VALUES,
        "governed effects must track the canonical M0 effect vocabulary",
    )
    _assert_no_security_failure(
        set(EFFECT_CLASSIFICATION_VALUES).isdisjoint(RISK_CLASSIFICATION_VALUES),
        "effect and risk vocabularies must remain separate",
    )


def test_unknown_policy_for_governed_effects_is_not_authorizing_or_rewritten() -> None:
    decision = PolicyDecision(
        subject_ref=ObjectReference.from_id(fixed_id(WorkId)),
        principal=human_principal(),
        requested_effects=tuple(EffectClassification),
        resource_refs=(_provider_ref(),),
        scope="project sandbox",
        outcome=PolicyDecisionOutcome.UNKNOWN,
        reason="policy unavailable",
        decided_at=UTC_NOW,
    )
    serialized = decision.to_json_compatible()
    parsed = PolicyDecision.from_json_compatible(serialized)

    _assert_no_security_failure(serialized["outcome"] == "UNKNOWN", "UNKNOWN was not serialized")
    _assert_no_security_failure(
        parsed.outcome is PolicyDecisionOutcome.UNKNOWN,
        "UNKNOWN was not preserved during round trip",
    )
    _assert_no_security_failure(not decision.is_authorizing, "UNKNOWN must not authorize effects")
    _assert_no_security_failure(
        decision.outcome is not PolicyDecisionOutcome.DENY,
        "UNKNOWN must not be rewritten as DENY",
    )
    _assert_no_security_failure(
        set(serialized["requested_effects"]) == set(GOVERNED_EFFECT_VALUES),  # type: ignore[arg-type]
        "governed effect set was not represented in policy decision evidence",
    )


def test_security_records_do_not_serialize_secret_values_or_credential_fields() -> None:
    serialized_records = [to_json_compatible(record) for record in _security_records()]
    json.dumps(serialized_records, allow_nan=False, sort_keys=True)

    for node in _walk(serialized_records):
        if isinstance(node, str):
            _assert_no_security_failure(
                SECRET_SHAPED_VALUE_RE.search(node) is None,
                "serialized security records must not contain secret-shaped key/value material",
            )
    for node in _walk(serialized_records):
        if isinstance(node, dict):
            prohibited = set(node).intersection(PROHIBITED_SECRET_VALUE_FIELDS)
            _assert_no_security_failure(
                not prohibited,
                "serialized security records expose prohibited secret field(s): "
                f"{sorted(prohibited)}",
            )


def test_secret_principal_and_authority_contracts_reject_secret_value_shapes() -> None:
    with pytest.raises(ValueError, match="secret-shaped"):
        SecretReference(
            secret_provider_ref=_provider_ref(),
            name="password=supersecret",
            scope="local",
            purpose="database",
        )
    with pytest.raises(ValueError, match="credential-bearing URLs"):
        Permission(
            action="read",
            resource_type="artifact",
            scope="https://user:password@example.test/resource",
            permitted_effects=(EffectClassification.EXTERNAL_READ,),
        )
    with pytest.raises(ValueError, match="unexpected field"):
        Principal.from_json_compatible(
            {
                "principal_type": "HUMAN",
                "identity": "operator",
                "credentials": {"token": "secret"},
            }
        )


def test_security_contract_dataclass_fields_do_not_add_secret_value_slots() -> None:
    security_contracts = (
        Approval,
        Authority,
        ConfigurationProfile,
        Permission,
        PolicyDecision,
        Principal,
        SecretReference,
    )
    for contract in security_contracts:
        field_names = {field.name for field in fields(contract)}
        prohibited = field_names.intersection(PROHIBITED_SECRET_VALUE_FIELDS)
        _assert_no_security_failure(
            not prohibited,
            f"{contract.__name__} declares prohibited secret field(s): {sorted(prohibited)}",
        )


def test_security_contract_source_has_no_runtime_security_imports() -> None:
    import_roots = _import_roots(CONTRACTS_SOURCE)
    violations = import_roots.intersection(SECURITY_IMPLEMENTATION_IMPORTS)

    _assert_no_security_failure(
        not violations,
        "curios_contracts imports security/provider/runtime implementation roots: "
        f"{sorted(violations)}",
    )


def test_local_docker_configuration_examples_remain_placeholder_and_curios_prefixed() -> None:
    env_files = sorted(path for path in (REPO_ROOT / "infrastructure").rglob(".env*"))
    _assert_no_security_failure(
        env_files == [LOCAL_DOCKER_ENV_EXAMPLE],
        "only the committed LOCAL_DOCKER .env.example may exist under infrastructure",
    )

    entries = [
        line.strip()
        for line in LOCAL_DOCKER_ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    _assert_no_security_failure(entries != [], "LOCAL_DOCKER .env.example is empty")
    for entry in entries:
        name, separator, value = entry.partition("=")
        _assert_no_security_failure(separator == "=", "environment entry lacks assignment")
        _assert_no_security_failure(
            name.startswith("CURIOS_"),
            f"environment variable {name!r} must use the CURIOS_ prefix",
        )
        _assert_no_security_failure(value != "", f"environment variable {name!r} is empty")
        _assert_no_security_failure(
            "\n" not in value and "\r" not in value,
            f"environment variable {name!r} contains line breaks",
        )


def test_core_context_and_services_do_not_implement_security_authority_engines() -> None:
    core_context_fields = set(get_type_hints(CoreContext))
    _assert_no_security_failure(
        core_context_fields == {"observability", "authority"},
        f"CoreContext field set changed: {sorted(core_context_fields)}",
    )
    _assert_no_security_failure(
        get_type_hints(CoreContext)["authority"] == Authority | None,
        "CoreContext authority must remain the frozen optional Authority contract",
    )
    _assert_no_security_failure(
        _declared_class_names(CORE_SOURCE).isdisjoint(CORE_SECURITY_RUNTIME_NAMES),
        "curios_core declared a deferred security runtime class",
    )
    forbidden_methods = {
        name
        for name in _function_names(CORE_SOURCE)
        if any(part in name for part in CORE_FORBIDDEN_SECURITY_METHOD_PARTS)
    }
    _assert_no_security_failure(
        not forbidden_methods,
        f"curios_core declared deferred security authority method(s): {sorted(forbidden_methods)}",
    )

    result = CoreServices().list_provider_descriptors(CoreContext())
    _assert_no_security_failure(result.value == (), "CoreServices changed default behavior")


def test_later_task_security_provider_runtime_surfaces_remain_absent() -> None:
    existing = [path for path in LATER_TASK_PATHS if (REPO_ROOT / path).exists()]

    _assert_no_security_failure(
        not existing,
        f"TASK-BOOT-018+ path(s) unexpectedly exist: {existing}",
    )
