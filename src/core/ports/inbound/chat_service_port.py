from abc import ABC, abstractmethod
from typing import List, Optional
from src.core.domain.entities.chat import ChatMessage, Conversation

class ChatServicePort(ABC):
    """Port for chat service operations."""
    
    @abstractmethod
    async def create_conversation(self, title: str, account_alias: Optional[str] = None) -> Conversation:
        """Create a new conversation with auto-generated ID."""
        pass
    
    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        pass
    
    @abstractmethod
    async def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """List conversations with pagination."""
        pass
    
    @abstractmethod
    async def update_conversation_title(self, conversation_id: str, title: str) -> Optional[Conversation]:
        """Update conversation title."""
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and all its messages."""
        pass
    
    @abstractmethod
    async def add_message_to_conversation(self, conversation_id: str, role: str, content: str) -> ChatMessage:
        """Add message to conversation."""
        pass
    
    @abstractmethod
    async def get_conversation_messages(self, conversation_id: str, limit: int = 100, offset: int = 0) -> List[ChatMessage]:
        """Get messages for a conversation with pagination."""
        pass
    
    @abstractmethod
    async def get_or_create_default_conversation(self) -> Conversation:
        """Get or create a default conversation for the session."""
        pass
    
    @abstractmethod
    async def create_conversation_from_message(self, first_message: str, account_alias: Optional[str] = None) -> Conversation:
        """Create a new conversation with a title generated from the first message."""
        pass
    
    @abstractmethod
    async def create_conversation_with_first_message(self, user_message: str, title: str = None, account_alias: Optional[str] = None) -> tuple[Conversation, ChatMessage]:
        """Atomically create a conversation with the first user message."""
        pass 