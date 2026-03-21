"""Health endpoints."""

from collections.abc import Callable

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from fake_openai_server.schemas.health import HealthResponse


def create_health_router(
    *,
    service_name: str,
    model_name: str,
    ready_check: Callable[[], bool],
) -> APIRouter:
    """Create liveness and readiness probes for a service."""

    router = APIRouter(prefix="/health", tags=["health"])

    @router.get("/live", response_model=HealthResponse)
    def live() -> HealthResponse:
        """Return process liveness for orchestrators."""

        return HealthResponse(status="ok", service=service_name, model=model_name)

    @router.get(
        "/ready",
        response_model=HealthResponse,
        responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
    )
    def ready() -> HealthResponse | JSONResponse:
        """Return readiness only after inference dependencies are initialized."""

        if ready_check():
            return HealthResponse(status="ok", service=service_name, model=model_name)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=HealthResponse(
                status="not_ready",
                service=service_name,
                model=model_name,
            ).model_dump(),
        )

    return router
