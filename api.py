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


def set_aws_credentials_if_available():
    """Set AWS credentials as environment variables if they are available"""
    config = get_config()
    
    # Always set the region, even if no credentials are configured
    os.environ["AWS_DEFAULT_REGION"] = config.aws.default_region
    logger.info(f"aws_region_set | region=<{config.aws.default_region}>")
    
    # Check if any AWS credentials are configured
    has_keys = bool(config.aws.access_key_id and config.aws.secret_access_key)
    has_profile = bool(config.aws.profile)
    
    if not has_keys and not has_profile:
        logger.info("no_aws_credentials_configured | credentials can be set later via UI")
        return
    
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
    
    # Set AWS credentials if available, but don't require them at startup
    set_aws_credentials_if_available()
    
    # Initialize agent (credentials will be set dynamically later if needed)
    agent, docs_tools, diagram_tools, github_tools = initialize_agent()
    
    if not agent:
        raise RuntimeError("Failed to initialize agent. Check your environment configuration.")
    
    configure_container(agent, docs_tools, diagram_tools, github_tools)
    
    container = get_container()
    
    # Initialize services with better error logging
    try:
        task_service = container.task_application_service()
        logger.info("task_service_initialized | status=success")
    except Exception as e:
        logger.error(f"task_service_initialization_failed | error=<{str(e)}>")
        raise
    
    try:
        aws_service = container.aws_application_service()
        logger.info("aws_service_initialized | status=success")
    except Exception as e:
        logger.error(f"aws_service_initialization_failed | error=<{str(e)}>")
        raise
    
    try:
        chat_service = container.chat_application_service()
        logger.info("chat_service_initialized | status=success")
    except Exception as e:
        logger.error(f"chat_service_initialization_failed | error=<{str(e)}>")
        raise
    
    try:
        aws_account_service = container.aws_account_application_service()
        logger.info("aws_account_service_initialized | status=success")
    except Exception as e:
        logger.error(f"aws_account_service_initialization_failed | error=<{str(e)}>")
        raise
    
    try:
        api_adapter = FastAPIAdapter(task_service, aws_service, chat_service, aws_account_service)
        logger.info("fastapi_adapter_initialized | status=success")
    except Exception as e:
        logger.error(f"fastapi_adapter_initialization_failed | error=<{str(e)}>")
        raise
    
    logger.info("API server initialized successfully - AWS credentials can be set via UI")
    logger.info("multi_account_endpoints_registered | status=available")
    
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
            # In debug mode, use reload with string reference to allow hot reloading
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
            # In production mode, use the same app instance for consistency
            uvicorn.run(
                app,
                host=host,
                port=port,
                access_log=True,
                log_level="info"
            )
        
    except Exception as e:
        logger.error(f"api_startup_failed | error=<{str(e)}>")
        return 1
    
    return 0

# Create the app instance once and reuse it
app = create_api_app()


if __name__ == "__main__":
    exit(main()) 