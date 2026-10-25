"""Abstract base adapter for learning management websites."""

import re
from abc import ABC, abstractmethod
from typing import Optional
from playwright.sync_api import Page
from course_automation.ai.base import BaseAIProvider
from course_automation.storage.models import ActivityStatus, ActivitySummary, CourseSummary, SubmissionRecord


class BaseSiteAdapter(ABC):
    """Abstract adapter defining standard website lifecycle hooks."""

    name: str = "base"

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this adapter supports the given URL."""
        pass

    @abstractmethod
    def extract_course_slug(self, url: str) -> str:
        """Extract unique course identifier slug from URL."""
        pass

    @abstractmethod
    def inspect_course(self, page: Page, url: str) -> CourseSummary:
        """Inspect and parse full course structure, modules, activities, and progress."""
        pass

    @abstractmethod
    def navigate_to_activity(self, page: Page, activity: ActivitySummary) -> bool:
        """Navigate browser directly to specific activity."""
        pass

    @abstractmethod
    def solve_activity(
        self,
        page: Page,
        activity: ActivitySummary,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
    ) -> SubmissionRecord:
        """Process or solve activity with optional AI assistance and safety controls."""
        pass

    @abstractmethod
    def verify_activity_status(self, page: Page, activity: ActivitySummary) -> ActivityStatus:
        """Verify the actual completion status of activity on the live website."""
        pass
