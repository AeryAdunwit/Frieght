from __future__ import annotations

import logging
import os
from typing import Any

_LOGGING_CONFIGURED = False


def configure_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    level_name = os.environ.get("LOG_LEVEL", "INFO").strip().upper() or "INFO"
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    _LOGGING_CONFIGURED = True


def _format_value(value: Any) -> str:
    if value is None:
        return "null"
    text = str(value).strip()
    if not text:
        return '""'
    return text.replace("\r", " ").replace("\n", " ")


def format_log_context(**context: Any) -> str:
    parts: list[str] = []
    for key, value in context.items():
        if value is None:
            continue
        parts.append(f"{key}={_format_value(value)}")
    return " ".join(parts)


def log_with_context(logger: logging.Logger, level: int, message: str, **context: Any) -> None:
    suffix = format_log_context(**context)
    logger.log(level, f"{message} | {suffix}" if suffix else message)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
