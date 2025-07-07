"""Domain-specific exceptions for the chat processing system"""


class DomainException(Exception):
    """Base exception for domain-specific errors"""
    pass


class AccountValidationError(DomainException):
    """Raised when AWS account validation fails"""
    pass


class ConversationNotFoundError(DomainException):
    """Raised when a conversation cannot be found"""
    pass


class AgentUnavailableError(DomainException):
    """Raised when the AI agent is not available"""
    pass


class MessageProcessingError(DomainException):
    """Raised when message processing fails"""
    pass 