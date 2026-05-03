"""
Structured JSON logging for the application.
Produces machine-readable logs with consistent fields for observability.
Falls back to human-readable text format when configured.
"""

import logging
import sys
from typing import Optional


def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Set up a logger with consistent formatting.

    When LOG_FORMAT=json (default), emits structured JSON lines.
    When LOG_FORMAT=text, emits human-readable output for local dev.

    Args:
        name: Logger name (typically __name__)
        level: Logging level override (default: reads from settings)

    Returns:
        Configured logger instance
    """
    # Import here to avoid circular imports at module load time
    from src.config import settings

    if level is None:
        level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers when module is re-imported
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if settings.log_format == "json":
        try:
            from pythonjsonlogger import jsonlogger

            formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        except ImportError:
            # Graceful degradation if python-json-logger is not installed
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
