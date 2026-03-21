"""Shared logging helpers for local and container execution."""

from __future__ import annotations

import json
import logging
import logging.config
from collections.abc import Mapping
from datetime import UTC, datetime
from logging import Logger
from typing import Any

from fastapi import Request


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON events."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        extra = getattr(record, "extra_data", None)
        if isinstance(extra, Mapping):
            payload.update(extra)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def build_logging_config(
    *,
    level: str,
    json_logs: bool,
    log_file: str | None,
) -> dict[str, Any]:
    """Build a logging config that works in both local and container runs."""

    formatter_name = "json" if json_logs else "plain"
    handlers = ["stdout"]
    handlers_config: dict[str, dict[str, Any]] = {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": formatter_name,
            "stream": "ext://sys.stdout",
        }
    }
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": JsonFormatter},
            "plain": {
                "format": ("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
            },
        },
        "handlers": handlers_config,
        "root": {
            "level": level,
            "handlers": handlers.copy(),
        },
        "loggers": {
            "uvicorn.error": {
                "level": level,
                "handlers": handlers.copy(),
                "propagate": False,
            },
            "uvicorn.access": {
                "level": level,
                "handlers": handlers.copy(),
                "propagate": False,
            },
        },
    }
    if log_file:
        handlers_config["log_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": formatter_name,
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "encoding": "utf-8",
        }
        handlers.append("log_file")
        config["root"]["handlers"] = handlers.copy()
        config["loggers"]["uvicorn.error"]["handlers"] = handlers.copy()
        config["loggers"]["uvicorn.access"]["handlers"] = handlers.copy()
    return config


def configure_logging(*, level: str, json_logs: bool, log_file: str | None) -> None:
    """Configure process-wide logging."""

    logging.config.dictConfig(
        build_logging_config(level=level, json_logs=json_logs, log_file=log_file)
    )


def get_logger(name: str) -> Logger:
    """Return a named application logger."""

    return logging.getLogger(name)


def request_log_extra(request: Request, **extra: Any) -> dict[str, Any]:
    """Build structured log extras for a request-scoped event."""

    return {
        "request_id": getattr(request.state, "request_id", None),
        "extra_data": extra,
    }
