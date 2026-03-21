"""Tests for typed runtime settings."""

import pytest
from pydantic import ValidationError

from fake_openai_server.config import EmbeddingsSettings, RerankerSettings


def test_embeddings_settings_accept_valid_device() -> None:
    """Embeddings settings should accept supported accelerator device strings."""

    settings = EmbeddingsSettings(model_name="test-model", device="cuda:0")

    assert settings.device == "cuda:0"


def test_reranker_settings_reject_invalid_device() -> None:
    """Reranker settings should fail fast for unsupported accelerator values."""

    with pytest.raises(ValidationError):
        RerankerSettings(model_name="test-model", device="tpu")
