from abc import ABC, abstractmethod
from typing import Dict, Any


class AgentRepositoryPort(ABC):
    """Outbound port for interacting with the AI agent"""

    @abstractmethod
    async def execute_prompt(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Execute a prompt using the AI agent"""
        pass

    @abstractmethod
    async def execute_chat_prompt(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Execute a chat prompt using the AI agent with priority handling"""
        pass

    @abstractmethod
    async def generate_diagram(self, description: str, diagram_type: str = "architecture") -> str:
        """Generate an AWS architecture diagram"""
        pass

    @abstractmethod
    async def search_documentation(self, query: str, service: str = None) -> str:
        """Search AWS documentation"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if agent is available"""
        pass 