"""Sanitized structured logging ensuring secrets and tokens are never leaked."""

import logging
import re
import sys

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


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the root package logger."""
    pkg_logger = logging.getLogger("course_automation")
    pkg_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not pkg_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SanitizingFilter())
        pkg_logger.addHandler(handler)

    return pkg_logger


logger = setup_logging()
