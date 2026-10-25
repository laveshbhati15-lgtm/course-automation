"""CodeChef site adapter package."""

from course_automation.sites.codechef.adapter import CodeChefAdapter
from course_automation.sites.codechef.editor import MonacoEditorController
from course_automation.sites.codechef.syllabus import CodeChefSyllabusParser
from course_automation.sites.codechef.verdicts import VerdictState, poll_verdict

__all__ = [
    "CodeChefAdapter",
    "CodeChefSyllabusParser",
    "MonacoEditorController",
    "VerdictState",
    "poll_verdict",
]
