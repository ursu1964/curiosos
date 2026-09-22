"""FastAPI application factory at the outer Curios service boundary."""

from __future__ import annotations

from typing import Any

from curios_contracts import Result, ResultStatus, to_json_compatible
from fastapi import FastAPI, HTTPException

from curios_api.composition import ApiComposition, create_api_composition

type JsonObject = dict[str, object]


def create_application(composition: ApiComposition | None = None) -> FastAPI:
    """Create the FastAPI application without making FastAPI semantic authority."""
    app_composition = composition or create_api_composition()
    app = FastAPI(title="CuriosOS API", version="0.0.0")

    @app.get("/health/live")
    async def health_live() -> JsonObject:
        return {"status": "ok", "service": "curios-api"}

    @app.get("/health/ready")
    async def health_ready() -> JsonObject:
        profile = app_composition.configuration_provider.load_configuration_profile()
        if profile.status is ResultStatus.FAILURE:
            _raise_unavailable(profile)

        providers = app_composition.core_services.list_provider_descriptors(app_composition.context)
        if providers.status is ResultStatus.FAILURE:
            _raise_unavailable(providers)

        return {
            "status": "ready",
            "configuration_profile": to_json_compatible(profile.value),
            "providers": to_json_compatible(providers.value or ()),
        }

    @app.get("/providers")
    async def providers() -> JsonObject:
        result = app_composition.core_services.list_provider_descriptors(app_composition.context)
        if result.status is ResultStatus.FAILURE:
            _raise_unavailable(result)
        return {"providers": to_json_compatible(result.value or ())}

    return app


def _raise_unavailable(result: Result[Any]) -> None:
    raise HTTPException(status_code=503, detail=result.to_json_compatible())
