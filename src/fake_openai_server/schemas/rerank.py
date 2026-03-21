"""Rerank API schemas."""

from pydantic import BaseModel, Field, field_validator


class RerankRequest(BaseModel):
    """Request payload for the rerank endpoint."""

    model: str = Field(min_length=1)
    query: str
    documents: list[str]
    top_n: int | None = Field(default=None, ge=1)

    @field_validator("documents")
    @classmethod
    def validate_documents(cls, value: list[str]) -> list[str]:
        """Reject empty document lists because reranking requires input documents."""

        if not value:
            raise ValueError("documents must not be empty")
        return value


class RerankUsage(BaseModel):
    """Usage information for a rerank response."""

    total_tokens: int = Field(ge=0, default=0)


class RerankDocument(BaseModel):
    """A reranked document wrapper."""

    text: str


class RerankResult(BaseModel):
    """One ranked result."""

    index: int = Field(ge=0)
    document: RerankDocument
    relevance_score: float


class RerankResponse(BaseModel):
    """Response payload for the rerank endpoint."""

    results: list[RerankResult]
    model: str
    usage: RerankUsage
