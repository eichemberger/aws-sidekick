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

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from infrastructure.dependency_injection import get_container, configure_container
from infrastructure.logging import get_logger, configure_logging
from adapters.inbound.fastapi_api_adapter import FastAPIAdapter
from main import initialize_agent


logger = get_logger(__name__)


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
    
    agent, docs_tools, diagram_tools, github_tools = initialize_agent()
    
    if not agent:
        raise RuntimeError("Failed to initialize agent. Check your environment configuration.")
    
    configure_container(agent, docs_tools, diagram_tools, github_tools)
    
    container = get_container()
    task_service = container.task_application_service()
    aws_service = container.aws_application_service()
    chat_service = container.chat_application_service()
    
    api_adapter = FastAPIAdapter(task_service, aws_service, chat_service)
    
    logger.info("API server initialized successfully")
    
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