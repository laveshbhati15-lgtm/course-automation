"""Sanitized structured logging ensuring secrets and tokens are never leaked."""

import logging
import os
import re
import sys
from typing import Optional

SENSITIVE_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE),
    re.compile(r"([?&]key=)[^&]+", re.IGNORECASE),
    re.compile(r"([?&]token=)[^&]+", re.IGNORECASE),
    re.compile(r"(cookie:\s*)[^\r\n]+", re.IGNORECASE),
]


class SanitizingFilter(logging.Filter):
    """Logging filter that masks sensitive credentials from output records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern in SENSITIVE_PATTERNS:
                record.msg = pattern.sub("[REDACTED]", record.msg)
        if record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern in SENSITIVE_PATTERNS:
                        arg = pattern.sub("[REDACTED]", arg)
                sanitized_args.append(arg)
            record.args = tuple(sanitized_args)
        return True


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Configure and return the root package logger."""
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO")
    pkg_logger = logging.getLogger("course_automation")
    target_level = getattr(logging, str(level).upper(), logging.INFO)
    pkg_logger.setLevel(target_level)

    if not pkg_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(target_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SanitizingFilter())
        pkg_logger.addHandler(handler)
    else:
        for handler in pkg_logger.handlers:
            handler.setLevel(target_level)

    return pkg_logger


logger = setup_logging()
