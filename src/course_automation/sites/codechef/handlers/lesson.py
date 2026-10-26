"""Handler for reading theory lessons, concepts, and sequential lesson navigation."""

import time
from typing import List, Optional, Tuple
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
        "button[class*='_nextButton_']",
        "button[class*='_next_']",
    ]

    TERMINAL_INDICATORS: List[str] = [
        "text='Course Completed'",
        "text='Module Completed'",
        "text='Course Finished'",
        "text='Congratulations'",
        "text='Back to Syllabus'",
        "text='Return to Syllabus'",
        "[data-testid='course-completed']",
        ".course-completion",
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
            if hasattr(stmt, "is_visible") and stmt.is_visible() is True:
                txt = stmt.inner_text()
                if isinstance(txt, str):
                    return txt.strip()
        except Exception:
            pass
        return ""

    @classmethod
    def find_next_control(cls, page: Page) -> Optional[Locator]:
        """Locate active, visible Next or Continue navigation button."""
        for sel in cls.NEXT_CONTROL_SELECTORS:
            try:
                loc = page.locator(sel).first
                cnt = loc.count() if hasattr(loc, "count") else 0
                if (isinstance(cnt, int) and cnt > 0) or hasattr(loc, "is_visible"):
                    if hasattr(loc, "is_visible") and loc.is_visible() is True:
                        return loc
            except Exception:
                continue
        return None

    def wait_for_next_control(self, page: Page, timeout_seconds: float = 3.0) -> Optional[Locator]:
        """Poll until Next navigation control is mounted and visible."""
        # Immediate check
        btn = self.find_next_control(page)
        if btn is not None:
            return btn

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            btn = self.find_next_control(page)
            if btn is not None:
                return btn
            time.sleep(0.1)
        return None

    @classmethod
    def _is_terminal_page(cls, page: Page) -> bool:
        """Check for terminal course completion or syllabus milestone indicators."""
        for pat in cls.TERMINAL_INDICATORS:
            try:
                loc = page.locator(pat).first
                cnt = loc.count() if hasattr(loc, "count") else 0
                if isinstance(cnt, int) and cnt > 0:
                    return True
                if hasattr(loc, "is_visible") and loc.is_visible() is True:
                    return True
            except Exception:
                continue
        return False

    @classmethod
    def _is_quiz_page(cls, page: Page) -> bool:
        """Check if current page has quiz/question controls."""
        try:
            from course_automation.sites.codechef.handlers.quiz import QuizActivityHandler
            return QuizActivityHandler.is_question_page(page)
        except Exception:
            return False

    @classmethod
    def _is_coding_page(cls, page: Page) -> bool:
        """Check if current page has an active code editor."""
        try:
            from course_automation.sites.codechef.editor import MonacoEditorController
            return MonacoEditorController.is_editor_present(page)
        except Exception:
            return False

    def diagnose_missing_or_disabled_next(
        self,
        page: Page,
        next_btn: Optional[Locator] = None,
    ) -> Tuple[str, str]:
        """Diagnose why navigation cannot proceed."""
        # 1. Check if button was found but disabled
        if next_btn is not None:
            is_en = False
            try:
                is_en = bool(next_btn.is_enabled())
            except Exception:
                pass
            if not is_en:
                if self._is_quiz_page(page):
                    return "WAITING_FOR_QUIZ_SUBMISSION", "Next navigation button is disabled awaiting quiz submission."
                if self._is_coding_page(page):
                    return "WAITING_FOR_CODE_SUBMISSION", "Next navigation button is disabled awaiting coding submission."
                return "NAVIGATION_CONTROL_DISABLED", "Next navigation control was found but remained disabled."

        # 2. Check if this is a terminal milestone page (course / module completion)
        if self._is_terminal_page(page):
            return "TERMINAL_PAGE_REACHED", "Course or module milestone completed; terminal syllabus page reached."

        # 3. Check if page is actually a quiz / MCQ that needs submission
        if self._is_quiz_page(page):
            return "WAITING_FOR_QUIZ_SUBMISSION", "Page contains question or quiz controls requiring submission before advancing."

        # 4. Check if page is actually a coding problem that needs submission
        if self._is_coding_page(page):
            return "WAITING_FOR_CODE_SUBMISSION", "Page contains code editor requiring solution submission before advancing."

        # 5. Default missing navigation control
        return "NAVIGATION_CONTROL_MISSING", "Next navigation control not found on page within timeout."

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

        # 2. Locate Next navigation control with readiness polling
        next_btn = self.wait_for_next_control(page, timeout_seconds=3.0)
        next_found = next_btn is not None
        next_enabled = False
        if next_btn:
            try:
                next_enabled = (next_btn.is_enabled() is True)
            except Exception:
                next_enabled = False

        logger.info(f"Next navigation control: found={next_found}, enabled={next_enabled}")

        if dry_run:
            logger.info("[DRY-RUN] Theory lesson read and verified. Advance click skipped.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="DRY_RUN_PASSED",
                details=f"Read {len(lesson_text)} chars. Next button: {'found & enabled' if next_enabled else 'missing/disabled'}.",
            )

        # 3. Advance to next lesson if control is enabled
        if next_btn and next_enabled:
            try:
                logger.info("Clicking Next button to record lesson completion...")
                initial_url = getattr(page, "url", "")
                next_btn.click()
                page.wait_for_timeout(1500)

                url_changed = getattr(page, "url", "") != initial_url
                logger.info(f"Advanced from {initial_url} -> {getattr(page, 'url', '')} (changed={url_changed})")

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

        # 4. Clear diagnostic verdict when Next button is missing or disabled
        diag_verdict, diag_reason = self.diagnose_missing_or_disabled_next(page, next_btn)
        logger.warning(f"Theory lesson navigation halted: {diag_verdict} - {diag_reason}")
        return SubmissionRecord(
            activity_id=activity.id,
            verdict=diag_verdict,
            details=f"Read lesson content ({len(lesson_text)} chars); {diag_reason}",
        )
