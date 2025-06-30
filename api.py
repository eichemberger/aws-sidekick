#!/usr/bin/env python3
"""
AWS Cloud Engineer Agent - API Server
Entry point for the REST API server using FastAPI
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# Add src directory to path before importing modules
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Now import the modules (after path setup)
from infrastructure.dependency_injection import get_container, configure_container  # noqa: E402
from infrastructure.logging import get_logger, configure_logging  # noqa: E402
from infrastructure.config import get_config  # noqa: E402
from adapters.inbound.fastapi_api_adapter import FastAPIAdapter  # noqa: E402
from main import initialize_agent  # noqa: E402


logger = get_logger(__name__)


def validate_and_set_aws_credentials():
    """Validate AWS credentials are available and set environment variables for MCP tools"""
    config = get_config()
    
    # Check if any AWS credentials are configured
    has_keys = bool(config.aws.access_key_id and config.aws.secret_access_key)
    has_profile = bool(config.aws.profile)
    
    if not has_keys and not has_profile:
        raise RuntimeError(
            "No AWS credentials found. Please configure either:\n"
            "1. AWS access keys: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY\n"
            "2. AWS profile: AWS_PROFILE\n"
            "Set these in your .env file or environment variables."
        )
    
    # Set environment variables for MCP tools to use
    if has_keys:
        os.environ["AWS_ACCESS_KEY_ID"] = config.aws.access_key_id
        os.environ["AWS_SECRET_ACCESS_KEY"] = config.aws.secret_access_key
        if config.aws.session_token:
            os.environ["AWS_SESSION_TOKEN"] = config.aws.session_token
        # Clear profile when using keys
        if "AWS_PROFILE" in os.environ:
            del os.environ["AWS_PROFILE"]
        logger.info("aws_credentials_initialized | type=<access_keys>")
    elif has_profile:
        os.environ["AWS_PROFILE"] = config.aws.profile
        # Clear explicit keys when using profile
        for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"]:
            if key in os.environ:
                del os.environ[key]
        logger.info(f"aws_credentials_initialized | type=<profile> | profile=<{config.aws.profile}>")
    
    # Always set the region
    os.environ["AWS_DEFAULT_REGION"] = config.aws.default_region
    logger.info(f"aws_region_set | region=<{config.aws.default_region}>")


def create_api_app():
    """Create and configure the FastAPI application"""
    load_dotenv(override=True)
    
    os.environ["BYPASS_TOOL_CONSENT"] = "true"
    
    # Check for the correct API key based on provider
    provider = os.getenv("MODEL_PROVIDER", "anthropic").lower()
    if provider == "anthropic":
        required_env_vars = ['ANTHROPIC_API_KEY']
    elif provider == "openai":
        required_env_vars = ['OPENAI_API_KEY']
    else:
        required_env_vars = []
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables for {provider}: {', '.join(missing_vars)}\n"
            "Please set these in your .env file or environment."
        )
    
    logger.info("initializing API server")
    
    # CRITICAL: Validate and set AWS credentials BEFORE initializing MCP
    try:
        validate_and_set_aws_credentials()
    except RuntimeError as e:
        logger.error(f"aws_credentials_validation_failed | {str(e)}")
        raise
    
    # Now initialize agent with credentials available
    agent, docs_tools, diagram_tools, github_tools = initialize_agent()
    
    if not agent:
        raise RuntimeError("Failed to initialize agent. Check your environment configuration.")
    
    configure_container(agent, docs_tools, diagram_tools, github_tools)
    
    container = get_container()
    task_service = container.task_application_service()
    aws_service = container.aws_application_service()
    chat_service = container.chat_application_service()
    
    api_adapter = FastAPIAdapter(task_service, aws_service, chat_service)
    
    logger.info("API server initialized successfully with AWS credentials")
    
    return api_adapter.app


def main():
    """Main function to run the API server"""
    try:
        log_level = os.getenv("LOG_LEVEL", "INFO")
        json_logs = os.getenv("LOG_FORMAT", "").lower() == "json"
        log_file = os.getenv("LOG_FILE")
        
        configure_logging(
            level=log_level,
            json_format=json_logs,
            log_file=Path(log_file) if log_file else None
        )
        
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", "8000"))
        debug = os.getenv("DEBUG", "false").lower() == "true"
        
        logger.info(f"host=<{host}> | port=<{port}> | debug=<{debug}> | starting API server")
        logger.info(f"docs_url=<http://{host}:{port}/docs> | API documentation available")
        
        if debug:
            uvicorn.run(
                "api:app",
                host=host,
                port=port,
                reload=True,
                reload_dirs=[".", "src"],
                reload_excludes=["data/", "*.db", "*.sqlite", "*.sqlite3"],
                access_log=True,
                log_level="debug"
            )
        else:
            app_instance = create_api_app()
            uvicorn.run(
                app_instance,
                host=host,
                port=port,
                access_log=True,
                log_level="info"
            )
        
    except Exception as e:
        logger.error(f"api_startup_failed | error=<{str(e)}>")
        return 1
    
    return 0

app = create_api_app()


if __name__ == "__main__":
    exit(main()) 