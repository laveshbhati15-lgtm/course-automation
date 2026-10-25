"""Tests for modular CodeChef activity handlers."""

from unittest.mock import MagicMock
from course_automation.sites.codechef.handlers import (
    CodingActivityHandler,
    LockedOrUnsupportedActivityHandler,
    QuizActivityHandler,
    TheoryLessonActivityHandler,
)
from course_automation.storage.models import ActivityStatus, ActivitySummary, ActivityType


def test_coding_handler_detect_languages():
    handler = CodingActivityHandler()
    page = MagicMock()
    activity = ActivitySummary(id="1", title="Problem", slug="p1", type=ActivityType.CODING)

    # From activity language
    activity.language = "python"
    assert handler.detect_programming_language(page, activity) == "python"

    # From dropdown element
    activity.language = None
    lang_el = MagicMock()
    lang_el.first.is_visible.return_value = True
    lang_el.first.inner_text.return_value = "Java 17"
    page.locator.return_value = lang_el
    assert handler.detect_programming_language(page, activity) == "java"

    # From Monaco language model
    lang_el.first.is_visible.return_value = False
    page.evaluate.return_value = "cpp"
    assert handler.detect_programming_language(page, activity) == "cpp"


def test_locked_handler():
    handler = LockedOrUnsupportedActivityHandler()
    page = MagicMock()
    locked_act = ActivitySummary(id="2", title="Assessment", slug="exam", status=ActivityStatus.LOCKED)

    assert handler.can_handle(locked_act, page) is True
    record = handler.execute(locked_act, page)
    assert record.verdict == "LOCKED_SKIPPED"
    assert "locked on website" in record.details


def test_quiz_handler():
    handler = QuizActivityHandler()
    page = MagicMock()
    quiz_act = ActivitySummary(id="3", title="Variables Quiz", slug="quiz1", type=ActivityType.QUIZ)

    assert handler.can_handle(quiz_act, page) is True

    # Mock options
    q_el = MagicMock()
    q_el.first.is_visible.return_value = True
    q_el.first.inner_text.return_value = "What is the size of int in C++?"

    opt_el1 = MagicMock()
    opt_el1.inner_text.return_value = "A) 2 bytes"
    opt_el2 = MagicMock()
    opt_el2.inner_text.return_value = "B) 4 bytes"

    def mock_loc(sel):
        mock = MagicMock()
        if "question" in sel or "h3" in sel:
            return q_el
        mock.all.return_value = [opt_el1, opt_el2]
        return mock

    page.locator.side_effect = mock_loc

    ai = MagicMock()
    from course_automation.ai.base import MCQReasoningResult
    ai.reason_mcq.return_value = MCQReasoningResult(
        question="What is the size of int in C++?",
        options=["A) 2 bytes", "B) 4 bytes"],
        selected_option_index=2,
        selected_option_text="B) 4 bytes",
        confidence=0.95,
        explanation="Standard sizeof(int) is 4 on 32/64 bit systems.",
    )

    record = handler.execute(quiz_act, page, ai_provider=ai, dry_run=True)
    assert record.verdict == "DRY_RUN_PASSED"
    assert "B) 4 bytes" in record.details


def test_theory_handler():
    handler = TheoryLessonActivityHandler()
    page = MagicMock()
    page.title.return_value = "Introduction to Inheritance"
    theory_act = ActivitySummary(id="4", title="Intro", slug="intro", type=ActivityType.THEORY)

    assert handler.can_handle(theory_act, page) is True
    record = handler.execute(theory_act, page)
    assert record.verdict == "INSPECTED_THEORY"
