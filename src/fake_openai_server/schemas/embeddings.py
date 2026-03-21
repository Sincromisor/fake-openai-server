"""Embeddings API schemas."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class EmbeddingRequest(BaseModel):
    """Request payload for the embeddings endpoint."""

    model: str = Field(min_length=1)
    input: Annotated[str | list[str], Field(union_mode="left_to_right")]

    @field_validator("input")
    @classmethod
    def validate_input(cls, value: str | list[str]) -> str | list[str]:
        """Reject empty input lists because they cannot be embedded meaningfully."""

        if isinstance(value, list) and not value:
            raise ValueError("input must not be an empty list")
        return value


class EmbeddingUsage(BaseModel):
    """Usage information for an embeddings response."""

    prompt_tokens: int = Field(ge=0, default=0)
    total_tokens: int = Field(ge=0, default=0)


class EmbeddingData(BaseModel):
    """One embedding item in the response payload."""

    object: str = "embedding"
    embedding: list[float]
    index: int = Field(ge=0)


class EmbeddingResponse(BaseModel):
    """Response payload for the embeddings endpoint."""

    object: str = "list"
    data: list[EmbeddingData]
    model: str
    usage: EmbeddingUsage
