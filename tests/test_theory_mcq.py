"""Comprehensive unit and integration tests for theory lessons, MCQs, and sequential navigation."""

import pytest
from unittest.mock import MagicMock, patch
from course_automation.ai.base import MCQReasoningResult
from course_automation.safety import SafetyGate
from course_automation.sites.codechef.adapter import CodeChefAdapter
from course_automation.sites.codechef.handlers.lesson import TheoryLessonActivityHandler
from course_automation.sites.codechef.handlers.quiz import QuizActivityHandler
from course_automation.sites.codechef.navigator import TheoryCourseNavigator
from course_automation.storage.db import DatabaseManager
from course_automation.storage.models import (
    ActivityStatus,
    ActivitySummary,
    ActivityType,
    CourseSummary,
    ModuleSummary,
    SubmissionRecord,
)


# ── 1. Theory Lesson Scrolling and Next Control ───────────────────────────────

def test_theory_handler_scrolling_and_text():
    handler = TheoryLessonActivityHandler()
    page = MagicMock()
    page.locator.return_value.first.is_visible.return_value = True
    page.locator.return_value.first.inner_text.return_value = "Database transactions must satisfy ACID properties."

    text = handler.scroll_and_load_content(page, steps=2)
    assert "ACID properties" in text
    assert page.mouse.wheel.call_count == 2


def test_theory_handler_find_next_button():
    handler = TheoryLessonActivityHandler()
    page = MagicMock()

    next_btn = MagicMock()
    next_btn.first.count.return_value = 1
    next_btn.first.is_visible.return_value = True
    next_btn.first.is_enabled.return_value = True

    def mock_loc(sel):
        if "Next" in sel:
            return next_btn
        mock = MagicMock()
        mock.first.count.return_value = 0
        return mock

    page.locator.side_effect = mock_loc
    found = handler.find_next_control(page)
    assert found == next_btn.first


def test_theory_handler_dry_run_zero_clicks():
    handler = TheoryLessonActivityHandler()
    page = MagicMock()
    next_btn = MagicMock()
    next_btn.first.count.return_value = 1
    next_btn.first.is_visible.return_value = True
    next_btn.first.is_enabled.return_value = True
    page.locator.return_value.first = next_btn.first

    activity = ActivitySummary(
        id="THEORY01",
        title="Introduction to Relational Algebra",
        slug="THEORY01",
        type=ActivityType.THEORY,
    )

    record = handler.execute(activity, page, dry_run=True)
    assert record.verdict == "DRY_RUN_PASSED"
    next_btn.first.click.assert_not_called()


def test_theory_handler_live_advances_next():
    handler = TheoryLessonActivityHandler()
    page = MagicMock()
    page.url = "https://codechef.com/learn/course/dbms/mod1/lesson/1"

    next_btn = MagicMock()
    next_btn.count.return_value = 1
    next_btn.is_visible.return_value = True
    next_btn.is_enabled.return_value = True

    with patch.object(handler, "find_next_control", return_value=next_btn),          patch.object(handler, "scroll_and_load_content", return_value="Lesson Content"):

        activity = ActivitySummary(
            id="THEORY01",
            title="Introduction to Relational Algebra",
            slug="THEORY01",
            type=ActivityType.THEORY,
        )

        record = handler.execute(activity, page, dry_run=False)
        assert record.verdict == "ACCEPTED"
        next_btn.click.assert_called_once()


# ── 2. MCQ Option Selection, Submission, and Verification ─────────────────────

def test_mcq_extract_question_and_options():
    handler = QuizActivityHandler()
    page = MagicMock()

    # Mock statement
    stmt = MagicMock()
    stmt.first.count.return_value = 1
    stmt.first.is_visible.return_value = True
    stmt.first.inner_text.return_value = "Which of the following is NOT an ACID property?"

    # Mock options
    opt1 = MagicMock()
    opt1.inner_text.return_value = "Atomicity"
    opt1.locator.return_value.first.count.return_value = 1
    opt1.locator.return_value.first.is_checked.return_value = False

    opt2 = MagicMock()
    opt2.inner_text.return_value = "Durability"
    opt2.locator.return_value.first.count.return_value = 1
    opt2.locator.return_value.first.is_checked.return_value = False

    opt3 = MagicMock()
    opt3.inner_text.return_value = "Scalability"
    opt3.locator.return_value.first.count.return_value = 1
    opt3.locator.return_value.first.is_checked.return_value = False

    def mock_loc(sel):
        if "_mcqStatement_" in sel or "statement" in sel:
            return stmt
        if "_optionBox_" in sel:
            mock = MagicMock()
            mock.all.return_value = [opt1, opt2, opt3]
            return mock
        mock = MagicMock()
        mock.all.return_value = []
        mock.first.count.return_value = 0
        return mock

    page.locator.side_effect = mock_loc

    q_text, opts = handler.extract_question_and_options(page)
    assert "ACID property" in q_text
    assert len(opts) == 3
    assert opts[0]["label"] == "Atomicity"
    assert opts[2]["label"] == "Scalability"


