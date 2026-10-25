"""Tests for configuration and environment handling."""

from pathlib import Path
from course_automation.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.ai_provider in ("gemini", "none")
    assert s.browser_headless is False
    assert isinstance(s.database_path, Path)
    assert isinstance(s.browser_user_data_dir, Path)


def test_resolve_paths(tmp_path: Path):
    s = Settings(
        database_path=tmp_path / "sub" / "test.db",
        browser_user_data_dir=tmp_path / "browser",
    ).resolve_paths()

    assert s.database_path.parent.exists()
    assert s.database_path.is_absolute()
