"""Multi-lesson sequential navigator for CodeChef courses (theory, quizzes, and coding)."""

import time
from dataclasses import dataclass, field
from typing import List, Optional
from playwright.sync_api import Page
from course_automation.ai.base import BaseAIProvider
from course_automation.logger import logger
from course_automation.safety import SafetyGate
from course_automation.sites.codechef.adapter import CodeChefAdapter
from course_automation.storage.db import DatabaseManager
from course_automation.storage.models import ActivityStatus, ActivitySummary, ActivityType, SubmissionRecord


@dataclass
class NavigatorStepResult:
    """Detailed result of a single activity navigation step."""
    activity_id: str
    activity_title: str
    activity_type: ActivityType
    url: str
    status_before: ActivityStatus
    verdict: str
    details: str
    is_terminal: bool = False


@dataclass
class NavigatorRunReport:
    """Summary report of a sequential navigation run."""
    course_slug: str
    course_title: str
    total_processed: int = 0
    completed_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    dry_run: bool = False
    steps: List[NavigatorStepResult] = field(default_factory=list)


class TheoryCourseNavigator:
    """Traverses incomplete theory lessons, quizzes, and labs with safety controls."""

    def __init__(
        self,
        adapter: CodeChefAdapter,
        db: DatabaseManager,
        safety_gate: SafetyGate,
        ai_provider: Optional[BaseAIProvider] = None,
        dry_run: bool = False,
        max_activities: int = 10,
        theory_only: bool = False,
        coding_only: bool = False,
    ):
        self.adapter = adapter
        self.db = db
        self.safety = safety_gate
        self.ai_provider = ai_provider
        self.dry_run = dry_run
        self.max_activities = max_activities
        self.theory_only = theory_only
        self.coding_only = coding_only

    def run(
        self,
        page: Page,
        course_url: str,
        module_id: Optional[str] = None,
        start_activity_id: Optional[str] = None,
    ) -> NavigatorRunReport:
        """Execute safe sequential progression through course curriculum."""
        from course_automation.browser.auth import AuthDetector, AuthState
        auth_state = AuthDetector.detect(page, "codechef")
        if auth_state in (AuthState.LOGGED_OUT, AuthState.LOGIN_PAGE):
            logger.warning("CodeChef session appears logged out or expired. Authentication may be required.")

        summary = self.adapter.inspect_course(page, course_url)
        self.db.save_course_summary(summary)

        report = NavigatorRunReport(
            course_slug=summary.slug,
            course_title=summary.title,
            dry_run=self.dry_run,
        )

        # 1. Filter target incomplete activities
        targets: List[ActivitySummary] = []
        for mod in summary.modules:
            if module_id and mod.id != module_id and mod.slug != module_id:
                continue

            for act in mod.activities:
                # Mode filtering
                if self.theory_only and act.type not in (ActivityType.THEORY, ActivityType.QUIZ):
                    continue
                if self.coding_only and act.type != ActivityType.CODING:
                    continue

                # Skip completed activities unless explicitly targeted by start_activity_id
                if not start_activity_id and act.status == ActivityStatus.COMPLETED:
                    continue

                if start_activity_id and act.id != start_activity_id and act.slug != start_activity_id:
                    continue

                targets.append(act)

        logger.info(
            f"Navigator queued {len(targets)} candidate activities "
            f"(max limit: {self.max_activities}, theory_only={self.theory_only}, coding_only={self.coding_only})."
        )

        # 2. Iterate through targets sequentially
        for act in targets:
            if report.total_processed >= self.max_activities:
                logger.info(f"Reached maximum activity limit of {self.max_activities}. Pausing navigation.")
                break

            logger.info(f"\n{'='*60}\n[STEP {report.total_processed + 1}] Processing: {act.title} ({act.id}) [{act.type.value}]\n{'='*60}")

            # Safety confirmation gate for live execution (skip prompt in dry-run mode since handlers are non-mutating)
            if not self.dry_run:
                action_label = f"Process & submit {act.type.value}: '{act.title}'"
                if not self.safety.confirm_action(action_label, f"URL: {act.url}"):
                    logger.info(f"User skipped action for {act.title}.")
                    report.skipped_count += 1
                    report.steps.append(
                        NavigatorStepResult(
                            activity_id=act.id,
                            activity_title=act.title,
                            activity_type=act.type,
                            url=act.url,
                            status_before=act.status,
                            verdict="USER_SKIPPED",
                            details="Action was declined by user.",
                        )
                    )
                    continue

            # Execute activity via adapter
            record: SubmissionRecord = self.adapter.solve_activity(
                page=page,
                activity=act,
                ai_provider=self.ai_provider,
                dry_run=self.dry_run,
            )

            # Record in SQLite database
            self.db.record_submission(record, summary.slug)

            # Classify step result
            report.total_processed += 1
            if record.verdict in ("ACCEPTED", "DRY_RUN_PASSED"):
                report.completed_count += 1
            elif "LOCKED" in record.verdict or "SKIPPED" in record.verdict:
                report.skipped_count += 1
            else:
                report.failed_count += 1

            report.steps.append(
                NavigatorStepResult(
                    activity_id=act.id,
                    activity_title=act.title,
                    activity_type=act.type,
                    url=act.url,
                    status_before=act.status,
                    verdict=record.verdict,
                    details=record.details or "",
                )
            )

            # Check for halting conditions (locked prerequisites or repeated errors)
            if "LOCKED" in record.verdict:
                logger.warning("Encountered locked prerequisite activity. Halting sequential navigation.")
                break

            # Short stabilization delay between activities
            time.sleep(1.0)

        # Save checkpoint of last visited activity
        if report.steps:
            last_act = report.steps[-1].activity_id
            self.db.set_checkpoint(f"{summary.slug}_last_activity", last_act)

        return report
