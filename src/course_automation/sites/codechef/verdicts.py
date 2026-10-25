"""Submission polling and verdict evaluation for CodeChef."""

import time
from enum import Enum
from typing import Tuple
from playwright.sync_api import Page
from course_automation.logger import logger


class VerdictState(str, Enum):
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    SERVER_UNAVAILABLE = "SERVER_UNAVAILABLE"
    RUNNING = "RUNNING"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


def poll_verdict(page: Page, timeout_seconds: int = 35) -> Tuple[VerdictState, str]:
    """Poll the page for a submission verdict and execution output."""
    logger.info(f"Polling for submission verdict (up to {timeout_seconds}s)...")
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        try:
            # Check for server error modal
            server_err = page.locator("text='Unable to connect to the CodeChef servers'").first
            if server_err.is_visible():
                return VerdictState.SERVER_UNAVAILABLE, "CodeChef server connection failed."

            # Check Accepted
            accepted_markers = [
                "text='Accepted'",
                "text='Correct Answer'",
                "[data-testid='verdict-accepted']",
                ".status-accepted",
            ]
            for m in accepted_markers:
                if page.locator(m).first.is_visible():
                    return VerdictState.ACCEPTED, "Solution successfully accepted by judge."

            # Check Compilation Error
            ce_markers = [
                "text='Compilation Error'",
                "text='Compile Error'",
                ".status-ce",
            ]
            for m in ce_markers:
                if page.locator(m).first.is_visible():
                    details = ""
                    out_el = page.locator(".error-output, .terminal-output, pre").first
                    if out_el.is_visible():
                        details = out_el.inner_text()
                    return VerdictState.COMPILATION_ERROR, details or "Compilation failed."

            # Check Wrong Answer
            wa_markers = [
                "text='Wrong Answer'",
                ".status-wa",
            ]
            for m in wa_markers:
                if page.locator(m).first.is_visible():
                    return VerdictState.WRONG_ANSWER, "Test case failed."

            # Check Time Limit Exceeded
            tle_markers = [
                "text='Time Limit Exceeded'",
                ".status-tle",
            ]
            for m in tle_markers:
                if page.locator(m).first.is_visible():
                    return VerdictState.TIME_LIMIT_EXCEEDED, "Time limit exceeded."

            # Check Runtime Error
            re_markers = [
                "text='Runtime Error'",
                ".status-re",
            ]
            for m in re_markers:
                if page.locator(m).first.is_visible():
                    return VerdictState.RUNTIME_ERROR, "Runtime exception raised."

        except Exception as e:
            logger.debug(f"Verdict polling error: {e}")

        time.sleep(1.5)

    return VerdictState.TIMEOUT, "Verdict polling timed out."
