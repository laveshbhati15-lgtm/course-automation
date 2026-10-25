"""Safety mechanisms and user confirmation gates for consequential actions."""

import sys
from course_automation.logger import logger


class SafetyGate:
    """Gatekeeper for consequential actions like code submission or quiz answers."""

    def __init__(self, dry_run: bool = False, auto_approve: bool = False):
        self.dry_run = dry_run
        self.auto_approve = auto_approve

    def confirm_action(self, action_name: str, details: str = "") -> bool:
        """Prompt the user to approve a consequential action."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Skipped action: {action_name}. Details: {details}")
            return False

        if self.auto_approve:
            logger.info(f"[AUTO-APPROVE] Executing action: {action_name}. Details: {details}")
            return True

        print(f"\n[SAFETY GATE] Action required: {action_name}")
        if details:
            print(f"Details: {details}")
        print("Do you want to proceed? [y/N]: ", end="", flush=True)

        try:
            choice = sys.stdin.readline().strip().lower()
            return choice in ("y", "yes")
        except Exception:
            return False
