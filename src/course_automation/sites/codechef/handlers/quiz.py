"""Handler for multiple-choice questions (MCQs) and quizzes."""

from typing import List, Optional
from playwright.sync_api import Page
from course_automation.ai.base import BaseAIProvider
from course_automation.logger import logger
from course_automation.sites.codechef.handlers.base import BaseActivityHandler
from course_automation.storage.models import ActivitySummary, ActivityType, SubmissionRecord


class QuizActivityHandler(BaseActivityHandler):
    """Processes multiple-choice questions and quizzes with mandatory human review."""

    def can_handle(self, activity: ActivitySummary, page: Page) -> bool:
        return activity.type == ActivityType.QUIZ

    @classmethod
    def extract_quiz_content(cls, page: Page) -> tuple[str, List[str]]:
        """Extract question statement and options from page DOM."""
        q_text = ""
        options = []

        q_el = page.locator(".mcq-question, .quiz-question, .question-text, h3").first
        if q_el.is_visible():
            q_text = q_el.inner_text().strip()

        opt_els = page.locator(".mcq-option, .quiz-option, label:has(input[type='radio'])").all()
        for opt in opt_els:
            text = opt.inner_text().strip()
            if text:
                options.append(text)

        return q_text, options

    def execute(
        self,
        activity: ActivitySummary,
        page: Page,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
    ) -> SubmissionRecord:
        """Inspect quiz question, solve via AI, and require human review."""
        q_text, options = self.extract_quiz_content(page)
        logger.info(f"Extracted MCQ: '{q_text[:80]}...' with {len(options)} options.")

        if not ai_provider or not options:
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="INSPECTED_QUIZ",
                details=f"Quiz inspected: {len(options)} options found.",
            )

        answer, explanation = ai_provider.solve_mcq(q_text or activity.title, options)
        logger.info(f"AI Suggestion: {answer} (Reason: {explanation})")

        return SubmissionRecord(
            activity_id=activity.id,
            verdict="SUGGESTION_READY",
            details=f"Suggested: {answer} | Explanation: {explanation}",
        )
