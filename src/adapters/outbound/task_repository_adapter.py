import asyncio
from typing import List, Optional, Dict
from core.ports.outbound.task_repository_port import TaskRepositoryPort
from core.domain.entities.task import Task


class InMemoryTaskRepositoryAdapter(TaskRepositoryPort):
    """In-memory task repository adapter"""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def save_task(self, task: Task) -> Task:
        """Save a task"""
        async with self._lock:
            self._tasks[task.id] = task
            return task

    async def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        async with self._lock:
            return self._tasks.get(task_id)

    async def get_tasks(self, limit: int = 100, offset: int = 0) -> List[Task]:
        """Get list of tasks with pagination"""
        async with self._lock:
            all_tasks = list(self._tasks.values())
            # Sort by creation date (newest first)
            all_tasks.sort(key=lambda t: t.created_at, reverse=True)
            return all_tasks[offset:offset + limit]

    async def update_task(self, task: Task) -> Task:
        """Update an existing task"""
        async with self._lock:
            if task.id not in self._tasks:
                raise ValueError(f"Task with ID {task.id} not found")
            self._tasks[task.id] = task
            return task

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False

    async def clear_all_tasks(self) -> None:
        """Clear all tasks (useful for testing)"""
        async with self._lock:
            self._tasks.clear()

    async def get_task_count(self) -> int:
        """Get total task count"""
        async with self._lock:
            return len(self._tasks) 