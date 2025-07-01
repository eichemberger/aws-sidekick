"""
Main entry point for the AWS Cloud Engineer Agent

This module initializes the hexagonal architecture and launches the application.
"""

import os
import sys
from typing import Optional
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.domain.value_objects.aws_credentials import AWSCredentials
from infrastructure.dependency_injection import configure_container
from infrastructure.config import initialize_config, get_config
from infrastructure.mcp_manager import get_mcp_manager
from infrastructure.logging import (
    get_logger, configure_logging, log_agent_lifecycle
)


logger = get_logger(__name__)


def initialize_agent():
    """Initialize the Strands agent and MCP clients using MCP manager"""
    logger.debug("initializing agent and MCP clients via MCP manager")
    
    mcp_manager = get_mcp_manager()
    return mcp_manager.initialize_mcp_servers_and_agent()


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
        config = initialize_config(require_aws_credentials=False)  # Don't require AWS credentials at startup
        
        # Validate configuration but skip AWS credential validation
        config.validate(require_aws_credentials=False)
        
        config.print_status()
        
        agent, docs_tools, diagram_tools, github_tools = initialize_agent()
        
        configure_container(agent, docs_tools, diagram_tools, github_tools)
        
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