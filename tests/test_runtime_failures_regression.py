"""Comprehensive regression tests for runtime failures:
1. Three coding failures (editor not found, injection failed, submit button failed).
2. Code inserted into editor never counts as completed without judge ACCEPTED.
3. CodeMirror 5, CodeMirror 6, Ace, and nested iframe editor support.
4. Buffer verification checks.
5. Quiz readiness polling, unsupported controls (checkboxes), and question vs theory distinction.
6. Lesson navigation readiness, disabled controls, terminal milestones, and misrouted activities.
"""

from unittest.mock import MagicMock, patch
import pytest

from course_automation.ai.base import MCQReasoningResult
from course_automation.sites.codechef.editor import MonacoEditorController, WebEditorController
from course_automation.sites.codechef.handlers import (
    CodingActivityHandler,
    QuizActivityHandler,
    TheoryLessonActivityHandler,
)
from course_automation.sites.codechef.navigator import TheoryCourseNavigator
from course_automation.sites.codechef.verdicts import VerdictState
from course_automation.storage.models import ActivityStatus, ActivitySummary, ActivityType, CourseSummary, ModuleSummary, SubmissionRecord


# ==============================================================================
# 1. CODING FAILURES REGRESSION TESTS
# ==============================================================================

def test_coding_failure_editor_not_found():
    """Verify that when no code editor mounts, handler returns EDITOR_NOT_FOUND."""
    handler = CodingActivityHandler()
    page = MagicMock()
    page.frames = [page]
    page.evaluate.return_value = False

    activity = ActivitySummary(
        id="PROB01",
        title="Array Inversion",
        slug="prob01",
        type=ActivityType.CODING,
        language="cpp",
    )
    ai = MagicMock()
    ai.generate_solution.return_value = "int main() {}"

    with patch.object(MonacoEditorController, "wait_for_editor_ready", return_value=False):
        record = handler.execute(activity, page, ai_provider=ai, dry_run=False)

    assert record.verdict == "EDITOR_NOT_FOUND"
    assert "not mounted or ready" in record.details


def test_coding_failure_editor_injection_failed():
    """Verify that when buffer injection fails, handler returns EDITOR_INJECTION_FAILED."""
    handler = CodingActivityHandler()
    page = MagicMock()
    activity = ActivitySummary(
        id="PROB02",
        title="Matrix Multiplication",
        slug="prob02",
        type=ActivityType.CODING,
        language="cpp",
    )
    ai = MagicMock()
    ai.generate_solution.return_value = "int main() {}"

    with patch.object(MonacoEditorController, "wait_for_editor_ready", return_value=True),          patch.object(MonacoEditorController, "set_editor_content", return_value=False):
        record = handler.execute(activity, page, ai_provider=ai, dry_run=False)

    assert record.verdict == "EDITOR_INJECTION_FAILED"
    assert "Failed to inject solution" in record.details


def test_coding_failure_submit_button_failed():
    """Verify that when submit button is missing or disabled, handler returns SUBMIT_BUTTON_FAILED."""
    handler = CodingActivityHandler()
    page = MagicMock()
    activity = ActivitySummary(
        id="PROB03",
        title="Graph BFS",
        slug="prob03",
        type=ActivityType.CODING,
        language="cpp",
    )
    ai = MagicMock()
    ai.generate_solution.return_value = "int main() {}"

    with patch.object(MonacoEditorController, "wait_for_editor_ready", return_value=True),          patch.object(MonacoEditorController, "set_editor_content", return_value=True),          patch.object(MonacoEditorController, "click_submit", return_value=False):
        record = handler.execute(activity, page, ai_provider=ai, dry_run=False)

    assert record.verdict == "SUBMIT_BUTTON_FAILED"
    assert "submit button" in record.details


def test_coding_insertion_does_not_count_as_accepted_on_judge_wrong_answer():
    """Verify that successful injection does NOT mark activity accepted if judge returns WRONG_ANSWER."""
    handler = CodingActivityHandler()
    page = MagicMock()
    activity = ActivitySummary(
        id="PROB04",
        title="Binary Search",
        slug="prob04",
        type=ActivityType.CODING,
        language="cpp",
    )
    ai = MagicMock()
    ai.generate_solution.return_value = "int main() { return 1; }"

    with patch.object(MonacoEditorController, "wait_for_editor_ready", return_value=True),          patch.object(MonacoEditorController, "set_editor_content", return_value=True),          patch.object(MonacoEditorController, "click_submit", return_value=True),          patch("course_automation.sites.codechef.handlers.coding.poll_verdict", return_value=(VerdictState.WRONG_ANSWER, "Test case 3 failed")):
        record = handler.execute(activity, page, ai_provider=ai, dry_run=False)

    assert record.verdict == "WRONG_ANSWER"
    assert record.verdict != "ACCEPTED"
    assert "Test case 3 failed" in record.details


