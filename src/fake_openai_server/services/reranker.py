"""Rerank inference service."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from typing import Protocol, cast

from fake_openai_server.errors import DependencyNotReadyError, InferenceError
from fake_openai_server.schemas.rerank import (
    RerankDocument,
    RerankRequest,
    RerankResponse,
    RerankResult,
    RerankUsage,
)


class SupportsRerankerModel(Protocol):
    """Runtime protocol for rerank backends."""

    def predict(self, sentences: Sequence[tuple[str, str]]) -> Sequence[float]:
        """Predict relevance scores for query-document pairs."""


def load_cross_encoder(model_name: str) -> SupportsRerankerModel:
    """Load the default sentence-transformer reranker backend."""

    from sentence_transformers import CrossEncoder

    return cast(SupportsRerankerModel, CrossEncoder(model_name))


class RerankerService:
    """Load and serve rerank inference for the API layer."""

    def __init__(
        self,
        *,
        model_name: str,
        model_loader: Callable[[str], SupportsRerankerModel] = load_cross_encoder,
    ) -> None:
        self.model_name = model_name
        self._model_loader = model_loader
        self._model: SupportsRerankerModel | None = None
        self._logger = logging.getLogger("fake_openai_server.reranker")

    def startup(self) -> None:
        """Load the model during application startup."""

        started_at = time.perf_counter()
        self._logger.info(
            "Loading reranker model",
            extra={"extra_data": {"model_name": self.model_name}},
        )
        self._model = self._model_loader(self.model_name)
        self._logger.info(
            "Reranker model loaded",
            extra={
                "extra_data": {
                    "model_name": self.model_name,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 3),
                }
            },
        )

    def is_ready(self) -> bool:
        """Report whether the model dependency has finished loading."""

        return self._model is not None

    def rerank(self, request: RerankRequest) -> RerankResponse:
        """Rerank documents against a query and return scored results."""

        if self._model is None:
            raise DependencyNotReadyError()
        pairs = [(request.query, document) for document in request.documents]
        started_at = time.perf_counter()
        self._logger.debug(
            "Running reranker inference",
            extra={
                "extra_data": {
                    "model_name": self.model_name,
                    "document_count": len(request.documents),
                }
            },
        )
        try:
            raw_scores = self._model.predict(pairs)
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise InferenceError() from exc
        ranked = sorted(
            zip(
                request.documents,
                raw_scores,
                range(len(request.documents)),
                strict=True,
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        if request.top_n is not None:
            ranked = ranked[: request.top_n]
        self._logger.info(
            "Rerank request completed",
            extra={
                "extra_data": {
                    "model_name": self.model_name,
                    "document_count": len(request.documents),
                    "result_count": len(ranked),
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 3),
                }
            },
        )
        return RerankResponse(
            results=[
                RerankResult(
                    index=index,
                    document=RerankDocument(text=document),
                    relevance_score=float(score),
                )
                for document, score, index in ranked
            ],
            model=request.model,
            usage=RerankUsage(),
        )
