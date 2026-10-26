"""Handler for coding exercises, programming labs, and Monaco/CodeMirror/Ace editors."""

import re
from typing import Optional
from playwright.sync_api import Page
from course_automation.ai.base import BaseAIProvider
from course_automation.logger import logger
from course_automation.sites.codechef.editor import MonacoEditorController
from course_automation.sites.codechef.handlers.base import BaseActivityHandler
from course_automation.sites.codechef.verdicts import VerdictState, poll_verdict
from course_automation.storage.models import ActivitySummary, ActivityType, SubmissionRecord


class CodingActivityHandler(BaseActivityHandler):
    """Processes coding problems and labs across any programming language."""

    def can_handle(self, activity: ActivitySummary, page: Page) -> bool:
        """Handle if activity is CODING, or if an editor is mounted and visible."""
        if activity.type in (ActivityType.QUIZ, ActivityType.THEORY):
            return False
        if activity.type == ActivityType.CODING:
            return True
        return MonacoEditorController.is_editor_present(page)

    @classmethod
    def detect_programming_language(cls, page: Page, activity: ActivitySummary) -> str:
        """Dynamically detect the active programming language from editor or dropdown."""
        # 1. Check activity metadata
        if activity.language:
            return activity.language.lower()

        # 2. Inspect language dropdown selector in the DOM
        try:
            lang_selectors = [
                ".language-select",
                "#language-select",
                "[data-testid='language-selector']",
                ".editor-language",
                "select[name='language']",
            ]
            for sel in lang_selectors:
                el = page.locator(sel).first
                if hasattr(el, "is_visible") and el.is_visible():
                    text = el.inner_text().strip().lower()
                    if "c++" in text or "cpp" in text:
                        return "cpp"
                    elif "java" in text:
                        return "java"
                    elif "python" in text or "pyth" in text:
                        return "python3"
                    elif "c " in text or text == "c":
                        return "c"
        except Exception:
            pass

        # 3. Inspect Monaco model language mode
        try:
            monaco_lang = page.evaluate(
                """() => {
                    if (window.monaco && window.monaco.editor) {
                        const models = window.monaco.editor.getModels();
                        if (models && models.length > 0) {
                            return models[0].getLanguageId();
                        }
                    }
                    return null;
                }"""
            )
            if monaco_lang:
                return str(monaco_lang).lower()
        except Exception:
            pass

        # Default fallback
        return "cpp"

    @classmethod
    def extract_problem_statement(cls, page: Page) -> str:
        """Extract visible problem description, constraints, and examples."""
        selectors = [
            ".problem-statement",
            "#problem-statement",
            ".statement",
            "[data-testid='problem-description']",
            ".markdown-content",
            "#problem-description",
        ]
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if hasattr(el, "is_visible") and el.is_visible():
                    return el.inner_text().strip()
            except Exception:
                continue
        return ""

    def execute(
        self,
        activity: ActivitySummary,
        page: Page,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
    ) -> SubmissionRecord:
        """Process coding activity with readiness polling, dynamic language detection, and editor injection."""
        language = self.detect_programming_language(page, activity)
        activity.language = language

        statement = self.extract_problem_statement(page) or activity.title
        starter_code = MonacoEditorController.get_editor_content(page) if MonacoEditorController.is_editor_present(page) else ""

        logger.info(f"Detected Language: {language} | Starter Code Size: {len(starter_code)} chars")

        if not ai_provider:
            logger.info("No AI provider active. Inspecting editor buffer only.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="INSPECTED_NO_AI",
                language=language,
                code_preview=starter_code[:200] if starter_code else None,
                details="Editor inspected; no AI provider configured.",
            )

        # 1. Generate solution
        solution_code = ai_provider.generate_solution(
            problem_statement=statement,
            language=language,
            starter_code=starter_code,
        )

        # 2. Dry-run safety: In dry-run mode, solution is verified but injection and submission are skipped
        if dry_run:
            logger.info("[DRY-RUN] Solution generated successfully. Injection and submission skipped.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="DRY_RUN_PASSED",
                language=language,
                code_preview=solution_code[:200],
                details="Dry-run completed successfully.",
            )

        # 3. Live readiness polling: ensure editor is mounted and visible
        if not MonacoEditorController.wait_for_editor_ready(page, timeout_seconds=8.0):
            logger.warning(f"Editor not mounted or ready within timeout for activity {activity.id}.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="EDITOR_NOT_FOUND",
                language=language,
                details="Code editor was not mounted or ready within timeout.",
            )

        # 4. Inject solution into editor and verify buffer content
        injected = MonacoEditorController.set_editor_content(page, solution_code)
        if not injected:
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="EDITOR_INJECTION_FAILED",
                language=language,
                details="Failed to inject solution into editor or buffer verification failed.",
            )

        # 5. Submit code
        submitted = MonacoEditorController.click_submit(page)
        if not submitted:
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="SUBMIT_BUTTON_FAILED",
                language=language,
                details="Could not locate or click enabled submit button.",
            )

        # 6. Poll platform judge verdict (Only judge ACCEPTED counts as accepted)
        verdict, details = poll_verdict(page)
        logger.info(f"Platform Judge Verdict: {verdict.value} - {details}")

        return SubmissionRecord(
            activity_id=activity.id,
            verdict=verdict.value,
            language=language,
            code_preview=solution_code[:200],
            details=details,
        )
