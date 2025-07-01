from dataclasses import dataclass
from datetime import datetime
from typing import Literal

@dataclass
class ChatMessage:
    """Chat message domain entity."""
    id: str
    conversation_id: str
    role: Literal['user', 'assistant']
    content: str
    timestamp: datetime
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class Conversation:
    """Conversation domain entity."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    account_id: str  # AWS account ID this conversation is associated with
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'title': self.title,
            'account_id': self.account_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 