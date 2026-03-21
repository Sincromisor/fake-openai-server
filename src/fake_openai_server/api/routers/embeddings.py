"""Embeddings endpoint router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from fake_openai_server.dependencies import get_embeddings_service
from fake_openai_server.logging import get_logger, request_log_extra
from fake_openai_server.schemas.embeddings import EmbeddingRequest, EmbeddingResponse
from fake_openai_server.schemas.error import ErrorResponse
from fake_openai_server.services.embeddings import EmbeddingsService

router = APIRouter(tags=["embeddings"])
logger = get_logger("fake_openai_server.api.embeddings")
EmbeddingsServiceDependency = Annotated[
    EmbeddingsService,
    Depends(get_embeddings_service),
]


@router.post(
    "/v1/embeddings",
    response_model=EmbeddingResponse,
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def create_embedding(
    request: EmbeddingRequest,
    http_request: Request,
    service: EmbeddingsServiceDependency,
) -> EmbeddingResponse:
    """Create embeddings for the requested input."""

    text_count = 1 if isinstance(request.input, str) else len(request.input)
    logger.info(
        "Embeddings request received",
        extra=request_log_extra(
            http_request,
            endpoint="/v1/embeddings",
            model=request.model,
            input_count=text_count,
        ),
    )
    return service.create_embedding(request)
