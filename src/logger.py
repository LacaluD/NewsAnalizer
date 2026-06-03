# pylint: disable=inconsistent-return-statements
"""Logging setup and compact exception utilities."""

import sys
import traceback
from pathlib import Path
from typing import Any

from loguru import logger

from src.constants import LOG_DIR_PATH, LOG_FILE_PATH


class MainLogger:
    """Initialize application logging handlers."""

    def __init__(self) -> None:
        self.logger = logger

    def ensure_log_path_exists(self) -> None:
        """Create log directory and file when missing."""
        LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)
        LOG_FILE_PATH.touch(exist_ok=True)

    def get_format(self, colorize: bool) -> str:
        """Return log message format for console or file output."""
        if colorize:
            return (
                "<green>[{time:YYYY-MM-DD HH:mm:ss}]</green> "
                "<level>[{level: <8}]</level> "
                "<cyan>{name}</cyan>:<yellow>{function}</yellow>:<white>{line}</white> - "
                "<level>{message}</level>"
            )

        return (
            "[{time:YYYY-MM-DD HH:mm:ss}] "
            "[{level: <8}] "
            "{name}:{function}:{line} - {message}"
        )

    def init_logger(self) -> Any:
        """Configure file and console Loguru handlers."""
        self.logger.remove()
        self.ensure_log_path_exists()

        self.logger.add(
            str(LOG_FILE_PATH),
            rotation="2 weeks",
            retention="30 days",
            compression="zip",
            enqueue=True,
            level="DEBUG",
            format=self.get_format(colorize=False),
        )

        self.logger.add(
            sys.stderr,
            level="INFO",
            colorize=True,
            format=self.get_format(colorize=True),
        )

        self.logger.info("Logger was initialized successfully")
        return self.logger


def format_exception_short(exc: Exception, limit: int = 1) -> str:
    """Return a compact traceback with the last `limit` frames."""
    tb = exc.__traceback__
    if not tb:
        return f"{type(exc).__name__}: {exc}"

    extracted = traceback.extract_tb(tb)
    if not extracted:
        return f"{type(exc).__name__}: {exc}"

    frames = extracted[-limit:] if limit <= len(extracted) else extracted

    frame_texts = []
    cwd = Path.cwd()
    for frame in frames:
        filename = frame.filename
        try:
            rel = Path(filename).relative_to(cwd)
            filename_display = str(Path("..") / rel)
        except Exception:
            filename_display = filename

        lineno = frame.lineno
        func = frame.name
        line = frame.line.strip() if frame.line else ""
        frame_texts.append(
            f'"{filename_display}", line {lineno}, in {func}\n    {line}'
        )

    return "\n".join(frame_texts) + f"\n{type(exc).__name__}: {exc}"


def log_exception_short(
    exc: Exception, prefix: str = "", level: str = "error", limit: int = 1
) -> None:
    """Log a compact exception message at the selected log level."""
    try:
        body = format_exception_short(exc, limit=limit)
        text = f"{prefix}: {body}" if prefix else body
        log_method = getattr(logger, level, None)
        if not log_method:
            logger.error(text)
        else:
            log_method(text)
    except Exception as err:  # pragma: no cover
        logger.error(f"Failed to log exception in short format: {err}")
