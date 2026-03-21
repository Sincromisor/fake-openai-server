"""Embeddings application entrypoint."""

from pydantic import ValidationError

from fake_openai_server.app import create_embeddings_app
from fake_openai_server.config import get_embeddings_settings
from fake_openai_server.errors import log_settings_error
from fake_openai_server.logging import configure_logging

configure_logging(level="INFO", json_logs=True, log_file=None)

try:
    app = create_embeddings_app(get_embeddings_settings())
except ValidationError as exc:  # pragma: no cover - startup failure path
    log_settings_error("embeddings", exc)
    raise
