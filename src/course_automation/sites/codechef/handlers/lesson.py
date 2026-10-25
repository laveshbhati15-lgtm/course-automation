"""Handler for theory lessons, articles, and video content."""

from typing import Optional
from playwright.sync_api import Page
from course_automation.ai.base import BaseAIProvider
from course_automation.logger import logger
from course_automation.sites.codechef.handlers.base import BaseActivityHandler
from course_automation.storage.models import ActivitySummary, ActivityType, SubmissionRecord


class TheoryLessonActivityHandler(BaseActivityHandler):
    """Processes reading, video, and theory lessons."""

    def can_handle(self, activity: ActivitySummary, page: Page) -> bool:
        return activity.type == ActivityType.THEORY

    def execute(
        self,
        activity: ActivitySummary,
        page: Page,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
    ) -> SubmissionRecord:
        """Inspect theory lesson content."""
        title = page.title()
        logger.info(f"Read theory lesson: '{activity.title}' (Page title: '{title}')")

        return SubmissionRecord(
            activity_id=activity.id,
            verdict="INSPECTED_THEORY",
            details="Theory lesson inspected successfully.",
        )
