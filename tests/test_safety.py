"""Tests for SafetyGate interactive and dry-run policies."""

from unittest.mock import patch
from course_automation.safety import SafetyGate


def test_safety_gate_dry_run():
    gate = SafetyGate(dry_run=True)
    assert gate.confirm_action("Submit code") is False


def test_safety_gate_auto_approve():
    gate = SafetyGate(auto_approve=True)
    assert gate.confirm_action("Submit code") is True


def test_safety_gate_interactive_approved():
    gate = SafetyGate(dry_run=False, auto_approve=False)
    with patch("sys.stdin.readline", return_value="y\n"):
        assert gate.confirm_action("Submit code") is True


def test_safety_gate_interactive_declined():
    gate = SafetyGate(dry_run=False, auto_approve=False)
    with patch("sys.stdin.readline", return_value="n\n"):
        assert gate.confirm_action("Submit code") is False
