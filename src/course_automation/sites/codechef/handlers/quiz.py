"""Quiz and Multiple Choice Question activity handler for CodeChef."""

import re
import time
from typing import Any, Dict, List, Optional, Tuple
from playwright.sync_api import Frame, Locator, Page
from course_automation.ai.base import BaseAIProvider, MCQReasoningResult
from course_automation.logger import logger
from course_automation.storage.models import ActivityStatus, ActivitySummary, ActivityType, SubmissionRecord
from course_automation.sites.codechef.handlers.base import BaseActivityHandler


class QuizActivityHandler(BaseActivityHandler):
    """Handler for CodeChef Multiple Choice Quizzes, supporting single-select and multi-select."""

    OPTION_SELECTORS = [
        "[class*='_optionBox_']",
        "[class*='_option_']",
        "[role='radio']",
        "[role='checkbox']",
        "label:has(input[type='radio'])",
        "label:has(input[type='checkbox'])",
        "div:has(> input[type='radio'])",
        "div:has(> input[type='checkbox'])",
        "div:has(input[type='radio'])",
        "div:has(input[type='checkbox'])",
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
        "[role='group']",
        ".MuiRadioGroup-root",
        ".MuiFormGroup-root",
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
        "[role='group']",
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
        "text='Correct'",
        "[class*='_correct_']",
        "[class*='_success_']",
        "[class*='_banner_']:has-text('Correct')",
        "[class*='_banner_']:has-text('Right')",
    ]

    FEEDBACK_INCORRECT_SELECTORS = [
        "text='Wrong Answer'",
        "text='Incorrect'",
        "[class*='_wrong_']",
        "[class*='_error_']",
        "[class*='_banner_']:has-text('Wrong')",
        "[class*='_banner_']:has-text('Incorrect')",
    ]

    def _get_frames(self, page: Page) -> List[Any]:
        """Safely retrieve all available frames, falling back to main page context."""
        try:
            frames = getattr(page, "frames", None)
            if frames and isinstance(frames, (list, tuple)):
                return [f for f in frames if f is not None] or [page]
        except Exception:
            pass
        return [page]

    def can_handle(self, activity: ActivitySummary, page: Page) -> bool:
        """Handle if activity is QUIZ or if radio/checkbox option elements are present on page."""
        if activity.type == ActivityType.QUIZ:
            return True
        for frame in self._get_frames(page):
            try:
                cnt = frame.locator("input[type='radio'], input[type='checkbox'], [class*='_optionBox_'], [role='radio'], [role='checkbox']").count()
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
        """Detect truly unsupported interactive controls (e.g. textarea essay/code, file upload) across frames."""
        for frame in self._get_frames(page):
            try:
                # Textarea outside editor/terminal
                ta = frame.locator("textarea:not(.monaco-editor textarea):not(.xterm-helper-textarea)").first
                cnt = ta.count() if hasattr(ta, "count") else 0
                is_vis = ta.is_visible() if hasattr(ta, "is_visible") else False
                if (isinstance(cnt, int) and cnt > 0) or (is_vis is True):
                    return "Textarea input detected (freeform essay question is unsupported by QuizHandler)."

                # File upload
                fi = frame.locator("input[type='file']").first
                cnt_f = fi.count() if hasattr(fi, "count") else 0
                if isinstance(cnt_f, int) and cnt_f > 0:
                    return "File upload input detected (file submission is unsupported by QuizHandler)."
            except Exception:
                continue
        return None

    def wait_for_options_or_question_ready(self, page: Page, timeout_seconds: float = 4.0) -> bool:
        """Wait for dynamic question options or controls to finish rendering across frames."""
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                for frame in self._get_frames(page):
                    # 1. Native radio and checkbox inputs
                    inputs = frame.locator("input[type='radio'], input[type='checkbox']")
                    i_cnt = inputs.count() if hasattr(inputs, "count") else 0
                    if isinstance(i_cnt, int) and i_cnt > 0:
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
            time.sleep(0.1)
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
                                    inp = loc.locator("input[type='radio'], input[type='checkbox']").first
                                    is_checked = False
                                    input_type = None
                                    try:
                                        cnt = inp.count() if hasattr(inp, "count") else 0
                                        if isinstance(cnt, int) and cnt > 0:
                                            is_checked = bool(inp.is_checked())
                                            input_type = inp.get_attribute("type") or "radio"
                                    except Exception:
                                        pass
                                    if not input_type and hasattr(loc, "get_attribute"):
                                        role = loc.get_attribute("role")
                                        if role in ("radio", "checkbox"):
                                            input_type = role

                                    temp_opts.append({
                                        "index": idx,
                                        "label": text,
                                        "locator": loc,
                                        "frame": frame,
                                        "is_checked": is_checked,
                                        "input_type": input_type,
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
                                        inp = ch.locator("input[type='radio'], input[type='checkbox']").first
                                        is_checked = False
                                        input_type = None
                                        try:
                                            cnt = inp.count() if hasattr(inp, "count") else 0
                                            if isinstance(cnt, int) and cnt > 0:
                                                is_checked = bool(inp.is_checked())
                                                input_type = inp.get_attribute("type") or "radio"
                                        except Exception:
                                            pass
                                        if not input_type and hasattr(ch, "get_attribute"):
                                            role = ch.get_attribute("role")
                                            if role in ("radio", "checkbox"):
                                                input_type = role
                                        temp_opts.append({
                                            "index": idx,
                                            "label": raw_text.strip(),
                                            "locator": ch,
                                            "frame": frame,
                                            "is_checked": is_checked,
                                            "input_type": input_type,
                                        })
                                if temp_opts:
                                    structured_options = temp_opts
                                    break
                    except Exception:
                        continue

            # Strategy C: Direct radio or checkbox input traversal
            if not structured_options:
                try:
                    radios_obj = frame.locator("input[type='radio']")
                    radios = radios_obj.all() if hasattr(radios_obj, "all") else []
                    cbs_obj = frame.locator("input[type='checkbox']")
                    cbs = cbs_obj.all() if hasattr(cbs_obj, "all") else []

                    inputs = radios if (radios and len(radios) >= 1) else (cbs if (cbs and len(cbs) >= 1) else [])
                    default_type = "radio" if (radios and len(radios) >= 1) else "checkbox"

                    if inputs and len(inputs) >= 1:
                        temp_opts = []
                        for idx, inp in enumerate(inputs, 1):
                            parent = inp.locator("xpath=ancestor::label | ancestor::div[contains(@class, 'option') or contains(@class, 'Option')] | ancestor::li | ancestor::div[1]").first
                            text = ""
                            if hasattr(parent, "inner_text"):
                                raw_t = parent.inner_text()
                                if isinstance(raw_t, str):
                                    text = raw_t.strip()
                            if not text:
                                text = f"Option {idx}"
                            target_loc = parent if (hasattr(parent, "count") and parent.count() > 0) else inp
                            is_checked = False
                            input_type = default_type
                            try:
                                is_checked = bool(inp.is_checked())
                                input_type = inp.get_attribute("type") or default_type
                            except Exception:
                                pass
                            temp_opts.append({
                                "index": idx,
                                "label": text,
                                "locator": target_loc,
                                "frame": frame,
                                "is_checked": is_checked,
                                "input_type": input_type,
                            })
                        if temp_opts:
                            structured_options = temp_opts
                except Exception:
                    pass

        clean_question = "\n\n".join(question_parts).strip()
        return clean_question, structured_options

    def determine_question_type(
        self, options: List[Dict[str, Any]], question_text: str = ""
    ) -> Tuple[bool, bool]:
        """Determine whether the question is multiple-select or single-select from the real DOM.

        Returns:
            (is_multiple_choice, is_ambiguous)
        """
        if not options:
            return False, False

        input_types = [opt.get("input_type") for opt in options if opt.get("input_type")]
        has_checkbox = "checkbox" in input_types
        has_radio = "radio" in input_types

        # Ambiguity rule 1: Mixed inputs (both checkbox and radio on the same question)
        if has_checkbox and has_radio:
            return True, True

        q_lower = (question_text or "").lower()
        multi_cues = ["select all that apply", "choose all", "select all correct", "one or more"]
        single_cues = ["select only one", "choose only one", "single correct", "exactly one"]

        # Ambiguity rule 2: Explicit conflicting cues between statement and input types
        if has_checkbox and any(cue in q_lower for cue in single_cues):
            return True, True
        if has_radio and any(cue in q_lower for cue in multi_cues):
            return False, True

        if has_checkbox:
            return True, False

        if has_radio:
            return False, False

        # If no native inputs found, inspect text cues in statement
        general_multi_cues = ["select all that apply", "choose all", "select all correct", "one or more", "which of the following are"]
        general_single_cues = ["which of the following is", "choose the correct", "select the best"]

        if any(cue in q_lower for cue in general_multi_cues):
            return True, False
        if any(cue in q_lower for cue in general_single_cues):
            return False, False

        # Default to single-choice, unambiguous
        return False, False

    def match_option_locator(
        self, options: List[Dict[str, Any]], reasoning: MCQReasoningResult
    ) -> Optional[Dict[str, Any]]:
        """Legacy helper for matching single option locator."""
        locs = self.match_option_locators(options, reasoning, is_multiple_choice=False)
        return locs[0] if locs else None

    def match_option_locators(
        self,
        options: List[Dict[str, Any]],
        reasoning: MCQReasoningResult,
        is_multiple_choice: bool = False,
    ) -> List[Dict[str, Any]]:
        """Match structured reasoning result to one or more DOM option locators."""
        if not options:
            return []

        matched: List[Dict[str, Any]] = []

        # Target indices
        target_indices: List[int] = []
        if reasoning.selected_option_indices:
            target_indices = [idx for idx in reasoning.selected_option_indices if isinstance(idx, int)]
        elif reasoning.selected_option_index is not None:
            target_indices = [reasoning.selected_option_index]

        # Target texts
        target_texts: List[str] = []
        if reasoning.selected_option_texts:
            target_texts = [t for t in reasoning.selected_option_texts if t]
        elif reasoning.selected_option_text:
            target_texts = [reasoning.selected_option_text]

        # 1. Match by 1-based index
        for idx in target_indices:
            for opt in options:
                if opt["index"] == idx and opt not in matched:
                    matched.append(opt)

        # 2. Match by exact or normalized text if indices did not match all
        if not is_multiple_choice and not matched:
            for opt in options:
                label_clean = opt["label"].strip().lower()
                for target in target_texts:
                    t_clean = target.strip().lower()
                    if t_clean and (label_clean == t_clean or t_clean in label_clean or label_clean in t_clean):
                        if opt not in matched:
                            matched.append(opt)
                            break
                if matched:
                    break
        elif is_multiple_choice:
            for target in target_texts:
                t_clean = target.strip().lower()
                if not t_clean:
                    continue
                for opt in options:
                    label_clean = opt["label"].strip().lower()
                    if (label_clean == t_clean or t_clean in label_clean or label_clean in t_clean):
                        if opt not in matched:
                            matched.append(opt)
                            break

        return matched

    def verify_submission_feedback(self, page: Page, timeout_seconds: int = 5) -> Tuple[bool, str]:
        """Poll page frames for clear acceptance or rejection feedback."""
        start = time.time()
        while time.time() - start < timeout_seconds:
            for frame in self._get_frames(page):
                for sel in self.FEEDBACK_CORRECT_SELECTORS:
                    try:
                        loc = frame.locator(sel).first
                        cnt = loc.count() if hasattr(loc, "count") else 0
                        if ((isinstance(cnt, int) and cnt > 0) or loc.is_visible()) and loc.is_visible():
                            txt = loc.inner_text() if hasattr(loc, "inner_text") else "Correct Answer"
                            return True, str(txt).strip()
                    except Exception:
                        continue

                for sel in self.FEEDBACK_INCORRECT_SELECTORS:
                    try:
                        loc = frame.locator(sel).first
                        cnt = loc.count() if hasattr(loc, "count") else 0
                        if ((isinstance(cnt, int) and cnt > 0) or loc.is_visible()) and loc.is_visible():
                            txt = loc.inner_text() if hasattr(loc, "inner_text") else "Wrong Answer"
                            return False, str(txt).strip()
                    except Exception:
                        continue

            time.sleep(0.3)
        return False, "No feedback banner detected within timeout."

    def execute(
        self,
        activity: ActivitySummary,
        page: Page,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
    ) -> SubmissionRecord:
        """Execute MCQ solving workflow supporting both single-select and multi-select questions."""
        logger.info(f"Inspecting quiz page for activity '{activity.title}' ({activity.id})...")

        # 1. Wait for option elements or question statement to be rendered
        self.wait_for_options_or_question_ready(page, timeout_seconds=4.0)

        q_text, options = self.extract_question_and_options(page)
        if not options:
            time.sleep(0.3)
            q_text, options = self.extract_question_and_options(page)

        option_labels = [opt["label"] for opt in options]
        logger.info(f"Discovered {len(options)} options for question: '{q_text[:120]}...'")

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

        # 3. Determine single-select vs multiple-select and check for ambiguity
        is_multiple_choice, is_ambiguous = self.determine_question_type(options, q_text)
        mode_label = "multiple-select" if is_multiple_choice else "single-select"
        logger.info(f"Question structure detected: {mode_label} (ambiguous={is_ambiguous}) with {len(options)} options.")

        # Safety requirement: Never automatically select or submit when ambiguous
        if is_ambiguous:
            logger.warning(f"Question control structure or options are ambiguous for activity {activity.id}.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="AMBIGUOUS_QUESTION_CONTROLS",
                details="Question control types or option structures are ambiguous. Automatic selection blocked for safety.",
            )

        if not ai_provider:
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="INSPECTED_NO_AI",
                details=f"Discovered {len(options)} {mode_label} options; no AI provider configured.",
            )

        # 4. Reason about question and options
        reasoning = ai_provider.reason_mcq(
            q_text or activity.title,
            option_labels,
            is_multiple_choice=is_multiple_choice,
        )
        choice_summary = ", ".join([f"[{idx}] {txt}" for idx, txt in zip(reasoning.selected_option_indices, reasoning.selected_option_texts)]) or reasoning.selected_option_text
        logger.info(
            f"AI Reasoning Result ({mode_label}) -> Choices: '{choice_summary}' "
            f"(Confidence: {round(reasoning.confidence*100, 1)}%)"
        )
        logger.info(f"Rationale: {reasoning.explanation}")

        # 5. Match chosen options to DOM locators
        matched_options = self.match_option_locators(options, reasoning, is_multiple_choice=is_multiple_choice)
        if not matched_options:
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="OPTION_MATCH_FAILED",
                details=f"Could not map AI choices '{choice_summary}' to DOM options.",
            )

        # 6. Dry run safety: report proposed options without clicking or submitting
        if dry_run:
            matched_desc = ", ".join([f"Option [{opt['index']}] ('{opt['label']}')" for opt in matched_options])
            logger.info(f"[DRY-RUN] ({mode_label}) Intended to select: {matched_desc}. Action skipped.")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="DRY_RUN_PASSED",
                details=f"Dry run passed ({mode_label}): intended {matched_desc}. Confidence: {round(reasoning.confidence*100, 1)}%.",
            )

        # 7. Human confirmation gate if confidence is low or required
        if reasoning.requires_human_confirmation:
            print("\n" + "=" * 60)
            print(f"HUMAN CONFIRMATION REQUIRED ({mode_label}, Confidence < 85%)")
            print("=" * 60)
            print(f"Question: {q_text}")
            for opt in matched_options:
                print(f"Proposed: Option [{opt['index']}] - {opt['label']}")
            print(f"Confidence: {round(reasoning.confidence * 100, 1)}%")
            print(f"Explanation: {reasoning.explanation}")
            print("=" * 60)
            approved = False
            try:
                import sys
                if sys.stdin and sys.stdin.isatty():
                    print("Approve selecting these option(s)? [y/N]: ", end="", flush=True)
                    ans = sys.stdin.readline().strip().lower()
                    if ans in ("y", "yes"):
                        approved = True
            except Exception:
                pass

            if not approved:
                logger.info("Human confirmation was not provided for low-confidence MCQ. Aborting submission for safety.")
                return SubmissionRecord(
                    activity_id=activity.id,
                    verdict="USER_DECLINED",
                    details="Human confirmation required for low confidence or ambiguous MCQ; automatic submission blocked.",
                )

        # 8. Click the matching option(s) across frames
        try:
            for opt in matched_options:
                loc = opt["locator"]
                logger.info(f"Selecting Option [{opt['index']}]: '{opt['label']}'...")
                loc.click()
                page.wait_for_timeout(400)

                # Verify selection checked
                input_el = loc.locator("input[type='radio'], input[type='checkbox']").first
                cnt = input_el.count() if hasattr(input_el, "count") else 0
                if (isinstance(cnt, int) and cnt > 0) and hasattr(input_el, "is_checked"):
                    if not input_el.is_checked():
                        try:
                            input_el.click(force=True)
                        except Exception:
                            pass
                    is_checked = bool(input_el.is_checked())
                else:
                    is_checked = True
                logger.info(f"Option [{opt['index']}] checked status: {is_checked}")
        except Exception as e:
            logger.error(f"Error selecting options: {e}")
            return SubmissionRecord(
                activity_id=activity.id,
                verdict="SELECTION_FAILED",
                details=f"Failed to click option(s): {e}",
            )

        # 9. Click Submit button across frames
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
                details="Selected option(s), but submit button was not enabled.",
            )

        logger.info("Clicking Submit button...")
        sub_btn.click()
        page.wait_for_timeout(1000)

        # 10. Verify accepted feedback banner (Only confirmed correct feedback counts as ACCEPTED)
        is_correct, feedback = self.verify_submission_feedback(page, timeout_seconds=5)
        logger.info(f"Submission verdict from website: correct={is_correct} | feedback='{feedback}'")

        if not is_correct:
            verdict_val = "WRONG_ANSWER" if ("wrong" in feedback.lower() or "incorrect" in feedback.lower()) else "VERDICT_UNVERIFIED"
            return SubmissionRecord(
                activity_id=activity.id,
                verdict=verdict_val,
                details=f"Website did not confirm correct answer: {feedback}",
            )

        # 11. Locate Next button and advance across frames
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

        matched_labels = ", ".join([f"Option [{opt['index']}] ('{opt['label']}')" for opt in matched_options])
        return SubmissionRecord(
            activity_id=activity.id,
            verdict="ACCEPTED",
            details=f"Selected {matched_labels}. Verdict confirmed: {feedback}",
        )
