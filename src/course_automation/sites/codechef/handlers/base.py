"""Abstract base class for CodeChef activity handlers."""

from abc import ABC, abstractmethod
from typing import Optional
from playwright.sync_api import Page
from course_automation.ai.base import BaseAIProvider
from course_automation.storage.models import ActivitySummary, SubmissionRecord


class BaseActivityHandler(ABC):
    """Handler for specific activity types (coding problems, quizzes, theory, locked)."""

    @abstractmethod
    def can_handle(self, activity: ActivitySummary, page: Page) -> bool:
        """Return True if this handler is appropriate for the given activity."""
        pass

    @abstractmethod
    def execute(
        self,
        activity: ActivitySummary,
        page: Page,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
    ) -> SubmissionRecord:
        """Execute processing or solving for this activity."""
        pass
