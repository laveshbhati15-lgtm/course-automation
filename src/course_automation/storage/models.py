"""Data models for courses, modules, activities, and submissions."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    CODING = "CODING"
    THEORY = "THEORY"
    QUIZ = "QUIZ"
    UNKNOWN = "UNKNOWN"


class ActivityStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    LOCKED = "LOCKED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ActivitySummary(BaseModel):
    id: str
    title: str
    slug: str
    type: ActivityType = ActivityType.UNKNOWN
    status: ActivityStatus = ActivityStatus.NOT_STARTED
    url: str = ""
    module_id: str = ""
    language: Optional[str] = None
    score: Optional[float] = None


class ModuleSummary(BaseModel):
    id: str
    title: str
    slug: str
    activities: List[ActivitySummary] = Field(default_factory=list)
    completion_pct: float = 0.0


class CourseSummary(BaseModel):
    id: str
    title: str
    slug: str
    url: str
    modules: List[ModuleSummary] = Field(default_factory=list)
    total_activities: int = 0
    completed_activities: int = 0

    @property
    def progress_percentage(self) -> float:
        if self.total_activities == 0:
            return 0.0
        return round((self.completed_activities / self.total_activities) * 100, 1)


class SubmissionRecord(BaseModel):
    activity_id: str
    verdict: str
    language: str = ""
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    code_preview: Optional[str] = None
    details: Optional[str] = None
