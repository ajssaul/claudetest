from pydantic import BaseModel
from typing import Optional
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NEEDS_REVISION = "needs_revision"
    FAILED = "failed"


class ReviewVerdict(str, Enum):
    PASS = "PASS"
    REVISE = "REVISE"
    REJECT = "REJECT"


class Task(BaseModel):
    topic: str
    leaders: list[str] = []
    count: int
    categories: list[str] = []
    moods: list[str] = []
    constraints: str = ""


class AgentMessage(BaseModel):
    from_agent: str
    to_agent: str
    content: dict
    status: TaskStatus
    revision_count: int = 0
    feedback_route: Optional[str] = None


class FeedbackRequest(BaseModel):
    """에이전트가 이전 단계에 반려할 때 사용하는 모델"""
    action: str
    route: str
    reason: str
    requirements: Optional[str] = None
    problematic_items: list[int] = []
    revision_instructions: Optional[str] = None
    additional_needed: Optional[int] = None
    passed_wisdoms: list = []


class ReviewResult(BaseModel):
    index: int
    verdict: ReviewVerdict
    issues: list[str] = []
    revision_instructions: Optional[str] = None
