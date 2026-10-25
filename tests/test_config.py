"""Tests for configuration and environment handling."""

from pathlib import Path
from course_automation.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.ai_provider in ("gemini", "none")
    assert s.browser_headless is False
    assert s.gemini_model == "gemini-flash-lite-latest"
    assert isinstance(s.database_path, Path)
    assert isinstance(s.browser_user_data_dir, Path)


def test_settings_gemini_key_aliases(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key-abc")
    s = Settings()
    assert s.gemini_api_key == "test-google-key-abc"

    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key-xyz")
    s2 = Settings()
    assert s2.gemini_api_key == "test-gemini-key-xyz"


def test_settings_custom_values():
    s = Settings(
        ai_provider="none",
        browser_headless=True,
        dry_run=True,
        log_level="DEBUG",
    )
    assert s.ai_provider == "none"
    assert s.browser_headless is True
    assert s.dry_run is True
    assert s.log_level == "DEBUG"


def test_resolve_paths(tmp_path: Path):
    s = Settings(
        database_path=tmp_path / "sub" / "test.db",
        browser_user_data_dir=tmp_path / "browser",
    ).resolve_paths()

    assert s.database_path.parent.exists()
    assert s.database_path.is_absolute()
