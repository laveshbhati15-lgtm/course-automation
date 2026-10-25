"""Active browser tab inspection and automatic course detection."""

import re
from dataclasses import dataclass
from typing import List, Optional
from playwright.sync_api import BrowserContext, Page
from course_automation.logger import logger


@dataclass
class ActiveSessionInfo:
    """Information discovered from an active browser tab."""
    url: str
    title: str
    course_slug: Optional[str] = None
    module_slug: Optional[str] = None
    activity_slug: Optional[str] = None
    is_problem_page: bool = False
    is_syllabus_page: bool = False
    page: Optional[Page] = None


class ActiveSessionDetector:
    """Discovers active course and lesson tabs across a browser session."""

    # Matches /learn/course/<course_slug> optionally followed by /<module>/problems/<problem> or /lesson/<lesson>
    CODECHEF_COURSE_REGEX = re.compile(
        r"https?://(?:www\.)?codechef\.com/learn/course/([a-zA-Z0-9_\-]+)(?:/([a-zA-Z0-9_\-]+))?(?:/(?:problems|lesson)/([a-zA-Z0-9_\-]+))?",
        re.IGNORECASE
    )

    @classmethod
    def parse_codechef_url(cls, url: str) -> Optional[ActiveSessionInfo]:
        """Parse CodeChef URL into structured session details."""
        match = cls.CODECHEF_COURSE_REGEX.search(url)
        if not match:
            return None

        course_slug = match.group(1)
        module_slug = match.group(2)
        activity_slug = match.group(3)

        is_problem = "/problems/" in url
        is_syllabus = not module_slug and not activity_slug

        return ActiveSessionInfo(
            url=url,
            title="",
            course_slug=course_slug,
            module_slug=module_slug,
            activity_slug=activity_slug,
            is_problem_page=is_problem,
            is_syllabus_page=is_syllabus,
        )

    @classmethod
    def detect_active_course(cls, context: BrowserContext) -> Optional[ActiveSessionInfo]:
        """Scan all open tabs in context to locate an active CodeChef course."""
        pages = context.pages
        logger.info(f"Scanning {len(pages)} open browser tab(s) for active CodeChef courses...")

        # 1. Check pages in reverse order (most recently opened or active first)
        for page in reversed(pages):
            try:
                url = page.url
                info = cls.parse_codechef_url(url)
                if info:
                    info.title = page.title()
                    info.page = page
                    logger.info(f"Found active CodeChef course: {info.course_slug} on tab: '{info.title}' ({url})")
                    return info
            except Exception as e:
                logger.debug(f"Error inspecting tab: {e}")

        logger.warning("No active CodeChef course tab was found in the browser session.")
        return None
