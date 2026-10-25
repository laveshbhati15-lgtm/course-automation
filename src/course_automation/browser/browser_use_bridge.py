"""Browser Use integration documentation and optional execution bridge.

NOTE ON BROWSER AUTOMATION BACKENDS:
1. Playwright (Default Backend):
   - 100% Local, deterministic, fast, and free.
   - Connects to existing Chrome sessions via CDP (port 9222) or launches isolated profiles.
   - Does NOT consume LLM tokens or require external agent credits.
   - Recommended and supported for all standard course inspection and solving workflows.

2. Browser Use (Optional Agentic Framework):
   - Autonomous multi-step visual browser agent powered by an LLM.
   - CONSUMES PAID LLM TOKENS on every interaction step (sends screenshots and DOM trees).
   - Requires 'browser-use' package and an explicit LLM API key (e.g. Gemini, Anthropic, OpenAI).
"""

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
    def get_status(cls) -> Dict[str, Any]:
        """Return clear status of Browser Use backend."""
        available = cls.is_available()
        return {
            "installed": available,
            "status": "ready" if available else "not_installed",
            "backend": "browser_use" if available else "playwright (native)",
            "token_cost_warning": "Autonomous Browser Use agents consume LLM tokens per action.",
        }

    @classmethod
    def run_agent_task(cls, task_description: str, cdp_url: Optional[str] = None) -> Optional[str]:
        """Run an autonomous Browser Use agent task.
        
        Raises RuntimeError if browser-use is not installed or credentials are missing.
        Never returns a placeholder string.
        """
        if not cls.is_available():
            raise RuntimeError(
                "The 'browser-use' package is not installed. Course Automation uses "
                "standard local Playwright as its default backend (free, zero token cost). "
                "To enable autonomous Browser Use agents, install 'browser-use' and configure an LLM key."
            )

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required to run Browser Use agents. "
                "Autonomous visual agents consume LLM tokens for each browser step."
            )

        logger.info(f"Executing Browser Use agent task: '{task_description}' (Target: {cdp_url or 'default'})...")
        # Real execution:
        try:
            import asyncio
            from browser_use import Agent
            from browser_use.llm.google.chat import ChatGoogle

            llm = ChatGoogle(model="gemini-2.5-flash", api_key=api_key)
            agent = Agent(task=task_description, llm=llm)
            result = asyncio.run(agent.run())
            return str(result)
        except Exception as e:
            logger.error(f"Browser Use execution failed: {e}")
            raise
