"""
Dependency Injection Container for Hexagonal Architecture

This module wires all the components together according to the hexagonal architecture pattern.
It handles the creation and configuration of all dependencies.
"""

from typing import Optional
from .config import get_config
from .mcp_manager import get_mcp_manager

# Domain and Ports
from core.domain.value_objects.aws_credentials import AWSCredentials
from core.ports.inbound.task_service_port import TaskServicePort
from core.ports.inbound.aws_service_port import AWSServicePort
from core.ports.inbound.chat_service_port import ChatServicePort
from core.ports.outbound.aws_client_port import AWSClientPort
from core.ports.outbound.agent_repository_port import AgentRepositoryPort
from core.ports.outbound.task_repository_port import TaskRepositoryPort
from core.ports.outbound.chat_repository_port import ChatRepositoryPort

# Use Cases
from core.use_cases.execute_task_use_case import ExecuteTaskUseCase
from core.use_cases.aws_analysis_use_case import AWSAnalysisUseCase

# Application Services
from application.services.task_application_service import TaskApplicationService
from application.services.aws_application_service import AWSApplicationService
from application.services.chat_application_service import ChatApplicationService

# Adapters
from adapters.outbound.aws_client_adapter import AWSClientAdapter
from adapters.outbound.agent_repository_adapter import AgentRepositoryAdapter
from adapters.outbound.task_repository_adapter import InMemoryTaskRepositoryAdapter
from adapters.outbound.sqlite_task_repository_adapter import SQLiteTaskRepositoryAdapter
from adapters.outbound.sqlite_chat_repository_adapter import SQLiteChatRepositoryAdapter
from adapters.outbound.mcp_reinitialization_adapter import MCPReinitializationAdapter


class DependencyContainer:
    """Dependency injection container"""

    def __init__(self):
        self._instances = {}
        self._mcp_manager = get_mcp_manager()
        self._mcp_reinitialization_adapter = None

    def configure_agent(self, agent, docs_tools, diagram_tools, github_tools=None):
        """Configure the agent and tools"""
        # Store in MCP manager for lifecycle management
        self._mcp_manager._agent = agent
        self._mcp_manager._docs_tools = docs_tools
        self._mcp_manager._diagram_tools = diagram_tools
        self._mcp_manager._github_tools = github_tools

    def reinitialize_agent_with_new_credentials(self):
        """Reinitialize agent and MCP servers with updated credentials"""
        # Clear agent repository to force recreation with new agent
        if 'agent_repository' in self._instances:
            del self._instances['agent_repository']
        
        # Reinitialize MCP servers and agent
        agent, docs_tools, diagram_tools, github_tools = self._mcp_manager.reinitialize_with_credentials()
        
        # Update configuration
        self.configure_agent(agent, docs_tools, diagram_tools, github_tools)

    def get_mcp_reinitialization_adapter(self) -> MCPReinitializationAdapter:
        """Get MCP reinitialization adapter"""
        if self._mcp_reinitialization_adapter is None:
            self._mcp_reinitialization_adapter = MCPReinitializationAdapter()
            # Set the container reference to avoid circular dependency
            self._mcp_reinitialization_adapter.set_container(self)
        return self._mcp_reinitialization_adapter

    def get_aws_client_adapter(self) -> AWSClientPort:
        """Get AWS client adapter"""
        if 'aws_client' not in self._instances:
            self._instances['aws_client'] = AWSClientAdapter()
        return self._instances['aws_client']

    def get_agent_repository_adapter(self) -> AgentRepositoryPort:
        """Get agent repository adapter"""
        if 'agent_repository' not in self._instances:
            agent, docs_tools, diagram_tools, github_tools = self._mcp_manager.get_current_agent_and_tools()
            self._instances['agent_repository'] = AgentRepositoryAdapter(
                agent,
                docs_tools,
                diagram_tools,
                github_tools
            )
        return self._instances['agent_repository']

    def get_task_repository_adapter(self) -> TaskRepositoryPort:
        """Get task repository adapter"""
        if 'task_repository' not in self._instances:
            config = get_config()
            if config.database.type == "sqlite":
                self._instances['task_repository'] = SQLiteTaskRepositoryAdapter(
                    db_path=config.database.sqlite_path
                )
            else:
                # Default to in-memory for backwards compatibility
                self._instances['task_repository'] = InMemoryTaskRepositoryAdapter()
        return self._instances['task_repository']

    def get_chat_repository_adapter(self) -> ChatRepositoryPort:
        """Get chat repository adapter"""
        if 'chat_repository' not in self._instances:
            config = get_config()
            # Always use SQLite for chats since they need persistence
            chat_db_path = config.database.sqlite_path.replace('tasks.db', 'chats.db')
            self._instances['chat_repository'] = SQLiteChatRepositoryAdapter(
                db_path=chat_db_path
            )
        return self._instances['chat_repository']

    def get_execute_task_use_case(self) -> ExecuteTaskUseCase:
        """Get execute task use case"""
        if 'execute_task_use_case' not in self._instances:
            self._instances['execute_task_use_case'] = ExecuteTaskUseCase(
                agent_repository=self.get_agent_repository_adapter(),
                task_repository=self.get_task_repository_adapter()
            )
        return self._instances['execute_task_use_case']

    def get_aws_analysis_use_case(self) -> AWSAnalysisUseCase:
        """Get AWS analysis use case"""
        if 'aws_analysis_use_case' not in self._instances:
            self._instances['aws_analysis_use_case'] = AWSAnalysisUseCase(
                aws_client=self.get_aws_client_adapter(),
                agent_repository=self.get_agent_repository_adapter()
            )
        return self._instances['aws_analysis_use_case']

    def get_task_service(self) -> TaskServicePort:
        """Get task application service"""
        if 'task_service' not in self._instances:
            self._instances['task_service'] = TaskApplicationService(
                execute_task_use_case=self.get_execute_task_use_case(),
                task_repository=self.get_task_repository_adapter()
            )
        return self._instances['task_service']

    def get_aws_service(self, default_credentials: Optional[AWSCredentials] = None) -> AWSServicePort:
        """Get AWS application service"""
        if 'aws_service' not in self._instances:
            self._instances['aws_service'] = AWSApplicationService(
                aws_analysis_use_case=self.get_aws_analysis_use_case(),
                mcp_reinitialization_port=self.get_mcp_reinitialization_adapter(),
                default_credentials=default_credentials
            )
        return self._instances['aws_service']

    def get_chat_service(self) -> ChatServicePort:
        """Get chat application service"""
        if 'chat_service' not in self._instances:
            self._instances['chat_service'] = ChatApplicationService(
                chat_repository=self.get_chat_repository_adapter()
            )
        return self._instances['chat_service']



    # Convenience methods for API compatibility
    def task_application_service(self) -> TaskServicePort:
        """Get task application service (convenience method)"""
        return self.get_task_service()

    def aws_application_service(self, default_credentials: Optional[AWSCredentials] = None) -> AWSServicePort:
        """Get AWS application service (convenience method)"""
        return self.get_aws_service(default_credentials)

    def chat_application_service(self) -> ChatServicePort:
        """Get chat application service (convenience method)"""
        return self.get_chat_service()

    def reset(self):
        """Reset all instances (useful for testing)"""
        self._instances.clear()


# Global container instance
_container = DependencyContainer()

def get_container() -> DependencyContainer:
    """Get the global dependency container"""
    return _container

def configure_container(agent, docs_tools, diagram_tools, github_tools=None):
    """Configure the global container with agent and tools"""
    _container.configure_agent(agent, docs_tools, diagram_tools, github_tools) 