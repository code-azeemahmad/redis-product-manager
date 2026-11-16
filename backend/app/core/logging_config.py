"""Structured logging configuration with correlation ID support.

Following architectural rules:
- Thread-safe and asyncio-safe request correlation ID via contextvars.
- Never logs credentials, secrets, authorization headers, or sensitive payloads.
- Bounded-cardinality metadata attached to every log record.
"""

from contextvars import ContextVar
import json
import logging
import sys
from typing import Any, Dict

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def get_correlation_id() -> str:
    """Retrieve the current request correlation ID."""
    return request_id_ctx.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the current request correlation ID."""
    request_id_ctx.set(correlation_id)


class CorrelationIdFilter(logging.Filter):
    """Injects correlation ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = request_id_ctx.get() or "-"
        return True


class JSONLogFormatter(logging.Formatter):
    """Formats log records as structured JSON for production environments."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "correlation_id": getattr(record, "correlation_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO", structured_json: bool = False) -> None:
    """Configure root and application loggers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Avoid duplicate handlers on re-configuration
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(CorrelationIdFilter())

    if structured_json:
        formatter = JSONLogFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] [req:%(correlation_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
