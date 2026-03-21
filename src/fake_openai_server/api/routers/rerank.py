"""Rerank endpoint router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from fake_openai_server.dependencies import get_reranker_service
from fake_openai_server.logging import get_logger, request_log_extra
from fake_openai_server.schemas.error import ErrorResponse
from fake_openai_server.schemas.rerank import RerankRequest, RerankResponse
from fake_openai_server.services.reranker import RerankerService

router = APIRouter(tags=["rerank"])
logger = get_logger("fake_openai_server.api.rerank")
RerankerServiceDependency = Annotated[
    RerankerService,
    Depends(get_reranker_service),
]


@router.post(
    "/v1/rerank",
    response_model=RerankResponse,
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def rerank(
    request: RerankRequest,
    http_request: Request,
    service: RerankerServiceDependency,
) -> RerankResponse:
    """Rerank documents for the requested query."""

    logger.info(
        "Rerank request received",
        extra=request_log_extra(
            http_request,
            endpoint="/v1/rerank",
            model=request.model,
            document_count=len(request.documents),
        ),
    )
    return service.rerank(request)