def test_coding_insertion_does_not_count_as_accepted_on_compilation_error():
    """Verify that compilation errors from judge are accurately recorded and not marked accepted."""
    handler = CodingActivityHandler()
    page = MagicMock()
    activity = ActivitySummary(
        id="PROB05",
        title="Syntax Lab",
        slug="prob05",
        type=ActivityType.CODING,
        language="cpp",
    )
    ai = MagicMock()
    ai.generate_solution.return_value = "syntax error here"

    with patch.object(MonacoEditorController, "wait_for_editor_ready", return_value=True),          patch.object(MonacoEditorController, "set_editor_content", return_value=True),          patch.object(MonacoEditorController, "click_submit", return_value=True),          patch("course_automation.sites.codechef.handlers.coding.poll_verdict", return_value=(VerdictState.COMPILATION_ERROR, "error: expected ';'")):
        record = handler.execute(activity, page, ai_provider=ai, dry_run=False)

    assert record.verdict == "COMPILATION_ERROR"
    assert record.verdict != "ACCEPTED"


# ==============================================================================
# 2. MULTI-EDITOR & MULTI-FRAME TECHNOLOGY SUPPORT
# ==============================================================================

def test_editor_buffer_verification_failure():
    """Verify that if injected text does not match editor buffer readback, injection returns False."""
    page = MagicMock()
    # evaluate returns True for injection JS, but buffer read returns stale text
    def mock_eval(script):
        if "raw = atob" in script:
            return True
        return "old stale code"

    page.evaluate.side_effect = mock_eval
    success = MonacoEditorController.set_editor_content(page, "new desired code solution")
    assert success is False


def test_editor_nested_iframe_support():
    """Verify that MonacoEditorController traverses page.frames to detect editor inside an iframe."""
    main_frame = MagicMock()
    main_frame.evaluate.return_value = False

    child_frame = MagicMock()
    child_frame.evaluate.return_value = True

    page = MagicMock()
    page.frames = [main_frame, child_frame]

    assert MonacoEditorController.is_editor_present(page) is True


def test_editor_get_content_from_child_frame():
    """Verify that buffer content is read from child frame when main frame is empty."""
    main_frame = MagicMock()
    main_frame.evaluate.return_value = None

    child_frame = MagicMock()
    child_frame.evaluate.return_value = "def solve(): pass"

    page = MagicMock()
    page.frames = [main_frame, child_frame]

    content = MonacoEditorController.get_editor_content(page)
    assert content == "def solve(): pass"


def test_editor_click_submit_in_child_frame():
    """Verify that submit button inside child iframe is detected and clicked."""
    main_frame = MagicMock()
    main_btn = MagicMock()
    main_btn.is_visible.return_value = False
    main_frame.locator.return_value.first = main_btn

    child_frame = MagicMock()
    child_btn = MagicMock()
    child_btn.is_visible.return_value = True
    child_frame.locator.return_value.first = child_btn

    page = MagicMock()
    page.frames = [main_frame, child_frame]

    assert MonacoEditorController.click_submit(page) is True
    child_btn.click.assert_called_once()


def test_web_editor_controller_alias():
    """Ensure backward-compatibility alias WebEditorController is present."""
    assert WebEditorController is MonacoEditorController


# ==============================================================================
# 3. QUIZ HANDLER REGRESSION TESTS
# ==============================================================================

def test_quiz_unsupported_controls_textarea_detected():
    """Verify that question with unsupported textarea controls returns UNSUPPORTED_QUESTION_CONTROLS."""
    handler = QuizActivityHandler()
    page = MagicMock()
    activity = ActivitySummary(id="Q01", title="Freeform Essay Quiz", slug="q01", type=ActivityType.QUIZ)

    with patch.object(handler, "extract_question_and_options", return_value=("Explain Swing architecture:", [])), \
         patch.object(handler, "detect_unsupported_controls", return_value="Textarea input detected (freeform essay question is unsupported by QuizHandler)."):
        record = handler.execute(activity, page, dry_run=False)

    assert record.verdict == "UNSUPPORTED_QUESTION_CONTROLS"
    assert "Textarea input detected" in record.details


def test_quiz_question_options_not_found():
    """Verify that quiz page with missing options returns QUESTION_OPTIONS_NOT_FOUND, not theory delegation."""
    handler = QuizActivityHandler()
    page = MagicMock()
    activity = ActivitySummary(id="Q02", title="Unrendered Quiz", slug="q02", type=ActivityType.QUIZ)

    with patch.object(handler, "extract_question_and_options", return_value=("What is O(1)?", [])),          patch.object(handler, "detect_unsupported_controls", return_value=None),          patch.object(handler, "is_question_page", return_value=True):
        record = handler.execute(activity, page, dry_run=False)

    assert record.verdict == "QUESTION_OPTIONS_NOT_FOUND"
    assert "no selectable options" in record.details


