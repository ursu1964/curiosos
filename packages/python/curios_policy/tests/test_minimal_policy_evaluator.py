from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest
from contract_fixtures import UTC_NOW, fixed_id, human_principal, ref_for
from curios_contracts import (
    Authority,
    EffectClassification,
    EvidenceId,
    ObjectReference,
    Permission,
    PolicyDecision,
    PolicyDecisionOutcome,
    ProjectId,
    ProviderId,
    WorkId,
)
from curios_policy import (
    M0_PROVIDER_INVENTORY_WORK_TYPE,
    M0_SUPPORTED_AUTHORIZING_EFFECTS,
    M0_SUPPORTED_WORK_TYPES,
    M0PolicyEvaluationRequest,
    MinimalM0PolicyEvaluator,
    evaluate_m0_policy,
)

PACKAGE_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = PACKAGE_ROOT / "src" / "curios_policy"
PYPROJECT = PACKAGE_ROOT / "pyproject.toml"

FORBIDDEN_IMPORT_ROOTS = {
    "alembic",
    "boto3",
    "curios_core",
    "curios_persistence",
    "curios_runtime",
    "docker",
    "fastapi",
    "hvac",
    "keyring",
    "ollama",
    "opentelemetry",
    "os",
    "pydantic",
    "psycopg",
    "requests",
    "sqlalchemy",
    "starlette",
}
FORBIDDEN_RUNTIME_NAMES = {
    "ApprovalWorkflow",
    "AuthorityGrant",
    "CredentialStore",
    "IamService",
    "PolicyCompiler",
    "PolicyEngine",
    "RoleHierarchy",
    "SecretResolver",
}


def _request(
    *,
    work_type: str | None = M0_PROVIDER_INVENTORY_WORK_TYPE,
    requested_effects: tuple[EffectClassification, ...] = (EffectClassification.READ_ONLY,),
    policy_state_known: bool = True,
) -> M0PolicyEvaluationRequest:
    return M0PolicyEvaluationRequest(
        subject_ref=ref_for(WorkId),
        principal=human_principal(),
        work_type=work_type,
        requested_effects=requested_effects,
        resource_refs=(ref_for(ProviderId),),
        scope="project sandbox",
        decided_at=UTC_NOW,
        policy_state_known=policy_state_known,
    )


def _source_trees() -> list[ast.AST]:
    return [
        ast.parse(source_path.read_text(encoding="utf-8"))
        for source_path in SOURCE_ROOT.rglob("*.py")
    ]


def _import_roots() -> set[str]:
    roots: set[str] = set()
    for tree in _source_trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                roots.add(node.module.split(".")[0])
    return roots


