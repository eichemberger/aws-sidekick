"""
Centralized exception handling for FastAPI adapter
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Callable
import functools

from core.domain.exceptions import (
    DomainException,
    AccountValidationError,
    ConversationNotFoundError,
    AgentUnavailableError,
    MessageProcessingError
)
from infrastructure.logging import get_logger


def create_domain_exception_handlers(app):
    """Register domain exception handlers with FastAPI app"""
    logger = get_logger(__name__)
    
    @app.exception_handler(AccountValidationError)
    async def handle_account_validation_error(request: Request, exc: AccountValidationError):
        """Handle AWS account validation errors"""
        logger.warning(f"Account validation error: {exc}")
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "error_type": "account_validation_error"}
        )
    
    @app.exception_handler(ConversationNotFoundError)
    async def handle_conversation_not_found_error(request: Request, exc: ConversationNotFoundError):
        """Handle conversation not found errors"""
        logger.warning(f"Conversation not found: {exc}")
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "error_type": "conversation_not_found"}
        )
    
    @app.exception_handler(AgentUnavailableError)
    async def handle_agent_unavailable_error(request: Request, exc: AgentUnavailableError):
        """Handle agent unavailable errors"""
        logger.error(f"Agent unavailable: {exc}")
        return JSONResponse(
            status_code=503,
            content={"detail": str(exc), "error_type": "agent_unavailable"}
        )
    
    @app.exception_handler(MessageProcessingError)
    async def handle_message_processing_error(request: Request, exc: MessageProcessingError):
        """Handle message processing errors"""
        logger.error(f"Message processing error: {exc}")
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "error_type": "message_processing_error"}
        )
    
    @app.exception_handler(DomainException)
    async def handle_domain_error(request: Request, exc: DomainException):
        """Handle generic domain errors (fallback for other domain exceptions)"""
        logger.error(f"Domain error: {exc}")
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "error_type": "domain_error"}
        )
    
    @app.exception_handler(ValueError)
    async def handle_value_error(request: Request, exc: ValueError):
        """Handle validation errors from value objects"""
        logger.warning(f"Validation error: {exc}")
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "error_type": "validation_error"}
        )


def handle_unexpected_error(operation_name: str = "operation") -> HTTPException:
    """
    Create a standardized HTTPException for unexpected errors
    
    Args:
        operation_name: Name of the operation that failed (for logging context)
    
    Returns:
        HTTPException with 500 status code
    """
    logger = get_logger(__name__)
    error_message = f"Failed to {operation_name}"
    logger.error(f"Unexpected error in {operation_name}")
    return HTTPException(status_code=500, detail=error_message)


def with_error_handling(operation_name: str):
    """
    Decorator to wrap endpoint functions with standardized error handling
    
    Usage:
        @with_error_handling("process chat message")
        async def chat_endpoint():
            # Your endpoint logic
            pass
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (DomainException, ValueError, HTTPException):
                # Let domain exceptions and HTTPExceptions be handled by registered handlers
                raise
            except Exception as e:
                # Log the actual exception for debugging
                logger = get_logger(__name__)
                logger.error(f"Unexpected error in {operation_name}: {e}", exc_info=True)
                raise handle_unexpected_error(operation_name)
        return wrapper
    return decorator 