def test_quiz_delegation_to_theory_on_pure_reading_page():
    """Verify that only pure reading pages with no question indicators delegate to theory handler."""
    handler = QuizActivityHandler()
    page = MagicMock()
    # Misclassified activity that is actually a pure theory concept
    activity = ActivitySummary(id="Q03", title="Theory Concept", slug="q03", type=ActivityType.THEORY)

    with patch.object(handler, "extract_question_and_options", return_value=("", [])),          patch.object(handler, "detect_unsupported_controls", return_value=None),          patch.object(handler, "is_question_page", return_value=False),          patch("course_automation.sites.codechef.handlers.lesson.TheoryLessonActivityHandler.execute") as mock_theory:
        mock_theory.return_value = SubmissionRecord(activity_id="Q03", verdict="DRY_RUN_PASSED", details="Read theory")
        record = handler.execute(activity, page, dry_run=True)

    assert record.verdict == "DRY_RUN_PASSED"
    mock_theory.assert_called_once()


def test_quiz_feedback_verification_timeout_not_accepted():
    """Verify that quiz submission without confirmed feedback banner returns VERDICT_UNVERIFIED."""
    handler = QuizActivityHandler()
    page = MagicMock()
    opt_loc = MagicMock()
    opt_loc.locator.return_value.first.count.return_value = 1
    opt_loc.locator.return_value.first.is_checked.return_value = True

    options = [{"index": 1, "label": "Option A", "locator": opt_loc}]
    ai = MagicMock()
    ai.reason_mcq.return_value = MCQReasoningResult(
        question="Q?", options=["Option A"], selected_option_index=1, confidence=0.95
    )

    sub_btn = MagicMock()
    sub_btn.count.return_value = 1
    sub_btn.is_visible.return_value = True
    sub_btn.is_enabled.return_value = True

    page.locator.return_value.first = sub_btn

    with patch.object(handler, "extract_question_and_options", return_value=("Q?", options)),          patch.object(handler, "verify_submission_feedback", return_value=(False, "No feedback banner detected within timeout.")):

        activity = ActivitySummary(id="Q04", title="Slow Feedback Quiz", slug="q04", type=ActivityType.QUIZ)
        record = handler.execute(activity, page, ai_provider=ai, dry_run=False)

    assert record.verdict == "VERDICT_UNVERIFIED"
    assert record.verdict != "ACCEPTED"


# ==============================================================================
# 4. LESSON NAVIGATION REGRESSION TESTS
# ==============================================================================

def test_lesson_navigation_control_disabled():
    """Verify that when Next button exists but is disabled, handler returns NAVIGATION_CONTROL_DISABLED."""
    handler = TheoryLessonActivityHandler()
    page = MagicMock()
    next_btn = MagicMock()
    next_btn.is_enabled.return_value = False

    with patch.object(handler, "find_next_control", return_value=next_btn),          patch.object(handler, "_is_quiz_page", return_value=False),          patch.object(handler, "_is_coding_page", return_value=False):
        activity = ActivitySummary(id="L01", title="Disabled Nav Lesson", slug="l01", type=ActivityType.THEORY)
        record = handler.execute(activity, page, dry_run=False)

    assert record.verdict == "NAVIGATION_CONTROL_DISABLED"
    assert "remained disabled" in record.details


def test_lesson_navigation_control_missing_timeout():
    """Verify that when Next button is not found after polling, handler returns NAVIGATION_CONTROL_MISSING."""
    handler = TheoryLessonActivityHandler()
    page = MagicMock()

    with patch.object(handler, "find_next_control", return_value=None),          patch.object(handler, "_is_terminal_page", return_value=False),          patch.object(handler, "_is_quiz_page", return_value=False),          patch.object(handler, "_is_coding_page", return_value=False):
        activity = ActivitySummary(id="L02", title="Missing Nav Lesson", slug="l02", type=ActivityType.THEORY)
        record = handler.execute(activity, page, dry_run=False)

    assert record.verdict == "NAVIGATION_CONTROL_MISSING"
    assert "not found on page" in record.details


def test_lesson_terminal_page_milestone():
    """Verify that reaching a terminal milestone page returns TERMINAL_PAGE_REACHED."""
    handler = TheoryLessonActivityHandler()
    page = MagicMock()

    with patch.object(handler, "find_next_control", return_value=None),          patch.object(handler, "_is_terminal_page", return_value=True):
        activity = ActivitySummary(id="L03", title="Course Final Page", slug="l03", type=ActivityType.THEORY)
        record = handler.execute(activity, page, dry_run=False)

    assert record.verdict == "TERMINAL_PAGE_REACHED"
    assert "terminal syllabus page reached" in record.details


