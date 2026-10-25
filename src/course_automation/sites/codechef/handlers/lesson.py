"""Handler for reading theory lessons, concepts, and sequential lesson navigation."""

import time
from typing import List, Optional
from playwright.sync_api import Locator, Page
from course_automation.ai.base import BaseAIProvider
from course_automation.logger import logger
from course_automation.sites.codechef.handlers.base import BaseActivityHandler
from course_automation.storage.models import ActivityStatus, ActivitySummary, ActivityType, SubmissionRecord


class TheoryLessonActivityHandler(BaseActivityHandler):
    """Processes theory and reading lessons: scrolling, loading content, and advancing."""

    NEXT_CONTROL_SELECTORS: List[str] = [
        "button:has-text('Next')",
        "a:has-text('Next')",
        "button:has-text('Continue')",
        "a:has-text('Continue')",
        "[class*='_next__problem-link_']",
        "[class*='_next__container_'] button",
        "[class*='_next__container_'] a",
        "[data-testid='next-button']",
    ]

    def can_handle(self, activity: ActivitySummary, page: Page) -> bool:
        """Handle if activity is THEORY or page is a concept/reading lesson without radio options."""
        if activity.type == ActivityType.THEORY:
            return True
        # If radio inputs exist, it should be handled by QuizActivityHandler
        try:
            if page.locator("input[type='radio'], label[class*='_optionBox_']").count() > 0:
                return False
            # Check presence of problem statement
            stmt = page.locator("#problem-statement, .statement, [class*='_problemBodyContent_']").first
            return stmt.is_visible()
        except Exception:
            return False

    @classmethod
    def scroll_and_load_content(cls, page: Page, steps: int = 4, delay_per_step: float = 0.3) -> str:
        """Scroll incrementally down through the page to trigger dynamic content and MathJax."""
        logger.info("Scrolling through lesson to trigger dynamically loaded content...")
        try:
            for step in range(steps):
                page.mouse.wheel(0, 450)
                page.wait_for_timeout(int(delay_per_step * 1000))

            # Final scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(400)
        except Exception as e:
            logger.debug(f"Scroll interaction notice: {e}")

        # Extract text content
        try:
            stmt = page.locator("#problem-statement, .statement, [class*='_problemBodyContent_']").first
            if stmt.is_visible():
                return stmt.inner_text().strip()
        except Exception:
            pass
        return ""

    @classmethod
    def find_next_control(cls, page: Page) -> Optional[Locator]:
        """Locate active, enabled Next or Continue navigation button."""
        for sel in cls.NEXT_CONTROL_SELECTORS:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    return loc
            except Exception:
                continue
        return None

    def execute(
        self,
        activity: ActivitySummary,
        page: Page,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
    ) -> SubmissionRecord:
        """Read and scroll through theory lesson, locate Next button, and advance safely."""
        logger.info(f"Opening theory lesson: '{activity.title}' ({activity.url})")

        # 1. Scroll through content to trigger dynamic elements
        lesson_text = self.scroll_and_load_content(page)
        logger.info(f"Loaded lesson content: {len(lesson_text)} characters.")

        # 2. Locate Next navigation control
        next_btn = self.find_next_control(page)
        next_found = next_btn is not None
        next_enabled = next_btn.is_enabled() if next_btn else False

        logger.info(f"Next navigation control: found={next_found}, enabled={next_enabled}")

        if dry_run:
            logger.info("[DRY-RUN] Theory lesson read and verified. Advance click skipped.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="DRY_RUN_PASSED",
                details=f"Read {len(lesson_text)} chars. Next button: {'found & enabled' if next_enabled else 'missing'}.",
            )

        # 3. Advance to next lesson if control is enabled
        if next_btn and next_enabled:
            try:
                logger.info("Clicking Next button to record lesson completion...")
                initial_url = page.url
                next_btn.click()
                page.wait_for_timeout(1500)

                # Check if URL updated or progress confirmed
                url_changed = page.url != initial_url
                logger.info(f"Advanced from {initial_url} -> {page.url} (changed={url_changed})")

                return SubmissionRecord(
                    activity_id=activity.id,
                    verdict="ACCEPTED",
                    details=f"Theory lesson read ({len(lesson_text)} chars) and advanced successfully.",
                )
            except Exception as e:
                logger.warning(f"Error clicking Next button: {e}")
                return SubmissionRecord(
                    activity_id=activity.id,
                    verdict="NAVIGATION_ERROR",
                    details=f"Read lesson, but clicking Next button encountered error: {e}",
                )

        return SubmissionRecord(
            activity_id=activity.id,
            verdict="INSPECTED_THEORY",
            details=f"Read lesson content ({len(lesson_text)} chars); Next button not ready or enabled.",
        )
