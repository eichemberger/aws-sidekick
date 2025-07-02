"""
MCP Server Manager

This module manages MCP server lifecycle and handles reinitialization when 
AWS credentials change, ensuring that MCP tools use updated credentials.
"""

import os
import atexit
from typing import Tuple, List, Any
from .config import get_config
from .logging import get_logger, log_agent_lifecycle, log_model_interaction

logger = get_logger(__name__)


class MCPServerManager:
    """Manages MCP server lifecycle and reinitialization"""
    
    def __init__(self):
        self._agent = None
        self._docs_tools = None
        self._diagram_tools = None
        self._github_tools = None
        self._mcp_clients = {}
        self._cleanup_registered = False
    
    def initialize_mcp_servers_and_agent(self) -> Tuple[Any, List, List, List]:
        """Initialize MCP servers and create agent with current environment"""
        logger.debug("initializing MCP servers and agent")
        
        # Log AWS credential availability for debugging
        has_access_key = bool(os.getenv("AWS_ACCESS_KEY_ID"))
        has_profile = bool(os.getenv("AWS_PROFILE"))
        aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        
        if has_access_key:
            logger.info(f"aws_credentials_detected | type=<access_keys> | region=<{aws_region}>")
        elif has_profile:
            logger.info(f"aws_credentials_detected | type=<profile> | profile=<{os.getenv('AWS_PROFILE')}> | region=<{aws_region}>")
        else:
            logger.warning("no_aws_credentials_detected | MCP tools may fail to execute")
        
        try:
            from strands import Agent
            from strands.tools.mcp import MCPClient
            from strands.models.anthropic import AnthropicModel
            from strands.models.openai import OpenAIModel
            from mcp import StdioServerParameters, stdio_client
            from strands_tools import use_aws

            config = get_config()
            
            # Clean up existing clients if any
            self._cleanup_existing_clients()

            # Load system prompt from configuration
            system_prompt = config.system_prompt.prompt
            if not system_prompt.strip():
                logger.warning("system_prompt_empty | using fallback prompt")
                system_prompt = "You are a helpful AWS Cloud Engineer assistant."
            
            logger.debug(f"system_prompt_loaded | length=<{len(system_prompt)}> characters")

            if config.debug:
                config.print_status()

            # Initialize MCP clients dynamically based on configuration
            all_tools = []
            enabled_servers = list(config.mcp.servers.keys())
            logger.info(f"initializing_mcp_servers | enabled_count=<{len(enabled_servers)}> | servers=<{enabled_servers}>")

            # Initialize each enabled MCP server
            for server_name, server_config in config.mcp.servers.items():
                try:
                    logger.debug(f"tool_name=<{server_name}> | registering MCP client | description=<{server_config.description or 'N/A'}>")
                    
                    # Prepare environment for the server - inherit current process environment
                    # and overlay any server-specific environment variables
                    server_env = os.environ.copy()  # Start with current process environment
                    if server_config.env:
                        server_env.update(server_config.env)  # Add server-specific vars
                    
                    # For GitHub server, ensure token is set
                    if server_name == "github":
                        # Check both the config and the actual environment variable
                        github_token = server_env.get('GITHUB_PERSONAL_ACCESS_TOKEN')
                        if not config.github.is_available or not github_token or github_token.strip() == '':
                            logger.warning(f"tool_name=<{server_name}> | skipping | github_token not available | config_available={config.github.is_available} | env_token_set={bool(github_token)}")
                            continue
                    
                    # Debug: Log AWS environment being passed to this MCP server
                    logger.debug(f"tool_name=<{server_name}> | aws_access_key={'***' if server_env.get('AWS_ACCESS_KEY_ID') else 'NOT_SET'} | aws_profile={server_env.get('AWS_PROFILE', 'NOT_SET')} | aws_region={server_env.get('AWS_DEFAULT_REGION', 'NOT_SET')}")
                    
                    mcp_client = MCPClient(lambda sc=server_config, se=server_env: stdio_client(
                        StdioServerParameters(
                            command=sc.command,
                            args=sc.args,
                            env=se
                        )
                    ))
                    mcp_client.start()
                    self._mcp_clients[server_name] = mcp_client
                    
                    # Get tools from this server and verify readiness
                    server_tools = mcp_client.list_tools_sync()
                    all_tools.extend(server_tools)
                    
                    # Verify MCP client basic functionality
                    if len(server_tools) == 0:
                        logger.warning(f"tool_name=<{server_name}> | no_tools_available | server may not be ready")
                    
                    logger.debug(f"tool_name=<{server_name}> | MCP client started successfully | tool_count=<{len(server_tools)}>")
                    
                except Exception as e:
                    logger.warning(f"tool_name=<{server_name}> | initialization failed | {str(e)}")
                    continue
            
            # For backwards compatibility, separate tools by type (this can be simplified later)
            docs_tools = []
            diagram_tools = []
            github_tools = []
            
            # Categorize tools based on their server source
            for server_name, client in self._mcp_clients.items():
                try:
                    server_tools = client.list_tools_sync()
                    if 'docs' in server_name.lower():
                        docs_tools.extend(server_tools)
                    elif 'diagram' in server_name.lower():
                        diagram_tools.extend(server_tools)
                    elif 'github' in server_name.lower():
                        github_tools.extend(server_tools)
                    # Other tools are available but not categorized for now
                except Exception as e:
                    logger.warning(f"tool_name=<{server_name}> | failed to get tools | {str(e)}")
            
            logger.debug(f"tool_count=<{len(all_tools)}> | categorized | docs=<{len(docs_tools)}> | diagram=<{len(diagram_tools)}> | github=<{len(github_tools)}>")

            # Initialize AI model
            logger.debug(**log_model_interaction(
                model_provider=config.model.provider,
                operation="initializing",
                model_id=config.model.model_id
            ))
            
            if config.model.provider == "anthropic":
                model = AnthropicModel(
                    model_id=config.model.model_id,
                    client_args={
                        "api_key": config.model.api_key,
                    },
                    max_tokens=config.model.max_tokens,
                )
            elif config.model.provider == "openai":
                model = OpenAIModel(
                    model_id=config.model.model_id,
                    client_args={
                        "api_key": config.model.api_key,
                    },
                    params={
                        "max_completion_tokens": config.model.max_tokens,
                    }
                )
            else:
                raise ValueError(f"Unsupported model provider: {config.model.provider}")
            
            logger.debug(**log_model_interaction(
                model_provider=config.model.provider,
                operation="initialized",
                model_id=config.model.model_id
            ))

            # Create agent with all tools
            logger.debug(**log_agent_lifecycle(phase="creating"))
            agent = Agent(
                tools=[use_aws] + docs_tools + diagram_tools + github_tools,
                model=model,
                system_prompt=system_prompt
            )
            
            # Verify agent is ready with all tools
            total_tools = 1 + len(docs_tools) + len(diagram_tools) + len(github_tools)  # +1 for use_aws
            logger.debug(f"agent_created | total_tools=<{total_tools}> | verifying_readiness")
            
            logger.debug(**log_agent_lifecycle(phase="ready"))

            # Register cleanup if not already done
            if not self._cleanup_registered:
                atexit.register(self._cleanup_all_clients)
                self._cleanup_registered = True

            # Store references
            self._agent = agent
            self._docs_tools = docs_tools
            self._diagram_tools = diagram_tools
            self._github_tools = github_tools

            return agent, docs_tools, diagram_tools, github_tools

        except ImportError as e:
            logger.error(f"import_error=<{str(e)}> | Failed to import required dependencies")
            return None, None, None, None
        except Exception as e:
            logger.error(f"initialization_error=<{str(e)}> | Failed to initialize MCP servers and agent")
            return None, None, None, None

    async def reinitialize_with_credentials(self) -> Tuple[Any, List, List, List]:
        """Reinitialize MCP servers and agent with current environment variables"""
        logger.info("credentials_changed | reinitializing MCP servers and agent with new credentials")
        
        # Log current AWS environment variables (without exposing secrets)
        aws_env_vars = {
            'AWS_DEFAULT_REGION': os.environ.get('AWS_DEFAULT_REGION'),
            'AWS_PROFILE': os.environ.get('AWS_PROFILE'),
            'has_access_key': bool(os.environ.get('AWS_ACCESS_KEY_ID')),
            'has_secret_key': bool(os.environ.get('AWS_SECRET_ACCESS_KEY')),
            'has_session_token': bool(os.environ.get('AWS_SESSION_TOKEN'))
        }
        logger.info(f"aws_environment=<{aws_env_vars}> | reinitializing with updated credentials")
        
        # Clean up existing clients first
        logger.info("cleaning up existing MCP clients before reinitialization")
        self._cleanup_existing_clients()
        
        # Reinitialize everything
        result = self.initialize_mcp_servers_and_agent()
        
        if result[0] is not None:
            # Verify agent is ready by testing MCP server connectivity
            await self._verify_agent_readiness(result[0])
            logger.info("MCP servers and agent reinitialized successfully with new credentials")
        else:
            logger.error("Failed to reinitialize MCP servers and agent")
            
        return result

    async def _verify_agent_readiness(self, agent) -> None:
        """Verify that the agent and MCP servers are ready to handle tool calls"""
        try:
            # Test MCP server connectivity by checking tool availability
            for server_name, client in self._mcp_clients.items():
                try:
                    # Verify each MCP client is still responsive
                    client.list_tools_sync()
                    logger.debug(f"tool_name=<{server_name}> | readiness_verified")
                except Exception as e:
                    logger.warning(f"tool_name=<{server_name}> | readiness_check_failed | {str(e)}")
                    # Don't fail the whole process, just warn
            
            logger.debug("agent_readiness_verified | all_mcp_servers_responsive")
            
        except Exception as e:
            logger.warning(f"agent_readiness_verification_failed | {str(e)} | proceeding_anyway")

    def _cleanup_existing_clients(self):
        """Clean up existing MCP clients"""
        for name, client in self._mcp_clients.items():
            try:
                logger.debug(f"tool_name=<{name}> | stopping MCP client")
                client.stop(None, None, None)
            except Exception as e:
                logger.warning(f"tool_name=<{name}> | error stopping MCP client | {str(e)}")
        self._mcp_clients.clear()

    def _cleanup_all_clients(self):
        """Clean up all MCP clients (called on exit)"""
        try:
            logger.debug(**log_agent_lifecycle(phase="shutting_down"))
            self._cleanup_existing_clients()
            logger.debug("MCP server cleanup complete")
        except Exception as e:
            logger.error(f"cleanup failed | error=<{str(e)}>")

    def get_current_agent_and_tools(self) -> Tuple[Any, List, List, List]:
        """Get current agent and tools"""
        return self._agent, self._docs_tools, self._diagram_tools, self._github_tools


# Global MCP server manager instance
_mcp_manager = MCPServerManager()

def get_mcp_manager() -> MCPServerManager:
    """Get the global MCP server manager"""
    return _mcp_manager 