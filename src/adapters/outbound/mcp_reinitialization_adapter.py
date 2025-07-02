"""
MCP Reinitialization Adapter

This adapter implements the MCP reinitialization port by interfacing with the
dependency injection container and MCP manager to reinitialize services.
"""

from core.ports.outbound.mcp_reinitialization_port import MCPReinitializationPort
from infrastructure.logging import get_logger

logger = get_logger(__name__)


class MCPReinitializationAdapter(MCPReinitializationPort):
    """Adapter for reinitializing MCP servers and agent when credentials change"""
    
    def __init__(self):
        self._container = None  # Will be set by dependency injection
    
    def set_container(self, container):
        """Set the dependency injection container (called during initialization)"""
        self._container = container
    
    async def reinitialize_with_new_credentials(self) -> None:
        """Reinitialize MCP servers and agent with updated AWS credentials"""
        if not self._container:
            logger.error("container_not_set | cannot reinitialize MCP servers")
            raise RuntimeError("Dependency injection container not set")
        
        try:
            await self._container.reinitialize_agent_with_new_credentials()
            logger.info("mcp_servers_reinitialized | credentials_propagated_to_tools")
        except Exception as e:
            logger.warning(f"mcp_reinitialization_failed | error=<{str(e)}> | credentials may not be available to all tools")
            raise 