def test_mcq_dry_run_zero_clicks_and_zero_submissions():
    handler = QuizActivityHandler()
    page = MagicMock()

    opt_loc = MagicMock()
    options = [
        {"index": 1, "label": "Atomicity", "locator": MagicMock()},
        {"index": 2, "label": "Scalability", "locator": opt_loc},
    ]

    ai = MagicMock()
    ai.reason_mcq.return_value = MCQReasoningResult(
        question="Which is not ACID?",
        options=["Atomicity", "Scalability"],
        selected_option_index=2,
        selected_option_text="Scalability",
        confidence=0.98,
        explanation="Scalability is a system property, not ACID.",
    )

    with patch.object(handler, "extract_question_and_options", return_value=("Which is not ACID?", options)):
        activity = ActivitySummary(id="MCQ01", title="ACID Quiz", slug="MCQ01", type=ActivityType.QUIZ)
        record = handler.execute(activity, page, ai_provider=ai, dry_run=True)

        assert record.verdict == "DRY_RUN_PASSED"
        assert "Option [2]" in record.details
        opt_loc.click.assert_not_called()


def test_mcq_live_selection_correct_feedback():
    handler = QuizActivityHandler()
    page = MagicMock()

    opt_loc = MagicMock()
    opt_loc.locator.return_value.first.count.return_value = 1
    opt_loc.locator.return_value.first.is_checked.return_value = True

    options = [
        {"index": 1, "label": "Atomicity", "locator": MagicMock()},
        {"index": 2, "label": "Scalability", "locator": opt_loc},
    ]

    sub_btn = MagicMock()
    sub_btn.first.count.return_value = 1
    sub_btn.first.is_visible.return_value = True
    sub_btn.first.is_enabled.return_value = True

    next_btn = MagicMock()
    next_btn.first.count.return_value = 1
    next_btn.first.is_visible.return_value = True
    next_btn.first.is_enabled.return_value = True

    def mock_loc(sel):
        if "Submit" in sel:
            return sub_btn
        if "Next" in sel:
            return next_btn
        mock = MagicMock()
        mock.first.count.return_value = 0
        return mock

    page.locator.side_effect = mock_loc

    ai = MagicMock()
    ai.reason_mcq.return_value = MCQReasoningResult(
        question="Which is not ACID?",
        options=["Atomicity", "Scalability"],
        selected_option_index=2,
        selected_option_text="Scalability",
        confidence=0.95,
        explanation="Scalability is not an ACID property.",
    )

    with patch.object(handler, "extract_question_and_options", return_value=("Which is not ACID?", options)),          patch.object(handler, "verify_submission_feedback", return_value=(True, "Correct Answer")):

        activity = ActivitySummary(id="MCQ01", title="ACID Quiz", slug="MCQ01", type=ActivityType.QUIZ)
        record = handler.execute(activity, page, ai_provider=ai, dry_run=False)

        assert record.verdict == "ACCEPTED"
        opt_loc.click.assert_called_once()
        sub_btn.first.click.assert_called_once()
        next_btn.first.click.assert_called_once()


def test_mcq_wrong_answer_feedback():
    handler = QuizActivityHandler()
    page = MagicMock()
    opt_loc = MagicMock()
    opt_loc.locator.return_value.first.count.return_value = 1
    opt_loc.locator.return_value.first.is_checked.return_value = True

    options = [{"index": 1, "label": "Atomicity", "locator": opt_loc}]

    sub_btn = MagicMock()
    sub_btn.first.count.return_value = 1
    sub_btn.first.is_visible.return_value = True
    sub_btn.first.is_enabled.return_value = True

    def mock_loc(sel):
        if "Submit" in sel:
            return sub_btn
        mock = MagicMock()
        mock.first.count.return_value = 0
        return mock

    page.locator.side_effect = mock_loc

    ai = MagicMock()
    ai.reason_mcq.return_value = MCQReasoningResult(
        question="Q?", options=["Atomicity"], selected_option_index=1, confidence=0.9
    )

    with patch.object(handler, "extract_question_and_options", return_value=("Q?", options)),          patch.object(handler, "verify_submission_feedback", return_value=(False, "Incorrect choice")):

        activity = ActivitySummary(id="MCQ01", title="Quiz", slug="MCQ01", type=ActivityType.QUIZ)
        record = handler.execute(activity, page, ai_provider=ai, dry_run=False)

        assert record.verdict == "WRONG_ANSWER"
        assert "Incorrect choice" in record.details