def test_lesson_misrouted_quiz_detected():
    """Verify that when lesson handler encounters an unanswered quiz, it returns WAITING_FOR_QUIZ_SUBMISSION."""
    handler = TheoryLessonActivityHandler()
    page = MagicMock()

    with patch.object(handler, "find_next_control", return_value=None),          patch.object(handler, "_is_terminal_page", return_value=False),          patch.object(handler, "_is_quiz_page", return_value=True):
        activity = ActivitySummary(id="L04", title="Misrouted Quiz Lesson", slug="l04", type=ActivityType.THEORY)
        record = handler.execute(activity, page, dry_run=False)

    assert record.verdict == "WAITING_FOR_QUIZ_SUBMISSION"
    assert "quiz controls requiring submission" in record.details


def test_lesson_misrouted_coding_detected():
    """Verify that when lesson handler encounters a coding problem, it returns WAITING_FOR_CODE_SUBMISSION."""
    handler = TheoryLessonActivityHandler()
    page = MagicMock()

    with patch.object(handler, "find_next_control", return_value=None),          patch.object(handler, "_is_terminal_page", return_value=False),          patch.object(handler, "_is_quiz_page", return_value=False),          patch.object(handler, "_is_coding_page", return_value=True):
        activity = ActivitySummary(id="L05", title="Misrouted Code Lesson", slug="l05", type=ActivityType.THEORY)
        record = handler.execute(activity, page, dry_run=False)

    assert record.verdict == "WAITING_FOR_CODE_SUBMISSION"
    assert "code editor requiring solution submission" in record.details


# ==============================================================================
# 5. NAVIGATOR RUN REPORT FALSE-POSITIVE COMPLETION TESTS
# ==============================================================================

def test_navigator_never_counts_failed_or_unverified_coding_as_completed(tmp_path):
    """Verify TheoryCourseNavigator does not increment completed_count for non-ACCEPTED verdicts."""
    from course_automation.storage.db import DatabaseManager
    from course_automation.safety import SafetyGate

    db = DatabaseManager(db_path=tmp_path / "nav_fail_test.db")
    adapter = MagicMock()
    safety = SafetyGate(auto_approve=True)
    page = MagicMock()

    act1 = ActivitySummary(id="C1", title="Prob 1", slug="c1", type=ActivityType.CODING, status=ActivityStatus.NOT_STARTED)
    act2 = ActivitySummary(id="C2", title="Prob 2", slug="c2", type=ActivityType.CODING, status=ActivityStatus.NOT_STARTED)
    act3 = ActivitySummary(id="C3", title="Prob 3", slug="c3", type=ActivityType.CODING, status=ActivityStatus.NOT_STARTED)

    mock_summary = CourseSummary(
        id="c-course",
        slug="c-course",
        title="C Coding Course",
        url="https://codechef.com/learn/course/c-course",
        modules=[
            ModuleSummary(id="m1", slug="m1", title="Mod 1", activities=[act1, act2, act3], completion_pct=0.0)
        ],
        total_activities=3,
        completed_activities=0,
    )
    adapter.inspect_course.return_value = mock_summary

    # act1 fails with EDITOR_INJECTION_FAILED
    # act2 fails with WRONG_ANSWER
    # act3 passes with ACCEPTED
    verdicts = [
        SubmissionRecord(activity_id="C1", verdict="EDITOR_INJECTION_FAILED", details="Injection failure"),
        SubmissionRecord(activity_id="C2", verdict="WRONG_ANSWER", details="Judge failed"),
        SubmissionRecord(activity_id="C3", verdict="ACCEPTED", details="Judge accepted"),
    ]
    adapter.solve_activity.side_effect = verdicts

    navigator = TheoryCourseNavigator(adapter=adapter, db=db, safety_gate=safety, dry_run=False, max_activities=3)
    report = navigator.run(page, "https://codechef.com/learn/course/c-course")

    assert report.total_processed == 3
    assert report.completed_count == 1  # Only C3 counted!
    assert report.failed_count == 2     # C1 and C2 failed!
    assert report.skipped_count == 0


# ==============================================================================
# 6. QUIZ OPTION DETECTION & NO-OPTIONS REGRESSION TESTS
# ==============================================================================

