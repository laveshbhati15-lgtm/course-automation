"""Browser automation session and authentication utilities."""

from course_automation.browser.session import BrowserSession
from course_automation.browser.auth import AuthDetector, AuthState

__all__ = ["BrowserSession", "AuthDetector", "AuthState"]
