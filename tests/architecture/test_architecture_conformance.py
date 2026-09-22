from __future__ import annotations

import ast
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

CONTRACTS_PACKAGE = REPO_ROOT / "packages/python/curios_contracts"
CONTRACTS_SOURCE = CONTRACTS_PACKAGE / "src/curios_contracts"
CORE_PACKAGE = REPO_ROOT / "packages/python/curios_core"
CORE_SOURCE = CORE_PACKAGE / "src/curios_core"
TYPESCRIPT_CONTRACTS_PACKAGE = REPO_ROOT / "packages/typescript/curios-contracts"
TYPESCRIPT_CONTRACTS_WORKSPACE = "packages/typescript/curios-contracts"

ARCHITECTURE_FAILURE = "ARCHITECTURE_FAILURE"

CONTRACTS_RULE = "curios_contracts must not depend on provider/framework/runtime packages"
CORE_RULE = "curios_core must not depend on provider/framework/runtime packages"
PROVIDER_DIRECTION_RULE = "contracts/core must not depend outward on provider implementations"
CANONICAL_SQLALCHEMY_RULE = "canonical contract classes must not be SQLAlchemy ORM models"
CANONICAL_FASTAPI_RULE = "FastAPI request/response models must not become canonical authority"
CANONICAL_PROVIDER_TYPE_RULE = "provider-native types must not appear in canonical contracts"
OBJECT_REFERENCE_RULE = "ObjectReference is the single generic reference abstraction"
FRONTEND_DIRECTION_RULE = "TypeScript package must not be upstream of canonical semantics"
INFRASTRUCTURE_RULE = "canonical domain packages must not import tooling or infrastructure"

FASTAPI_IMPORTS = frozenset({"fastapi", "starlette"})
SQLALCHEMY_IMPORTS = frozenset({"alembic", "sqlalchemy", "sqlmodel"})
POSTGRES_IMPORTS = frozenset({"asyncpg", "pg8000", "psycopg", "psycopg2"})
OLLAMA_PROVIDER_SDK_IMPORTS = frozenset(
    {
        "anthropic",
        "boto3",
        "cohere",
        "google.genai",
        "langchain",
        "llama_index",
        "ollama",
        "openai",
    }
)
OTEL_IMPLEMENTATION_IMPORTS = frozenset(
    {
        "opentelemetry.exporter",
        "opentelemetry.instrumentation",
        "opentelemetry.sdk",
    }
)
DOCKER_TOOLING_IMPORTS = frozenset({"compose", "docker", "python_on_whales"})
FRONTEND_RUNTIME_IMPORTS = frozenset({"node", "npm", "react", "typescript", "vite"})
REPOSITORY_TOOLING_IMPORTS = frozenset({"infrastructure", "tooling"})

CONTRACTS_FORBIDDEN_IMPORTS = frozenset(
    {
        "curios_core",
        *FASTAPI_IMPORTS,
        *SQLALCHEMY_IMPORTS,
        *POSTGRES_IMPORTS,
        *OLLAMA_PROVIDER_SDK_IMPORTS,
        *OTEL_IMPLEMENTATION_IMPORTS,
        *DOCKER_TOOLING_IMPORTS,
        *FRONTEND_RUNTIME_IMPORTS,
        *REPOSITORY_TOOLING_IMPORTS,
    }
)

CORE_FORBIDDEN_IMPORTS = frozenset(
    {
        *FASTAPI_IMPORTS,
        *SQLALCHEMY_IMPORTS,
        *POSTGRES_IMPORTS,
        *OLLAMA_PROVIDER_SDK_IMPORTS,
        *OTEL_IMPLEMENTATION_IMPORTS,
        *DOCKER_TOOLING_IMPORTS,
        *REPOSITORY_TOOLING_IMPORTS,
    }
)

