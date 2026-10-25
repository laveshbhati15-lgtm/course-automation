"""Tests for CodeChef syllabus parsing."""

from unittest.mock import MagicMock
from course_automation.sites.codechef.syllabus import CodeChefSyllabusParser
from course_automation.storage.models import ActivityStatus, ActivityType


def test_extract_slug():
    url = "https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2"
    assert CodeChefSyllabusParser.extract_slug(url) == "cu-oops-sem3-2026-c2"

    url_with_subpath = "https://www.codechef.com/learn/course/cu-adsa-sem3-2026-b1/QWER01/problems/BSTIMP"
    assert CodeChefSyllabusParser.extract_slug(url_with_subpath) == "cu-adsa-sem3-2026-b1"


def test_parse_api_data(sample_syllabus_payload):
    url = "https://www.codechef.com/learn/course/test-course-101"
    summary = CodeChefSyllabusParser.parse_api_data(sample_syllabus_payload, url, "test-course-101")

    assert summary.title == "Object Oriented Programming in Java"
    assert summary.total_activities == 3
    assert summary.completed_activities == 1
    assert summary.progress_percentage == 33.3

    assert len(summary.modules) == 2
    mod1 = summary.modules[0]
    assert len(mod1.activities) == 2
    assert mod1.activities[0].status == ActivityStatus.COMPLETED
    assert mod1.activities[0].type == ActivityType.THEORY
    assert mod1.activities[1].status == ActivityStatus.NOT_STARTED
    assert mod1.activities[1].type == ActivityType.CODING
