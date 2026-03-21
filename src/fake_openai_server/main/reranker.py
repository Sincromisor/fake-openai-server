"""Reranker application entrypoint."""

from pydantic import ValidationError

from fake_openai_server.app import create_reranker_app
from fake_openai_server.config import get_reranker_settings
from fake_openai_server.errors import log_settings_error
from fake_openai_server.logging import configure_logging

configure_logging(level="INFO", json_logs=True, log_file=None)

try:
    app = create_reranker_app(get_reranker_settings())
except ValidationError as exc:  # pragma: no cover - startup failure path
    log_settings_error("reranker", exc)
    raise
