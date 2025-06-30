import uuid
from typing import Dict, Any, Optional
from core.domain.entities.task import Task, TaskStatus
from core.ports.outbound.agent_repository_port import AgentRepositoryPort
from core.ports.outbound.task_repository_port import TaskRepositoryPort


class ExecuteTaskUseCase:
    """Use case for executing cloud engineering tasks"""

    def __init__(
        self,
        agent_repository: AgentRepositoryPort,
        task_repository: TaskRepositoryPort
    ):
        self._agent_repository = agent_repository
        self._task_repository = task_repository

    async def execute(self, description: str, context: Optional[Dict[str, Any]] = None) -> Task:
        """Execute a cloud engineering task"""
        
        task = Task(
            id=str(uuid.uuid4()),
            description=description,
            status=TaskStatus.PENDING
        )

        try:
            task = await self._task_repository.save_task(task)
            
            task.mark_in_progress()
            await self._task_repository.update_task(task)

            if not self._agent_repository.is_available():
                raise Exception("AI agent is not available")

            prompt = self._prepare_prompt(description, context)
            
            result = await self._agent_repository.execute_prompt(prompt, context)
            
            task.mark_completed(result)
            
        except Exception as e:
            task.mark_failed(str(e))
        
        finally:
            task = await self._task_repository.update_task(task)

        return task

    def _prepare_prompt(self, description: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Prepare the prompt for the AI agent"""
        prompt = description
        
        if context:
            prompt += f"\n\nContext: {context}"

        return prompt

 