"""Secret redaction utilities to prevent leaking API keys or credentials in prompts."""

import re

PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+ PRIVATE KEY-----"),
    re.compile(r"([?&](?:key|token|auth|secret)=)[^&\s]+", re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    """Redact detected secrets and credentials from a text string."""
    if not text:
        return text
    sanitized = text
    for pattern in PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized
