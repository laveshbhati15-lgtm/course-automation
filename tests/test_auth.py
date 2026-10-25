"""Tests for authentication state detection."""

from unittest.mock import MagicMock
from course_automation.browser.auth import AuthDetector, AuthState


def test_detect_login_page():
    page = MagicMock()
    page.url = "https://www.codechef.com/login"
    assert AuthDetector.detect_codechef(page) == AuthState.LOGIN_PAGE


def test_detect_authenticated():
    page = MagicMock()
    page.url = "https://www.codechef.com/learn/course/test"
    locator = MagicMock()
    locator.first.is_visible.side_effect = lambda: True
    page.locator.return_value = locator

    assert AuthDetector.detect_codechef(page) == AuthState.AUTHENTICATED


def test_detect_logged_out():
    page = MagicMock()
    page.url = "https://www.codechef.com/learn/course/test"

    logged_in_selectors = {
        "#user-details-menu",
        "[data-testid='user-profile-menu']",
        ".user-name",
        ".notification-icon",
        "button[aria-label*='user' i]",
        "a[href*='/users/']",
        "button:has-text('Logout')",
    }

    def mock_locator(sel):
        mock = MagicMock()
        if sel in logged_in_selectors:
            mock.first.is_visible.return_value = False
        else:
            mock.first.is_visible.return_value = True
        return mock

    page.locator.side_effect = mock_locator
    assert AuthDetector.detect_codechef(page) == AuthState.LOGGED_OUT