def test_quiz_question_with_no_options_never_guesses_or_completes_dry_run():
    """Verify that a question with statement but 0 options returns QUESTION_OPTIONS_NOT_FOUND even in dry-run."""
    handler = QuizActivityHandler()
    page = MagicMock()
    page.frames = [page]

    # Statement exists
    stmt_loc = MagicMock()
    stmt_loc.count.return_value = 1
    stmt_loc.is_visible.return_value = True
    stmt_loc.inner_text.return_value = "Quiz Application Using Java Swing: Build a GUI application."

    def mock_locator(sel):
        mock = MagicMock()
        if "statement" in sel or "problemBody" in sel:
            mock.first = stmt_loc
            mock.count.return_value = 1
            return mock
        mock.all.return_value = []
        mock.count.return_value = 0
        mock.first.count.return_value = 0
        mock.first.is_visible.return_value = False
        return mock

    page.locator.side_effect = mock_locator

    activity = ActivitySummary(
        id="JAVASWING",
        title="Quiz Application Using Java Swing",
        slug="JAVASWING",
        type=ActivityType.QUIZ,
    )
    ai = MagicMock()

    # Dry-run execution
    record_dry = handler.execute(activity, page, ai_provider=ai, dry_run=True)
    assert record_dry.verdict == "QUESTION_OPTIONS_NOT_FOUND"
    assert record_dry.verdict != "DRY_RUN_PASSED"
    assert "no selectable options" in record_dry.details
    ai.reason_mcq.assert_not_called()

    # Live execution
    record_live = handler.execute(activity, page, ai_provider=ai, dry_run=False)
    assert record_live.verdict == "QUESTION_OPTIONS_NOT_FOUND"
    assert record_live.verdict != "ACCEPTED"
    ai.reason_mcq.assert_not_called()


def test_quiz_option_detection_div_optionbox():
    """Verify that options in div elements with _optionBox_ class are correctly extracted."""
    handler = QuizActivityHandler()
    page = MagicMock()
    page.frames = [page]

    stmt = MagicMock()
    stmt.count.return_value = 1
    stmt.is_visible.return_value = True
    stmt.inner_text.return_value = "What is JFrame in Java Swing?"

    opt1 = MagicMock()
    opt1.inner_text.return_value = "A top-level container window"
    opt1.locator.return_value.first.count.return_value = 0

    opt2 = MagicMock()
    opt2.inner_text.return_value = "A layout manager"
    opt2.locator.return_value.first.count.return_value = 0

    def mock_loc(sel):
        mock = MagicMock()
        if "statement" in sel:
            mock.first = stmt
            mock.count.return_value = 1
            return mock
        if "_optionBox_" in sel:
            mock.all.return_value = [opt1, opt2]
            mock.count.return_value = 2
            return mock
        mock.all.return_value = []
        mock.count.return_value = 0
        mock.first.count.return_value = 0
        mock.first.is_visible.return_value = False
        return mock

    page.locator.side_effect = mock_loc

    q_text, options = handler.extract_question_and_options(page)
    assert "What is JFrame" in q_text
    assert len(options) == 2
    assert options[0]["label"] == "A top-level container window"
    assert options[1]["label"] == "A layout manager"


def test_quiz_option_detection_options_container_children():
    """Verify fallback extraction from children of _optionsContainer_ when class selectors differ."""
    handler = QuizActivityHandler()
    page = MagicMock()
    page.frames = [page]

    stmt = MagicMock()
    stmt.count.return_value = 1
    stmt.is_visible.return_value = True
    stmt.inner_text.return_value = "Which component displays text in Swing?"

    child1 = MagicMock()
    child1.inner_text.return_value = "JLabel"
    child1.locator.return_value.first.count.return_value = 0

    child2 = MagicMock()
    child2.inner_text.return_value = "JButton"
    child2.locator.return_value.first.count.return_value = 0

    container = MagicMock()
    container.count.return_value = 1
    container.is_visible.return_value = True
    container.locator.return_value.all.return_value = [child1, child2]

    def mock_loc(sel):
        mock = MagicMock()
        if "statement" in sel:
            mock.first = stmt
            mock.count.return_value = 1
            return mock
        if "_optionsContainer_" in sel:
            mock.first = container
            mock.count.return_value = 1
            return mock
        mock.all.return_value = []
        mock.count.return_value = 0
        mock.first.count.return_value = 0
        mock.first.is_visible.return_value = False
        return mock

    page.locator.side_effect = mock_loc

    q_text, options = handler.extract_question_and_options(page)
    assert "Which component displays text" in q_text
    assert len(options) == 2
    assert options[0]["label"] == "JLabel"
    assert options[1]["label"] == "JButton"


