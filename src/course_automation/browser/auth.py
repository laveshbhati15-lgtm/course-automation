"""Authentication detection and manual login assistance."""

import time
from enum import Enum
from playwright.sync_api import Page
from course_automation.logger import logger


class AuthState(str, Enum):
    AUTHENTICATED = "AUTHENTICATED"
    LOGGED_OUT = "LOGGED_OUT"
    LOGIN_PAGE = "LOGIN_PAGE"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    UNKNOWN = "UNKNOWN"


class AuthDetector:
    """Non-intrusive DOM-based detector for authentication state."""

    @staticmethod
    def detect_codechef(page: Page) -> AuthState:
        """Determine authentication status on CodeChef without changing page state."""
        url = page.url.lower()

        if "/login" in url:
            return AuthState.LOGIN_PAGE

        # Check for presence of logged-in indicators
        try:
            # Check user details or profile badge
            user_selectors = [
                "#user-details-menu",
                "[data-testid='user-profile-menu']",
                ".user-name",
                ".notification-icon",
                "button[aria-label*='user' i]",
                "a[href*='/users/']",
                "button:has-text('Logout')",
            ]
            for sel in user_selectors:
                if page.locator(sel).first.is_visible():
                    return AuthState.AUTHENTICATED

            # Check for login buttons or guest markers
            guest_selectors = [
                "a[href*='/login']",
                "button:has-text('Log In')",
                "button:has-text('Login')",
                ".login-btn",
                "input[name='email']",
                "input[name='password']",
            ]
            for sel in guest_selectors:
                if page.locator(sel).first.is_visible():
                    return AuthState.LOGGED_OUT

        except Exception as e:
            logger.debug(f"Auth detection error: {e}")

        return AuthState.UNKNOWN

    @classmethod
    def detect(cls, page: Page, site: str = "codechef") -> AuthState:
        """Detect auth state for specified site."""
        if site.lower() == "codechef":
            return cls.detect_codechef(page)
        return AuthState.UNKNOWN

    @classmethod
    def wait_for_manual_login(
        cls,
        page: Page,
        site: str = "codechef",
        login_url: str = "https://www.codechef.com/login",
        timeout_seconds: int = 300,
    ) -> bool:
        """Guide user through manual login in the browser and wait for completion."""
        print("\n" + "=" * 60)
        print("MANUAL AUTHENTICATION REQUIRED")
        print("=" * 60)
        print(f"Opening login page: {login_url}")
        print("Please log in using your credentials in the opened browser window.")
        print(f"Waiting up to {timeout_seconds} seconds for successful login...")
        print("=" * 60 + "\n")

        page.goto(login_url, wait_until="domcontentloaded")

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            state = cls.detect(page, site)
            if state == AuthState.AUTHENTICATED:
                print("\n[SUCCESS] Authentication detected! Session saved to profile.")
                return True
            time.sleep(2)

        print("\n[TIMEOUT] Authentication was not completed within the time limit.")
        return False
