"""
MCP Reinitialization Port

This port defines the interface for reinitializing MCP servers when AWS credentials change.
It follows the hexagonal architecture pattern by defining the outbound port in the core domain.
"""

from abc import ABC, abstractmethod


class MCPReinitializationPort(ABC):
    """Port for reinitializing MCP servers and agent when credentials change"""
    
    @abstractmethod
    async def reinitialize_with_new_credentials(self) -> None:
        """Reinitialize MCP servers and agent with updated AWS credentials"""
        pass 