def test_quiz_option_detection_nested_iframe():
    """Verify that options and statement inside a nested iframe are discovered."""
    handler = QuizActivityHandler()

    main_frame = MagicMock()
    main_frame.locator.return_value.first.count.return_value = 0
    main_frame.locator.return_value.all.return_value = []

    iframe = MagicMock()
    stmt = MagicMock()
    stmt.count.return_value = 1
    stmt.is_visible.return_value = True
    stmt.inner_text.return_value = "Inside Iframe: What is JPanel?"

    opt1 = MagicMock()
    opt1.inner_text.return_value = "A lightweight container"
    opt1.locator.return_value.first.count.return_value = 0

    opt2 = MagicMock()
    opt2.inner_text.return_value = "A database connection"
    opt2.locator.return_value.first.count.return_value = 0

    def iframe_loc(sel):
        mock = MagicMock()
        if "statement" in sel:
            mock.first = stmt
            mock.count.return_value = 1
            return mock
        if "_optionBox_" in sel or "MuiFormControlLabel" in sel:
            mock.all.return_value = [opt1, opt2]
            mock.count.return_value = 2
            return mock
        mock.all.return_value = []
        mock.count.return_value = 0
        mock.first.count.return_value = 0
        mock.first.is_visible.return_value = False
        return mock

    iframe.locator.side_effect = iframe_loc

    page = MagicMock()
    page.frames = [main_frame, iframe]

    q_text, options = handler.extract_question_and_options(page)
    assert "Inside Iframe: What is JPanel?" in q_text
    assert len(options) == 2
    assert options[0]["label"] == "A lightweight container"
    assert options[1]["label"] == "A database connection"


def test_quiz_option_detection_direct_radio_inputs():
    """Verify fallback to direct input[type='radio'] elements when wrappers have custom classes."""
    handler = QuizActivityHandler()
    page = MagicMock()
    page.frames = [page]

    stmt = MagicMock()
    stmt.count.return_value = 1
    stmt.is_visible.return_value = True
    stmt.inner_text.return_value = "Swing is thread safe?"

    radio1 = MagicMock()
    radio1.is_checked.return_value = False
    parent1 = MagicMock()
    parent1.count.return_value = 1
    parent1.inner_text.return_value = "No, Swing is not thread safe"
    radio1.locator.return_value.first = parent1

    radio2 = MagicMock()
    radio2.is_checked.return_value = False
    parent2 = MagicMock()
    parent2.count.return_value = 1
    parent2.inner_text.return_value = "Yes, Swing is completely thread safe"
    radio2.locator.return_value.first = parent2

    def mock_loc(sel):
        mock = MagicMock()
        if "statement" in sel:
            mock.first = stmt
            mock.count.return_value = 1
            return mock
        if sel == "input[type='radio']":
            mock.all.return_value = [radio1, radio2]
            mock.count.return_value = 2
            return mock
        mock.all.return_value = []
        mock.count.return_value = 0
        mock.first.count.return_value = 0
        mock.first.is_visible.return_value = False
        return mock

    page.locator.side_effect = mock_loc

    q_text, options = handler.extract_question_and_options(page)
    assert len(options) == 2
    assert "No, Swing is not thread safe" in options[0]["label"]
    assert "Yes, Swing is completely thread safe" in options[1]["label"]


def test_quiz_option_detection_checkbox_inputs():
    """Verify that options rendered with checkboxes in CodeChef DOM are extracted with input_type='checkbox'."""
    handler = QuizActivityHandler()
    page = MagicMock()
    page.frames = [page]

    stmt = MagicMock()
    stmt.count.return_value = 1
    stmt.is_visible.return_value = True
    stmt.inner_text.return_value = "Which of the following are valid Swing components? (Select all that apply)"

    opt1 = MagicMock()
    opt1.inner_text.return_value = "JButton"
    cb1 = MagicMock()
    cb1.count.return_value = 1
    cb1.is_checked.return_value = False
    cb1.get_attribute.return_value = "checkbox"
    opt1.locator.return_value.first = cb1

    opt2 = MagicMock()
    opt2.inner_text.return_value = "JFrame"
    cb2 = MagicMock()
    cb2.count.return_value = 1
    cb2.is_checked.return_value = False
    cb2.get_attribute.return_value = "checkbox"
    opt2.locator.return_value.first = cb2

    opt3 = MagicMock()
    opt3.inner_text.return_value = "JNotAComponent"
    cb3 = MagicMock()
    cb3.count.return_value = 1
    cb3.is_checked.return_value = False
    cb3.get_attribute.return_value = "checkbox"
    opt3.locator.return_value.first = cb3

    def mock_loc(sel):
        mock = MagicMock()
        if "statement" in sel:
            mock.first = stmt
            mock.count.return_value = 1
            return mock
        if "[class*='_optionBox_']" in sel:
            mock.all.return_value = [opt1, opt2, opt3]
            mock.count.return_value = 3
            return mock
        mock.all.return_value = []
        mock.count.return_value = 0
        mock.first.count.return_value = 0
        mock.first.is_visible.return_value = False
        return mock

    page.locator.side_effect = mock_loc

    q_text, options = handler.extract_question_and_options(page)
    assert len(options) == 3
    assert options[0]["label"] == "JButton"
    assert options[0]["input_type"] == "checkbox"
    assert options[1]["label"] == "JFrame"
    assert options[1]["input_type"] == "checkbox"

    is_multi, is_ambig = handler.determine_question_type(options, q_text)
    assert is_multi is True
    assert is_ambig is False


