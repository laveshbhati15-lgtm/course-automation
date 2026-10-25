"""Syllabus discovery and parsing for CodeChef courses."""

import json
import re
from typing import Any, Dict, List, Optional
from playwright.sync_api import Page
from course_automation.logger import logger
from course_automation.storage.models import (
    ActivityStatus,
    ActivitySummary,
    ActivityType,
    CourseSummary,
    ModuleSummary,
)


class CodeChefSyllabusParser:
    """Discovers and parses CodeChef course structures via internal API and DOM fallback."""

    SLUG_PATTERN = re.compile(r"/learn/course/([a-zA-Z0-9_\-]+)", re.IGNORECASE)

    @classmethod
    def extract_slug(cls, url: str) -> str:
        """Extract course slug from URL."""
        match = cls.SLUG_PATTERN.search(url)
        if match:
            return match.group(1)
        # Fallback if bare slug passed
        parts = url.strip("/").split("/")
        return parts[-1]

    @classmethod
    def fetch_syllabus_api(cls, page: Page, course_slug: str) -> Optional[Dict[str, Any]]:
        """Fetch syllabus JSON payload using authenticated page fetch context."""
        api_url = f"/api/learn/syllabus/{course_slug}"
        logger.info(f"Fetching CodeChef syllabus API: {api_url}...")
        try:
            result = page.evaluate(
                f"""async () => {{
                    try {{
                        const res = await fetch('{api_url}', {{
                            headers: {{ 'Accept': 'application/json' }}
                        }});
                        if (res.ok) {{
                            return await res.json();
                        }}
                    }} catch (e) {{}}
                    return null;
                }}"""
            )
            return result
        except Exception as e:
            logger.warning(f"Failed to fetch syllabus from internal API: {e}")
            return None

    @classmethod
    def parse_api_data(cls, data: Dict[str, Any], course_url: str, course_slug: str) -> CourseSummary:
        """Parse raw syllabus JSON data into standard CourseSummary hierarchy."""
        course_title = data.get("course_name") or data.get("title") or course_slug
        course_id = str(data.get("course_id", course_slug))
        raw_modules = data.get("modules") or data.get("units") or data.get("chapters") or []

        modules: List[ModuleSummary] = []
        total_activities = 0
        completed_activities = 0

        for mod_idx, mod in enumerate(raw_modules, 1):
            mod_title = mod.get("name") or mod.get("title") or f"Module {mod_idx}"
            mod_id = str(mod.get("id") or f"mod_{mod_idx}")
            mod_slug = mod.get("slug") or mod_id

            items = mod.get("activities") or mod.get("items") or mod.get("lessons") or []
            activities: List[ActivitySummary] = []
            mod_completed = 0

            for act_idx, act in enumerate(items, 1):
                act_title = act.get("name") or act.get("title") or f"Activity {act_idx}"
                act_id = str(act.get("id") or act.get("code") or f"act_{act_idx}")
                act_slug = act.get("slug") or act.get("code") or act_id

                # Classify type
                raw_type = (act.get("type") or act.get("item_type") or "").upper()
                if "PROBLEM" in raw_type or "CODE" in raw_type or "LAB" in raw_type:
                    act_type = ActivityType.CODING
                elif "QUIZ" in raw_type or "MCQ" in raw_type:
                    act_type = ActivityType.QUIZ
                elif "THEORY" in raw_type or "READ" in raw_type or "VIDEO" in raw_type:
                    act_type = ActivityType.THEORY
                else:
                    act_type = ActivityType.UNKNOWN

                # Classify status
                raw_status = str(act.get("status") or "").lower()
                is_solved = act.get("is_solved") or act.get("completed") or (raw_status in ["completed", "solved", "submitted"])
                is_locked = act.get("is_locked") or (raw_status == "locked")

                if is_solved:
                    act_status = ActivityStatus.COMPLETED
                    mod_completed += 1
                    completed_activities += 1
                elif is_locked:
                    act_status = ActivityStatus.LOCKED
                elif raw_status in ["attempted", "partially_solved", "in_progress"]:
                    act_status = ActivityStatus.IN_PROGRESS
                else:
                    act_status = ActivityStatus.NOT_STARTED

                total_activities += 1

                # Construct activity URL
                act_url = act.get("url") or ""
                if not act_url:
                    if act_type == ActivityType.CODING:
                        act_url = f"https://www.codechef.com/learn/course/{course_slug}/{mod_slug}/problems/{act_slug}"
                    else:
                        act_url = f"https://www.codechef.com/learn/course/{course_slug}/{mod_slug}/lesson/{act_slug}"

                activities.append(
                    ActivitySummary(
                        id=act_id,
                        title=act_title,
                        slug=act_slug,
                        type=act_type,
                        status=act_status,
                        url=act_url,
                        module_id=mod_id,
                        language=act.get("language"),
                    )
                )

            comp_pct = round((mod_completed / len(items)) * 100, 1) if items else 0.0
            modules.append(
                ModuleSummary(
                    id=mod_id,
                    title=mod_title,
                    slug=mod_slug,
                    activities=activities,
                    completion_pct=comp_pct,
                )
            )

        return CourseSummary(
            id=course_id,
            title=course_title,
            slug=course_slug,
            url=course_url,
            modules=modules,
            total_activities=total_activities,
            completed_activities=completed_activities,
        )

    @classmethod
    def parse_dom_fallback(cls, page: Page, course_url: str, course_slug: str) -> CourseSummary:
        """Inspect visible DOM tree if API is inaccessible."""
        logger.info("Parsing syllabus from DOM structure...")
        title = page.title() or course_slug

        # Look for course item cards or list entries
        items = page.locator(".course-item, [data-testid*='course-item'], .lesson-card, .activity-card").all()
        activities: List[ActivitySummary] = []
        completed = 0

        for idx, item in enumerate(items, 1):
            text = item.inner_text()
            title_line = text.splitlines()[0] if text else f"Lesson {idx}"
            is_completed = "completed" in text.lower() or "solved" in text.lower()
            status = ActivityStatus.COMPLETED if is_completed else ActivityStatus.NOT_STARTED
            if is_completed:
                completed += 1

            activities.append(
                ActivitySummary(
                    id=f"dom_{idx}",
                    title=title_line,
                    slug=f"lesson-{idx}",
                    type=ActivityType.UNKNOWN,
                    status=status,
                    url=course_url,
                    module_id="mod_1",
                )
            )

        modules = [
            ModuleSummary(
                id="mod_1",
                title="Overview Module",
                slug="overview",
                activities=activities,
                completion_pct=round((completed / len(activities)) * 100, 1) if activities else 0.0,
            )
        ]

        return CourseSummary(
            id=course_slug,
            title=title,
            slug=course_slug,
            url=course_url,
            modules=modules,
            total_activities=len(activities),
            completed_activities=completed,
        )
