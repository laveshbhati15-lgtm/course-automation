"""Comprehensive regression tests covering edge cases, failures, and safety."""

import pytest
from unittest.mock import MagicMock, patch
from course_automation.ai.gemini import GeminiProvider
from course_automation.browser.active_session import ActiveSessionDetector
from course_automation.browser.browser_use_bridge import BrowserUseBridge
from course_automation.browser.session import BrowserSession, probe_local_cdp
from course_automation.sites.codechef.adapter import CodeChefAdapter
from course_automation.sites.codechef.handlers import (
    CodingActivityHandler,
    LockedOrUnsupportedActivityHandler,
)
from course_automation.sites.codechef.syllabus import CodeChefSyllabusParser
from course_automation.storage.models import ActivityStatus, ActivitySummary, ActivityType


# ── 1. Malformed URLs and Edge Slugs ──────────────────────────────────────────

def test_malformed_urls():
    assert CodeChefSyllabusParser.extract_slug("") == ""
    assert CodeChefSyllabusParser.extract_slug("https://example.com") == "example.com"
    assert CodeChefSyllabusParser.extract_slug("https://codechef.com/learn/course/") == ""
    assert CodeChefSyllabusParser.extract_slug("cu-oops-sem3-2026-c2") == "cu-oops-sem3-2026-c2"
    assert CodeChefSyllabusParser.extract_slug("///python///") == "python"


def test_unsupported_domains():
    adapter = CodeChefAdapter()
    assert adapter.can_handle("https://www.codechef.com/learn/course/test") is True
    assert adapter.can_handle("https://hackerrank.com/domains/tutorials") is False
    assert adapter.can_handle("https://leetcode.com/problems/two-sum") is False


# ── 2. Empty Syllabuses and Malformed API Payloads ─────────────────────────────

def test_empty_syllabus_api():
    payload = {"status": "success", "course_name": "Empty Course", "modules": []}
    summary = CodeChefSyllabusParser.parse_api_data(payload, "https://codechef.com/learn/course/empty", "empty")
    assert summary.total_activities == 0
    assert summary.completed_activities == 0
    assert summary.progress_percentage == 0.0
    assert summary.modules == []


def test_malformed_syllabus_api_null_fields():
    payload = {
        "status": "success",
        "name": None,
        "modules": [
            {
                "name": None,
                "submodules": [
                    {"contest_code": None, "problems_with_status": [{"code": None, "name": None, "status": None}]}
                ],
            }
        ],
    }
    summary = CodeChefSyllabusParser.parse_api_data(payload, "https://codechef.com/learn/course/nulls", "nulls")
    assert summary.total_activities == 1
    assert summary.completed_activities == 0
    assert summary.modules[0].activities[0].status == ActivityStatus.NOT_STARTED


# ── 3. API Failure with DOM Fallback ──────────────────────────────────────────

def test_api_failure_triggers_dom_fallback():
    adapter = CodeChefAdapter()
    page = MagicMock()
    page.url = "https://www.codechef.com/learn/course/test-course"
    page.title.return_value = "Test Course Title"

    # API returns None (simulating network error or 404)
    with patch.object(CodeChefSyllabusParser, "fetch_syllabus_api", return_value=None):
        card = MagicMock()
        card.inner_text.return_value = "Lesson 1: Introduction\nStatus: Completed"
        page.locator.return_value.all.return_value = [card]

        summary = adapter.inspect_course(page, "https://www.codechef.com/learn/course/test-course")
        assert summary.total_activities == 1
        assert summary.completed_activities == 1
        assert summary.modules[0].activities[0].status == ActivityStatus.COMPLETED


# ── 4. Course Switching In Same Session ────────────────────────────────────────

def test_course_switching_isolation():
    adapter = CodeChefAdapter()
    page = MagicMock()

    # Course A
    page.url = "https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2"
    payload_a = {"name": "Java OOP", "modules": []}
    with patch.object(CodeChefSyllabusParser, "fetch_syllabus_api", return_value=payload_a):
        summary_a = adapter.inspect_course(page, page.url)

    # Course B
    page.url = "https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2"
    payload_b = {"name": "ADSA C++", "modules": []}
    with patch.object(CodeChefSyllabusParser, "fetch_syllabus_api", return_value=payload_b):
        summary_b = adapter.inspect_course(page, page.url)

    assert summary_a.slug == "cu-oops-sem3-2026-c2"
    assert summary_a.title == "Java OOP"
    assert summary_b.slug == "cu-adsa-sem3-2026-c2"
    assert summary_b.title == "ADSA C++"


# ── 5. Locked and Unsupported Activity Safety ─────────────────────────────────

def test_locked_activity_never_marked_completed():
    handler = LockedOrUnsupportedActivityHandler()
    page = MagicMock()
    locked_activity = ActivitySummary(
        id="EXAM01",
        title="Midterm Assessment",
        slug="EXAM01",
        status=ActivityStatus.LOCKED,
        type=ActivityType.CODING,
    )

    record = handler.execute(locked_activity, page)
    assert record.verdict == "LOCKED_SKIPPED"
    assert record.verdict != "ACCEPTED"
    assert "locked on website" in record.details


def test_unsupported_activity_never_marked_completed():
    handler = LockedOrUnsupportedActivityHandler()
    page = MagicMock()
    unsupported = ActivitySummary(
        id="UNKNOWN01",
        title="Third-party Survey",
        slug="UNKNOWN01",
        status=ActivityStatus.NOT_STARTED,
        type=ActivityType.UNKNOWN,
    )

    record = handler.execute(unsupported, page)
    assert record.verdict == "UNSUPPORTED_FORMAT"
    assert record.verdict != "ACCEPTED"


# ── 6. Dry Run Never Submits Code ─────────────────────────────────────────────

def test_dry_run_safety_zero_submissions():
    handler = CodingActivityHandler()
    page = MagicMock()
    ai = MagicMock()
    ai.generate_solution.return_value = "int main() { return 0; }"

    activity = ActivitySummary(
        id="SOLVE01",
        title="Sum of Two Numbers",
        slug="SOLVE01",
        type=ActivityType.CODING,
    )

    with patch("course_automation.sites.codechef.editor.MonacoEditorController.set_editor_content") as mock_set,          patch("course_automation.sites.codechef.editor.MonacoEditorController.click_submit") as mock_submit:

        record = handler.execute(activity, page, ai_provider=ai, dry_run=True)

        assert record.verdict == "DRY_RUN_PASSED"
        # Crucial safety check: injection and submit MUST NOT be called in dry run
        mock_set.assert_not_called()
        mock_submit.assert_not_called()


# ── 7. AI Provider Missing Key or Missing Library ─────────────────────────────

def test_gemini_provider_missing_key():
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not set"):
        GeminiProvider(api_key=None)


def test_browser_use_bridge_uninstalled_raises_error():
    with patch.object(BrowserUseBridge, "is_available", return_value=False):
        with pytest.raises(RuntimeError, match="browser-use' package is not installed"):
            BrowserUseBridge.run_agent_task("inspect website")


# ── 8. Browser CDP Probe Failure Fallback ──────────────────────────────────────

def test_probe_cdp_offline():
    # Probe non-existent port
    assert probe_local_cdp("http://127.0.0.1:59999") is False
