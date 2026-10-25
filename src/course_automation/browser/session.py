"""Browser session manager using standard Playwright with persistent context or CDP."""

import urllib.request
from pathlib import Path
from typing import Optional
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
from course_automation.config import settings
from course_automation.logger import logger


def probe_local_cdp(url: str = "http://127.0.0.1:9222") -> bool:
    """Check if a Chrome instance is actively listening on remote debugging port."""
    try:
        req = urllib.request.Request(f"{url.rstrip('/')}/json/version", headers={"User-Agent": "CourseAutomation"})
        with urllib.request.urlopen(req, timeout=1.0) as res:
            return res.status == 200
    except Exception:
        return False


class BrowserSession:
    """Manages Playwright browser connection via CDP or isolated persistent context."""

    def __init__(
        self,
        user_data_dir: Optional[Path] = None,
        headless: Optional[bool] = None,
        cdp_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        auto_probe_cdp: bool = True,
    ):
        self.user_data_dir = (user_data_dir or settings.browser_user_data_dir).expanduser().resolve()
        self.headless = headless if headless is not None else settings.browser_headless
        self.cdp_url = cdp_url or settings.browser_cdp_url
        self.timeout_ms = timeout_ms or settings.browser_timeout_ms
        self.auto_probe_cdp = auto_probe_cdp

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._is_cdp: bool = False

    def __enter__(self) -> "BrowserSession":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self) -> None:
        """Initialize playwright and launch browser or connect over CDP."""
        logger.info("Initializing Playwright browser session...")
        self._playwright = sync_playwright().start()

        # Determine if we should connect over CDP
        target_cdp = self.cdp_url
        if not target_cdp and self.auto_probe_cdp and probe_local_cdp("http://127.0.0.1:9222"):
            target_cdp = "http://127.0.0.1:9222"
            logger.info("Auto-detected active Chrome instance listening on port 9222.")

        if target_cdp:
            logger.info(f"Connecting to browser over CDP at {target_cdp}...")
            try:
                self._browser = self._playwright.chromium.connect_over_cdp(target_cdp)
                self._context = self._browser.contexts[0] if self._browser.contexts else self._browser.new_context()
                self._is_cdp = True
                logger.info(f"Connected over CDP successfully ({len(self._context.pages)} open tab(s)).")
            except Exception as e:
                logger.warning(f"Failed to connect to CDP at {target_cdp}: {e}. Falling back to persistent context.")
                target_cdp = None

        if not target_cdp:
            self.user_data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Launching persistent browser context at {self.user_data_dir} (headless={self.headless})...")
            self._context = self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
                viewport={"width": 1280, "height": 800},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
                timeout=self.timeout_ms,
            )
            self._is_cdp = False

        self._context.set_default_timeout(self.timeout_ms)

    def close(self) -> None:
        """Safely disconnect or close browser session."""
        try:
            if self._context and not self._is_cdp:
                # For standalone persistent context, close it cleanly
                self._context.close()
            # For CDP, we do not close the user's browser or context
        except Exception as e:
            logger.debug(f"Browser cleanup error: {e}")
        finally:
            self._context = None
            self._browser = None

        try:
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            logger.debug(f"Playwright stop error: {e}")
        finally:
            self._playwright = None

        logger.info("Browser session disconnected cleanly.")

    @property
    def context(self) -> BrowserContext:
        """Return the active browser context."""
        if not self._context:
            raise RuntimeError("BrowserSession has not been started. Use 'with BrowserSession():'")
        return self._context

    @property
    def is_cdp(self) -> bool:
        """Return True if session is connected over Chrome DevTools Protocol."""
        return self._is_cdp

    def get_or_create_page(self) -> Page:
        """Retrieve existing open page or create a new one."""
        pages = self.context.pages
        if pages:
            return pages[0]
        return self.context.new_page()

    def navigate_safely(self, page: Page, url: str) -> bool:
        """Navigate to URL with error catching and retry."""
        logger.info(f"Navigating to {url}...")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            return True
        except Exception as e:
            logger.warning(f"Failed to navigate to {url}: {e}. Retrying with commit wait...")
            try:
                page.goto(url, wait_until="commit", timeout=self.timeout_ms)
                return True
            except Exception as e2:
                logger.error(f"Navigation error for {url}: {e2}")
                return False
