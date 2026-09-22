from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest
from curios_config import (
    ConfigurationProvider,
    StaticConfigurationProvider,
    local_docker_configuration_profile,
    local_docker_configuration_provider,
)
from curios_contracts import (
    ConfigurationProfile,
    ConfigurationProfileName,
    Result,
    ResultStatus,
)

SOURCE_ROOT = Path(__file__).parents[1] / "src" / "curios_config"
PACKAGE_ROOT = Path(__file__).parents[1]
PYPROJECT = PACKAGE_ROOT / "pyproject.toml"

FORBIDDEN_IMPORT_ROOTS = {
    "alembic",
    "boto3",
    "curios_core",
    "docker",
    "dotenv",
    "fastapi",
    "httpx",
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
    "AuthorityProvider",
    "IamService",
    "PolicyEngine",
    "SecretResolver",
    "Settings",
}


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


def test_local_docker_configuration_profile_is_canonical_contract() -> None:
    profile = local_docker_configuration_profile()

    assert isinstance(profile, ConfigurationProfile)
    assert profile.profile is ConfigurationProfileName.LOCAL_DOCKER
    assert profile.to_json_compatible() == {
        "profile": "LOCAL_DOCKER",
        "schema_version": "1.0.0",
        "description": "Local Docker development profile identity.",
    }


def test_static_configuration_provider_returns_profile_result() -> None:
    provider = local_docker_configuration_provider()
    result = provider.load_configuration_profile()

    assert isinstance(provider, ConfigurationProvider)
    assert isinstance(result, Result)
    assert result.status is ResultStatus.SUCCESS
    assert result.value == local_docker_configuration_profile()


def test_static_configuration_provider_accepts_only_canonical_profile() -> None:
    profile = local_docker_configuration_profile()

    assert (
        StaticConfigurationProvider(profile=profile).load_configuration_profile().value is profile
    )
    with pytest.raises(TypeError, match="profile must be a ConfigurationProfile"):
        StaticConfigurationProvider(profile=object())  # type: ignore[arg-type]


def test_configuration_provider_source_has_no_framework_or_runtime_imports() -> None:
    assert _import_roots().isdisjoint(FORBIDDEN_IMPORT_ROOTS)


def test_configuration_provider_does_not_define_settings_or_deferred_engines() -> None:
    assert _declared_class_names().isdisjoint(FORBIDDEN_RUNTIME_NAMES)


def test_configuration_provider_package_depends_only_on_contracts() -> None:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    dependencies = set(project["dependencies"])

    assert dependencies == {"curios-contracts"}
    for dependency in FORBIDDEN_IMPORT_ROOTS:
        assert dependency not in dependencies