SQLALCHEMY_ORM_MARKERS = frozenset(
    {
        "DeclarativeBase",
        "MappedAsDataclass",
        "as_declarative",
        "declarative_base",
        "mapped_as_dataclass",
        "mapped_column",
        "registry.mapped",
        "sqlalchemy.orm.DeclarativeBase",
        "sqlalchemy.orm.MappedAsDataclass",
    }
)
SQLALCHEMY_ORM_CLASS_ATTRIBUTES = frozenset({"__mapper_args__", "__tablename__", "__table_args__"})

GENERIC_REFERENCE_CLASS_NAMES = frozenset(
    {
        "CuriosReference",
        "EntityReference",
        "GenericReference",
        "Reference",
        "ReferencePointer",
        "ResourceReference",
        "RuntimeReference",
    }
)


@dataclass(frozen=True, slots=True)
class ImportUse:
    file: Path
    module: str
    lineno: int


@dataclass(frozen=True, slots=True)
class Violation:
    rule: str
    file: Path
    dependency: str
    lineno: int | None = None
    detail: str | None = None

    def render(self) -> str:
        location = _relative(self.file)
        if self.lineno is not None:
            location = f"{location}:{self.lineno}"
        message = (
            f"{ARCHITECTURE_FAILURE}: {self.rule}; file={location}; dependency={self.dependency}"
        )
        if self.detail:
            message = f"{message}; detail={self.detail}"
        return message


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _python_files(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    return tuple(sorted(path for path in root.rglob("*.py") if path.is_file()))


def _parse_python(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())


def _expr_name(node: ast.AST) -> str:
    match node:
        case ast.Name(id=name):
            return name
        case ast.Attribute(value=value, attr=attr):
            parent = _expr_name(value)
            return f"{parent}.{attr}" if parent else attr
        case ast.Call(func=func):
            return _expr_name(func)
        case ast.Subscript(value=value):
            return _expr_name(value)
        case _:
            return ""


def _annotation_exprs(annotation: ast.AST) -> tuple[ast.AST, ...]:
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        try:
            return (ast.parse(annotation.value, mode="eval").body,)
        except SyntaxError:
            return ()
    return (annotation,)


def _module_matches(module: str, forbidden: str) -> bool:
    return module == forbidden or module.startswith(f"{forbidden}.")


def _dependency_matches(dependency: str, forbidden: str) -> bool:
    return dependency == forbidden or dependency.startswith(f"{forbidden}-")


def _distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _is_provider_implementation_module(module: str) -> bool:
    root = module.split(".", maxsplit=1)[0]
    return (
        root == "providers"
        or bool(re.fullmatch(r"curios_.*providers?", root))
        or bool(re.fullmatch(r"curios_.*providers?_.*", root))
        or bool(re.fullmatch(r"curios_.*_provider", root))
    )


def _provider_implementation_import_roots() -> frozenset[str]:
    roots = {"providers"}
    python_packages_root = REPO_ROOT / "packages/python"
    if not python_packages_root.exists():
        return frozenset(roots)

    for package_path in python_packages_root.glob("*provider*"):
        if not package_path.is_dir():
            continue
        roots.add(package_path.name.replace("-", "_"))
        pyproject_path = package_path / "pyproject.toml"
        if pyproject_path.exists():
            project_name = _read_toml(pyproject_path).get("project", {}).get("name")
            if isinstance(project_name, str) and "provider" in project_name:
                roots.add(project_name.replace("-", "_"))
        source_path = package_path / "src"
        if source_path.exists():
            roots.update(path.name for path in source_path.iterdir() if path.is_dir())

    return frozenset(roots)


def _imports(source_files: tuple[Path, ...]) -> tuple[ImportUse, ...]:
    imports: list[ImportUse] = []
    for source_file in source_files:
        tree = _parse_python(source_file)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(
                    ImportUse(file=source_file, module=alias.name, lineno=node.lineno)
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
                imports.append(ImportUse(file=source_file, module=node.module, lineno=node.lineno))
    return tuple(imports)


def _forbidden_import_violations(
    *,
    rule: str,
    source_root: Path,
    forbidden_imports: frozenset[str],
) -> tuple[Violation, ...]:
    violations: list[Violation] = []
    for import_use in _imports(_python_files(source_root)):
        for forbidden in forbidden_imports:
            if _module_matches(import_use.module, forbidden):
                violations.append(
                    Violation(
                        rule=rule,
                        file=import_use.file,
                        dependency=forbidden,
                        lineno=import_use.lineno,
                        detail=f"imports {import_use.module!r}",
                    )
                )
        if _is_provider_implementation_module(import_use.module):
            violations.append(
                Violation(
                    rule=PROVIDER_DIRECTION_RULE,
                    file=import_use.file,
                    dependency=import_use.module,
                    lineno=import_use.lineno,
                    detail="provider implementation import",
                )
            )
    return tuple(violations)


def _read_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _dependency_name(requirement: str) -> str:
    name = re.split(r"[\s<>=!~;\[]", requirement, maxsplit=1)[0]
    return _distribution_name(name)


def _project_dependencies(pyproject_path: Path) -> tuple[str, ...]:
    if not pyproject_path.exists():
        return ()
    data = _read_toml(pyproject_path)
    project = data.get("project", {})
    dependencies = list(project.get("dependencies", []))
    for optional_dependencies in project.get("optional-dependencies", {}).values():
        dependencies.extend(optional_dependencies)
    return tuple(_dependency_name(dependency) for dependency in dependencies)


def _pnpm_workspace_packages(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()

    packages: list[str] = []
    in_packages_block = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped == "packages:":
            in_packages_block = True
            continue
        if in_packages_block and stripped.startswith("- "):
            packages.append(stripped[2:].strip("\"'"))
        elif in_packages_block and stripped and not raw_line.startswith(" "):
            break
    return tuple(packages)


def _metadata_violations(
    *,
    rule: str,
    pyproject_path: Path,
    forbidden_dependencies: frozenset[str],
) -> tuple[Violation, ...]:
    violations: list[Violation] = []
    for dependency in _project_dependencies(pyproject_path):
        for forbidden in forbidden_dependencies:
            normalized_forbidden = _distribution_name(forbidden)
            if _dependency_matches(dependency, normalized_forbidden):
                violations.append(
                    Violation(
                        rule=rule,
                        file=pyproject_path,
                        dependency=dependency,
                        detail=f"project dependency matches {normalized_forbidden!r}",
                    )
                )
    return tuple(violations)


def _assert_no_violations(violations: tuple[Violation, ...]) -> None:
    assert not violations, "\n".join(violation.render() for violation in violations)


def _imported_aliases_by_forbidden_module(
    source_file: Path,
    forbidden_imports: frozenset[str],
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    tree = _parse_python(source_file)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in forbidden_imports:
                    if _module_matches(alias.name, forbidden):
                        aliases[alias.asname or alias.name.split(".", maxsplit=1)[0]] = forbidden
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
            for forbidden in forbidden_imports:
                if _module_matches(node.module, forbidden):
                    for alias in node.names:
                        aliases[alias.asname or alias.name] = forbidden
    return aliases


def _annotation_names(annotation: ast.AST) -> tuple[tuple[str, int], ...]:
    names: list[tuple[str, int]] = []
    for expression in _annotation_exprs(annotation):
        for node in ast.walk(expression):
            name = _expr_name(node)
            if name:
                names.append((name, getattr(node, "lineno", getattr(annotation, "lineno", 0))))
    return tuple(names)


def _class_field_names(class_def: ast.ClassDef) -> frozenset[str]:
    fields: set[str] = set()
    for statement in class_def.body:
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            fields.add(statement.target.id)
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    fields.add(target.id)
    return frozenset(fields)


def test_curios_contracts_source_and_metadata_have_no_outward_dependencies() -> None:
    violations = (
        *_forbidden_import_violations(
            rule=CONTRACTS_RULE,
            source_root=CONTRACTS_SOURCE,
            forbidden_imports=CONTRACTS_FORBIDDEN_IMPORTS,
        ),
        *_metadata_violations(
            rule=CONTRACTS_RULE,
            pyproject_path=CONTRACTS_PACKAGE / "pyproject.toml",
            forbidden_dependencies=CONTRACTS_FORBIDDEN_IMPORTS,
        ),
    )

    _assert_no_violations(violations)


def test_curios_core_source_and_metadata_have_no_outward_dependencies() -> None:
    violations = (
        *_forbidden_import_violations(
            rule=CORE_RULE,
            source_root=CORE_SOURCE,
            forbidden_imports=CORE_FORBIDDEN_IMPORTS,
        ),
        *_metadata_violations(
            rule=CORE_RULE,
            pyproject_path=CORE_PACKAGE / "pyproject.toml",
            forbidden_dependencies=CORE_FORBIDDEN_IMPORTS,
        ),
    )

    _assert_no_violations(violations)


def test_canonical_contract_classes_are_not_sqlalchemy_orm_models() -> None:
    violations: list[Violation] = []
    for source_file in _python_files(CONTRACTS_SOURCE):
        tree = _parse_python(source_file)
        for class_def in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            base_and_decorator_names = {
                *(_expr_name(base) for base in class_def.bases),
                *(_expr_name(decorator) for decorator in class_def.decorator_list),
            }
            forbidden_markers = base_and_decorator_names & SQLALCHEMY_ORM_MARKERS
            forbidden_attributes = _class_field_names(class_def) & SQLALCHEMY_ORM_CLASS_ATTRIBUTES
            if forbidden_markers:
                violations.append(
                    Violation(
                        rule=CANONICAL_SQLALCHEMY_RULE,
                        file=source_file,
                        dependency="sqlalchemy-orm",
                        lineno=class_def.lineno,
                        detail=f"{class_def.name} uses {sorted(forbidden_markers)!r}",
                    )
                )
            if forbidden_attributes:
                violations.append(
                    Violation(
                        rule=CANONICAL_SQLALCHEMY_RULE,
                        file=source_file,
                        dependency="sqlalchemy-orm",
                        lineno=class_def.lineno,
                        detail=f"{class_def.name} declares {sorted(forbidden_attributes)!r}",
                    )
                )

    _assert_no_violations(tuple(violations))


def test_fastapi_request_response_models_are_not_canonical_authority() -> None:
    violations: list[Violation] = []
    for source_file in _python_files(CONTRACTS_SOURCE):
        aliases = _imported_aliases_by_forbidden_module(source_file, FASTAPI_IMPORTS)
        tree = _parse_python(source_file)
        for class_def in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            for node in (*class_def.bases, *class_def.decorator_list):
                name = _expr_name(node)
                root = name.split(".", maxsplit=1)[0]
                if root in aliases or any(
                    _module_matches(name, module) for module in FASTAPI_IMPORTS
                ):
                    violations.append(
                        Violation(
                            rule=CANONICAL_FASTAPI_RULE,
                            file=source_file,
                            dependency=aliases.get(root, root),
                            lineno=class_def.lineno,
                            detail=f"{class_def.name} uses {name!r}",
                        )
                    )

    _assert_no_violations(tuple(violations))


def test_provider_native_types_are_not_canonical_contract_annotations() -> None:
    forbidden_type_imports = frozenset(
        {
            *FASTAPI_IMPORTS,
            *OLLAMA_PROVIDER_SDK_IMPORTS,
            *OTEL_IMPLEMENTATION_IMPORTS,
            *POSTGRES_IMPORTS,
            *SQLALCHEMY_IMPORTS,
        }
    )
    violations: list[Violation] = []
    for source_file in _python_files(CONTRACTS_SOURCE):
        aliases = _imported_aliases_by_forbidden_module(source_file, forbidden_type_imports)
        tree = _parse_python(source_file)
        annotated_nodes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AnnAssign | ast.arg | ast.FunctionDef | ast.AsyncFunctionDef)
        ]
        for node in annotated_nodes:
            annotation = getattr(node, "annotation", None) or getattr(node, "returns", None)
            if annotation is None:
                continue
            for name, lineno in _annotation_names(annotation):
                root = name.split(".", maxsplit=1)[0]
                matched_dependency = aliases.get(root)
                if matched_dependency is None:
                    matched_dependency = next(
                        (
                            forbidden
                            for forbidden in forbidden_type_imports
                            if _module_matches(name, forbidden)
                        ),
                        None,
                    )
                if matched_dependency is not None:
                    violations.append(
                        Violation(
                            rule=CANONICAL_PROVIDER_TYPE_RULE,
                            file=source_file,
                            dependency=matched_dependency,
                            lineno=lineno or getattr(node, "lineno", None),
                            detail=f"annotation uses {name!r}",
                        )
                    )

    _assert_no_violations(tuple(violations))


def test_object_reference_remains_the_single_generic_reference_abstraction() -> None:
    object_reference_locations: list[tuple[Path, int]] = []
    violations: list[Violation] = []
    for source_file in _python_files(CONTRACTS_SOURCE):
        tree = _parse_python(source_file)
        for class_def in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            if class_def.name == "ObjectReference":
                object_reference_locations.append((source_file, class_def.lineno))
                continue
            if class_def.name in GENERIC_REFERENCE_CLASS_NAMES:
                violations.append(
                    Violation(
                        rule=OBJECT_REFERENCE_RULE,
                        file=source_file,
                        dependency=class_def.name,
                        lineno=class_def.lineno,
                        detail="generic reference class name",
                    )
                )
            fields = _class_field_names(class_def)
            if {"kind", "ref_id"}.issubset(fields):
                violations.append(
                    Violation(
                        rule=OBJECT_REFERENCE_RULE,
                        file=source_file,
                        dependency=class_def.name,
                        lineno=class_def.lineno,
                        detail="duplicates the generic kind/ref_id reference shape",
                    )
                )

    if len(object_reference_locations) != 1:
        details = ", ".join(
            f"{_relative(path)}:{line}" for path, line in object_reference_locations
        )
        violations.append(
            Violation(
                rule=OBJECT_REFERENCE_RULE,
                file=CONTRACTS_SOURCE,
                dependency="ObjectReference",
                detail=(
                    "expected exactly one declaration, "
                    f"found {len(object_reference_locations)} {details}"
                ),
            )
        )

    _assert_no_violations(tuple(violations))


def test_provider_direction_allows_absent_providers_and_blocks_outward_imports() -> None:
    provider_import_roots = _provider_implementation_import_roots()
    violations = (
        *_forbidden_import_violations(
            rule=PROVIDER_DIRECTION_RULE,
            source_root=CONTRACTS_SOURCE,
            forbidden_imports=provider_import_roots,
        ),
        *_forbidden_import_violations(
            rule=PROVIDER_DIRECTION_RULE,
            source_root=CORE_SOURCE,
            forbidden_imports=provider_import_roots,
        ),
    )

    _assert_no_violations(violations)


def test_frontend_package_is_not_upstream_of_canonical_python_contracts() -> None:
    root_pyproject = _read_toml(REPO_ROOT / "pyproject.toml")
    python_workspace_members = tuple(root_pyproject["tool"]["uv"]["workspace"]["members"])
    node_workspaces = _pnpm_workspace_packages(REPO_ROOT / "pnpm-workspace.yaml")

    violations: list[Violation] = []
    if "packages/python/curios_contracts" not in python_workspace_members:
        violations.append(
            Violation(
                rule=FRONTEND_DIRECTION_RULE,
                file=REPO_ROOT / "pyproject.toml",
                dependency="curios-contracts",
                detail="canonical Python contracts are not registered in the Python workspace",
            )
        )
    for member in python_workspace_members:
        if member.startswith("packages/typescript/"):
            violations.append(
                Violation(
                    rule=FRONTEND_DIRECTION_RULE,
                    file=REPO_ROOT / "pyproject.toml",
                    dependency=member,
                    detail="TypeScript workspace member appears in canonical Python workspace",
                )
            )
    for workspace in node_workspaces:
        if workspace.startswith("packages/python/"):
            violations.append(
                Violation(
                    rule=FRONTEND_DIRECTION_RULE,
                    file=REPO_ROOT / "pnpm-workspace.yaml",
                    dependency=workspace,
                    detail="Python canonical package appears in Node workspace",
                )
            )
    if TYPESCRIPT_CONTRACTS_PACKAGE.exists() and not any(
        workspace in {"packages/typescript/*", TYPESCRIPT_CONTRACTS_WORKSPACE}
        for workspace in node_workspaces
    ):
        violations.append(
            Violation(
                rule=FRONTEND_DIRECTION_RULE,
                file=REPO_ROOT / "pnpm-workspace.yaml",
                dependency=TYPESCRIPT_CONTRACTS_WORKSPACE,
                detail="TypeScript contracts package exists outside the Node workspace config",
            )
        )

    _assert_no_violations(tuple(violations))


def test_canonical_domain_packages_do_not_import_tooling_or_infrastructure() -> None:
    violations = (
        *_forbidden_import_violations(
            rule=INFRASTRUCTURE_RULE,
            source_root=CONTRACTS_SOURCE,
            forbidden_imports=frozenset({*DOCKER_TOOLING_IMPORTS, *REPOSITORY_TOOLING_IMPORTS}),
        ),
        *_forbidden_import_violations(
            rule=INFRASTRUCTURE_RULE,
            source_root=CORE_SOURCE,
            forbidden_imports=frozenset({*DOCKER_TOOLING_IMPORTS, *REPOSITORY_TOOLING_IMPORTS}),
        ),
        *_metadata_violations(
            rule=INFRASTRUCTURE_RULE,
            pyproject_path=CONTRACTS_PACKAGE / "pyproject.toml",
            forbidden_dependencies=frozenset(
                {*DOCKER_TOOLING_IMPORTS, *REPOSITORY_TOOLING_IMPORTS}
            ),
        ),
        *_metadata_violations(
            rule=INFRASTRUCTURE_RULE,
            pyproject_path=CORE_PACKAGE / "pyproject.toml",
            forbidden_dependencies=frozenset(
                {*DOCKER_TOOLING_IMPORTS, *REPOSITORY_TOOLING_IMPORTS}
            ),
        ),
    )

    _assert_no_violations(violations)


def test_metadata_dependency_matching_covers_distribution_name_variants() -> None:
    assert _dependency_matches(
        _dependency_name("google-genai>=1"), _distribution_name("google.genai")
    )
    assert _dependency_matches(
        _dependency_name("opentelemetry-exporter-otlp"),
        _distribution_name("opentelemetry.exporter"),
    )
    assert _dependency_matches(
        _dependency_name("python_on_whales"), _distribution_name("python_on_whales")
    )
    assert _dependency_matches(_dependency_name("curios-core"), _distribution_name("curios_core"))


def test_architecture_failure_messages_name_rule_file_and_dependency() -> None:
    rendered = Violation(
        rule=CONTRACTS_RULE,
        file=CONTRACTS_SOURCE / "example.py",
        dependency="fastapi",
        lineno=12,
        detail="imports 'fastapi'",
    ).render()

    assert rendered == (
        f"{ARCHITECTURE_FAILURE}: {CONTRACTS_RULE}; "
        "file=packages/python/curios_contracts/src/curios_contracts/example.py:12; "
        "dependency=fastapi; detail=imports 'fastapi'"
    )
