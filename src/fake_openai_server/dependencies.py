"""FastAPI dependency helpers."""

from fastapi import Request

from fake_openai_server.errors import ServiceError
from fake_openai_server.services.embeddings import EmbeddingsService
from fake_openai_server.services.reranker import RerankerService


def get_embeddings_service(request: Request) -> EmbeddingsService:
    """Return the embeddings service from app state."""

    service = getattr(request.app.state, "embeddings_service", None)
    if service is None:
        raise ServiceError(
            message="Embeddings service is unavailable.",
            error_type="server_error",
            status_code=500,
            code="service_unavailable",
        )
    return service


def get_reranker_service(request: Request) -> RerankerService:
    """Return the reranker service from app state."""

    service = getattr(request.app.state, "reranker_service", None)
    if service is None:
        raise ServiceError(
            message="Reranker service is unavailable.",
            error_type="server_error",
            status_code=500,
            code="service_unavailable",
        )
    return service
