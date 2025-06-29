import uuid
from datetime import datetime
from typing import List, Optional
from src.core.ports.inbound.chat_service_port import ChatServicePort
from src.core.ports.outbound.chat_repository_port import ChatRepositoryPort
from src.core.domain.entities.chat import ChatMessage, Conversation
from src.infrastructure.logging import get_logger, log_operation

logger = get_logger(__name__)

class ChatApplicationService(ChatServicePort):
    """Application service for chat operations."""
    
    def __init__(self, chat_repository: ChatRepositoryPort):
        self.chat_repository = chat_repository
    
    async def create_conversation(self, title: str) -> Conversation:
        """Create a new conversation with auto-generated ID."""
        now = datetime.now()
        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=title,
            created_at=now,
            updated_at=now
        )
        
        result = await self.chat_repository.create_conversation(conversation)
        
        log_operation(
            logger=logger,
            operation_type="create_conversation",
            entity_id=result.id,
            success=True,
            details={"title": title}
        )
        
        return result
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        return await self.chat_repository.get_conversation(conversation_id)
    
    async def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """List conversations with pagination."""
        return await self.chat_repository.list_conversations(limit, offset)
    
    async def update_conversation_title(self, conversation_id: str, title: str) -> Optional[Conversation]:
        """Update conversation title."""
        conversation = await self.chat_repository.get_conversation(conversation_id)
        if not conversation:
            return None
        
        conversation.title = title
        conversation.updated_at = datetime.now()
        
        result = await self.chat_repository.update_conversation(conversation)
        
        log_operation(
            logger=logger,
            operation_type="update_conversation_title",
            entity_id=conversation_id,
            success=True,
            details={"new_title": title}
        )
        
        return result
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and all its messages."""
        success = await self.chat_repository.delete_conversation(conversation_id)
        
        log_operation(
            logger=logger,
            operation_type="delete_conversation",
            entity_id=conversation_id,
            success=success
        )
        
        return success
    
    async def add_message_to_conversation(self, conversation_id: str, role: str, content: str) -> ChatMessage:
        """Add message to conversation."""
        # Verify conversation exists
        conversation = await self.chat_repository.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        message = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,  # type: ignore
            content=content,
            timestamp=datetime.now()
        )
        
        result = await self.chat_repository.add_message(message)
        
        log_operation(
            logger=logger,
            operation_type="add_message",
            entity_id=result.id,
            success=True,
            details={
                "conversation_id": conversation_id,
                "role": role,
                "content_length": len(content)
            }
        )
        
        return result
    
    async def get_conversation_messages(self, conversation_id: str, limit: int = 100, offset: int = 0) -> List[ChatMessage]:
        """Get messages for a conversation with pagination."""
        return await self.chat_repository.get_messages(conversation_id, limit, offset)
    
    async def get_or_create_default_conversation(self) -> Conversation:
        """Get or create a default conversation for the session."""
        # Try to get the most recent conversation
        conversations = await self.chat_repository.list_conversations(limit=1, offset=0)
        
        if conversations:
            return conversations[0]
        
        # Create a default conversation if none exist
        return await self.create_conversation("New Conversation")
    
    def _generate_conversation_title(self, first_message: str) -> str:
        """Generate a meaningful conversation title from the first message."""
        # Clean and truncate the message
        title = first_message.strip()
        
        # Remove common prefixes
        prefixes_to_remove = [
            "can you", "could you", "please", "i need", "i want", "help me",
            "analyze", "check", "show me", "tell me", "what", "how", "why"
        ]
        
        title_lower = title.lower()
        for prefix in prefixes_to_remove:
            if title_lower.startswith(prefix):
                title = title[len(prefix):].strip()
                break
        
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        
        # Truncate to reasonable length
        if len(title) > 50:
            title = title[:47] + "..."
        
        # Fallback if title becomes empty or too short
        if len(title) < 3:
            title = "New Conversation"
            
        return title
    
    async def create_conversation_from_message(self, first_message: str) -> Conversation:
        """Create a new conversation with a title generated from the first message."""
        title = self._generate_conversation_title(first_message)
        return await self.create_conversation(title)
    
    async def create_conversation_with_first_message(self, user_message: str, title: str = None) -> tuple[Conversation, ChatMessage]:
        """Atomically create a conversation with the first user message.
        
        This ensures that conversation creation and first message addition
        happen atomically, preventing orphaned conversations.
        """
        now = datetime.now()
        
        # Generate title from message if not provided
        if not title:
            title = self._generate_conversation_title(user_message)
        
        # Create entities
        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=title,
            created_at=now,
            updated_at=now
        )
        
        first_message = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="user",
            content=user_message,
            timestamp=now
        )
        
        # Use atomic repository operation
        result_conversation, result_message = await self.chat_repository.create_conversation_with_message(
            conversation, first_message
        )
        
        log_operation(
            logger=logger,
            operation_type="create_conversation_with_first_message",
            entity_id=result_conversation.id,
            success=True,
            details={
                "title": title,
                "message_length": len(user_message)
            }
        )
        
        return result_conversation, result_message 