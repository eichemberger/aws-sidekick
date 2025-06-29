import uuid
from typing import Dict, Any, Optional
from core.domain.entities.task import Task, TaskType, TaskStatus
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

    async def execute(self, description: str, task_type: TaskType, context: Optional[Dict[str, Any]] = None) -> Task:
        """Execute a cloud engineering task"""
        
        task = Task(
            id=str(uuid.uuid4()),
            description=description,
            task_type=task_type,
            status=TaskStatus.PENDING
        )

        try:
            task = await self._task_repository.save_task(task)
            
            task.mark_in_progress()
            await self._task_repository.update_task(task)

            if not self._agent_repository.is_available():
                raise Exception("AI agent is not available")

            prompt = self._prepare_prompt(description, task_type, context)
            
            result = await self._agent_repository.execute_prompt(prompt, context)
            
            task.mark_completed(result)
            
        except Exception as e:
            task.mark_failed(str(e))
        
        finally:
            task = await self._task_repository.update_task(task)

        return task

    def _prepare_prompt(self, description: str, task_type: TaskType, context: Optional[Dict[str, Any]] = None) -> str:
        """Prepare the prompt for the AI agent based on task type"""
        

        
        base_prompt = f"Task: {description}\n\n"
        
        if task_type == TaskType.ANALYSIS:
            base_prompt += "Please analyze the following AWS infrastructure and provide detailed insights:\n"
        elif task_type == TaskType.OPTIMIZATION:
            base_prompt += "Please provide optimization recommendations for the following AWS setup:\n"
        elif task_type == TaskType.TROUBLESHOOTING:
            base_prompt += "Please help troubleshoot the following AWS issue:\n"
        elif task_type == TaskType.SECURITY_AUDIT:
            base_prompt += "Please perform a security audit of the following AWS configuration:\n"
        elif task_type == TaskType.DIAGRAM_GENERATION:
            base_prompt += "Please generate an AWS architecture diagram for:\n"
        elif task_type == TaskType.DOCUMENTATION:
            base_prompt += "Please provide documentation for the following AWS setup:\n"
        else:
            base_prompt += "Please help with the following AWS task:\n"

        if context:
            base_prompt += f"\nContext: {context}\n"

        return base_prompt

 