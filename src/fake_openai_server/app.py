"""FastAPI application factories."""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from fake_openai_server.api.routers.embeddings import router as embeddings_router
from fake_openai_server.api.routers.health import create_health_router
from fake_openai_server.api.routers.rerank import router as rerank_router
from fake_openai_server.config import EmbeddingsSettings, RerankerSettings
from fake_openai_server.errors import register_exception_handlers
from fake_openai_server.logging import configure_logging, get_logger, request_log_extra
from fake_openai_server.services.embeddings import EmbeddingsService
from fake_openai_server.services.reranker import RerankerService


def create_embeddings_app(
    settings: EmbeddingsSettings,
    *,
    service: EmbeddingsService | None = None,
) -> FastAPI:
    """Create the embeddings FastAPI application."""

    configure_logging(
        level=settings.log_level,
        json_logs=settings.log_json,
        log_file=settings.log_file,
    )
    embeddings_service = service or EmbeddingsService(
        model_name=settings.model_name,
        device=settings.device,
    )
    app = FastAPI(
        title="Fake OpenAI Embeddings API",
        description="OpenAI-compatible local embeddings API server.",
        version="0.1.0",
        openapi_tags=[
            {"name": "embeddings", "description": "Embeddings inference endpoints."},
            {"name": "health", "description": "Liveness and readiness endpoints."},
        ],
        lifespan=_lifespan(
            service_name="embeddings",
            startup=embeddings_service.startup,
        ),
    )
    app.state.embeddings_service = embeddings_service
    _install_shared_app_behavior(app, service_name="embeddings")
    app.include_router(embeddings_router)
    app.include_router(
        create_health_router(
            service_name="embeddings",
            model_name=settings.model_name,
            ready_check=embeddings_service.is_ready,
        )
    )
    register_exception_handlers(app)
    return app


def create_reranker_app(
    settings: RerankerSettings,
    *,
    service: RerankerService | None = None,
) -> FastAPI:
    """Create the reranker FastAPI application."""

    configure_logging(
        level=settings.log_level,
        json_logs=settings.log_json,
        log_file=settings.log_file,
    )
    reranker_service = service or RerankerService(
        model_name=settings.model_name,
        device=settings.device,
    )
    app = FastAPI(
        title="Fake OpenAI Rerank API",
        description="OpenAI-compatible local rerank API server.",
        version="0.1.0",
        openapi_tags=[
            {"name": "rerank", "description": "Rerank inference endpoints."},
            {"name": "health", "description": "Liveness and readiness endpoints."},
        ],
        lifespan=_lifespan(
            service_name="reranker",
            startup=reranker_service.startup,
        ),
    )
    app.state.reranker_service = reranker_service
    _install_shared_app_behavior(app, service_name="reranker")
    app.include_router(rerank_router)
    app.include_router(
        create_health_router(
            service_name="reranker",
            model_name=settings.model_name,
            ready_check=reranker_service.is_ready,
        )
    )
    register_exception_handlers(app)
    return app


def _install_shared_app_behavior(app: FastAPI, *, service_name: str) -> None:
    logger = get_logger(f"fake_openai_server.{service_name}.http")

    @app.middleware("http")
    async def add_request_context(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.request_id = str(uuid.uuid4())
        started_at = time.perf_counter()
        response = await call_next(request)
        response.headers["x-request-id"] = request.state.request_id
        logger.info(
            "Request completed",
            extra=request_log_extra(
                request,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round((time.perf_counter() - started_at) * 1000, 3),
            ),
        )
        return response


def _lifespan(*, service_name: str, startup: Callable[[], None]):
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger = get_logger(f"fake_openai_server.{service_name}.startup")
        logger.info("Service startup initiated")
        startup()
        logger.info("Service startup completed")
        yield
        logger.info("Service shutdown completed")

    return lifespan
