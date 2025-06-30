from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.entities.task import Task


class TaskServicePort(ABC):
    """Inbound port for task management operations"""

    @abstractmethod
    async def execute_task(self, description: str) -> Task:
        """Execute a cloud engineering task (waits for completion)"""
        pass

    @abstractmethod
    async def execute_task_async(self, description: str) -> str:
        """Execute a cloud engineering task asynchronously (returns task ID immediately)"""
        pass

    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        pass

    @abstractmethod
    async def get_tasks(self, limit: int = 100, offset: int = 0) -> List[Task]:
        """Get list of tasks"""
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        pass 