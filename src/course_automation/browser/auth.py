"""Authentication detection and manual login assistance."""

import time
import urllib.parse
from enum import Enum
from typing import Optional
from playwright.sync_api import Page
from course_automation.logger import logger


class AuthState(str, Enum):
    AUTHENTICATED = "AUTHENTICATED"
    LOGGED_OUT = "LOGGED_OUT"
    LOGIN_PAGE = "LOGIN_PAGE"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    UNKNOWN = "UNKNOWN"


def _safe_count(loc) -> int:
    """Safely obtain locator element count without throwing on mocks."""
    try:
        c = loc.count()
        return int(c) if isinstance(c, (int, float)) else 0
    except Exception:
        return 0


class AuthDetector:
    """Non-intrusive DOM and session-based detector for authentication state."""

    @staticmethod
    def has_codechef_auth_cookies(page: Page) -> bool:
        """Check if browser context has active CodeChef authentication cookies."""
        try:
            context = getattr(page, "context", None)
            if not context or not hasattr(context, "cookies"):
                return False

            try:
                cookies = context.cookies(["https://www.codechef.com", "https://codechef.com"])
            except TypeError:
                cookies = context.cookies()

            if not isinstance(cookies, list):
                return False

            auth_cookie_names = {
                "remember_me",
                "codechef_session",
                "auth_token",
                "token",
                "user_id",
                "session_id",
                "session",
            }
            for cookie in cookies:
                if not isinstance(cookie, dict):
                    continue
                name = str(cookie.get("name", ""))
                value = str(cookie.get("value", ""))
                # Drupal session cookie starts with SESS or known auth cookie names
                if (name.startswith("SESS") or name.lower() in auth_cookie_names) and bool(value.strip()):
                    return True
        except Exception as e:
            logger.debug(f"Cookie detection error: {e}")
        return False

    @classmethod
    def detect_codechef(cls, page: Page) -> AuthState:
        """Determine authentication status on CodeChef without altering page state."""
        try:
            if hasattr(page, "is_closed") and page.is_closed() is True:
                return AuthState.UNKNOWN
        except Exception:
            return AuthState.UNKNOWN

        try:
            raw_url = page.url if isinstance(getattr(page, "url", None), str) else ""
        except Exception:
            raw_url = ""

        parsed = urllib.parse.urlparse(raw_url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        url_lower = raw_url.lower()

        # Check for OAuth / Third-party authentication flow
        oauth_domains = ["accounts.google.com", "github.com", "facebook.com"]
        if any(d in domain for d in oauth_domains):
            return AuthState.LOGIN_PAGE

        # Check for direct login, registration, or SSO endpoints
        auth_paths = ["/login", "/register", "/signup", "/password/reset", "/oauth"]
        if any(p in path for p in auth_paths) or "/login" in url_lower:
            return AuthState.LOGIN_PAGE

        try:
            # 1. Primary legacy and visible user profile selectors
            primary_user_selectors = [
                "#user-details-menu",
                "[data-testid='user-profile-menu']",
                ".user-name",
                ".notification-icon",
                "button[aria-label*='user' i]",
                "a[href*='/users/']",
                "button:has-text('Logout')",
            ]
            for sel in primary_user_selectors:
                try:
                    if page.locator(sel).first.is_visible() is True:
                        logger.debug(f"Auth detector matched primary user element: {sel}")
                        return AuthState.AUTHENTICATED
                except Exception:
                    pass

            # 2. Check for login buttons or guest markers
            guest_selectors = [
                "a[href*='/login']",
                "button:has-text('Log In')",
                "button:has-text('Login')",
                ".login-btn",
                "input[name='email']",
                "input[name='password']",
                "input[type='password']",
                "button:has-text('Sign In')",
            ]
            for sel in guest_selectors:
                try:
                    if page.locator(sel).first.is_visible() is True:
                        return AuthState.LOGGED_OUT
                except Exception:
                    pass

            # 3. Modern CodeChef Learn user indicators (avatars, modern menus, profile buttons)
            modern_user_selectors = [
                "[data-testid*='avatar']",
                "[data-testid*='profile']",
                "[class*='avatar']",
                "[class*='user-avatar']",
                "img[src*='avatar']",
                "img[alt*='avatar' i]",
                "img[alt*='profile' i]",
                "button[aria-label*='profile' i]",
                "button[aria-label*='account' i]",
                "button[id*='user']",
                "a[href*='/logout']",
                "button:has-text('Log out')",
                "button:has-text('Sign out')",
                "a[href*='/ratings/']",
            ]
            for sel in modern_user_selectors:
                try:
                    loc = page.locator(sel)
                    if loc.first.is_visible() is True or _safe_count(loc) > 0:
                        logger.debug(f"Auth detector matched modern user element: {sel}")
                        return AuthState.AUTHENTICATED
                except Exception:
                    pass

            # 4. Check for attached dropdown logout options in DOM even if menu unexpanded
            try:
                logout_loc = page.locator("a[href*='/logout'], button:has-text('Logout'), button:has-text('Log out')")
                if _safe_count(logout_loc) > 0:
                    logger.debug("Auth detector matched attached logout element in DOM.")
                    return AuthState.AUTHENTICATED
            except Exception:
                pass

            # 5. Authenticated course page indicators on CodeChef Learn
            is_learn_page = ("/learn" in path or "/dashboard" in path) and ("codechef.com" in domain or not domain)
            if is_learn_page:
                course_selectors = [
                    ".course-item",
                    "[data-testid*='course-item']",
                    ".lesson-card",
                    ".activity-card",
                    "[class*='syllabus']",
                    "[class*='curriculum']",
                    "[class*='module']",
                    ".monaco-editor",
                    "[data-testid='editor']",
                    "button:has-text('Continue Learning')",
                    "button:has-text('Resume')",
                    "text='Course Outline'",
                    "text='Continue Learning'",
                ]
                for sel in course_selectors:
                    try:
                        loc = page.locator(sel)
                        if loc.first.is_visible() is True or _safe_count(loc) > 0:
                            logger.debug(f"Auth detector matched course element: {sel}")
                            return AuthState.AUTHENTICATED
                    except Exception:
                        pass

            # 6. Active CodeChef session cookies in browser context
            if cls.has_codechef_auth_cookies(page):
                if is_learn_page or "codechef.com" in domain or not domain:
                    logger.debug("Auth detector matched valid CodeChef session cookies in context.")
                    return AuthState.AUTHENTICATED

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
        poll_interval: float = 2.0,
    ) -> bool:
        """Guide user through manual login in the browser and wait for completion."""
        print("\n" + "=" * 60)
        print("MANUAL AUTHENTICATION REQUIRED")
        print("=" * 60)
        print(f"Opening login page: {login_url}")
        print("Please log in using your credentials in the opened browser window.")
        print(f"Waiting up to {timeout_seconds} seconds for successful login...")
        print("=" * 60 + "\n")

        context = getattr(page, "context", None)

        try:
            if hasattr(page, "is_closed") and not page.is_closed():
                page.goto(login_url, wait_until="domcontentloaded")
        except Exception as e:
            logger.debug(f"Initial navigation notice: {e}")

        start_time = time.time()
        last_logged_state: Optional[AuthState] = None
        last_logged_url: str = ""

        while time.time() - start_time < timeout_seconds:
            # Check for browser or tab closure
            try:
                pages = context.pages if context and hasattr(context, "pages") else ([page] if hasattr(page, "is_closed") and not page.is_closed() else [])
            except Exception:
                pages = []

            active_pages = []
            for p in pages:
                try:
                    if hasattr(p, "is_closed") and not p.is_closed():
                        active_pages.append(p)
                except Exception:
                    pass

            if not active_pages:
                logger.info("All browser tabs closed by user before authentication completed.")
                print("\n[INFO] Browser was closed before authentication completed.")
                return False

            # Scan open tabs in reverse order (active/most recently opened first)
            authenticated_page: Optional[Page] = None
            current_state = AuthState.UNKNOWN
            current_page = active_pages[0]

            for p in reversed(active_pages):
                try:
                    st = cls.detect(p, site)
                    if st == AuthState.AUTHENTICATED:
                        authenticated_page = p
                        current_state = AuthState.AUTHENTICATED
                        break
                    elif st in (AuthState.LOGIN_PAGE, AuthState.LOGGED_OUT):
                        current_state = st
                        current_page = p
                except Exception as e:
                    logger.debug(f"Error inspecting tab during auth wait: {e}")

            # Safe diagnostic logging (URL without query parameters or tokens)
            try:
                target_p = authenticated_page or current_page
                raw_url = target_p.url if isinstance(getattr(target_p, "url", None), str) else ""
                safe_url = raw_url.split("?")[0].split("#")[0] or "about:blank"
            except Exception:
                safe_url = "unknown"

            if current_state != last_logged_state or safe_url != last_logged_url:
                logger.info(f"Auth detector state: {current_state.value} (url: {safe_url})")
                last_logged_state = current_state
                last_logged_url = safe_url

            if authenticated_page:
                # Validate session stability to handle in-flight redirects
                logger.info("Authentication detected. Validating session stability...")
                try:
                    if hasattr(authenticated_page, "wait_for_load_state"):
                        authenticated_page.wait_for_load_state("domcontentloaded", timeout=3000)
                except Exception:
                    pass

                confirmed_state = cls.detect(authenticated_page, site)
                if confirmed_state == AuthState.AUTHENTICATED:
                    print("\n[SUCCESS] Authentication detected! Session saved to profile.")
                    logger.info("Authentication confirmed and verified successfully.")
                    return True

            time.sleep(poll_interval)

        print("\n[TIMEOUT] Authentication was not completed within the time limit.")
        logger.warning(f"Authentication timed out after {timeout_seconds} seconds.")
        return False
