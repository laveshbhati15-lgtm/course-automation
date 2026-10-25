"""CodeChef site adapter implementing course inspection and problem automation."""

import time
from typing import Optional
from playwright.sync_api import Page
from course_automation.ai.base import BaseAIProvider
from course_automation.logger import logger
from course_automation.sites.base import BaseSiteAdapter
from course_automation.sites.codechef.editor import MonacoEditorController
from course_automation.sites.codechef.syllabus import CodeChefSyllabusParser
from course_automation.sites.codechef.verdicts import VerdictState, poll_verdict
from course_automation.storage.models import (
    ActivityStatus,
    ActivitySummary,
    ActivityType,
    CourseSummary,
    SubmissionRecord,
)


class CodeChefAdapter(BaseSiteAdapter):
    """Adapter for CodeChef Learn courses and Monaco-based coding environments."""

    name: str = "codechef"

    def can_handle(self, url: str) -> bool:
        """Check if URL belongs to CodeChef."""
        return "codechef.com" in url.lower()

    def extract_course_slug(self, url: str) -> str:
        """Extract course slug from CodeChef URL."""
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
        page.wait_for_timeout(2000)
        return True

    def _extract_problem_statement(self, page: Page) -> str:
        """Extract visible problem description text from page."""
        statement_selectors = [
            ".problem-statement",
            "#problem-statement",
            ".statement",
            "[data-testid='problem-description']",
            ".markdown-content",
        ]
        for sel in statement_selectors:
            el = page.locator(sel).first
            if el.is_visible():
                return el.inner_text()
        return ""

    def solve_activity(
        self,
        page: Page,
        activity: ActivitySummary,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
    ) -> SubmissionRecord:
        """Process coding or theory activity."""
        self.navigate_to_activity(page, activity)

        if activity.type == ActivityType.CODING or MonacoEditorController.is_editor_present(page):
            return self._solve_coding_activity(page, activity, ai_provider, dry_run)
        else:
            logger.info(f"Activity {activity.title} is not a coding lab. Marking inspected.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="INSPECTED",
                details="Non-coding activity visited.",
            )

    def _solve_coding_activity(
        self,
        page: Page,
        activity: ActivitySummary,
        ai_provider: Optional[BaseAIProvider],
        dry_run: bool,
    ) -> SubmissionRecord:
        """Handle coding exercise: read statement, starter code, inject solution, and submit."""
        statement = self._extract_problem_statement(page)
        starter_code = MonacoEditorController.get_editor_content(page)
        language = activity.language or "cpp"

        logger.info(f"Problem: {activity.title} | Language: {language}")
        logger.info(f"Starter code length: {len(starter_code)} characters")

        if not ai_provider:
            logger.warning("No AI provider configured. Inspecting editor buffer only.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="INSPECTED_NO_AI",
                language=language,
                code_preview=starter_code[:200] if starter_code else None,
                details="Editor inspected; no AI provider was configured to generate solution.",
            )

        solution_code = ai_provider.generate_solution(
            problem_statement=statement or activity.title,
            language=language,
            starter_code=starter_code,
        )

        if dry_run:
            logger.info("[DRY-RUN] Solution generated but injection and submission skipped.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="DRY_RUN_PASSED",
                language=language,
                code_preview=solution_code[:200],
                details="Dry-run completed successfully.",
            )

        # Inject code into Monaco
        injected = MonacoEditorController.set_editor_content(page, solution_code)
        if not injected:
            logger.error("Failed to inject code into Monaco editor.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="EDITOR_INJECTION_FAILED",
                language=language,
                details="Could not set editor value.",
            )

        # Submit code
        submitted = MonacoEditorController.click_submit(page)
        if not submitted:
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="SUBMIT_BUTTON_FAILED",
                language=language,
                details="Could not click submit button.",
            )

        # Poll verdict
        verdict, details = poll_verdict(page)
        logger.info(f"Verdict for {activity.title}: {verdict.value} - {details}")

        return SubmissionRecord(
            activity_id=activity.id,
            verdict=verdict.value,
            language=language,
            code_preview=solution_code[:200],
            details=details,
        )

    def verify_activity_status(self, page: Page, activity: ActivitySummary) -> ActivityStatus:
        """Verify activity status by checking page elements."""
        try:
            if page.locator("text='Accepted'").first.is_visible() or page.locator(".status-accepted").first.is_visible():
                return ActivityStatus.COMPLETED
        except Exception:
            pass
        return activity.status
