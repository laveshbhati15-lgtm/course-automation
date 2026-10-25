"""Handler for locked activities, prerequisites, and unsupported formats."""

from typing import Optional
from playwright.sync_api import Page
from course_automation.ai.base import BaseAIProvider
from course_automation.logger import logger
from course_automation.sites.codechef.handlers.base import BaseActivityHandler
from course_automation.storage.models import ActivityStatus, ActivitySummary, SubmissionRecord


class LockedOrUnsupportedActivityHandler(BaseActivityHandler):
    """Reports locked or unsupported activities honestly without falsifying completion."""

    def can_handle(self, activity: ActivitySummary, page: Page) -> bool:
        return activity.status == ActivityStatus.LOCKED or activity.type.value == "UNKNOWN"

    def execute(
        self,
        activity: ActivitySummary,
        page: Page,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
    ) -> SubmissionRecord:
        """Report locked or unsupported activity without attempting invalid submissions."""
        if activity.status == ActivityStatus.LOCKED:
            logger.warning(f"Activity '{activity.title}' ({activity.id}) is LOCKED. Prerequisite required.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="LOCKED_SKIPPED",
                details="Activity is locked on website. Prerequisites required.",
            )

        logger.info(f"Activity '{activity.title}' format is not supported for automated solving.")
        return SubmissionRecord(
            activity_id=activity.id,
            verdict="UNSUPPORTED_FORMAT",
            details="Activity format is not supported for automatic execution.",
        )
