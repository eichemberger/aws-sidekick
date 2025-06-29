from abc import ABC, abstractmethod
from typing import List, Optional
from src.core.domain.entities.chat import ChatMessage, Conversation

class ChatRepositoryPort(ABC):
    """Port for chat repository operations."""
    
    @abstractmethod
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
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
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update conversation."""
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and all its messages."""
        pass
    
    @abstractmethod
    async def add_message(self, message: ChatMessage) -> ChatMessage:
        """Add message to conversation."""
        pass
    
    @abstractmethod
    async def get_messages(self, conversation_id: str, limit: int = 100, offset: int = 0) -> List[ChatMessage]:
        """Get messages for a conversation with pagination."""
        pass
    
    @abstractmethod
    async def get_message(self, message_id: str) -> Optional[ChatMessage]:
        """Get specific message by ID."""
        pass
    
    @abstractmethod
    async def delete_message(self, message_id: str) -> bool:
        """Delete specific message."""
        pass
    
    @abstractmethod
    async def create_conversation_with_message(self, conversation: Conversation, first_message: ChatMessage) -> tuple[Conversation, ChatMessage]:
        """Atomically create a conversation and add the first message."""
        pass
    
    @abstractmethod
    async def add_messages_batch(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        """Add multiple messages atomically."""
        pass 