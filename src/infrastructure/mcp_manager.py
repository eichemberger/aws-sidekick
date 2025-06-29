"""
MCP Server Manager

This module manages MCP server lifecycle and handles reinitialization when 
AWS credentials change, ensuring that MCP tools use updated credentials.
"""

import os
import atexit
from typing import Optional, Tuple, List, Any
from .config import get_config
from .logging import get_logger, log_agent_lifecycle, log_model_interaction, log_tool_registration

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

            SYSTEM_PROMPT = """
            You are a Senior AWS Cloud Engineer with deep expertise in cloud infrastructure, automation, and DevOps practices. 
            You don't just provide advice - you execute solutions and get things done. Your comprehensive toolkit includes:

            **Infrastructure as Code & Deployment:**
            1. AWS CDK - Design, synthesize, and deploy cloud infrastructure using TypeScript/Python
            2. Terraform - Plan, apply, and manage infrastructure with HashiCorp's tooling
            3. CloudFormation - Create and manage AWS resources declaratively

            **Monitoring & Cost Management:**
            4. AWS Cost Explorer - Analyze spending patterns, identify cost optimization opportunities
            5. CloudWatch Logs - Query, analyze, and troubleshoot application and infrastructure logs
            6. Performance monitoring and alerting setup

            **AWS Operations & Analysis:**
            7. Comprehensive AWS resource analysis and configuration auditing
            8. Security posture assessment and remediation
            9. Architecture design and infrastructure diagrams
            10. Real-time troubleshooting and incident response

            **Development & Collaboration:**
            11. GitHub repository management - code review, issue tracking, pull requests
            12. CI/CD pipeline design and implementation
            13. Infrastructure code analysis and best practices enforcement

            **Your Communication Style:**
            
            **For Simple, Direct Questions:**
            - Provide concise, direct answers
            - Get straight to the point without unnecessary elaboration
            - Answer exactly what was asked, no more, no less
            
            **For Ambiguous or Complex Questions (e.g., "help me troubleshoot", "optimize my infrastructure"):**
            - Provide comprehensive analysis and detailed recommendations
            - Explore multiple scenarios and provide best practices
            - Use all available tools to gather complete information
            - Provide actionable insights and optimization suggestions

            **For Infrastructure Changes (Deployment, Modification, Deletion):**
            - ONLY execute when given explicit, clear commands
            - Ask for clarification when requests are ambiguous
            - Confirm destructive operations before proceeding
            - Provide detailed plans before implementation
            - Request specific approval for infrastructure modifications

            **General Principles:**
            - Always consider security, cost optimization, and operational excellence
            - Use infrastructure as code whenever possible for repeatability
            - Provide complete, runnable solutions with all necessary dependencies
            - Follow AWS Well-Architected Framework principles

            **Execution Standards:**
            - All AWS operations default to us-east-1 region unless specified otherwise
            - Include proper error handling and logging in all implementations
            - Implement security best practices by default
            - For ambiguous infrastructure requests, ask: "What specifically would you like me to do?"

            You are here to analyze, recommend, and carefully execute cloud infrastructure operations. 
            Be direct and concise for simple questions, comprehensive for complex ones.

            IMPORTANT: Never include <thinking> tags or expose your internal thought process in responses.
            """

            if config.debug:
                config.print_status()

            if not config.github.is_available:
                logger.warning("github_token=<missing> | GitHub MCP server will not be available without this token")

            # Initialize AWS Documentation MCP client
            logger.debug("tool_name=<aws_docs> | registering MCP client")
            aws_docs_config = config.mcp.servers["aws_docs"]
            aws_docs_mcp_client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command=aws_docs_config.command, 
                    args=aws_docs_config.args
                )
            ))
            aws_docs_mcp_client.start()
            self._mcp_clients['aws_docs'] = aws_docs_mcp_client
            logger.debug("tool_name=<aws_docs> | MCP client started successfully")

            # Initialize AWS Diagram MCP client
            logger.debug("tool_name=<aws_diagram> | registering MCP client")
            aws_diagram_config = config.mcp.servers["aws_diagram"]
            aws_diagram_mcp_client = MCPClient(lambda: stdio_client(
                StdioServerParameters(
                    command=aws_diagram_config.command, 
                    args=aws_diagram_config.args
                )
            ))
            aws_diagram_mcp_client.start()
            self._mcp_clients['aws_diagram'] = aws_diagram_mcp_client
            logger.debug("tool_name=<aws_diagram> | MCP client started successfully")

            # Initialize GitHub MCP client if token available
            github_mcp_client = None
            github_tools = []
            if config.github.is_available:
                try:
                    logger.debug("tool_name=<github> | registering MCP client")
                    github_config = config.mcp.servers["github"]
                    github_mcp_client = MCPClient(lambda: stdio_client(
                        StdioServerParameters(
                            command=github_config.command, 
                            args=github_config.args,
                            env=github_config.env
                        )
                    ))
                    github_mcp_client.start()
                    self._mcp_clients['github'] = github_mcp_client
                    github_tools = github_mcp_client.list_tools_sync()
                    logger.debug(f"tool_name=<github> | loaded tool count=<{len(github_tools)}>")
                except Exception as e:
                    logger.warning(f"tool_name=<github> | initialization failed | {str(e)}")
                    github_mcp_client = None
                    github_tools = []

            # Get tools from MCP clients
            docs_tools = aws_docs_mcp_client.list_tools_sync()
            diagram_tools = aws_diagram_mcp_client.list_tools_sync()
            
            logger.debug(f"tool_count=<{len(docs_tools) + len(diagram_tools) + len(github_tools) + 1}> | tools configured")

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
                system_prompt=SYSTEM_PROMPT
            )
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

    def reinitialize_with_credentials(self) -> Tuple[Any, List, List, List]:
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
        logger.debug(f"aws_environment=<{aws_env_vars}> | reinitializing with updated credentials")
        
        return self.initialize_mcp_servers_and_agent()

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