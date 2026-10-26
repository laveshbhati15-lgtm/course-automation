"""Handler for multiple-choice questions (MCQs), quizzes, option selection, and verification."""

import re
import time
from typing import Any, Dict, List, Optional, Tuple
from playwright.sync_api import Locator, Page
from course_automation.ai.base import BaseAIProvider, MCQReasoningResult
from course_automation.logger import logger
from course_automation.sites.codechef.handlers.base import BaseActivityHandler
from course_automation.storage.models import ActivityStatus, ActivitySummary, ActivityType, SubmissionRecord


class QuizActivityHandler(BaseActivityHandler):
    """Processes MCQs and quizzes: option extraction, AI reasoning, option selection, submission, and verification."""

    # Robust selectors for individual option elements (tag-agnostic to support both label and div)
    OPTION_SELECTORS = [
        "[class*='_optionBox_']",
        "[class*='_optionContainer_'] > *",
        "[class*='_optionsContainer_'] > *",
        "[class*='_mcqOption_']",
        "[class*='_mcq_option_']",
        "[class*='optionBox']",
        "[class*='mcqOption']",
        "[class*='_option_']",
        "label[class*='_optionBox_']",
        "div[class*='_optionBox_']",
        "label.MuiFormControlLabel-root",
        ".MuiFormControlLabel-root",
        "[role='radio']",
        "label:has(input[type='radio'])",
        "div:has(> input[type='radio'])",
        "div:has(input[type='radio'])",
        "button[class*='option']",
        "button[class*='_option']",
        "[data-testid*='option']",
        "[data-testid*='mcq-option']",
        ".option-container > *",
    ]

    OPTION_CONTAINER_SELECTORS = [
        "[class*='_optionsContainer_']",
        "[class*='_optionContainer_']",
        "[role='radiogroup']",
        ".MuiRadioGroup-root",
        ".options-container",
        ".options",
    ]

    QUESTION_INDICATOR_SELECTORS = [
        "[class*='_mcq_']",
        "[class*='_mcqStatement_']",
        "[class*='_questionStatement_']",
        "[class*='_optionsContainer_']",
        "[class*='_optionContainer_']",
        "button[class*='_submit_']",
        "[data-testid='submit-button']",
        "input[type='radio']",
        "input[type='checkbox']",
        "[role='radiogroup']",
    ]

    SUBMIT_SELECTORS = [
        "button:has-text('Submit')",
        "button[class*='_submit_']",
        "[data-testid='submit-button']",
        "button[class*='_submitButton_']",
    ]

    NEXT_SELECTORS = [
        "button:has-text('Next')",
        "a:has-text('Next')",
        "button:has-text('Continue')",
        "[class*='_next__container_'] button",
        "[class*='_next__problem-link_']",
        "button[class*='_nextButton_']",
    ]

    FEEDBACK_CORRECT_SELECTORS = [
        "text='Correct Answer'",
        "text='Correct!'",
        "[class*='_correct_']",
        "[class*='_success_']",
        ".status-accepted",
    ]

    FEEDBACK_WRONG_SELECTORS = [
        "text='Wrong Answer'",
        "text='Incorrect'",
        "[class*='_wrong_']",
        "[class*='_incorrect_']",
    ]

    @staticmethod
    def _get_frames(page: Any) -> List[Any]:
        """Retrieve all active browsing contexts/frames, falling back to [page]."""
        try:
            frames = getattr(page, "frames", None)
            if isinstance(frames, (list, tuple)):
                return [f for f in frames if f is not None] or [page]
        except Exception:
            pass
        return [page]

    def can_handle(self, activity: ActivitySummary, page: Page) -> bool:
        """Handle if activity is QUIZ or if radio option elements are present on page."""
        if activity.type == ActivityType.QUIZ:
            return True
        for frame in self._get_frames(page):
            try:
                cnt = frame.locator("input[type='radio'], [class*='_optionBox_'], [role='radio']").count()
                if isinstance(cnt, int) and cnt > 0:
                    return True
            except Exception:
                continue
        return False

    def is_question_page(self, page: Page, activity: Optional[ActivitySummary] = None) -> bool:
        """Distinguish actual question/quiz pages from purely passive theory lessons across frames."""
        if activity and activity.type == ActivityType.QUIZ:
            return True

        for frame in self._get_frames(page):
            try:
                url = getattr(frame, "url", "") or ""
                if any(term in url.lower() for term in ("/quiz", "/mcq", "assessment", "question")):
                    return True
            except Exception:
                pass

            for sel in self.QUESTION_INDICATOR_SELECTORS:
                try:
                    loc = frame.locator(sel).first
                    cnt = loc.count() if hasattr(loc, "count") else 0
                    if isinstance(cnt, int) and cnt > 0:
                        return True
                    if hasattr(loc, "is_visible") and loc.is_visible() is True:
                        return True
                except Exception:
                    continue

        return False

    def detect_unsupported_controls(self, page: Page) -> Optional[str]:
        """Detect multi-select checkboxes or unsupported interactive controls across frames."""
        for frame in self._get_frames(page):
            try:
                cb = frame.locator("input[type='checkbox']").first
                cnt = cb.count() if hasattr(cb, "count") else 0
                is_vis = cb.is_visible() if hasattr(cb, "is_visible") else False
                if (isinstance(cnt, int) and cnt > 0) or (is_vis is True):
                    return "Checkbox input detected (multi-select MCQ is unsupported)."
            except Exception:
                continue
        return None

    def wait_for_options_or_question_ready(self, page: Page, timeout_seconds: float = 6.0) -> bool:
        """Wait for dynamic question options or controls to finish rendering across frames."""
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                for frame in self._get_frames(page):
                    # 1. Native radio inputs
                    radios = frame.locator("input[type='radio']")
                    r_cnt = radios.count() if hasattr(radios, "count") else 0
                    if isinstance(r_cnt, int) and r_cnt > 0:
                        return True

                    # 2. Option selectors
                    for sel in self.OPTION_SELECTORS:
                        loc = frame.locator(sel).first
                        cnt = loc.count() if hasattr(loc, "count") else 0
                        if isinstance(cnt, int) and cnt > 0:
                            return True
                        if hasattr(loc, "is_visible") and loc.is_visible() is True:
                            return True

                    # 3. Option container with children
                    for c_sel in self.OPTION_CONTAINER_SELECTORS:
                        container = frame.locator(c_sel).first
                        c_cnt = container.count() if hasattr(container, "count") else 0
                        if (isinstance(c_cnt, int) and c_cnt > 0) or (hasattr(container, "is_visible") and container.is_visible() is True):
                            children = container.locator("> *")
                            ch_cnt = children.count() if hasattr(children, "count") else 0
                            if isinstance(ch_cnt, int) and ch_cnt > 0:
                                return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def extract_question_and_options(self, page: Page) -> Tuple[str, List[Dict[str, Any]]]:
        """Extract clean question text and structured option details with DOM locators across frames."""
        question_parts: List[str] = []
        structured_options: List[Dict[str, Any]] = []

        for frame in self._get_frames(page):
            # 1. Extract complete question text from this frame
            try:
                body_el = frame.locator("#problem-statement, .statement, [class*='_problemBodyContent_']").first
                cnt = body_el.count() if hasattr(body_el, "count") else 0
                is_vis = body_el.is_visible() if hasattr(body_el, "is_visible") else False
                if (isinstance(cnt, int) and cnt > 0) or (is_vis is True):
                    raw_txt = body_el.inner_text()
                    if isinstance(raw_txt, str) and raw_txt.strip():
                        question_parts.append(raw_txt.strip())

                stmt_el = frame.locator("[class*='_mcqStatement_'], [class*='_questionStatement_']").first
                cnt_s = stmt_el.count() if hasattr(stmt_el, "count") else 0
                is_vis_s = stmt_el.is_visible() if hasattr(stmt_el, "is_visible") else False
                if (isinstance(cnt_s, int) and cnt_s > 0) or (is_vis_s is True):
                    raw_txt = stmt_el.inner_text()
                    if isinstance(raw_txt, str) and raw_txt.strip() and raw_txt.strip() not in question_parts:
                        question_parts.append(raw_txt.strip())

                if not question_parts:
                    mcq_el = frame.locator("[class*='_mcq_']").first
                    cnt_m = mcq_el.count() if hasattr(mcq_el, "count") else 0
                    is_vis_m = mcq_el.is_visible() if hasattr(mcq_el, "is_visible") else False
                    if (isinstance(cnt_m, int) and cnt_m > 0) or (is_vis_m is True):
                        raw = mcq_el.inner_text()
                        if isinstance(raw, str):
                            raw = raw.strip()
                            opts_container = frame.locator("[class*='_optionsContainer_'], [class*='_optionContainer_'], .options").first
                            if hasattr(opts_container, "count") and opts_container.count() > 0:
                                opt_txt = opts_container.inner_text()
                                if isinstance(opt_txt, str):
                                    raw = raw.replace(opt_txt.strip(), "")
                            raw = re.sub(r" (Submit|Next|Continue) ", "", raw).strip()
                            if raw:
                                question_parts.append(raw)
            except Exception as e:
                logger.debug(f"Frame question statement extraction notice: {e}")

            # 2. Extract structured options from this frame
            if not structured_options:
                # Strategy A: Use OPTION_SELECTORS
                for sel in self.OPTION_SELECTORS:
                    try:
                        locs_obj = frame.locator(sel)
                        locs = locs_obj.all() if hasattr(locs_obj, "all") else []
                        if locs:
                            temp_opts = []
                            for idx, loc in enumerate(locs, 1):
                                raw_text = loc.inner_text()
                                if isinstance(raw_text, str) and raw_text.strip():
                                    text = raw_text.strip()
                                    radio = loc.locator("input[type='radio']").first
                                    is_checked = False
                                    try:
                                        cnt = radio.count() if hasattr(radio, "count") else 0
                                        if isinstance(cnt, int) and cnt > 0:
                                            is_checked = bool(radio.is_checked())
                                    except Exception:
                                        pass

                                    temp_opts.append({
                                        "index": idx,
                                        "label": text,
                                        "locator": loc,
                                        "frame": frame,
                                        "is_checked": is_checked,
                                    })
                            if len(temp_opts) >= 1:
                                structured_options = temp_opts
                                break
                    except Exception:
                        continue

            # Strategy B: If no options found, inspect OPTION_CONTAINER_SELECTORS direct children
            if not structured_options:
                for c_sel in self.OPTION_CONTAINER_SELECTORS:
                    try:
                        container = frame.locator(c_sel).first
                        c_cnt = container.count() if hasattr(container, "count") else 0
                        if (isinstance(c_cnt, int) and c_cnt > 0) or (hasattr(container, "is_visible") and container.is_visible() is True):
                            children = container.locator("> div, > label, > button, > li").all()
                            if children and len(children) >= 1:
                                temp_opts = []
                                for idx, ch in enumerate(children, 1):
                                    raw_text = ch.inner_text()
                                    if isinstance(raw_text, str) and raw_text.strip():
                                        radio = ch.locator("input[type='radio']").first
                                        is_checked = False
                                        try:
                                            cnt = radio.count() if hasattr(radio, "count") else 0
                                            if isinstance(cnt, int) and cnt > 0:
                                                is_checked = bool(radio.is_checked())
                                        except Exception:
                                            pass
                                        temp_opts.append({
                                            "index": idx,
                                            "label": raw_text.strip(),
                                            "locator": ch,
                                            "frame": frame,
                                            "is_checked": is_checked,
                                        })
                                if temp_opts:
                                    structured_options = temp_opts
                                    break
                    except Exception:
                        continue

            # Strategy C: Direct radio input traversal
            if not structured_options:
                try:
                    radios_obj = frame.locator("input[type='radio']")
                    radios = radios_obj.all() if hasattr(radios_obj, "all") else []
                    if radios and len(radios) >= 1:
                        temp_opts = []
                        for idx, r in enumerate(radios, 1):
                            parent = r.locator("xpath=ancestor::label | ancestor::div[contains(@class, 'option') or contains(@class, 'Option')] | ancestor::li | ancestor::div[1]").first
                            text = ""
                            if hasattr(parent, "inner_text"):
                                raw_t = parent.inner_text()
                                if isinstance(raw_t, str):
                                    text = raw_t.strip()
                            if not text:
                                text = f"Option {idx}"
                            target_loc = parent if (hasattr(parent, "count") and parent.count() > 0) else r
                            is_checked = False
                            try:
                                is_checked = bool(r.is_checked())
                            except Exception:
                                pass
                            temp_opts.append({
                                "index": idx,
                                "label": text,
                                "locator": target_loc,
                                "frame": frame,
                                "is_checked": is_checked,
                            })
                        if temp_opts:
                            structured_options = temp_opts
                except Exception:
                    pass

            if structured_options and question_parts:
                break

        question_text = chr(10).join(question_parts)
        return question_text, structured_options

    def match_option_locator(
        self,
        options: List[Dict[str, Any]],
        reasoning: MCQReasoningResult,
    ) -> Optional[Dict[str, Any]]:
        """Match the reasoned answer to the specific structured option."""
        # 1. Match by 1-based index if valid
        if isinstance(reasoning.selected_option_index, int) and 1 <= reasoning.selected_option_index <= len(options):
            return options[reasoning.selected_option_index - 1]

        # 2. Match by exact or normalized text
        target = reasoning.selected_option_text.strip().lower()
        if target:
            for opt in options:
                lbl = opt["label"].strip().lower()
                if lbl == target or target in lbl or lbl in target:
                    return opt

        return None

    def verify_submission_feedback(self, page: Page, timeout_seconds: int = 5) -> Tuple[bool, str]:
        """Check for platform feedback confirming whether answer was accepted or wrong across frames."""
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            for frame in self._get_frames(page):
                # Check correct
                for sel in self.FEEDBACK_CORRECT_SELECTORS:
                    try:
                        el = frame.locator(sel).first
                        cnt = el.count() if hasattr(el, "count") else 0
                        is_vis = el.is_visible() if hasattr(el, "is_visible") else False
                        if (isinstance(cnt, int) and cnt > 0) or is_vis:
                            return True, el.inner_text().strip() or "Correct Answer confirmed."
                    except Exception:
                        pass

                # Check wrong
                for sel in self.FEEDBACK_WRONG_SELECTORS:
                    try:
                        el = frame.locator(sel).first
                        cnt = el.count() if hasattr(el, "count") else 0
                        is_vis = el.is_visible() if hasattr(el, "is_visible") else False
                        if (isinstance(cnt, int) and cnt > 0) or is_vis:
                            return False, el.inner_text().strip() or "Wrong Answer detected."
                    except Exception:
                        pass

            time.sleep(0.5)

        return False, "No feedback banner detected within timeout."

    def execute(
        self,
        activity: ActivitySummary,
        page: Page,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
    ) -> SubmissionRecord:
        """Execute full MCQ workflow: extraction, reasoning, selection, submission, and verification."""
        # 1. Wait for dynamic question controls if not already loaded
        q_text, options = self.extract_question_and_options(page)
        if not options:
            self.wait_for_options_or_question_ready(page, timeout_seconds=5.0)
            q_text, options = self.extract_question_and_options(page)
        option_labels = [opt["label"] for opt in options]

        logger.info(f"MCQ Prompt: '{q_text[:90]}...' ({len(options)} options discovered)")

        # 2. If no options were found, diagnose why (never guess an answer or mark completed)
        if not options:
            unsupported = self.detect_unsupported_controls(page)
            if unsupported:
                logger.warning(f"Unsupported controls detected for activity {activity.id}: {unsupported}")
                return SubmissionRecord(
                    activity_id=activity.id,
                    verdict="UNSUPPORTED_QUESTION_CONTROLS",
                    details=f"Quiz activity contains unsupported controls: {unsupported}",
                )

            if self.is_question_page(page, activity):
                logger.warning(f"Quiz question detected on activity {activity.id}, but options could not be found.")
                return SubmissionRecord(
                    activity_id=activity.id,
                    verdict="QUESTION_OPTIONS_NOT_FOUND",
                    details="Question context detected, but no selectable options loaded within timeout.",
                )

            # Genuine passive theory page without any question indicators
            logger.info("No question context detected on page. Delegating to TheoryLessonActivityHandler...")
            from course_automation.sites.codechef.handlers.lesson import TheoryLessonActivityHandler
            return TheoryLessonActivityHandler().execute(activity, page, ai_provider, dry_run)

        if not ai_provider:
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="INSPECTED_NO_AI",
                details=f"Discovered {len(options)} options; no AI provider configured.",
            )

        # 3. Reason about question and options
        reasoning = ai_provider.reason_mcq(q_text or activity.title, option_labels)
        logger.info(
            f"AI Reasoning Result -> Choice: '{reasoning.selected_option_text}' "
            f"(Index: {reasoning.selected_option_index}, Confidence: {round(reasoning.confidence*100, 1)}%)"
        )
        logger.info(f"Rationale: {reasoning.explanation}")

        # 4. Match chosen option to locator
        matched_option = self.match_option_locator(options, reasoning)
        if not matched_option:
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="OPTION_MATCH_FAILED",
                details=f"Could not map AI choice '{reasoning.selected_option_text}' to DOM option.",
            )

        # 5. Dry run safety: report proposed option without clicking or submitting
        if dry_run:
            logger.info(f"[DRY-RUN] Intended to select Option [{matched_option['index']}]: '{matched_option['label']}'. Action skipped.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="DRY_RUN_PASSED",
                details=f"Dry run passed: intended Option [{matched_option['index']}] ('{matched_option['label']}'). Confidence: {round(reasoning.confidence*100, 1)}%.",
            )

        # 6. Human confirmation gate if confidence is low
        if reasoning.requires_human_confirmation:
            print("\n" + "=" * 60)
            print("HUMAN CONFIRMATION REQUIRED (Confidence < 85%)")
            print("=" * 60)
            print(f"Question: {q_text}")
            print(f"Proposed: Option [{matched_option['index']}] - {matched_option['label']}")
            print(f"Confidence: {round(reasoning.confidence * 100, 1)}%")
            print(f"Explanation: {reasoning.explanation}")
            print("=" * 60)
            try:
                import sys
                print("Approve selecting this option? [y/N]: ", end="", flush=True)
                ans = sys.stdin.readline().strip().lower()
                if ans not in ("y", "yes"):
                    logger.info("User declined low-confidence MCQ submission.")
                    return SubmissionRecord(
                        activity_id=activity.id,
                        verdict="USER_DECLINED",
                        details="Human declined selecting low-confidence option.",
                    )
            except Exception:
                pass

        # 7. Click the matching option across frames
        try:
            loc = matched_option["locator"]
            logger.info(f"Selecting Option [{matched_option['index']}]: '{matched_option['label']}'...")
            loc.click()
            page.wait_for_timeout(600)

            # Verify selection checked
            radio = loc.locator("input[type='radio']").first
            cnt = radio.count() if hasattr(radio, "count") else 0
            if (isinstance(cnt, int) and cnt > 0) and hasattr(radio, "is_checked"):
                if not radio.is_checked():
                    try:
                        radio.click(force=True)
                    except Exception:
                        pass
                is_checked = bool(radio.is_checked())
            else:
                is_checked = True
            logger.info(f"Option selection checked status: {is_checked}")
        except Exception as e:
            logger.error(f"Error selecting option: {e}")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="SELECTION_FAILED",
                details=f"Failed to click option: {e}",
            )

        # 8. Click Submit button across frames
        sub_btn = None
        for frame in self._get_frames(page):
            for sel in self.SUBMIT_SELECTORS:
                b = frame.locator(sel).first
                cnt = b.count() if hasattr(b, "count") else 0
                is_vis = b.is_visible() if hasattr(b, "is_visible") else False
                is_en = b.is_enabled() if hasattr(b, "is_enabled") else False
                if ((isinstance(cnt, int) and cnt > 0) or (is_vis is True)) and is_en:
                    sub_btn = b
                    break
            if sub_btn:
                break

        if not sub_btn:
            logger.warning("Submit button not found or not enabled after option selection.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="SUBMIT_BUTTON_UNAVAILABLE",
                details="Selected option, but submit button was not enabled.",
            )

        logger.info("Clicking Submit button...")
        sub_btn.click()
        page.wait_for_timeout(1000)

        # 9. Verify accepted feedback banner (Only confirmed correct feedback counts as ACCEPTED)
        is_correct, feedback = self.verify_submission_feedback(page, timeout_seconds=5)
        logger.info(f"Submission verdict from website: correct={is_correct} | feedback='{feedback}'")

        if not is_correct:
            verdict_val = "WRONG_ANSWER" if ("wrong" in feedback.lower() or "incorrect" in feedback.lower()) else "VERDICT_UNVERIFIED"
            return SubmissionRecord(
                activity_id=activity.id,
                verdict=verdict_val,
                details=f"Website did not confirm correct answer: {feedback}",
            )

        # 10. Locate Next button and advance across frames
        next_btn = None
        for frame in self._get_frames(page):
            for sel in self.NEXT_SELECTORS:
                nb = frame.locator(sel).first
                cnt = nb.count() if hasattr(nb, "count") else 0
                if (isinstance(cnt, int) and cnt > 0) and nb.is_visible() and nb.is_enabled():
                    next_btn = nb
                    break
            if next_btn:
                break

        if next_btn:
            logger.info("Advancing to next activity via Next button...")
            next_btn.click()
            page.wait_for_timeout(1500)

        return SubmissionRecord(
            activity_id=activity.id,
            verdict="ACCEPTED",
            details=f"Selected Option [{matched_option['index']}] ('{matched_option['label']}'). Verdict confirmed: {feedback}",
        )
