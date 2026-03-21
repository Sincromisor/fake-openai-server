"""Health endpoint schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health status for liveness and readiness probes."""

    status: str
    service: str
    model: str
