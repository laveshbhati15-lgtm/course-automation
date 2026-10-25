"""Tests for CLI entry points and offline command execution."""

from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from course_automation.cli import app
from course_automation.storage.db import DatabaseManager
from course_automation.storage.models import CourseSummary, ModuleSummary, ActivitySummary, ActivityType, ActivityStatus

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Course Automation version" in result.stdout


def test_cli_config():
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "Course Automation Configuration" in result.stdout
    assert "AI Provider" in result.stdout


def test_cli_general_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage: course-automation" in result.stdout
    assert "inspect" in result.stdout
    assert "solve" in result.stdout
    assert "status" in result.stdout


def test_cli_inspect_help():
    result = runner.invoke(app, ["inspect", "--help"])
    assert result.exit_code == 0
    assert "--incomplete-only" in result.stdout
    assert "--select-module" in result.stdout


def test_cli_solve_help():
    result = runner.invoke(app, ["solve", "--help"])
    assert result.exit_code == 0
    assert "--theory-only" in result.stdout
    assert "--coding-only" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--max-activities" in result.stdout


def test_cli_status_empty_db(tmp_path):
    db_path = tmp_path / "empty.db"
    with patch("course_automation.cli.DatabaseManager") as mock_db_cls:
        mock_db = DatabaseManager(db_path=db_path)
        mock_db_cls.return_value = mock_db
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "No courses currently recorded" in result.stdout


def test_cli_status_with_synthetic_course(tmp_path):
    db_path = tmp_path / "test.db"
    db = DatabaseManager(db_path=db_path)

    act1 = ActivitySummary(
        id="ACT1",
        title="Intro Lesson",
        slug="act-1",
        type=ActivityType.THEORY,
        status=ActivityStatus.COMPLETED,
    )
    act2 = ActivitySummary(
        id="ACT2",
        title="Quiz 1",
        slug="act-2",
        type=ActivityType.QUIZ,
        status=ActivityStatus.NOT_STARTED,
    )

    summary = CourseSummary(
        id="synthetic-course",
        slug="synthetic-course",
        title="Synthetic Open Source Course",
        url="https://codechef.com/learn/course/synthetic-course",
        modules=[
            ModuleSummary(
                id="mod_1",
                slug="mod-1",
                title="Unit 1: Fundamentals",
                activities=[act1, act2],
                completion_pct=50.0,
            )
        ],
        total_activities=2,
        completed_activities=1,
    )
    db.save_course_summary(summary)

    with patch("course_automation.cli.DatabaseManager", return_value=db):
        # 1. Query all courses
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "synthetic-course" in result.stdout

        # 2. Query specific course details
        result_course = runner.invoke(app, ["status", "synthetic-course"])
        assert result_course.exit_code == 0
        assert "Synthetic Open Source Course" in result_course.stdout
        assert "Unit 1: Fundamentals" in result_course.stdout
