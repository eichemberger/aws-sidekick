from dataclasses import dataclass
from datetime import datetime
from typing import Literal

MessageRole = Literal["user", "assistant"]

@dataclass
class ChatMessage:
    """Domain entity representing a chat message"""
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    timestamp: datetime
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }


@dataclass
class Conversation:
    """Domain entity representing a conversation"""
    id: str
    title: str
    account_id: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "title": self.title,
            "account_id": self.account_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class ChatProcessingResult:
    """Result of processing a chat message"""
    response: str
    conversation_id: str
    message_id: str
    timestamp: datetime
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "response": self.response,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp
        } 