"""Browser automation session, authentication, and active tab inspection."""

from course_automation.browser.auth import AuthDetector, AuthState
from course_automation.browser.session import BrowserSession
from course_automation.browser.active_session import ActiveSessionDetector, ActiveSessionInfo
from course_automation.browser.browser_use_bridge import BrowserUseBridge

__all__ = [
    "AuthDetector",
    "AuthState",
    "BrowserSession",
    "ActiveSessionDetector",
    "ActiveSessionInfo",
    "BrowserUseBridge",
]
