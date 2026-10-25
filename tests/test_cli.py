"""Tests for CLI entry points."""

from typer.testing import CliRunner
from course_automation.cli import app

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
