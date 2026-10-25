"""Dynamic syllabus discovery and parsing for any CodeChef course."""

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
    """Discovers and parses CodeChef course structures across any subject or language."""

    SLUG_PATTERN = re.compile(r"/learn/course/([a-zA-Z0-9_\-]+)", re.IGNORECASE)

    @classmethod
    def extract_slug(cls, url_or_slug: str) -> str:
        """Extract course slug dynamically from any URL or raw slug string."""
        if not url_or_slug:
            return ""
        match = cls.SLUG_PATTERN.search(url_or_slug)
        if match:
            return match.group(1)
        cleaned = url_or_slug.strip().strip("/")
        parts = cleaned.split("/")
        res = parts[-1] if parts else ""
        return "" if res in ("course", "learn") else res

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
    def infer_course_language(cls, course_slug: str, course_name: str) -> str:
        """Heuristically infer default language from course title or slug."""
        text = f"{course_slug} {course_name}".lower()
        if "java" in text or "oops" in text:
            return "java"
        elif "python" in text or "pyth" in text:
            return "python3"
        elif "adsa" in text or "cpp" in text or "c++" in text:
            return "cpp"
        elif " b1" in text or "-b1" in text:
            return "c"
        return "cpp"

    @classmethod
    def parse_api_data(cls, data: Dict[str, Any], course_url: str, course_slug: str) -> CourseSummary:
        """Parse raw syllabus JSON data into standard CourseSummary hierarchy.
        
        Handles both the live CodeChef structure (modules -> submodules -> problems_with_status)
        and flat structure (modules -> activities/items).
        """
        course_title = data.get("course_name") or data.get("name") or data.get("title") or course_slug.replace("-", " ").title()
        course_id = str(data.get("slug") or data.get("course_id") or course_slug)
        raw_modules = (
            data.get("modules")
            or data.get("units")
            or data.get("chapters")
            or data.get("curriculum")
            or []
        )

        default_lang = cls.infer_course_language(course_slug, course_title)

        modules: List[ModuleSummary] = []
        total_activities = 0
        completed_activities = 0

        for mod_idx, mod in enumerate(raw_modules, 1):
            mod_title = mod.get("name") or mod.get("title") or f"Unit {mod_idx}"
            mod_id = str(mod.get("id") or f"mod_{mod_idx}")
            mod_slug = mod.get("slug") or mod_id

            activities: List[ActivitySummary] = []
            mod_completed = 0

            # 1. Check for live CodeChef submodules structure
            submodules = mod.get("submodules") or []
            if submodules:
                for sub in submodules:
                    contest_code = sub.get("contest_code") or mod_slug
                    prob_list = sub.get("problems_with_status") or sub.get("problems") or []
                    for act_idx, act in enumerate(prob_list, 1):
                        act_code = act.get("code") or act.get("id") or f"act_{act_idx}"
                        act_name = act.get("name") or act_code
                        raw_status = str(act.get("status") or "").lower()

                        is_solved = (raw_status == "solved") or act.get("is_solved") or act.get("completed")
                        is_locked = (raw_status == "locked") or act.get("is_locked")
                        is_in_progress = raw_status in ["attempted", "partially_solved", "in_progress"]

                        if is_solved:
                            act_status = ActivityStatus.COMPLETED
                            mod_completed += 1
                            completed_activities += 1
                        elif is_locked:
                            act_status = ActivityStatus.LOCKED
                        elif is_in_progress:
                            act_status = ActivityStatus.IN_PROGRESS
                        else:
                            act_status = ActivityStatus.NOT_STARTED

                        total_activities += 1

                        # Classify type based on contentType or problem name
                        raw_content_type = str(act.get("contentType") or act.get("type") or "").lower()
                        act_title_lower = act_name.lower()

                        if raw_content_type == "mcq" or "mcq" in act_title_lower or "quiz" in act_title_lower:
                            act_type = ActivityType.QUIZ
                        elif raw_content_type in ["default", "reading", "concept", "theory", "video"] or "what are" in act_title_lower or "introduction" in act_title_lower:
                            act_type = ActivityType.THEORY
                        elif raw_content_type in ["labs", "problem", "coding"]:
                            act_type = ActivityType.CODING
                        else:
                            act_type = ActivityType.CODING if (act.get("difficulty_rating") and act.get("difficulty_rating") != "-1") else ActivityType.THEORY

                        act_url = f"https://www.codechef.com/learn/course/{course_slug}/{contest_code}/problems/{act_code}"
                        activities.append(
                            ActivitySummary(
                                id=act_code,
                                title=act_name,
                                slug=act_code,
                                type=act_type,
                                status=act_status,
                                url=act_url,
                                module_id=mod_id,
                                language=default_lang,
                            )
                        )
            else:
                # 2. Check for flat activities / items / lessons structure
                items = (
                    mod.get("activities")
                    or mod.get("items")
                    or mod.get("lessons")
                    or mod.get("problems")
                    or []
                )
                for act_idx, act in enumerate(items, 1):
                    act_title = act.get("name") or act.get("title") or f"Activity {act_idx}"
                    act_id = str(act.get("id") or act.get("code") or f"act_{act_idx}")
                    act_slug = act.get("slug") or act.get("code") or act_id

                    raw_type = str(act.get("type") or act.get("item_type") or "").upper()
                    if any(k in raw_type for k in ["PROBLEM", "CODE", "LAB", "CODING"]):
                        act_type = ActivityType.CODING
                    elif any(k in raw_type for k in ["QUIZ", "MCQ", "ASSESSMENT"]):
                        act_type = ActivityType.QUIZ
                    elif any(k in raw_type for k in ["THEORY", "READ", "VIDEO", "ARTICLE"]):
                        act_type = ActivityType.THEORY
                    else:
                        act_type = ActivityType.UNKNOWN

                    raw_status = str(act.get("status") or "").lower()
                    is_solved = bool(act.get("is_solved") or act.get("completed") or (raw_status in ["completed", "solved", "submitted"]))
                    is_locked = bool(act.get("is_locked") or (raw_status == "locked"))

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

                    act_url = act.get("url") or ""
                    if not act_url:
                        base_course = f"https://www.codechef.com/learn/course/{course_slug}"
                        if act_type == ActivityType.CODING:
                            act_url = f"{base_course}/{mod_slug}/problems/{act_slug}"
                        else:
                            act_url = f"{base_course}/{mod_slug}/lesson/{act_slug}"

                    activities.append(
                        ActivitySummary(
                            id=act_id,
                            title=act_title,
                            slug=act_slug,
                            type=act_type,
                            status=act_status,
                            url=act_url,
                            module_id=mod_id,
                            language=act.get("language") or default_lang,
                        )
                    )

            comp_pct = round((mod_completed / len(activities)) * 100, 1) if activities else 0.0
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
        logger.info(f"Parsing syllabus for {course_slug} from DOM structure...")
        title = page.title() or course_slug.replace("-", " ").title()

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
                title="Course Overview",
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
