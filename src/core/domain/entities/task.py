from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Domain entity representing a cloud engineering task"""
    id: str
    description: str
    account_alias: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    def mark_in_progress(self) -> None:
        """Mark task as in progress"""
        self.status = TaskStatus.IN_PROGRESS

    def mark_completed(self, result: str) -> None:
        """Mark task as completed with result"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """Mark task as failed with error message"""
        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == TaskStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if task is failed"""
        return self.status == TaskStatus.FAILED

    def duration(self) -> Optional[float]:
        """Get task duration in seconds if completed"""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None 