"""Tests for verdict parsing and polling."""

from unittest.mock import MagicMock
from course_automation.sites.codechef.verdicts import VerdictState, poll_verdict


def test_poll_verdict_accepted():
    page = MagicMock()
    mock_el = MagicMock()
    mock_el.first.is_visible.side_effect = [False, True]  # Not server err, but Accepted
    page.locator.return_value = mock_el

    verdict, details = poll_verdict(page, timeout_seconds=1)
    assert verdict == VerdictState.ACCEPTED


def test_poll_verdict_server_unavailable():
    page = MagicMock()
    mock_el = MagicMock()
    mock_el.first.is_visible.return_value = True
    page.locator.return_value = mock_el

    verdict, details = poll_verdict(page, timeout_seconds=1)
    assert verdict == VerdictState.SERVER_UNAVAILABLE
