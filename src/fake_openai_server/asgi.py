"""ASGI factories and runtime commands for service entrypoints."""

from __future__ import annotations

import uvicorn
from pydantic import ValidationError

from fake_openai_server.app import create_embeddings_app, create_reranker_app
from fake_openai_server.config import (
    EmbeddingsSettings,
    RerankerSettings,
    get_embeddings_settings,
    get_reranker_settings,
)
from fake_openai_server.errors import log_settings_error
from fake_openai_server.logging import configure_logging


def create_embeddings_api() -> object:
    """Create the embeddings ASGI application from environment settings."""

    return _create_embeddings_api_from_settings(get_embeddings_settings())


def create_reranker_api() -> object:
    """Create the reranker ASGI application from environment settings."""

    return _create_reranker_api_from_settings(get_reranker_settings())


def run_embeddings() -> None:
    """Run the embeddings API service with the configured host and port."""

    settings = get_embeddings_settings()
    _create_embeddings_api_from_settings(settings)
    uvicorn.run(
        "fake_openai_server.asgi:create_embeddings_api",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_config=None,
    )


def run_reranker() -> None:
    """Run the reranker API service with the configured host and port."""

    settings = get_reranker_settings()
    _create_reranker_api_from_settings(settings)
    uvicorn.run(
        "fake_openai_server.asgi:create_reranker_api",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_config=None,
    )


def _create_embeddings_api_from_settings(settings: EmbeddingsSettings) -> object:
    configure_logging(
        level=settings.log_level,
        json_logs=settings.log_json,
        log_file=settings.log_file,
    )
    try:
        return create_embeddings_app(settings)
    except ValidationError as exc:  # pragma: no cover - startup failure path
        log_settings_error("embeddings", exc)
        raise


def _create_reranker_api_from_settings(settings: RerankerSettings) -> object:
    configure_logging(
        level=settings.log_level,
        json_logs=settings.log_json,
        log_file=settings.log_file,
    )
    try:
        return create_reranker_app(settings)
    except ValidationError as exc:  # pragma: no cover - startup failure path
        log_settings_error("reranker", exc)
        raise
