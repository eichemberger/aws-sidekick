"""
Middleware configuration for FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.config import get_config
from infrastructure.logging import get_logger


def setup_cors_middleware(app: FastAPI) -> None:
    """
    Configure CORS middleware for the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    logger = get_logger(__name__)
    config = get_config()
    
    logger.info("configuring_cors_middleware | setting_up_cors_policy")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=config.api.cors_allow_credentials,
        allow_methods=config.api.cors_allow_methods,
        allow_headers=config.api.cors_allow_headers,
    )
    
    logger.info(f"cors_middleware_configured | origins={config.api.cors_origins}")


def setup_all_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    logger = get_logger(__name__)
    logger.info("setting_up_all_middleware | starting_middleware_configuration")
    
    setup_cors_middleware(app)
    logger.info("all_middleware_configured | middleware_setup_complete") 