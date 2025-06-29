"""
Main entry point for the AWS Cloud Engineer Agent

This module initializes the hexagonal architecture and launches the application.
"""

import os
import sys
import atexit
from typing import Optional
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.domain.value_objects.aws_credentials import AWSCredentials
from infrastructure.dependency_injection import get_container, configure_container
from infrastructure.config import initialize_config, get_config
from infrastructure.logging import (
    get_logger, configure_logging, log_agent_lifecycle, 
    log_tool_registration, log_model_interaction
)


logger = get_logger(__name__)


def initialize_agent():
    """Initialize the Strands agent and MCP clients"""
    logger.debug("initializing agent and MCP clients")
    
    try:
        from strands import Agent
        from strands.tools.mcp import MCPClient
        from strands.models.anthropic import AnthropicModel
        from strands.models.openai import OpenAIModel
        from mcp import StdioServerParameters, stdio_client
        from strands_tools import use_aws

        config = get_config()

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

        logger.debug("tool_name=<aws_docs> | registering MCP client")
        aws_docs_config = config.mcp.servers["aws_docs"]
        aws_docs_mcp_client = MCPClient(lambda: stdio_client(
            StdioServerParameters(
                command=aws_docs_config.command, 
                args=aws_docs_config.args
            )
        ))
        aws_docs_mcp_client.start()
        logger.debug("tool_name=<aws_docs> | MCP client started successfully")

        logger.debug("tool_name=<aws_diagram> | registering MCP client")
        aws_diagram_config = config.mcp.servers["aws_diagram"]
        aws_diagram_mcp_client = MCPClient(lambda: stdio_client(
            StdioServerParameters(
                command=aws_diagram_config.command, 
                args=aws_diagram_config.args
            )
        ))
        aws_diagram_mcp_client.start()
        logger.debug("tool_name=<aws_diagram> | MCP client started successfully")

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
                github_tools = github_mcp_client.list_tools_sync()
                logger.debug(f"tool_name=<github> | loaded tool count=<{len(github_tools)}>")
            except Exception as e:
                logger.warning(f"tool_name=<github> | initialization failed | {str(e)}")
                github_mcp_client = None
                github_tools = []

        docs_tools = aws_docs_mcp_client.list_tools_sync()
        diagram_tools = aws_diagram_mcp_client.list_tools_sync()
        
        logger.debug(f"tool_count=<{len(docs_tools) + len(diagram_tools) + len(github_tools) + 1}> | tools configured")

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

        logger.debug(**log_agent_lifecycle(phase="creating"))
        agent = Agent(
            tools=[use_aws] + docs_tools + diagram_tools + github_tools,
            model=model,
            system_prompt=SYSTEM_PROMPT
        )
        logger.debug(**log_agent_lifecycle(phase="ready"))

        def cleanup():
            try:
                logger.debug(**log_agent_lifecycle(phase="shutting_down"))
                aws_docs_mcp_client.stop(None, None, None)
                aws_diagram_mcp_client.stop(None, None, None)
                if github_mcp_client:
                    github_mcp_client.stop(None, None, None)
                logger.debug("thread pool executor shutdown complete")
            except Exception as e:
                logger.error(f"cleanup failed | error=<{str(e)}>")

        atexit.register(cleanup)

        return agent, docs_tools, diagram_tools, github_tools

    except ImportError as e:
        logger.error(f"import_error=<{str(e)}> | Failed to import required dependencies")
        return None, None, None, None
    except Exception as e:
        logger.error(f"initialization_error=<{str(e)}> | Failed to initialize agent")
        return None, None, None, None


def create_default_credentials() -> Optional[AWSCredentials]:
    """Create default AWS credentials from configuration"""
    try:
        config = get_config()
        return AWSCredentials(
            access_key_id=config.aws.access_key_id,
            secret_access_key=config.aws.secret_access_key,
            session_token=config.aws.session_token,
            region=config.aws.default_region,
            profile=config.aws.profile
        )
    except Exception:
        logger.warning("default_credentials_creation_failed")
        return None


def main():
    """Main entry point"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    json_logs = os.getenv("LOG_FORMAT", "").lower() == "json"
    log_file = os.getenv("LOG_FILE")
    
    configure_logging(
        level=log_level,
        json_format=json_logs,
        log_file=Path(log_file) if log_file else None
    )
    
    logger.info(**log_agent_lifecycle(phase="starting", message="Initializing AWS Cloud Engineer Agent"))
    
    try:
        config = initialize_config()
        config.print_status()
        
        agent, docs_tools, diagram_tools, github_tools = initialize_agent()
        
        configure_container(agent, docs_tools, diagram_tools, github_tools)
        
        container = get_container()
        default_credentials = create_default_credentials()
        
        logger.info(**log_agent_lifecycle(
            phase="initialized",
            docs_tools=len(docs_tools) if docs_tools else 0,
            diagram_tools=len(diagram_tools) if diagram_tools else 0,
            github_tools=len(github_tools) if github_tools else 0
        ))
        
    except ValueError as e:
        logger.error(f"configuration_error=<{str(e)}> | Please check your .env file")
        sys.exit(1)
    except Exception as e:
        logger.error(f"startup_error=<{str(e)}> | Failed to initialize application")
        sys.exit(1)


if __name__ == "__main__":
    main() 