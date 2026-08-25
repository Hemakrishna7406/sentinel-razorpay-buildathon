"""
Sentinel — Structured JSON Logger

Wraps Python's standard logging module to emit JSON lines that carry the full
correlation chain (intent_id, agent_id, decision) on every log record.

Design contract:
- Never raises. If JSON serialization fails, falls back to plain text.
- Carries intent_id / agent_id as context fields when set via bind().
- Works as a drop-in replacement for the standard logger:
    from observability.logging import get_logger
    logger = get_logger(__name__)
    logger.info("event", intent_id="INT-123", decision="ALLOW", latency_ms=127)
"""

import json
import logging
import os
import sys
import time
from typing import Any


from core.config import settings
ENVIRONMENT = settings.ENVIRONMENT
LOG_LEVEL = settings.LOG_LEVEL.upper()
JSON_LOGS = settings.JSON_LOGS


class _JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        base = {
            "timestamp": self._format_time(record),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
            "environment": ENVIRONMENT,
        }

        # Merge any extra kwargs passed to logger.info(..., key=value)
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName",
            } and not key.startswith("_"):
                base[key] = value

        if record.exc_info:
            base["exception"] = self.formatException(record.exc_info)

        try:
            return json.dumps(base, default=str)
        except Exception:
            return f'{{"level":"{record.levelname}","message":"{record.getMessage()}"}}'

    @staticmethod
    def _format_time(record: logging.LogRecord) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created))


class _PlainFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(record.created))} {record.levelname:<8} [{record.name}] {record.getMessage()}"
        extras = {
            k: v for k, v in record.__dict__.items()
            if k in {"intent_id", "agent_id", "decision", "latency_ms"}
        }
        if extras:
            base += " " + " ".join(f"{k}={v}" for k, v in extras.items())
        return base


def _configure_root() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter() if JSON_LOGS else _PlainFormatter())
    root.addHandler(handler)
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))


_configure_root()


class BoundLogger:
    """
    A logger that pre-binds context fields and includes them on every call.

    Usage:
        logger = get_logger(__name__)
        bound = logger.bind(intent_id="INT-123", agent_id="agent-01")
        bound.info("evaluation complete", decision="ALLOW", latency_ms=127)
    """

    def __init__(self, name: str, context: dict[str, Any] | None = None):
        self._logger = logging.getLogger(name)
        self._context = context or {}

    def bind(self, **kwargs: Any) -> "BoundLogger":
        return BoundLogger(self._logger.name, {**self._context, **kwargs})

    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        if self._logger.isEnabledFor(level):
            extra = {**self._context, **kwargs}
            self._logger.log(level, msg, extra=extra, stacklevel=3)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, msg, **kwargs)

    # Allow use as a drop-in where code calls logger.exception()
    def exception(self, msg: str, **kwargs: Any) -> None:
        if self._logger.isEnabledFor(logging.ERROR):
            extra = {**self._context, **kwargs}
            self._logger.exception(msg, extra=extra, stacklevel=2)


def get_logger(name: str) -> BoundLogger:
    """Return a structured BoundLogger for the given module name."""
    return BoundLogger(name)
