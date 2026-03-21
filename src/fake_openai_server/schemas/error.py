"""Error response schemas."""

from pydantic import BaseModel


class ErrorBody(BaseModel):
    """OpenAI-compatible error body."""

    message: str
    type: str
    param: str | None = None
    code: str | None = None


class ErrorResponse(BaseModel):
    """OpenAI-compatible error response envelope."""

    error: ErrorBody
