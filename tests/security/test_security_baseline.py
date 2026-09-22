from __future__ import annotations

import ast
import json
import re
import subprocess
import tomllib
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
ROOT_PACKAGE_FILES = (
    REPO_ROOT / "package.json",
    REPO_ROOT / "pnpm-workspace.yaml",
    REPO_ROOT / "pyproject.toml",
)

SECURITY_FAILURE = "SECURITY_FAILURE"

SECRET_SHAPED_VALUE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|client[_-]?secret|credential|password|private[_-]?key|secret|token|access[_-]?token)\s*[:=]"
)
SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    (?P<key>
        [A-Za-z0-9_.-]*
        (?:api[_-]?key|authorization|client[_-]?secret|credential|password|private[_-]?key|secret|token|access[_-]?token)
        [A-Za-z0-9_.-]*
    )
    \s*[:=]\s*
    (?P<quote>['"]?)
    (?P<value>[^\s'"#]+)
    (?P=quote)
    """
)
CREDENTIAL_URL_RE = re.compile(r"://[^/\s:@]+(?::[^/\s@]*)?@")
SECRET_FIELD_TOKEN_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|client[_-]?secret|credential|password|private[_-]?key|secret|session|token|access[_-]?token|cookie)"
)
PROHIBITED_SECRET_VALUE_FIELDS = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "client_secret",
        "cookie",
        "credential",
        "credentials",
        "oauth_token",
        "password",
        "private_key",
        "secret",
        "secret_key",
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
    "services",
    "providers",
    "packages/python/curios_postgres",
    "packages/python/curios_telemetry",
)
AUTHORIZED_BOOT019_INTEGRATION_TESTS = frozenset(
    {
        "tests/integration/test_postgres_provider_integration.py",
    }
)
ALLOWED_TOP_LEVEL_PATHS = frozenset(
    {
        ".editorconfig",
        ".gitignore",
        ".prettierignore",
        "README.md",
        "apps",
        "docs",
        "eslint.config.mjs",
        "infrastructure",
        "package.json",
        "packages",
        "pnpm-lock.yaml",
        "pnpm-workspace.yaml",
        "prettier.config.mjs",
        "pyproject.toml",
        "tests",
        "tooling",
        "tsconfig.base.json",
        "tsconfig.json",
        "uv.lock",
    }
)
ALLOWED_APP_ROOTS = frozenset(
    {
        "apps/api",
        "apps/web",
    }
)
ALLOWED_PACKAGE_ROOTS = frozenset(
    {
        "packages/python/curios_config",
        "packages/python/curios_contracts",
        "packages/python/curios_core",
        "packages/python/curios_ollama",
        "packages/python/curios_observability",
        "packages/python/curios_postgres_provider",
        "packages/typescript/curios-contracts",
    }
)
ALLOWED_CORE_SOURCE_FILES = frozenset(
    {
        "__init__.py",
        "application.py",
        "context.py",
        "ports/__init__.py",
        "ports/providers.py",
        "py.typed",
    }
)
ALLOWED_CORE_EXPORTS = frozenset(
    {
        "CoreContext",
        "CoreServices",
        "ProviderCatalog",
        "ProviderDescriptorsResult",
        "__version__",
    }
)
SECRET_FIELD_ALLOWLIST = {
    SecretReference: frozenset(
        {
            "key",
            "name",
            "purpose",
            "resolver_ref",
            "scope",
            "secret_provider_ref",
        }
    )
}
SECURITY_SCAN_ROOTS = (
    "apps/api/src",
    "apps/api/tests",
    "apps/web",
    "docs",
    "infrastructure",
    "packages/python/curios_config/src",
    "packages/python/curios_contracts/src",
    "packages/python/curios_core/src",
    "packages/python/curios_observability/src",
    "packages/python/curios_ollama/src",
    "packages/python/curios_postgres_provider/src",
    "packages/typescript/curios-contracts/src",
)
SECURITY_SCAN_ROOT_FILES = frozenset(
    {
        ".editorconfig",
        ".gitignore",
        ".prettierignore",
        "README.md",
        "eslint.config.mjs",
        "package.json",
        "pnpm-workspace.yaml",
        "prettier.config.mjs",
        "pyproject.toml",
        "tsconfig.base.json",
        "tsconfig.json",
    }
)
SECURITY_SCAN_SUFFIXES = frozenset(
    {
        ".env.example",
        ".css",
        ".html",
        ".js",
        ".json",
        ".md",
        ".mjs",
        ".py",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".yaml",
        ".yml",
    }
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


def _tracked_files() -> tuple[Path, ...]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    return tuple(REPO_ROOT / line for line in result.stdout.splitlines() if line)


def _tracked_security_scan_files() -> tuple[Path, ...]:
    scanned: list[Path] = []
    for path in _tracked_files():
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative in SECURITY_SCAN_ROOT_FILES or any(
            relative == root or relative.startswith(f"{root}/") for root in SECURITY_SCAN_ROOTS
        ):
            if path.name in {"pnpm-lock.yaml", "uv.lock"}:
                continue
            if path.name == ".env.example" or path.suffix in SECURITY_SCAN_SUFFIXES:
                scanned.append(path)
    return tuple(sorted(scanned))


def _relative_repo_path(path: Path) -> str:
    if path.is_absolute():
        return path.relative_to(REPO_ROOT).as_posix()
    return path.as_posix()


def _is_approved_placeholder(path: Path, key: str, value: str) -> bool:
    relative = _relative_repo_path(path)
    if relative == "infrastructure/local/docker/.env.example":
        return (
            key.startswith("CURIOS_")
            and value.startswith("curios_")
            and ("dev" in value or "local" in value)
        )
    if relative == "infrastructure/local/docker/compose.yaml":
        return key == "POSTGRES_PASSWORD" and value.startswith("${CURIOS_POSTGRES_PASSWORD:-")
    return False


def _is_sensitive_name(name: str) -> bool:
    return SECRET_FIELD_TOKEN_RE.search(name) is not None


def _looks_like_secret_value(value: str) -> bool:
    if value == "":
        return False
    if value.startswith(("sk-", "pk_", "ghp_", "gho_", "xoxb-", "AKIA")):
        return True
    if SECRET_SHAPED_VALUE_RE.search(value) is not None:
        return True
    has_lower = any(character.islower() for character in value)
    has_upper = any(character.isupper() for character in value)
    has_digit = any(character.isdigit() for character in value)
    return len(value) >= 20 and sum((has_lower, has_upper, has_digit)) >= 2


def _python_secret_scan_violations(path: Path, text: str) -> tuple[str, ...]:
    violations: list[str] = []
    tree = ast.parse(text, filename=path.as_posix())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if CREDENTIAL_URL_RE.search(node.value) is not None:
                violations.append(f"{path}:{node.lineno}: credential-bearing URL")
        elif isinstance(node, ast.Assign):
            target_names = [
                target.id
                for target in node.targets
                if isinstance(target, ast.Name) and _is_sensitive_name(target.id)
            ]
            if (
                target_names
                and isinstance(node.value, ast.Constant)
                and isinstance(
                    node.value.value,
                    str,
                )
            ):
                value = node.value.value
                if _looks_like_secret_value(value):
                    violations.append(
                        f"{path}:{node.lineno}: secret-shaped assignment {target_names[0]!r}"
                    )
        elif isinstance(node, ast.AnnAssign):
            if (
                isinstance(node.target, ast.Name)
                and _is_sensitive_name(node.target.id)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
                and _looks_like_secret_value(node.value.value)
            ):
                violations.append(
                    f"{path}:{node.lineno}: secret-shaped assignment {node.target.id!r}"
                )
        elif isinstance(node, ast.keyword):
            if (
                node.arg is not None
                and _is_sensitive_name(node.arg)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
                and _looks_like_secret_value(node.value.value)
            ):
                violations.append(f"{path}:{node.value.lineno}: secret-shaped keyword {node.arg!r}")
        elif isinstance(node, ast.Dict):
            for key, value_node in zip(node.keys, node.values, strict=False):
                if (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and _is_sensitive_name(key.value)
                    and isinstance(value_node, ast.Constant)
                    and isinstance(value_node.value, str)
                    and _looks_like_secret_value(value_node.value)
                ):
                    violations.append(
                        f"{path}:{value_node.lineno}: secret-shaped mapping key {key.value!r}"
                    )
    return tuple(violations)


def _secret_scan_violations_for_text(path: Path, text: str) -> tuple[str, ...]:
    if path.suffix == ".py":
        return _python_secret_scan_violations(path, text)

    violations: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if CREDENTIAL_URL_RE.search(line) is not None:
            violations.append(f"{path}:{line_number}: credential-bearing URL")
        for match in SENSITIVE_ASSIGNMENT_RE.finditer(line):
            key = match.group("key")
            value = match.group("value").rstrip(",;")
            if _is_approved_placeholder(path, key, value):
                continue
            violations.append(f"{path}:{line_number}: secret-shaped assignment {key!r}")
    return tuple(violations)


def _secret_field_violations(contract: type[object]) -> tuple[str, ...]:
    allowed_fields = SECRET_FIELD_ALLOWLIST.get(contract, frozenset())
    violations: list[str] = []
    for field in fields(contract):
        if field.name in allowed_fields:
            continue
        if SECRET_FIELD_TOKEN_RE.search(field.name) is not None:
            violations.append(field.name)
    return tuple(sorted(violations))


def _tracked_package_roots() -> frozenset[str]:
    roots: set[str] = set()
    for path in _tracked_files():
        parts = path.relative_to(REPO_ROOT).parts
        if len(parts) >= 3 and parts[0] == "packages":
            roots.add("/".join(parts[:3]))
    return frozenset(roots)


def _tracked_app_roots() -> frozenset[str]:
    roots: set[str] = set()
    for path in _tracked_files():
        parts = path.relative_to(REPO_ROOT).parts
        if len(parts) >= 2 and parts[0] == "apps":
            roots.add("/".join(parts[:2]))
    return frozenset(roots)


def _tracked_integration_tests() -> frozenset[str]:
    return frozenset(
        path.relative_to(REPO_ROOT).as_posix()
        for path in _tracked_files()
        if path.relative_to(REPO_ROOT).as_posix().startswith("tests/integration/")
    )


def _tracked_top_level_paths() -> frozenset[str]:
    return frozenset(path.relative_to(REPO_ROOT).parts[0] for path in _tracked_files())


def _core_source_files() -> frozenset[str]:
    return frozenset(
        path.relative_to(CORE_SOURCE).as_posix()
        for path in _tracked_files()
        if path.is_relative_to(CORE_SOURCE)
    )


def _core_public_exports() -> frozenset[str]:
    source = (CORE_SOURCE / "__init__.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename=(CORE_SOURCE / "__init__.py").as_posix())
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
            )
            and isinstance(node.value, ast.Tuple)
        ):
            values = [
                item.value
                for item in node.value.elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            ]
            return frozenset(values)
    return frozenset()


def _pnpm_workspace_packages(path: Path) -> frozenset[str]:
    packages: set[str] = set()
    in_packages_block = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped == "packages:":
            in_packages_block = True
            continue
        if in_packages_block and stripped.startswith("- "):
            packages.add(stripped[2:].strip("\"'"))
        elif in_packages_block and stripped and not raw_line.startswith(" "):
            break
    return frozenset(packages)


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


def test_tracked_security_surfaces_do_not_contain_secret_shaped_literals() -> None:
    violations = tuple(
        violation
        for path in _tracked_security_scan_files()
        for violation in _secret_scan_violations_for_text(
            path,
            path.read_text(encoding="utf-8"),
        )
    )

    _assert_no_security_failure(
        not violations,
        f"tracked security-scanned surfaces contain secret-shaped literals: {list(violations)}",
    )


def test_secret_scanner_rejects_secret_literals_and_allows_documented_placeholders() -> None:
    real_source = REPO_ROOT / "packages/python/curios_contracts/src/example.py"
    placeholder = REPO_ROOT / "infrastructure/local/docker/.env.example"

    assert _secret_scan_violations_for_text(real_source, 'api_key = "sk-live-value"')
    assert _secret_scan_violations_for_text(
        real_source,
        "url = 'https://user:password@example.test/resource'",
    )
    assert not _secret_scan_violations_for_text(
        placeholder,
        "CURIOS_POSTGRES_PASSWORD=curios_local_dev_password",
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
        prohibited = _secret_field_violations(contract)
        _assert_no_security_failure(
            not prohibited,
            f"{contract.__name__} declares prohibited secret field(s): {sorted(prohibited)}",
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "access_token",
        "api_key",
        "client_secret",
        "credential_material",
        "password",
        "private_key",
        "secret",
        "secret_key",
        "session_cookie",
    ),
)
def test_secret_field_detector_rejects_semantic_secret_value_variants(field_name: str) -> None:
    namespace = {"__annotations__": {field_name: str}}
    synthetic = type("SyntheticSecurityRecord", (), namespace)

    # Convert the synthetic class to a dataclass after construction so the
    # detector exercises real dataclass field metadata rather than raw strings.
    from dataclasses import dataclass

    synthetic_dataclass = dataclass(frozen=True)(synthetic)

    assert _secret_field_violations(synthetic_dataclass)


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
    _assert_no_security_failure(
        _core_source_files() == ALLOWED_CORE_SOURCE_FILES,
        f"curios_core source topology changed: {sorted(_core_source_files())}",
    )
    _assert_no_security_failure(
        _core_public_exports() == ALLOWED_CORE_EXPORTS,
        f"curios_core public exports changed: {sorted(_core_public_exports())}",
    )
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


def test_later_task_security_provider_runtime_surfaces_match_authorized_boot024_boundary() -> None:
    existing = [path for path in LATER_TASK_PATHS if (REPO_ROOT / path).exists()]
    unexpected_integration_tests = (
        _tracked_integration_tests() - AUTHORIZED_BOOT019_INTEGRATION_TESTS
    )
    unexpected_top_level = _tracked_top_level_paths() - ALLOWED_TOP_LEVEL_PATHS
    unexpected_apps = _tracked_app_roots() - ALLOWED_APP_ROOTS
    unexpected_packages = _tracked_package_roots() - ALLOWED_PACKAGE_ROOTS
    root_pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    python_workspace_members = frozenset(root_pyproject["tool"]["uv"]["workspace"]["members"])
    node_workspaces = _pnpm_workspace_packages(REPO_ROOT / "pnpm-workspace.yaml")

    _assert_no_security_failure(
        not existing,
        f"deferred provider/API/runtime path(s) unexpectedly exist: {existing}",
    )
    _assert_no_security_failure(
        not unexpected_integration_tests,
        "unexpected integration test path(s) outside TASK-BOOT-019: "
        f"{sorted(unexpected_integration_tests)}",
    )
    _assert_no_security_failure(
        not unexpected_top_level,
        f"unexpected tracked top-level path(s): {sorted(unexpected_top_level)}",
    )
    _assert_no_security_failure(
        not unexpected_apps,
        f"unexpected tracked application root(s): {sorted(unexpected_apps)}",
    )
    _assert_no_security_failure(
        not unexpected_packages,
        f"unexpected tracked package root(s): {sorted(unexpected_packages)}",
    )
    _assert_no_security_failure(
        python_workspace_members
        == {
            "apps/api",
            "packages/python/curios_config",
            "packages/python/curios_contracts",
            "packages/python/curios_core",
            "packages/python/curios_ollama",
            "packages/python/curios_observability",
            "packages/python/curios_postgres_provider",
        },
        f"unexpected Python workspace member(s): {sorted(python_workspace_members)}",
    )
    _assert_no_security_failure(
        node_workspaces == {"apps/*", "packages/typescript/*"},
        f"unexpected Node workspace member(s): {sorted(node_workspaces)}",
    )
