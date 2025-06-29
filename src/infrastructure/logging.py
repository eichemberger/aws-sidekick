"""
Structured logging configuration for the AWS Cloud Engineer Agent

This module provides centralized logging configuration using structlog
for consistent, structured logging across the application.

Based on Strands Agents SDK logging patterns for consistency.
"""

import sys
import logging
import structlog
from typing import Any, Dict, Optional, List
from enum import Enum
from pathlib import Path


class LogLevel(Enum):
    """Supported log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StrandsStyleFormatter(logging.Formatter):
    """Custom formatter to match Strands SDK logging style"""
    
    def format(self, record):
        # Extract structlog context if available
        context_parts = []
        
        # Get the base message
        base_msg = record.getMessage()
        
        # Extract context from record.__dict__
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName', 
                          'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                          'pathname', 'process', 'processName', 'relativeCreated', 
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                          'message', 'asctime']:
                if value is not None:
                    context_parts.append(f"{key}=<{value}>")
        
        # Build the formatted message
        parts = [record.levelname, record.name]
        
        if context_parts:
            parts.extend(context_parts)
            
        if base_msg and base_msg not in context_parts:
            parts.append(base_msg)
            
        return " | ".join(parts)


def configure_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[Path] = None,
    service_name: str = "aws-sidekick"
) -> None:
    """
    Configure structured logging for the application following Strands SDK patterns.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to output logs in JSON format
        log_file: Optional log file path
        service_name: Service name to include in all logs
    """
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler with Strands-style formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    if not json_format:
        console_handler.setFormatter(StrandsStyleFormatter())
    else:
        # For JSON format, use standard formatter
        console_handler.setFormatter(logging.Formatter('%(message)s'))
    
    root_logger.addHandler(console_handler)
    
    # Configure structlog processors
    processors: List[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Add service context
    processors.append(lambda _, __, event_dict: {**event_dict, "service": service_name})
    
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        # For console output, use a simple renderer
        processors.append(structlog.dev.ConsoleRenderer(
            colors=False,  # Disable colors to match Strands style
            exception_formatter=structlog.dev.plain_traceback,
        ))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure file logging if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        
        # Always use JSON format for file logs
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        root_logger.addHandler(file_handler)
        
    # Set specific log levels for our modules to match Strands patterns
    # Agent lifecycle logs
    logging.getLogger("aws-sidekick.agent").setLevel(logging.DEBUG)
    
    # Tool registry and execution logs
    logging.getLogger("aws-sidekick.tools").setLevel(logging.DEBUG)
    
    # Event loop logs
    logging.getLogger("aws-sidekick.event_loop").setLevel(logging.DEBUG)
    
    # Model interaction logs
    logging.getLogger("aws-sidekick.models").setLevel(logging.DEBUG)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog BoundLogger instance
    """
    # Map module names to Strands-style naming
    if name.startswith("src."):
        name = name.replace("src.", "aws-sidekick.")
    elif name == "__main__":
        name = "aws-sidekick.main"
    elif name == "api":
        name = "aws-sidekick.api"
        
    return structlog.get_logger(name)


def log_with_context(**context: Any) -> structlog.BoundLogger:
    """
    Get a logger with additional context.
    
    Args:
        **context: Key-value pairs to add to all logs from this logger
        
    Returns:
        Logger bound with the provided context
    """
    logger = structlog.get_logger()
    return logger.bind(**context)


# Strands-style logging helpers
def log_tool_execution(
    tool_name: str,
    parameters: Optional[Dict[str, Any]] = None,
    status: str = "executing",
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Create log structure for tool execution following Strands patterns.
    
    Args:
        tool_name: Name of the tool
        parameters: Tool parameters
        status: Execution status
        **kwargs: Additional context
    """
    event = {
        "tool_name": tool_name,
        "status": status,
    }
    
    if parameters:
        event["parameters"] = parameters
        
    event.update(kwargs)
    return event


def log_tool_registration(
    tool_name: str,
    tool_type: str = "function",
    is_dynamic: bool = False,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Create log structure for tool registration following Strands patterns.
    
    Args:
        tool_name: Name of the tool
        tool_type: Type of tool
        is_dynamic: Whether tool is dynamically loaded
        **kwargs: Additional context
    """
    return {
        "tool_name": tool_name,
        "tool_type": tool_type,
        "is_dynamic": is_dynamic,
        **kwargs
    }


def log_agent_lifecycle(
    phase: str,
    agent_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Create log structure for agent lifecycle events.
    
    Args:
        phase: Lifecycle phase (initializing, ready, shutting_down, etc.)
        agent_id: Agent identifier
        **kwargs: Additional context
    """
    event = {
        "phase": phase,
    }
    
    if agent_id:
        event["agent_id"] = agent_id
        
    event.update(kwargs)
    return event


def log_model_interaction(
    model_provider: str,
    operation: str,
    model_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Create log structure for model interactions.
    
    Args:
        model_provider: Model provider (anthropic, openai, etc.)
        operation: Operation being performed
        model_id: Model identifier
        **kwargs: Additional context
    """
    event = {
        "model_provider": model_provider,
        "operation": operation,
    }
    
    if model_id:
        event["model_id"] = model_id
        
    event.update(kwargs)
    return event


def log_operation(
    logger: structlog.BoundLogger,
    operation_type: str,
    entity_id: Optional[str] = None,
    success: bool = True,
    details: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> None:
    """
    Log a generic operation following Strands patterns.
    
    Args:
        logger: The logger instance to use
        operation_type: Type of operation (create_conversation, add_message, etc.)
        entity_id: ID of the entity being operated on
        success: Whether the operation was successful
        details: Additional operation details
        **kwargs: Additional context
    """
    log_data = {
        "operation_type": operation_type,
        "success": success,
    }
    
    if entity_id:
        log_data["entity_id"] = entity_id
        
    if details:
        log_data["details"] = details
        
    log_data.update(kwargs)
    
    # Log at appropriate level based on success
    if success:
        logger.info(f"operation_completed | operation_type=<{operation_type}>", **log_data)
    else:
        logger.error(f"operation_failed | operation_type=<{operation_type}>", **log_data)


# Configure logging on module import with defaults
# This can be overridden by calling configure_logging() with different parameters
configure_logging() 