"""Tests for secret redaction utility."""

from course_automation.ai.sanitizer import redact_secrets


def test_redact_google_api_key():
    text = "Using API key AIzaSyD3x9L0PqRstUvwXyz1234567890AbCdEf for request"
    redacted = redact_secrets(text)
    assert "AIza" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_bearer_token():
    text = "Authorization: Bearer ya29.a0AfH6SMCxyz123456789"
    redacted = redact_secrets(text)
    assert "Bearer" not in redacted
    assert "[REDACTED]" in redacted


def test_no_secrets():
    text = "Public class Solution { public static void main(String[] args) {} }"
    assert redact_secrets(text) == text
