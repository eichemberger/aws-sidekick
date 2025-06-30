import asyncio
import uuid
from typing import List, Optional
from core.ports.inbound.task_service_port import TaskServicePort
from core.domain.entities.task import Task, TaskStatus
from core.use_cases.execute_task_use_case import ExecuteTaskUseCase
from core.ports.outbound.task_repository_port import TaskRepositoryPort
from infrastructure.logging import get_logger


class TaskApplicationService(TaskServicePort):
    """Application service for task management"""

    def __init__(
        self,
        execute_task_use_case: ExecuteTaskUseCase,
        task_repository: TaskRepositoryPort
    ):
        self._execute_task_use_case = execute_task_use_case
        self._task_repository = task_repository
        self._logger = get_logger(__name__)

    async def execute_task(self, description: str) -> Task:
        """Execute a cloud engineering task (waits for completion)"""
        return await self._execute_task_use_case.execute(description)

    async def execute_task_async(self, description: str) -> str:
        """Execute a cloud engineering task asynchronously (returns task ID immediately)"""
        # Create task with pending status
        task = Task(
            id=str(uuid.uuid4()),
            description=description,
            status=TaskStatus.PENDING
        )
        
        # Save task immediately
        await self._task_repository.save_task(task)
        
        # Start background execution (fire and forget)
        asyncio.create_task(self._execute_task_background(task.id, description))
        
        # Return task ID immediately
        return task.id

    async def _execute_task_background(self, task_id: str, description: str):
        """Execute task in background and update status"""
        self._logger.info(f"task_background_started | task_id=<{task_id}> | description=<{description[:100]}...>")
        
        
        try:
            # Get the task to update
            task = await self._task_repository.get_task_by_id(task_id)
            if not task:
                self._logger.error(f"task_not_found | task_id=<{task_id}>")
                return
            
            # Mark as in progress
            task.mark_in_progress()
            await self._task_repository.update_task(task)
            self._logger.info(f"task_marked_in_progress | task_id=<{task_id}>")
            
            # Get the agent repository from the use case (to access MCP tools)
            agent_repository = self._execute_task_use_case._agent_repository
            
            # Check if agent is available
            if not agent_repository.is_available():
                self._logger.error(f"agent_not_available | task_id=<{task_id}>")
                task.mark_failed("AI agent is not available")
                await self._task_repository.update_task(task)
                return
            
            self._logger.info(f"agent_available | task_id=<{task_id}> | executing_prompt")
            
            # Execute the task directly with the agent repository
            result = await agent_repository.execute_prompt(description, None)
            
            self._logger.info(f"task_execution_completed | task_id=<{task_id}> | result_length=<{len(str(result))}>")
            
            # Update task with result
            task.mark_completed(result)
            await self._task_repository.update_task(task)
            
            self._logger.info(f"task_background_completed | task_id=<{task_id}>")
            
        except Exception as e:
            self._logger.error(f"task_background_error | task_id=<{task_id}> | error=<{str(e)}>")
            
            # Handle any errors in background execution
            try:
                task = await self._task_repository.get_task_by_id(task_id)
                if task:
                    task.mark_failed(f"Background execution failed: {str(e)}")
                    await self._task_repository.update_task(task)
                    self._logger.info(f"task_marked_failed | task_id=<{task_id}>")
            except Exception as update_error:
                self._logger.error(f"task_update_error | task_id=<{task_id}> | error=<{str(update_error)}>")
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