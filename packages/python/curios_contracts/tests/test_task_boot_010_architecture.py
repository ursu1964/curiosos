from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).parents[1] / "src" / "curios_contracts"

FORBIDDEN_IMPORT_ROOTS = {
    "boto3",
    "fastapi",
    "httpx",
    "openai",
    "pydantic",
    "requests",
    "sqlalchemy",
}


def test_contract_source_has_no_provider_or_framework_imports() -> None:
    imported_roots: set[str] = set()
    for source_path in SOURCE_ROOT.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(FORBIDDEN_IMPORT_ROOTS)


def test_task_boot_010_modules_do_not_implement_event_or_observability_contracts() -> None:
    task_010_modules = (
        "artifacts.py",
        "errors.py",
        "evidence.py",
        "results.py",
        "verification.py",
    )
    source_text = "\n".join(
        (SOURCE_ROOT / source_path).read_text(encoding="utf-8") for source_path in task_010_modules
    )

    assert "EventEnvelope" not in source_text
    assert "ObservabilityContext" not in source_text
