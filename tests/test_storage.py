"""Tests for SQLite database persistence."""

from course_automation.storage.db import DatabaseManager
from course_automation.storage.models import (
    ActivityStatus,
    ActivitySummary,
    ActivityType,
    CourseSummary,
    ModuleSummary,
    SubmissionRecord,
)


def test_db_persistence(tmp_db_path):
    db = DatabaseManager(db_path=tmp_db_path)

    summary = CourseSummary(
        id="c1",
        title="Test Course",
        slug="test-slug",
        url="https://example.com/course",
        modules=[
            ModuleSummary(
                id="m1",
                title="Module 1",
                slug="m1-slug",
                activities=[
                    ActivitySummary(
                        id="a1",
                        title="Problem 1",
                        slug="p1",
                        type=ActivityType.CODING,
                        status=ActivityStatus.NOT_STARTED,
                        url="https://example.com/p1",
                        module_id="m1",
                    ),
                    ActivitySummary(
                        id="a2",
                        title="Theory 1",
                        slug="t1",
                        type=ActivityType.THEORY,
                        status=ActivityStatus.COMPLETED,
                        url="https://example.com/t1",
                        module_id="m1",
                    ),
                ],
                completion_pct=50.0,
            )
        ],
        total_activities=2,
        completed_activities=1,
    )

    db.save_course_summary(summary)
    loaded = db.get_course_summary("test-slug")

    assert loaded is not None
    assert loaded.title == "Test Course"
    assert loaded.total_activities == 2
    assert loaded.completed_activities == 1
    assert len(loaded.modules) == 1
    assert len(loaded.modules[0].activities) == 2

    # Check incomplete activities query
    incomplete = db.get_incomplete_activities("test-slug")
    assert len(incomplete) == 1
    assert incomplete[0].id == "a1"

    # Test submission recording
    record = SubmissionRecord(
        activity_id="a1",
        verdict="ACCEPTED",
        language="cpp",
        details="Passed all tests",
    )
    db.record_submission(record, "test-slug")

    # Test checkpoints
    db.set_checkpoint("last_activity", "a1")
    assert db.get_checkpoint("last_activity") == "a1"
