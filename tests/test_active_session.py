"""Tests for active browser tab discovery and course detection."""

from unittest.mock import MagicMock
from course_automation.browser.active_session import ActiveSessionDetector


def test_parse_codechef_url_syllabus():
    url = "https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2"
    info = ActiveSessionDetector.parse_codechef_url(url)
    assert info is not None
    assert info.course_slug == "cu-oops-sem3-2026-c2"
    assert info.module_slug is None
    assert info.activity_slug is None
    assert info.is_syllabus_page is True
    assert info.is_problem_page is False


def test_parse_codechef_url_problem():
    url = "https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2/WERWQS01/problems/INSSRTASCD"
    info = ActiveSessionDetector.parse_codechef_url(url)
    assert info is not None
    assert info.course_slug == "cu-adsa-sem3-2026-c2"
    assert info.module_slug == "WERWQS01"
    assert info.activity_slug == "INSSRTASCD"
    assert info.is_problem_page is True
    assert info.is_syllabus_page is False


def test_parse_codechef_url_lesson():
    url = "https://www.codechef.com/learn/course/python/LTCPY01/lesson/intro-python"
    info = ActiveSessionDetector.parse_codechef_url(url)
    assert info is not None
    assert info.course_slug == "python"
    assert info.module_slug == "LTCPY01"
    assert info.activity_slug == "intro-python"


def test_parse_non_codechef_url():
    url = "https://github.com/trending"
    assert ActiveSessionDetector.parse_codechef_url(url) is None


def test_detect_active_course_from_context():
    context = MagicMock()
    page1 = MagicMock()
    page1.url = "https://google.com"
    page1.title.return_value = "Google"

    page2 = MagicMock()
    page2.url = "https://www.codechef.com/learn/course/cu-adsa-sem3-2026-b1/QWER01/problems/BSTIMP"
    page2.title.return_value = "BST Implementation | CodeChef"

    context.pages = [page1, page2]

    detected = ActiveSessionDetector.detect_active_course(context)
    assert detected is not None
    assert detected.course_slug == "cu-adsa-sem3-2026-b1"
    assert detected.activity_slug == "BSTIMP"
    assert detected.page == page2
