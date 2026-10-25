"""Tests for editor automation."""

from unittest.mock import MagicMock
from course_automation.sites.codechef.editor import MonacoEditorController


def test_is_editor_present_true():
    page = MagicMock()
    page.evaluate.return_value = True
    assert MonacoEditorController.is_editor_present(page) is True


def test_get_editor_content():
    page = MagicMock()
    page.evaluate.return_value = "class Solution { }"
    assert MonacoEditorController.get_editor_content(page) == "class Solution { }"


def test_set_editor_content():
    page = MagicMock()
    # evaluate returns True, and subsequent get_editor_content returns matching code
    page.evaluate.return_value = "int main() { return 0; }"
    success = MonacoEditorController.set_editor_content(page, "int main() { return 0; }")
    assert success is True


def test_click_run():
    page = MagicMock()
    btn = MagicMock()
    btn.first.is_visible.return_value = True
    page.locator.return_value = btn

    assert MonacoEditorController.click_run(page) is True
    btn.first.click.assert_called_once()
