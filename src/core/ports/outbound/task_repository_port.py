from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.entities.task import Task


class TaskRepositoryPort(ABC):
    """Outbound port for task persistence"""

    @abstractmethod
    async def save_task(self, task: Task) -> Task:
        """Save a task"""
        pass

    @abstractmethod
    async def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        pass

    @abstractmethod
    async def get_tasks(self, limit: int = 100, offset: int = 0) -> List[Task]:
        """Get list of tasks with pagination"""
        pass

    @abstractmethod
    async def update_task(self, task: Task) -> Task:
        """Update an existing task"""
        pass

    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        pass 