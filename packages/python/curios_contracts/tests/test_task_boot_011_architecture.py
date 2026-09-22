from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).parents[1] / "src" / "curios_contracts"

FORBIDDEN_TASK_013_CLASSES = {
    "Approval",
    "Authority",
    "ConfigurationProfile",
    "EffectClassification",
    "Permission",
    "PolicyDecision",
    "Principal",
    "Risk",
    "RiskClassification",
    "SecretReference",
}

FORBIDDEN_RUNTIME_IMPLEMENTATIONS = {
    "AgentExecutor",
    "CapabilityResolver",
    "ModelRouter",
    "Router",
    "Scheduler",
}

FORBIDDEN_IMPORT_ROOTS = {
    "boto3",
    "fastapi",
    "httpx",
    "langchain",
    "llama_index",
    "openai",
    "pydantic",
    "requests",
    "sqlalchemy",
}


def _module_trees() -> list[ast.AST]:
    return [
        ast.parse(source_path.read_text(encoding="utf-8"))
        for source_path in SOURCE_ROOT.glob("*.py")
    ]


def test_task_boot_011_does_not_implement_task_013_contracts() -> None:
    class_names: set[str] = set()
    for tree in _module_trees():
        class_names.update(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))

    assert class_names.isdisjoint(FORBIDDEN_TASK_013_CLASSES)


def test_task_boot_011_does_not_implement_schedulers_routers_or_executors() -> None:
    declared_names: set[str] = set()
    for tree in _module_trees():
        declared_names.update(
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        )
        declared_names.update(
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        )

    assert declared_names.isdisjoint(FORBIDDEN_RUNTIME_IMPLEMENTATIONS)


def test_task_boot_011_source_has_no_provider_or_framework_imports() -> None:
    imported_roots: set[str] = set()
    for tree in _module_trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(FORBIDDEN_IMPORT_ROOTS)


def test_object_reference_remains_the_only_generic_reference_abstraction() -> None:
    object_reference_class_count = 0
    for tree in _module_trees():
        object_reference_class_count += sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == "ObjectReference"
        )

    assert object_reference_class_count == 1