def test_quiz_checkbox_multi_select_dry_run():
    """Verify that checkbox multi-select MCQ in dry-run reports all intended selections and does not click."""
    handler = QuizActivityHandler()
    page = MagicMock()
    page.frames = [page]

    loc1 = MagicMock()
    loc2 = MagicMock()
    options = [
        {"index": 1, "label": "JButton", "locator": loc1, "frame": page, "is_checked": False, "input_type": "checkbox"},
        {"index": 2, "label": "JFrame", "locator": loc2, "frame": page, "is_checked": False, "input_type": "checkbox"},
        {"index": 3, "label": "JNonComponent", "locator": MagicMock(), "frame": page, "is_checked": False, "input_type": "checkbox"},
    ]

    activity = ActivitySummary(
        id="JAVASWING_MULTI",
        title="Quiz Application Using Java Swing",
        slug="javaswing_multi",
        type=ActivityType.QUIZ,
    )

    ai_provider = MagicMock()
    ai_provider.reason_mcq.return_value = MCQReasoningResult(
        question="Select all valid Swing components",
        options=["JButton", "JFrame", "JNonComponent"],
        selected_option_indices=[1, 2],
        selected_option_texts=["JButton", "JFrame"],
        is_multiple_choice=True,
        confidence=0.96,
        explanation="JButton and JFrame are standard javax.swing top-level/control components.",
        requires_human_confirmation=False,
    )

    with patch.object(handler, "wait_for_options_or_question_ready", return_value=True), \
         patch.object(handler, "extract_question_and_options", return_value=("Select all valid Swing components", options)):
        record = handler.execute(activity, page, ai_provider=ai_provider, dry_run=True)

    assert record.verdict == "DRY_RUN_PASSED"
    assert "multiple-select" in record.details
    assert "Option [1] ('JButton')" in record.details
    assert "Option [2] ('JFrame')" in record.details
    # Locators must NOT be clicked in dry-run
    loc1.click.assert_not_called()
    loc2.click.assert_not_called()


def test_quiz_checkbox_multi_select_live_execution():
    """Verify that live execution of checkbox multi-select clicks all options, verifies submit, and confirms feedback."""
    handler = QuizActivityHandler()
    page = MagicMock()
    page.frames = [page]

    loc1 = MagicMock()
    cb1 = MagicMock()
    cb1.count.return_value = 1
    cb1.is_checked.return_value = True
    loc1.locator.return_value.first = cb1

    loc2 = MagicMock()
    cb2 = MagicMock()
    cb2.count.return_value = 1
    cb2.is_checked.return_value = True
    loc2.locator.return_value.first = cb2

    options = [
        {"index": 1, "label": "JButton", "locator": loc1, "frame": page, "is_checked": False, "input_type": "checkbox"},
        {"index": 2, "label": "JFrame", "locator": loc2, "frame": page, "is_checked": False, "input_type": "checkbox"},
    ]

    activity = ActivitySummary(
        id="JAVASWING_LIVE",
        title="Quiz Application Using Java Swing",
        slug="javaswing_live",
        type=ActivityType.QUIZ,
    )

    ai_provider = MagicMock()
    ai_provider.reason_mcq.return_value = MCQReasoningResult(
        question="Select all valid Swing components",
        options=["JButton", "JFrame"],
        selected_option_indices=[1, 2],
        selected_option_texts=["JButton", "JFrame"],
        is_multiple_choice=True,
        confidence=0.95,
        explanation="Both are Swing components.",
        requires_human_confirmation=False,
    )

    submit_btn = MagicMock()
    submit_btn.count.return_value = 1
    submit_btn.is_visible.return_value = True
    submit_btn.is_enabled.return_value = True

    def mock_loc(sel):
        mock = MagicMock()
        if "Submit" in sel:
            mock.first = submit_btn
            mock.count.return_value = 1
            mock.is_visible.return_value = True
            mock.is_enabled.return_value = True
            return mock
        mock.all.return_value = []
        mock.count.return_value = 0
        mock.first.count.return_value = 0
        mock.first.is_visible.return_value = False
        mock.first.is_enabled.return_value = False
        return mock

    page.locator.side_effect = mock_loc

    with patch.object(handler, "wait_for_options_or_question_ready", return_value=True), \
         patch.object(handler, "extract_question_and_options", return_value=("Select components", options)), \
         patch.object(handler, "verify_submission_feedback", return_value=(True, "Correct Answer")):
        record = handler.execute(activity, page, ai_provider=ai_provider, dry_run=False)

    assert record.verdict == "ACCEPTED"
    assert "Option [1] ('JButton')" in record.details
    assert "Option [2] ('JFrame')" in record.details
    loc1.click.assert_called_once()
    loc2.click.assert_called_once()
    submit_btn.click.assert_called_once()


