"""Tests for CodeChef adapter logic and dry-run execution."""

from unittest.mock import MagicMock
from course_automation.sites.codechef.adapter import CodeChefAdapter
from course_automation.storage.models import ActivityStatus, ActivitySummary, ActivityType


def test_can_handle():
    adapter = CodeChefAdapter()
    assert adapter.can_handle("https://www.codechef.com/learn/course/cu-oops") is True
    assert adapter.can_handle("https://leetcode.com/problemset") is False


def test_solve_activity_dry_run():
    adapter = CodeChefAdapter()
    page = MagicMock()
    page.url = "https://www.codechef.com/learn/course/test"

    ai_provider = MagicMock()
    ai_provider.generate_solution.return_value = "public class Solution {}"

    activity = ActivitySummary(
        id="RECT01",
        title="Rectangle Class",
        slug="RECT01",
        type=ActivityType.CODING,
        url="https://www.codechef.com/learn/course/test/problems/RECT01",
        language="java",
    )

    # In dry-run mode, solution is generated, but submission is skipped
    record = adapter.solve_activity(
        page=page,
        activity=activity,
        ai_provider=ai_provider,
        dry_run=True,
    )

    assert record.verdict == "DRY_RUN_PASSED"
    assert record.language == "java"
    assert "public class Solution" in (record.code_preview or "")
    ai_provider.generate_solution.assert_called_once()
