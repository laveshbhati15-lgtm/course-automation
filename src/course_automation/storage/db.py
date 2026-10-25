"""SQLite persistence manager for course progress and checkpoints."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from course_automation.config import settings
from course_automation.logger import logger
from course_automation.storage.models import (
    ActivityStatus,
    ActivitySummary,
    ActivityType,
    CourseSummary,
    ModuleSummary,
    SubmissionRecord,
)


class DatabaseManager:
    """Manages SQLite storage for course inspection and progress tracking."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = (db_path or settings.database_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create tables if they do not exist."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS courses (
                    slug TEXT PRIMARY KEY,
                    id TEXT,
                    title TEXT,
                    url TEXT,
                    total_activities INTEGER,
                    completed_activities INTEGER,
                    last_inspected_at TEXT
                );

                CREATE TABLE IF NOT EXISTS modules (
                    id TEXT PRIMARY KEY,
                    course_slug TEXT,
                    title TEXT,
                    slug TEXT,
                    completion_pct REAL,
                    FOREIGN KEY(course_slug) REFERENCES courses(slug) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS activities (
                    id TEXT PRIMARY KEY,
                    module_id TEXT,
                    course_slug TEXT,
                    title TEXT,
                    slug TEXT,
                    type TEXT,
                    status TEXT,
                    url TEXT,
                    language TEXT,
                    last_updated_at TEXT,
                    FOREIGN KEY(course_slug) REFERENCES courses(slug) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_id TEXT,
                    course_slug TEXT,
                    verdict TEXT,
                    language TEXT,
                    submitted_at TEXT,
                    details TEXT
                );

                CREATE TABLE IF NOT EXISTS checkpoints (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                );
            """)

    def save_course_summary(self, summary: CourseSummary) -> None:
        """Persist or update full course summary."""
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO courses (slug, id, title, url, total_activities, completed_activities, last_inspected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    title=excluded.title,
                    url=excluded.url,
                    total_activities=excluded.total_activities,
                    completed_activities=excluded.completed_activities,
                    last_inspected_at=excluded.last_inspected_at
                """,
                (
                    summary.slug,
                    summary.id,
                    summary.title,
                    summary.url,
                    summary.total_activities,
                    summary.completed_activities,
                    now,
                ),
            )

            for mod in summary.modules:
                conn.execute(
                    """
                    INSERT INTO modules (id, course_slug, title, slug, completion_pct)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title=excluded.title,
                        slug=excluded.slug,
                        completion_pct=excluded.completion_pct
                    """,
                    (mod.id, summary.slug, mod.title, mod.slug, mod.completion_pct),
                )

                for act in mod.activities:
                    conn.execute(
                        """
                        INSERT INTO activities (id, module_id, course_slug, title, slug, type, status, url, language, last_updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            title=excluded.title,
                            slug=excluded.slug,
                            type=excluded.type,
                            status=excluded.status,
                            url=excluded.url,
                            language=excluded.language,
                            last_updated_at=excluded.last_updated_at
                        """,
                        (
                            act.id,
                            mod.id,
                            summary.slug,
                            act.title,
                            act.slug,
                            act.type.value,
                            act.status.value,
                            act.url,
                            act.language,
                            now,
                        ),
                    )

    def get_course_summary(self, course_slug: str) -> Optional[CourseSummary]:
        """Load course summary and hierarchy from local database."""
        with self._get_connection() as conn:
            c_row = conn.execute("SELECT * FROM courses WHERE slug = ?", (course_slug,)).fetchone()
            if not c_row:
                return None

            modules: List[ModuleSummary] = []
            m_rows = conn.execute("SELECT * FROM modules WHERE course_slug = ?", (course_slug,)).fetchall()
            for m in m_rows:
                a_rows = conn.execute("SELECT * FROM activities WHERE module_id = ?", (m["id"],)).fetchall()
                activities = [
                    ActivitySummary(
                        id=a["id"],
                        title=a["title"],
                        slug=a["slug"],
                        type=ActivityType(a["type"]),
                        status=ActivityStatus(a["status"]),
                        url=a["url"],
                        module_id=a["module_id"],
                        language=a["language"],
                    )
                    for a in a_rows
                ]
                modules.append(
                    ModuleSummary(
                        id=m["id"],
                        title=m["title"],
                        slug=m["slug"],
                        activities=activities,
                        completion_pct=m["completion_pct"],
                    )
                )

            return CourseSummary(
                id=c_row["id"],
                title=c_row["title"],
                slug=c_row["slug"],
                url=c_row["url"],
                modules=modules,
                total_activities=c_row["total_activities"],
                completed_activities=c_row["completed_activities"],
            )

    def record_submission(self, record: SubmissionRecord, course_slug: str) -> None:
        """Store record of a submission."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO submissions (activity_id, course_slug, verdict, language, submitted_at, details)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.activity_id,
                    course_slug,
                    record.verdict,
                    record.language,
                    record.submitted_at.isoformat(),
                    record.details,
                ),
            )

    def get_incomplete_activities(self, course_slug: str) -> List[ActivitySummary]:
        """Fetch all activities that are not yet COMPLETED."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM activities
                WHERE course_slug = ? AND status != 'COMPLETED'
                ORDER BY id ASC
                """,
                (course_slug,),
            ).fetchall()

            return [
                ActivitySummary(
                    id=r["id"],
                    title=r["title"],
                    slug=r["slug"],
                    type=ActivityType(r["type"]),
                    status=ActivityStatus(r["status"]),
                    url=r["url"],
                    module_id=r["module_id"],
                    language=r["language"],
                )
                for r in rows
            ]

    def set_checkpoint(self, key: str, value: str) -> None:
        """Save a key-value checkpoint."""
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO checkpoints (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value, now),
            )

    def get_checkpoint(self, key: str) -> Optional[str]:
        """Retrieve checkpoint value."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT value FROM checkpoints WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None