def test_quiz_ambiguous_question_mixed_controls_never_submits():
    """Verify that question with conflicting radio and checkbox inputs is flagged ambiguous and never submits."""
    handler = QuizActivityHandler()
    page = MagicMock()
    page.frames = [page]

    loc1 = MagicMock()
    loc2 = MagicMock()
    options = [
        {"index": 1, "label": "Option A", "locator": loc1, "frame": page, "is_checked": False, "input_type": "radio"},
        {"index": 2, "label": "Option B", "locator": loc2, "frame": page, "is_checked": False, "input_type": "checkbox"},
    ]

    activity = ActivitySummary(
        id="AMBIG_01",
        title="Ambiguous Quiz Activity",
        slug="ambig_01",
        type=ActivityType.QUIZ,
    )
    ai_provider = MagicMock()

    with patch.object(handler, "wait_for_options_or_question_ready", return_value=True), \
         patch.object(handler, "extract_question_and_options", return_value=("Ambiguous Question?", options)):
        record = handler.execute(activity, page, ai_provider=ai_provider, dry_run=False)

    assert record.verdict == "AMBIGUOUS_QUESTION_CONTROLS"
    assert "ambiguous" in record.details.lower()
    loc1.click.assert_not_called()
    loc2.click.assert_not_called()
    ai_provider.reason_mcq.assert_not_called()


def test_quiz_ambiguous_question_conflicting_statement_and_controls_never_submits():
    """Verify that question with conflicting cues between statement and controls is flagged ambiguous."""
    handler = QuizActivityHandler()
    page = MagicMock()
    page.frames = [page]

    loc1 = MagicMock()
    loc2 = MagicMock()
    options = [
        {"index": 1, "label": "Option A", "locator": loc1, "frame": page, "is_checked": False, "input_type": "checkbox"},
        {"index": 2, "label": "Option B", "locator": loc2, "frame": page, "is_checked": False, "input_type": "checkbox"},
    ]

    activity = ActivitySummary(
        id="AMBIG_02",
        title="Conflicting Cues Quiz Activity",
        slug="ambig_02",
        type=ActivityType.QUIZ,
    )
    ai_provider = MagicMock()

    # Statement explicitly demands "Select only one", but controls are multi-select checkboxes
    conflicting_statement = "Select only one correct answer for this problem:"

    with patch.object(handler, "wait_for_options_or_question_ready", return_value=True), \
         patch.object(handler, "extract_question_and_options", return_value=(conflicting_statement, options)):
        record = handler.execute(activity, page, ai_provider=ai_provider, dry_run=False)

    assert record.verdict == "AMBIGUOUS_QUESTION_CONTROLS"
    assert "ambiguous" in record.details.lower()
    loc1.click.assert_not_called()
    loc2.click.assert_not_called()
    ai_provider.reason_mcq.assert_not_called()


def test_quiz_low_confidence_mcq_never_submits_without_human_confirmation():
    """Verify that low-confidence (<85%) reasoning blocks automatic submission for safety."""
    handler = QuizActivityHandler()
    page = MagicMock()
    page.frames = [page]

    loc1 = MagicMock()
    loc2 = MagicMock()
    options = [
        {"index": 1, "label": "Option A", "locator": loc1, "frame": page, "is_checked": False, "input_type": "radio"},
        {"index": 2, "label": "Option B", "locator": loc2, "frame": page, "is_checked": False, "input_type": "radio"},
    ]

    activity = ActivitySummary(
        id="LOW_CONF",
        title="Uncertain Question",
        slug="low_conf",
        type=ActivityType.QUIZ,
    )

    ai_provider = MagicMock()
    ai_provider.reason_mcq.return_value = MCQReasoningResult(
        question="Uncertain question?",
        options=["Option A", "Option B"],
        selected_option_index=1,
        selected_option_text="Option A",
        confidence=0.55,  # Low confidence!
        explanation="Not sure.",
        requires_human_confirmation=True,
    )

    with patch.object(handler, "wait_for_options_or_question_ready", return_value=True), \
         patch.object(handler, "extract_question_and_options", return_value=("Uncertain question?", options)):
        # In non-interactive test environment without stdin confirmation
        record = handler.execute(activity, page, ai_provider=ai_provider, dry_run=False)

    assert record.verdict == "USER_DECLINED"
    assert "Human confirmation required" in record.details
    loc1.click.assert_not_called()
    loc2.click.assert_not_called()
