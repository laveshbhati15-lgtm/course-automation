"""Browser session manager using standard Playwright with persistent context or CDP."""

from pathlib import Path
from typing import Optional
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
from course_automation.config import settings
from course_automation.logger import logger


class BrowserSession:
    """Manages an isolated Playwright browser session."""

    def __init__(
        self,
        user_data_dir: Optional[Path] = None,
        headless: Optional[bool] = None,
        cdp_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
    ):
        self.user_data_dir = (user_data_dir or settings.browser_user_data_dir).expanduser().resolve()
        self.headless = headless if headless is not None else settings.browser_headless
        self.cdp_url = cdp_url or settings.browser_cdp_url
        self.timeout_ms = timeout_ms or settings.browser_timeout_ms

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    def __enter__(self) -> "BrowserSession":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self) -> None:
        """Initialize playwright and launch browser or connect over CDP."""
        logger.info("Initializing Playwright browser session...")
        self._playwright = sync_playwright().start()

        if self.cdp_url:
            logger.info(f"Connecting to remote browser over CDP at {self.cdp_url}...")
            self._browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
            if self._browser.contexts:
                self._context = self._browser.contexts[0]
            else:
                self._context = self._browser.new_context()
        else:
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

        self._context.set_default_timeout(self.timeout_ms)

    def close(self) -> None:
        """Safely close context, browser, and playwright instance."""
        try:
            if self._context:
                self._context.close()
        except Exception as e:
            logger.debug(f"Context close error: {e}")
        finally:
            self._context = None

        try:
            if self._browser:
                self._browser.close()
        except Exception as e:
            logger.debug(f"Browser close error: {e}")
        finally:
            self._browser = None

        try:
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            logger.debug(f"Playwright stop error: {e}")
        finally:
            self._playwright = None

        logger.info("Browser session closed cleanly.")

    @property
    def context(self) -> BrowserContext:
        """Return the active browser context."""
        if not self._context:
            raise RuntimeError("BrowserSession has not been started. Use 'with BrowserSession():'")
        return self._context

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
