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

def test_quiz_unsupported_controls_checkbox_detected():
    """Verify that question with checkboxes returns UNSUPPORTED_QUESTION_CONTROLS."""
    handler = QuizActivityHandler()
    page = MagicMock()
    activity = ActivitySummary(id="Q01", title="Multi-Select Quiz", slug="q01", type=ActivityType.QUIZ)

    with patch.object(handler, "extract_question_and_options", return_value=("Select all that apply:", [])),          patch.object(handler, "detect_unsupported_controls", return_value="Checkbox input detected (multi-select MCQ is unsupported)."):
        record = handler.execute(activity, page, dry_run=False)

    assert record.verdict == "UNSUPPORTED_QUESTION_CONTROLS"
    assert "Checkbox input detected" in record.details


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