# ── 3. Sequential Multi-Lesson Navigator ──────────────────────────────────────

def test_navigator_sequential_run(tmp_path):
    db = DatabaseManager(db_path=tmp_path / "nav_test.db")
    adapter = MagicMock()
    safety = SafetyGate(auto_approve=True)
    page = MagicMock()

    act1 = ActivitySummary(id="T1", title="DBMS Intro", slug="t1", type=ActivityType.THEORY, status=ActivityStatus.NOT_STARTED)
    act2 = ActivitySummary(id="Q1", title="DBMS Quiz", slug="q1", type=ActivityType.QUIZ, status=ActivityStatus.NOT_STARTED)
    act3 = ActivitySummary(id="L1", title="Exam", slug="l1", type=ActivityType.QUIZ, status=ActivityStatus.LOCKED)

    mock_summary = CourseSummary(
        id="cu-dbms",
        slug="cu-dbms",
        title="Database Management Systems",
        url="https://codechef.com/learn/course/cu-dbms",
        modules=[
            ModuleSummary(
                id="mod_1",
                slug="intro",
                title="Unit 1",
                activities=[act1, act2, act3],
                completion_pct=0.0,
            )
        ],
        total_activities=3,
        completed_activities=0,
    )

    adapter.inspect_course.return_value = mock_summary

    def mock_solve(page, activity, ai_provider=None, dry_run=False):
        if activity.status == ActivityStatus.LOCKED:
            return SubmissionRecord(activity_id=activity.id, verdict="LOCKED_SKIPPED", details="Locked prerequisite")
        return SubmissionRecord(activity_id=activity.id, verdict="ACCEPTED", details="Completed successfully")

    adapter.solve_activity.side_effect = mock_solve

    navigator = TheoryCourseNavigator(
        adapter=adapter,
        db=db,
        safety_gate=safety,
        dry_run=False,
        max_activities=5,
    )

    report = navigator.run(page, "https://codechef.com/learn/course/cu-dbms")
    assert report.total_processed == 3
    assert report.completed_count == 2
    assert report.skipped_count == 1
    assert len(report.steps) == 3
    assert report.steps[0].verdict == "ACCEPTED"
    assert report.steps[1].verdict == "ACCEPTED"
    assert report.steps[2].verdict == "LOCKED_SKIPPED"


def test_navigator_dry_run(tmp_path):
    db = DatabaseManager(db_path=tmp_path / "nav_dry_test.db")
    adapter = MagicMock()
    safety = SafetyGate(dry_run=True)
    page = MagicMock()

    act1 = ActivitySummary(id="T1", title="DBMS Intro", slug="t1", type="THEORY", status="NOT_STARTED")
    mock_summary = CourseSummary(
        id="cu-dbms",
        slug="cu-dbms",
        title="Database Management Systems",
        url="https://codechef.com/learn/course/cu-dbms",
        modules=[
            ModuleSummary(
                id="mod_1",
                slug="intro",
                title="Unit 1",
                activities=[act1],
                completion_pct=0.0,
            )
        ],
        total_activities=1,
        completed_activities=0,
    )
    adapter.inspect_course.return_value = mock_summary
    adapter.solve_activity.return_value = SubmissionRecord(
        activity_id="T1",
        verdict="DRY_RUN_PASSED",
        details="Dry run passed: intended Option [1]",
    )

    navigator = TheoryCourseNavigator(
        adapter=adapter,
        db=db,
        safety_gate=safety,
        dry_run=True,
        max_activities=1,
    )

    report = navigator.run(page, "https://codechef.com/learn/course/cu-dbms")
    assert report.total_processed == 1
    assert report.completed_count == 1
    assert report.steps[0].verdict == "DRY_RUN_PASSED"
    adapter.solve_activity.assert_called_once()
