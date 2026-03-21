"""Embeddings inference service."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from typing import Protocol, cast

from fake_openai_server.errors import DependencyNotReadyError, InferenceError
from fake_openai_server.schemas.embeddings import (
    EmbeddingData,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingUsage,
)


class SupportsEmbeddingsModel(Protocol):
    """Runtime protocol for embedding backends."""

    def encode(
        self,
        sentences: Sequence[str],
        *,
        convert_to_numpy: bool,
    ) -> SupportsToList:
        """Encode texts into embeddings."""


class SupportsToList(Protocol):
    """Simple protocol for array-like results."""

    def tolist(self) -> list[list[float]]:
        """Return embeddings as plain Python lists."""


def load_sentence_transformer(
    model_name: str,
    device: str,
) -> SupportsEmbeddingsModel:
    """Load the default sentence-transformer embeddings backend."""

    from sentence_transformers import SentenceTransformer

    return cast(SupportsEmbeddingsModel, SentenceTransformer(model_name, device=device))


class EmbeddingsService:
    """Load and serve embeddings inference for the API layer."""

    def __init__(
        self,
        *,
        model_name: str,
        device: str,
        model_loader: Callable[[str, str], SupportsEmbeddingsModel] = (
            load_sentence_transformer
        ),
    ) -> None:
        self.model_name = model_name
        self.device = device
        self._model_loader = model_loader
        self._model: SupportsEmbeddingsModel | None = None
        self._logger = logging.getLogger("fake_openai_server.embeddings")

    def startup(self) -> None:
        """Load the model during application startup."""

        started_at = time.perf_counter()
        self._logger.info(
            "Loading embeddings model",
            extra={
                "extra_data": {
                    "model_name": self.model_name,
                    "device": self.device,
                }
            },
        )
        self._model = self._model_loader(self.model_name, self.device)
        self._logger.info(
            "Embeddings model loaded",
            extra={
                "extra_data": {
                    "model_name": self.model_name,
                    "device": self.device,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 3),
                }
            },
        )

    def is_ready(self) -> bool:
        """Report whether the model dependency has finished loading."""

        return self._model is not None

    def create_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Embed one or more texts and return an OpenAI-compatible response."""

        if self._model is None:
            raise DependencyNotReadyError()
        texts = [request.input] if isinstance(request.input, str) else request.input
        started_at = time.perf_counter()
        self._logger.debug(
            "Running embeddings inference",
            extra={
                "extra_data": {
                    "model_name": self.model_name,
                    "device": self.device,
                    "input_count": len(texts),
                }
            },
        )
        try:
            raw_embeddings = self._model.encode(texts, convert_to_numpy=True)
            embeddings = raw_embeddings.tolist()
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise InferenceError() from exc
        self._logger.info(
            "Embeddings request completed",
            extra={
                "extra_data": {
                    "model_name": self.model_name,
                    "device": self.device,
                    "input_count": len(texts),
                    "result_count": len(embeddings),
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 3),
                }
            },
        )
        return EmbeddingResponse(
            data=[
                EmbeddingData(index=index, embedding=embedding)
                for index, embedding in enumerate(embeddings)
            ],
            model=request.model,
            usage=EmbeddingUsage(),
        )
