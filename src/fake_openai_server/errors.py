"""Shared exceptions and exception handlers."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from fake_openai_server.schemas.error import ErrorBody, ErrorResponse


class ServiceError(Exception):
    """Base application exception with an OpenAI-compatible error shape."""

    def __init__(
        self,
        *,
        message: str,
        error_type: str,
        status_code: int,
        param: str | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.param = param
        self.code = code


class DependencyNotReadyError(ServiceError):
    """Raised when a request arrives before the model dependency is ready."""

    def __init__(self, message: str = "Model dependency is not ready yet.") -> None:
        super().__init__(
            message=message,
            error_type="server_error",
            status_code=503,
            code="dependency_not_ready",
        )


class InferenceError(ServiceError):
    """Raised when model inference fails unexpectedly."""

    def __init__(
        self,
        message: str = "The server failed to process the request.",
    ) -> None:
        super().__init__(
            message=message,
            error_type="server_error",
            status_code=500,
            code="inference_failed",
        )


def build_error_response(
    *,
    message: str,
    error_type: str,
    status_code: int,
    param: str | None = None,
    code: str | None = None,
) -> JSONResponse:
    """Create an OpenAI-compatible JSON error response."""

    payload = ErrorResponse(
        error=ErrorBody(
            message=message,
            type=error_type,
            param=param,
            code=code,
        )
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Register shared exception handlers for API errors."""

    logger = logging.getLogger("fake_openai_server.errors")

    @app.exception_handler(ServiceError)
    async def handle_service_error(_: Request, exc: ServiceError) -> JSONResponse:
        logger.warning(
            exc.message,
            extra={"extra_data": {"status_code": exc.status_code, "code": exc.code}},
        )
        return build_error_response(
            message=exc.message,
            error_type=exc.error_type,
            status_code=exc.status_code,
            param=exc.param,
            code=exc.code,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        message = _render_validation_message(exc.errors())
        logger.warning(
            "Request validation failed",
            extra={"extra_data": {"errors": exc.errors()}},
        )
        return build_error_response(
            message=message,
            error_type="invalid_request_error",
            status_code=422,
            code="validation_error",
        )

    @app.exception_handler(ValidationError)
    async def handle_settings_validation(
        _: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        logger.exception(
            "Configuration validation failed during request handling",
            extra={"extra_data": {"errors": exc.errors()}},
        )
        return build_error_response(
            message="The server configuration is invalid.",
            error_type="server_error",
            status_code=500,
            code="configuration_error",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server error", exc_info=exc)
        return build_error_response(
            message="The server encountered an unexpected error.",
            error_type="server_error",
            status_code=500,
            code="internal_error",
        )


def log_settings_error(
    service_name: str,
    exc: ValidationError,
) -> None:
    """Log a clear startup error when required environment variables are invalid."""

    logger = logging.getLogger("fake_openai_server.startup")
    logger.error(
        "Failed to load %s settings due to invalid environment variables",
        service_name,
        extra={"extra_data": {"environment_variables": _error_env_names(exc.errors())}},
    )


def _render_validation_message(errors: Iterable[Mapping[str, Any]]) -> str:
    first_error = next(iter(errors), None)
    if not first_error:
        return "Invalid request."
    location = ".".join(str(part) for part in first_error.get("loc", []))
    message = first_error.get("msg", "Invalid request.")
    return f"{location}: {message}" if location else message


def _error_env_names(errors: Iterable[Mapping[str, Any]]) -> list[str]:
    env_names: list[str] = []
    for error in errors:
        location = error.get("loc", [])
        if not location:
            continue
        env_names.append(str(location[-1]).upper())
    return env_names
