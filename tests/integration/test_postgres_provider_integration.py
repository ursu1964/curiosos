from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

import pytest
from curios_contracts import Result, ResultStatus
from curios_core import CoreContext
from curios_postgres_provider import PostgresProvider, PostgresReadiness

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "infrastructure/local/docker/compose.yaml"
ENV_FILE = REPO_ROOT / "infrastructure/local/docker/.env.example"
COMPOSE = (
    "docker",
    "compose",
    "--env-file",
    ENV_FILE.as_posix(),
    "-f",
    COMPOSE_FILE.as_posix(),
)
POSTGRES_VOLUME = "curios-local-docker_postgres_data"

pytestmark = pytest.mark.integration


def test_task_boot_019_postgres_provider_readiness_against_local_docker() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    try:
        result = _wait_for_readiness()
        assert result.value is not None
        assert result.value.database_name == _env_value("CURIOS_POSTGRES_DB")
        assert result.value.database_user == _env_value("CURIOS_POSTGRES_USER")
        assert result.value.server_version
        assert result.value.accepts_writes is True

        descriptors = PostgresProvider().list_provider_descriptors(CoreContext())
        assert descriptors.status is ResultStatus.SUCCESS
        assert descriptors.value is not None
        assert descriptors.value[0].provider_type.value == "database"
    finally:
        _run_compose("stop", "postgres")

    subprocess.run(
        ("docker", "volume", "inspect", POSTGRES_VOLUME),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _wait_for_readiness() -> Result[PostgresReadiness]:
    provider = PostgresProvider.from_sqlalchemy_url(_postgres_url())
    deadline = time.monotonic() + 75
    last_result: object | None = None
    try:
        while time.monotonic() < deadline:
            result = provider.check_readiness(CoreContext())
            if result.status is ResultStatus.SUCCESS:
                return result
            last_result = result
            time.sleep(1)
        pytest.fail(f"PostgreSQL provider did not become ready: {last_result!r}")
    finally:
        provider.dispose()


def _require_docker() -> None:
    try:
        subprocess.run(
            ("docker", "info"),
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        pytest.skip(f"Docker daemon is unavailable: {exc}")


def _run_compose(*args: str) -> None:
    subprocess.run(
        (*COMPOSE, *args),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _postgres_url() -> str:
    user = quote(_env_value("CURIOS_POSTGRES_USER"), safe="")
    credential = quote(_env_value("CURIOS_POSTGRES_PASSWORD"), safe="")
    host = os.environ.get("CURIOS_POSTGRES_HOST", "127.0.0.1")
    port = os.environ.get("CURIOS_POSTGRES_PORT", _env_value("CURIOS_POSTGRES_PORT"))
    database = quote(_env_value("CURIOS_POSTGRES_DB"), safe="")
    return f"postgresql+psycopg://{user}:{credential}@{host}:{port}/{database}"


def _env_value(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    prefix = f"{name}="
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix)
    msg = f"missing {name}"
    raise RuntimeError(msg)
