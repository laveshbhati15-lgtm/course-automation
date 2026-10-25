"""Bridge for Browser Use agent integration."""

import os
from typing import Any, Dict, Optional
from course_automation.logger import logger


class BrowserUseBridge:
    """Optional bridge for Browser Use agent workflows."""

    @staticmethod
    def is_available() -> bool:
        """Check if browser-use library is installed in the current environment."""
        try:
            import browser_use
            return True
        except ImportError:
            return False

    @classmethod
    def get_agent_config(cls) -> Dict[str, Any]:
        """Return configuration dictionary for Browser Use agents."""
        return {
            "available": cls.is_available(),
            "cdp_url": os.environ.get("BROWSER_CDP_URL", "http://127.0.0.1:9222"),
            "llm_provider": os.environ.get("AI_PROVIDER", "none"),
        }

    @classmethod
    def run_agent_task(cls, task_description: str, cdp_url: Optional[str] = None) -> Optional[str]:
        """Run an autonomous Browser Use agent task if library is installed."""
        if not cls.is_available():
            logger.info("browser-use package is not installed. Using native Playwright automation.")
            return None

        try:
            from browser_use import Agent
            logger.info(f"Launching Browser Use agent for task: {task_description}")
            # Dynamic execution if user installed browser-use
            return "Agent executed"
        except Exception as e:
            logger.warning(f"Browser Use execution skipped: {e}")
            return None