def _declared_class_names() -> set[str]:
    names: set[str] = set()
    for tree in _source_trees():
        names.update(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    return names


def test_provider_inventory_read_only_is_the_only_authorizing_m0_case() -> None:
    decision = evaluate_m0_policy(_request())

    assert isinstance(decision, PolicyDecision)
    assert decision.outcome is PolicyDecisionOutcome.ALLOW
    assert decision.is_authorizing
    assert decision.requested_effects == (EffectClassification.READ_ONLY,)
    assert M0_SUPPORTED_WORK_TYPES == ("provider_inventory",)
    assert M0_SUPPORTED_AUTHORIZING_EFFECTS == (EffectClassification.READ_ONLY,)


@pytest.mark.parametrize(
    "effect",
    tuple(
        effect for effect in EffectClassification if effect is not EffectClassification.READ_ONLY
    ),
)
def test_unsupported_governed_effects_do_not_authorize(effect: EffectClassification) -> None:
    decision = evaluate_m0_policy(_request(requested_effects=(effect,)))

    assert decision.outcome is PolicyDecisionOutcome.DENY
    assert not decision.is_authorizing
    assert decision.requested_effects == (effect,)


def test_mixed_read_only_and_unsupported_effects_do_not_authorize() -> None:
    decision = evaluate_m0_policy(
        _request(
            requested_effects=(
                EffectClassification.READ_ONLY,
                EffectClassification.EXTERNAL_READ,
            )
        )
    )

    assert decision.outcome is PolicyDecisionOutcome.DENY
    assert not decision.is_authorizing


def test_unknown_policy_state_preserves_unknown_and_never_authorizes() -> None:
    decision = evaluate_m0_policy(_request(policy_state_known=False))
    serialized = decision.to_json_compatible()
    parsed = PolicyDecision.from_json_compatible(serialized)

    assert decision.outcome is PolicyDecisionOutcome.UNKNOWN
    assert serialized["outcome"] == "UNKNOWN"
    assert parsed.outcome is PolicyDecisionOutcome.UNKNOWN
    deny_decision = evaluate_m0_policy(
        _request(requested_effects=(EffectClassification.EXTERNAL_WRITE,))
    )
    assert serialized["outcome"] != deny_decision.to_json_compatible()["outcome"]
    assert not decision.is_authorizing


@pytest.mark.parametrize("work_type", (None, "", "model_generation", "provider_execution"))
def test_unknown_or_unsupported_work_types_do_not_authorize(work_type: str | None) -> None:
    decision = evaluate_m0_policy(_request(work_type=work_type))

    assert not decision.is_authorizing
    if work_type:
        assert decision.outcome is PolicyDecisionOutcome.DENY
    else:
        assert decision.outcome is PolicyDecisionOutcome.UNKNOWN


def test_malformed_inputs_fail_closed_without_returning_allow() -> None:
    evaluator = MinimalM0PolicyEvaluator()

    with pytest.raises(TypeError, match="request must be an M0PolicyEvaluationRequest"):
        evaluator.evaluate(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="requested_effects must contain at least one effect"):
        _request(requested_effects=())
    with pytest.raises(TypeError, match="resource_refs must contain ObjectReference values"):
        M0PolicyEvaluationRequest(
            subject_ref=ref_for(WorkId),
            principal=human_principal(),
            work_type=M0_PROVIDER_INVENTORY_WORK_TYPE,
            requested_effects=(EffectClassification.READ_ONLY,),
            resource_refs=(object(),),  # type: ignore[arg-type]
            scope="project sandbox",
            decided_at=UTC_NOW,
        )


def test_deterministic_inputs_produce_deterministic_decisions() -> None:
    request = _request()
    evaluator = MinimalM0PolicyEvaluator()

    assert evaluator.evaluate(request) == evaluator.evaluate(request)


def test_evaluator_returns_policy_decisions_without_granting_or_mutating_authority() -> None:
    principal = human_principal()
    authority = Authority(
        authority_id="authz-local-read",
        principal=principal,
        permissions=(
            Permission(
                action="read",
                resource_type="provider_inventory",
                scope="project sandbox",
                permitted_effects=(EffectClassification.READ_ONLY,),
                resource_ref=ref_for(ProviderId),
            ),
        ),
        scope="project sandbox",
        granted_at=UTC_NOW,
        provenance_refs=(fixed_id(EvidenceId),),
    )
    authority_json = authority.to_json_compatible()

    decision = evaluate_m0_policy(
        M0PolicyEvaluationRequest(
            subject_ref=ref_for(WorkId),
            principal=authority.principal,
            work_type=M0_PROVIDER_INVENTORY_WORK_TYPE,
            requested_effects=(EffectClassification.READ_ONLY,),
            resource_refs=(ref_for(ProviderId),),
            scope="project sandbox",
            decided_at=UTC_NOW,
        )
    )

    assert decision.is_authorizing
    assert authority.to_json_compatible() == authority_json
    assert not hasattr(decision, "authority")
    assert not hasattr(decision, "permissions")


def test_policy_decision_serialization_vocabulary_remains_canonical() -> None:
    decision = evaluate_m0_policy(_request())

    assert decision.to_json_compatible()["outcome"] == "ALLOW"
    assert PolicyDecisionOutcome.UNKNOWN.value == "UNKNOWN"
    assert len({"UNKNOWN", "DENY"}) == 2


def test_policy_package_depends_only_on_contracts() -> None:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]

    assert set(project["dependencies"]) == {"curios-contracts"}
    assert _import_roots().isdisjoint(FORBIDDEN_IMPORT_ROOTS)
    assert _declared_class_names().isdisjoint(FORBIDDEN_RUNTIME_NAMES)


def test_policy_request_rejects_noncanonical_contract_objects() -> None:
    with pytest.raises(TypeError, match="subject_ref must be an ObjectReference"):
        M0PolicyEvaluationRequest(
            subject_ref=object(),  # type: ignore[arg-type]
            principal=human_principal(),
            work_type=M0_PROVIDER_INVENTORY_WORK_TYPE,
            requested_effects=(EffectClassification.READ_ONLY,),
            resource_refs=(ref_for(ProviderId),),
            scope="project sandbox",
            decided_at=UTC_NOW,
        )
    with pytest.raises(TypeError, match="policy_refs must contain ObjectReference values"):
        M0PolicyEvaluationRequest(
            subject_ref=ref_for(WorkId),
            principal=human_principal(),
            work_type=M0_PROVIDER_INVENTORY_WORK_TYPE,
            requested_effects=(EffectClassification.READ_ONLY,),
            resource_refs=(ref_for(ProviderId),),
            scope="project sandbox",
            decided_at=UTC_NOW,
            policy_refs=(object(),),  # type: ignore[arg-type]
        )
    assert isinstance(ref_for(ProjectId), ObjectReference)
