from __future__ import annotations

from pathlib import Path

SOURCE_ROOT = Path(__file__).parents[1] / "src" / "curios_contracts"


def _source_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_ROOT.glob("*.py"))


def test_event_observability_contracts_do_not_import_telemetry_brokers_or_providers() -> None:
    source = _source_text()

    forbidden_fragments = (
        "import opentelemetry",
        "from opentelemetry",
        "import kafka",
        "from kafka",
        "import nats",
        "from nats",
        "import pika",
        "from pika",
        "import redis",
        "from redis",
        "import boto3",
        "from boto3",
        "import openai",
        "from openai",
        "import anthropic",
        "from anthropic",
    )

    for fragment in forbidden_fragments:
        assert fragment not in source


def test_task_012_does_not_implement_task_010_contracts() -> None:
    source = _source_text()

    forbidden_contracts = (
        "class Result",
        "class Error",
        "class ArtifactReference",
        "class EvidenceReference",
        "class VerificationReference",
    )

    for contract in forbidden_contracts:
        assert contract not in source
