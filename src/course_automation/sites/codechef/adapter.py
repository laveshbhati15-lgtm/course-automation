"""CodeChef site adapter implementing course inspection and problem automation."""

from typing import List, Optional
from playwright.sync_api import Page
from course_automation.ai.base import BaseAIProvider
from course_automation.logger import logger
from course_automation.sites.base import BaseSiteAdapter
from course_automation.sites.codechef.handlers import (
    BaseActivityHandler,
    CodingActivityHandler,
    LockedOrUnsupportedActivityHandler,
    QuizActivityHandler,
    TheoryLessonActivityHandler,
)
from course_automation.sites.codechef.syllabus import CodeChefSyllabusParser
from course_automation.storage.models import (
    ActivityStatus,
    ActivitySummary,
    CourseSummary,
    SubmissionRecord,
)


class CodeChefAdapter(BaseSiteAdapter):
    """Adapter for CodeChef Learn courses across all subjects and programming languages."""

    name: str = "codechef"

    def __init__(self):
        # Ordered by specificity: locked/unsupported first, then coding, quiz, theory
        self.handlers: List[BaseActivityHandler] = [
            LockedOrUnsupportedActivityHandler(),
            CodingActivityHandler(),
            QuizActivityHandler(),
            TheoryLessonActivityHandler(),
        ]

    def can_handle(self, url: str) -> bool:
        """Check if URL belongs to CodeChef."""
        return "codechef.com" in url.lower()

    def extract_course_slug(self, url: str) -> str:
        """Extract course slug dynamically from CodeChef URL."""
        return CodeChefSyllabusParser.extract_slug(url)

    def inspect_course(self, page: Page, url: str) -> CourseSummary:
        """Inspect CodeChef course via syllabus API with DOM fallback."""
        slug = self.extract_course_slug(url)
        logger.info(f"Inspecting CodeChef course: {slug}")

        # Ensure page is loaded
        if page.url != url:
            page.goto(url, wait_until="domcontentloaded")

        # Try API discovery first
        api_data = CodeChefSyllabusParser.fetch_syllabus_api(page, slug)
        if api_data:
            return CodeChefSyllabusParser.parse_api_data(api_data, url, slug)

        # Fallback to DOM inspection
        return CodeChefSyllabusParser.parse_dom_fallback(page, url, slug)

    def navigate_to_activity(self, page: Page, activity: ActivitySummary) -> bool:
        """Navigate directly to activity URL."""
        if not activity.url:
            logger.error(f"Activity {activity.title} has no URL.")
            return False

        logger.info(f"Navigating to activity: {activity.title} ({activity.url})")
        page.goto(activity.url, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        return True

    def solve_activity(
        self,
        page: Page,
        activity: ActivitySummary,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
    ) -> SubmissionRecord:
        """Delegate solving/inspecting to appropriate registered handler."""
        self.navigate_to_activity(page, activity)

        for handler in self.handlers:
            if handler.can_handle(activity, page):
                logger.info(f"Dispatching to handler: {handler.__class__.__name__}")
                return handler.execute(activity, page, ai_provider, dry_run)

        logger.warning(f"No specific handler matched for {activity.title}. Recording inspection.")
        return SubmissionRecord(
            activity_id=activity.id,
            verdict="INSPECTED",
            details="Activity inspected without specialized handler.",
        )

    def verify_activity_status(self, page: Page, activity: ActivitySummary) -> ActivityStatus:
        """Verify activity status by checking page elements."""
        try:
            if page.locator("text='Accepted'").first.is_visible() or page.locator(".status-accepted").first.is_visible():
                return ActivityStatus.COMPLETED
        except Exception:
            pass
        return activity.status
