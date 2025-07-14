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
from core.ports.inbound.aws_account_service_port import AWSAccountServicePort
from core.ports.outbound.aws_client_port import AWSClientPort
from core.ports.outbound.agent_repository_port import AgentRepositoryPort
from core.ports.outbound.task_repository_port import TaskRepositoryPort
from core.ports.outbound.chat_repository_port import ChatRepositoryPort
from core.ports.outbound.aws_account_repository_port import AWSAccountRepositoryPort

# Use Cases
from core.use_cases.execute_task_use_case import ExecuteTaskUseCase
from core.use_cases.aws_analysis_use_case import AWSAnalysisUseCase
from core.use_cases.process_chat_message_use_case import ProcessChatMessageUseCase

# Application Services
from application.services.task_application_service import TaskApplicationService
from application.services.aws_application_service import AWSApplicationService
from application.services.chat_application_service import ChatApplicationService
from application.services.aws_account_application_service import AWSAccountApplicationService

# Adapters
from adapters.outbound.aws_client_adapter import AWSClientAdapter
from adapters.outbound.agent_repository_adapter import AgentRepositoryAdapter
from adapters.outbound.task_repository_adapter import InMemoryTaskRepositoryAdapter
from adapters.outbound.sqlite_task_repository_adapter import SQLiteTaskRepositoryAdapter
from adapters.outbound.sqlite_chat_repository_adapter import SQLiteChatRepositoryAdapter
from adapters.outbound.sqlite_aws_account_repository_adapter import SQLiteAWSAccountRepositoryAdapter
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

    async def reinitialize_agent_with_new_credentials(self):
        """Reinitialize agent and MCP servers with updated credentials"""
        from infrastructure.logging import get_logger
        logger = get_logger(__name__)
        
        logger.info("Starting MCP agent reinitialization with new credentials")
        
        # Clear agent repository to force recreation with new agent
        if 'agent_repository' in self._instances:
            del self._instances['agent_repository']
            logger.info("Cleared cached agent repository instance")
        
        # Also clear the AWS analysis use case which depends on agent
        if 'aws_analysis_use_case' in self._instances:
            del self._instances['aws_analysis_use_case']
            logger.info("Cleared cached AWS analysis use case instance")
        
        # Clear process chat message use case which depends on agent
        if 'process_chat_message_use_case' in self._instances:
            # Clear performance caches before deleting the instance
            try:
                self._instances['process_chat_message_use_case'].clear_caches()
                logger.info("Cleared performance caches from process chat message use case")
            except Exception as e:
                logger.warning(f"Failed to clear performance caches: {e}")
            
            del self._instances['process_chat_message_use_case']
            logger.info("Cleared cached process chat message use case instance")
        
        # Clear chat service as it depends on AWS services that depend on agent
        if 'chat_service' in self._instances:
            del self._instances['chat_service']
            logger.info("Cleared cached chat service instance")
        
        # Reinitialize MCP servers and agent
        logger.info("Calling MCP manager to reinitialize with credentials")
        agent, docs_tools, diagram_tools, github_tools = await self._mcp_manager.reinitialize_with_credentials()
        
        # Update configuration
        self.configure_agent(agent, docs_tools, diagram_tools, github_tools)
        logger.info("MCP agent reinitialization completed successfully")

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
            
            # Run chat database migration if needed
            import asyncio
            from infrastructure.chat_migration_helper import migrate_chat_database_if_needed
            
            # Run migration synchronously during initialization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                migration_success = loop.run_until_complete(migrate_chat_database_if_needed(chat_db_path))
                if not migration_success:
                    from infrastructure.logging import get_logger
                    logger = get_logger(__name__)
                    logger.warning("Chat database migration failed, continuing anyway")
            finally:
                loop.close()
            
            self._instances['chat_repository'] = SQLiteChatRepositoryAdapter(
                db_path=chat_db_path
            )
        return self._instances['chat_repository']

    def get_aws_account_repository_adapter(self) -> AWSAccountRepositoryPort:
        """Get AWS account repository adapter"""
        if 'aws_account_repository' not in self._instances:
            config = get_config()
            # Always use SQLite for AWS accounts since they need persistence
            account_db_path = config.database.sqlite_path.replace('tasks.db', 'aws_accounts.db')
            
            self._instances['aws_account_repository'] = SQLiteAWSAccountRepositoryAdapter(
                db_path=account_db_path
            )
        return self._instances['aws_account_repository']

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

    def get_process_chat_message_use_case(self) -> ProcessChatMessageUseCase:
        """Get process chat message use case with optimized dependencies"""
        if 'process_chat_message_use_case' not in self._instances:
            config = get_config()
            
            self._instances['process_chat_message_use_case'] = ProcessChatMessageUseCase(
                aws_account_repository=self.get_aws_account_repository_adapter(),
                chat_repository=self.get_chat_repository_adapter(),
                agent_repository=self.get_agent_repository_adapter(),
                aws_client=self.get_aws_client_adapter(),
                chat_service=self.get_chat_service(),
                agent_timeout=config.model.agent_timeout
            )
        return self._instances['process_chat_message_use_case']

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
                account_repository=self.get_aws_account_repository_adapter(),
                mcp_reinitialization_port=self.get_mcp_reinitialization_adapter(),
                default_credentials=default_credentials
            )
        return self._instances['aws_service']

    def get_chat_service(self) -> ChatServicePort:
        """Get chat application service"""
        if 'chat_service' not in self._instances:
            self._instances['chat_service'] = ChatApplicationService(
                chat_repository=self.get_chat_repository_adapter(),
                aws_service=self.get_aws_service(),
                aws_account_service=self.get_aws_account_service()
            )
        return self._instances['chat_service']

    def get_aws_account_service(self) -> AWSAccountServicePort:
        """Get AWS account application service"""
        if 'aws_account_service' not in self._instances:
            from infrastructure.logging import get_logger
            logger = get_logger(__name__)
            
            config = get_config()
            logger.info(f"initializing_aws_account_service | environment=<{config.environment}> | debug=<{config.debug}>")
            
            self._instances['aws_account_service'] = AWSAccountApplicationService(
                account_repository=self.get_aws_account_repository_adapter(),
                aws_client=self.get_aws_client_adapter()
            )
            logger.info("aws_account_service_created | multi_account_features=<enabled>")
        return self._instances['aws_account_service']



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

    def aws_account_application_service(self) -> AWSAccountServicePort:
        """Get AWS account application service (convenience method)"""
        return self.get_aws_account_service()

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