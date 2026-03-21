"""Typed settings for the fake OpenAI compatible services."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from fake_openai_server.runtime import AcceleratorDevice


class BaseServiceSettings(BaseSettings):
    """Shared runtime settings for each API service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    host: str
    port: int = Field(ge=1, le=65535)
    device: AcceleratorDevice
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = True
    log_file: str | None = None


class EmbeddingsSettings(BaseServiceSettings):
    """Settings for the embeddings API service."""

    model_name: str = Field(min_length=1, validation_alias="EMBEDDINGS_MODEL_NAME")
    host: str = Field(default="0.0.0.0", validation_alias="EMBEDDINGS_HOST")
    port: int = Field(default=8081, validation_alias="EMBEDDINGS_PORT", ge=1, le=65535)
    device: AcceleratorDevice = Field(
        default="cuda",
        validation_alias="EMBEDDINGS_DEVICE",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        validation_alias="EMBEDDINGS_LOG_LEVEL",
    )
    log_json: bool = Field(default=True, validation_alias="EMBEDDINGS_LOG_JSON")
    log_file: str | None = Field(default=None, validation_alias="EMBEDDINGS_LOG_FILE")


class RerankerSettings(BaseServiceSettings):
    """Settings for the reranker API service."""

    model_name: str = Field(min_length=1, validation_alias="RERANKER_MODEL_NAME")
    host: str = Field(default="0.0.0.0", validation_alias="RERANKER_HOST")
    port: int = Field(default=8082, validation_alias="RERANKER_PORT", ge=1, le=65535)
    device: AcceleratorDevice = Field(
        default="cuda",
        validation_alias="RERANKER_DEVICE",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        validation_alias="RERANKER_LOG_LEVEL",
    )
    log_json: bool = Field(default=True, validation_alias="RERANKER_LOG_JSON")
    log_file: str | None = Field(default=None, validation_alias="RERANKER_LOG_FILE")


@lru_cache(maxsize=1)
def get_embeddings_settings() -> EmbeddingsSettings:
    """Return cached embeddings settings loaded from the environment."""

    return EmbeddingsSettings()  # ty: ignore[missing-argument]


@lru_cache(maxsize=1)
def get_reranker_settings() -> RerankerSettings:
    """Return cached reranker settings loaded from the environment."""

    return RerankerSettings()  # ty: ignore[missing-argument]
