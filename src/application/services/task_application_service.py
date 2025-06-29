import asyncio
import uuid
from typing import List, Optional
from core.ports.inbound.task_service_port import TaskServicePort
from core.domain.entities.task import Task, TaskType, TaskStatus
from core.use_cases.execute_task_use_case import ExecuteTaskUseCase
from core.ports.outbound.task_repository_port import TaskRepositoryPort


class TaskApplicationService(TaskServicePort):
    """Application service for task management"""

    def __init__(
        self,
        execute_task_use_case: ExecuteTaskUseCase,
        task_repository: TaskRepositoryPort
    ):
        self._execute_task_use_case = execute_task_use_case
        self._task_repository = task_repository

    async def execute_task(self, description: str, task_type: TaskType) -> Task:
        """Execute a cloud engineering task (waits for completion)"""
        return await self._execute_task_use_case.execute(description, task_type)

    async def execute_task_async(self, description: str, task_type: TaskType) -> str:
        """Execute a cloud engineering task asynchronously (returns task ID immediately)"""
        # Create task with pending status
        task = Task(
            id=str(uuid.uuid4()),
            description=description,
            task_type=task_type,
            status=TaskStatus.PENDING
        )
        
        # Save task immediately
        await self._task_repository.save_task(task)
        
        # Start background execution (fire and forget)
        asyncio.create_task(self._execute_task_background(task.id, description, task_type))
        
        # Return task ID immediately
        return task.id

    async def _execute_task_background(self, task_id: str, description: str, task_type: TaskType):
        """Execute task in background and update status"""
        try:
            # Get the task to update
            task = await self._task_repository.get_task_by_id(task_id)
            if not task:
                return
            
            # Mark as in progress
            task.mark_in_progress()
            await self._task_repository.update_task(task)
            
            # Execute the actual task logic
            result_task = await self._execute_task_use_case.execute(description, task_type)
            
            # Update with final result
            if result_task.is_completed():
                task.mark_completed(result_task.result)
            elif result_task.is_failed():
                task.mark_failed(result_task.error_message)
            
            await self._task_repository.update_task(task)
            
        except Exception as e:
            # Handle any errors in background execution
            try:
                task = await self._task_repository.get_task_by_id(task_id)
                if task:
                    task.mark_failed(f"Background execution failed: {str(e)}")
                    await self._task_repository.update_task(task)
            except:
                # If we can't even update the task, log would be helpful but we don't have logging here
                pass

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return await self._task_repository.get_task_by_id(task_id)

    async def get_tasks(self, limit: int = 100, offset: int = 0) -> List[Task]:
        """Get list of tasks"""
        return await self._task_repository.get_tasks(limit=limit, offset=offset)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        task = await self._task_repository.get_task_by_id(task_id)
        if task and task.status.value in ["pending", "in_progress"]:
            task.mark_failed("Task cancelled by user")
            await self._task_repository.update_task(task)
            return True
        return False 