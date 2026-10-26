"""Synthetic and mock tests for authentication state detection and manual login flow."""

from unittest.mock import MagicMock, patch
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


def test_detect_authenticated_course_page():
    """Verify modern CodeChef Learn course page is recognized as AUTHENTICATED."""
    page = MagicMock()
    page.url = "https://www.codechef.com/learn/course/synthetic-dbms-course"
    page.is_closed.return_value = False

    def mock_locator(sel):
        mock = MagicMock()
        mock.first.is_visible.return_value = False
        mock.count.return_value = 0

        # Course curriculum item is present and visible
        if sel == ".course-item" or "[class*='syllabus']" in sel:
            mock.first.is_visible.return_value = True
            mock.count.return_value = 5
        return mock

    page.locator.side_effect = mock_locator
    assert AuthDetector.detect_codechef(page) == AuthState.AUTHENTICATED


def test_detect_authenticated_via_modern_avatar():
    """Verify modern avatar/profile button in top bar signals AUTHENTICATED."""
    page = MagicMock()
    page.url = "https://www.codechef.com/learn/course/synthetic-python-course"
    page.is_closed.return_value = False

    def mock_locator(sel):
        mock = MagicMock()
        mock.first.is_visible.return_value = False
        mock.count.return_value = 0

        if sel == "button[aria-label*='profile' i]" or sel == "[data-testid*='avatar']":
            mock.first.is_visible.return_value = True
        return mock

    page.locator.side_effect = mock_locator
    assert AuthDetector.detect_codechef(page) == AuthState.AUTHENTICATED


def test_detect_authenticated_via_cookies():
    """Verify context session cookie presence confirms AUTHENTICATED state."""
    page = MagicMock()
    page.url = "https://www.codechef.com/learn/course/synthetic-algo-course"
    page.is_closed.return_value = False

    # No DOM selectors match
    loc = MagicMock()
    loc.first.is_visible.return_value = False
    loc.count.return_value = 0
    page.locator.return_value = loc

    # Context holds Drupal session cookie
    context = MagicMock()
    context.cookies.return_value = [
        {"name": "SESS12345abcdef", "value": "mock_valid_session_token", "domain": ".codechef.com"}
    ]
    page.context = context

    assert AuthDetector.detect_codechef(page) == AuthState.AUTHENTICATED


def test_detect_redirects_and_oauth_flows():
    """Verify OAuth providers and intermediate redirect URLs return LOGIN_PAGE."""
    redirect_urls = [
        "https://accounts.google.com/o/oauth2/v2/auth?client_id=123",
        "https://github.com/login/oauth/authorize?scope=read:user",
        "https://www.codechef.com/oauth/authorize",
        "https://www.codechef.com/login?redirect=/learn/course/test",
    ]

    for url in redirect_urls:
        page = MagicMock()
        page.url = url
        page.is_closed.return_value = False
        assert AuthDetector.detect_codechef(page) == AuthState.LOGIN_PAGE, f"Failed for {url}"


def test_wait_for_manual_login_success():
    """Verify wait_for_manual_login validates session and returns True on authentication."""
    page = MagicMock()
    page.url = "https://www.codechef.com/learn/course/sample"
    page.is_closed.return_value = False
    context = MagicMock()
    context.pages = [page]
    page.context = context

    with patch.object(AuthDetector, "detect", return_value=AuthState.AUTHENTICATED):
        success = AuthDetector.wait_for_manual_login(
            page=page,
            timeout_seconds=5,
            poll_interval=0.01,
        )
        assert success is True
        page.goto.assert_called_once()


def test_wait_for_manual_login_multi_tab():
    """Verify detection scans multiple open tabs and detects authentication on second tab."""
    login_tab = MagicMock()
    login_tab.url = "https://www.codechef.com/login"
    login_tab.is_closed.return_value = False

    course_tab = MagicMock()
    course_tab.url = "https://www.codechef.com/learn/course/active-course"
    course_tab.is_closed.return_value = False

    context = MagicMock()
    context.pages = [login_tab, course_tab]
    login_tab.context = context

    def mock_detect(p, site="codechef"):
        if p == course_tab:
            return AuthState.AUTHENTICATED
        return AuthState.LOGIN_PAGE

    with patch.object(AuthDetector, "detect", side_effect=mock_detect):
        success = AuthDetector.wait_for_manual_login(
            page=login_tab,
            timeout_seconds=5,
            poll_interval=0.01,
        )
        assert success is True


def test_wait_for_manual_login_timeout():
    """Verify wait_for_manual_login returns False when timeout elapses."""
    page = MagicMock()
    page.url = "https://www.codechef.com/login"
    page.is_closed.return_value = False
    context = MagicMock()
    context.pages = [page]
    page.context = context

    with patch.object(AuthDetector, "detect", return_value=AuthState.LOGIN_PAGE):
        success = AuthDetector.wait_for_manual_login(
            page=page,
            timeout_seconds=0.05,
            poll_interval=0.01,
        )
        assert success is False


def test_wait_for_manual_login_browser_closure():
    """Verify wait_for_manual_login exits promptly when user closes browser/tabs."""
    page = MagicMock()
    page.url = "https://www.codechef.com/login"
    page.is_closed.return_value = False
    context = MagicMock()
    # User closes all tabs
    context.pages = []
    page.context = context

    success = AuthDetector.wait_for_manual_login(
        page=page,
        timeout_seconds=300,
        poll_interval=0.01,
    )
    assert success is False
