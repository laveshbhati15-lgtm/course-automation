"""Configuration management for Course Automation using Pydantic Settings."""

from pathlib import Path
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # AI Configuration
    ai_provider: Literal["gemini", "none"] = Field(
        default="none",
        description="Active AI provider. Set to gemini or none."
    )
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key."
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Default Gemini model to use for solving."
    )

    # Browser Configuration
    browser_headless: bool = Field(
        default=False,
        description="Run browser in headless mode."
    )
    browser_user_data_dir: Path = Field(
        default_factory=lambda: Path.home() / ".course_automation" / "browser_profile",
        description="Isolated persistent directory for browser context."
    )
    browser_cdp_url: Optional[str] = Field(
        default=None,
        description="Optional CDP URL to connect to an existing browser instance."
    )
    browser_timeout_ms: int = Field(
        default=30000,
        description="Default timeout for browser operations in milliseconds."
    )

    # Database Configuration
    database_path: Path = Field(
        default_factory=lambda: Path.home() / ".course_automation" / "progress.db",
        description="Path to SQLite progress database."
    )

    # General Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)."
    )
    dry_run: bool = Field(
        default=False,
        description="Enable dry-run mode: inspect and simulate without submitting actions."
    )

    def resolve_paths(self) -> "Settings":
        """Expand home directory ~ in file paths and ensure directories exist."""
        self.browser_user_data_dir = self.browser_user_data_dir.expanduser().resolve()
        self.database_path = self.database_path.expanduser().resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return self


settings = Settings().resolve_paths()
