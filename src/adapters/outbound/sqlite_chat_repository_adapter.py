import aiosqlite
from datetime import datetime
from typing import List, Optional
from src.core.ports.outbound.chat_repository_port import ChatRepositoryPort
from src.core.domain.entities.chat import ChatMessage, Conversation
from src.infrastructure.logging import get_logger, log_operation

logger = get_logger(__name__)

class DatabaseConnection:
    """Async context manager for database connections with foreign keys enabled."""
    
    def __init__(self, db_path: str, auto_commit: bool = True):
        self.db_path = db_path
        self.db = None
        self.auto_commit = auto_commit
        self._in_transaction = False
    
    async def __aenter__(self):
        self.db = await aiosqlite.connect(self.db_path)
        await self.db.execute("PRAGMA foreign_keys = ON")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            if self._in_transaction:
                if exc_type is None:
                    await self.commit()
                else:
                    await self.rollback()
            await self.db.close()
    
    async def execute(self, sql: str, parameters=None):
        """Execute SQL with optional parameters."""
        if parameters:
            return await self.db.execute(sql, parameters)
        return await self.db.execute(sql)
    
    async def executemany(self, sql: str, parameters_list):
        """Execute SQL with multiple parameter sets."""
        return await self.db.executemany(sql, parameters_list)
    
    async def begin_transaction(self):
        """Begin a transaction."""
        await self.db.execute("BEGIN")
        self._in_transaction = True
    
    async def commit(self):
        """Commit the current transaction."""
        if self._in_transaction:
            await self.db.commit()
            self._in_transaction = False
        elif self.auto_commit:
            await self.db.commit()
    
    async def rollback(self):
        """Rollback the current transaction."""
        if self._in_transaction:
            await self.db.rollback()
            self._in_transaction = False
    
    def cursor(self):
        """Get a cursor for the database."""
        return self.db.cursor()


class SQLiteChatRepositoryAdapter(ChatRepositoryPort):
    """SQLite implementation of chat repository."""
    
    def __init__(self, db_path: str = "data/chats.db"):
        self.db_path = db_path
    
    def _get_db_connection(self, auto_commit: bool = True):
        """Get database connection context manager with foreign keys enabled."""
        return DatabaseConnection(self.db_path, auto_commit=auto_commit)
    
    def _get_transaction(self):
        """Get a database connection with explicit transaction control."""
        return DatabaseConnection(self.db_path, auto_commit=False)
    
    async def _init_db(self):
        """Initialize database tables."""
        async with self._get_db_connection() as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_timestamp 
                ON chat_messages (conversation_id, timestamp DESC)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_updated 
                ON conversations (updated_at DESC)
            """)
            
            await db.commit()
    
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
        await self._init_db()
        
        async with self._get_db_connection() as db:
            await db.execute("""
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (conversation.id, conversation.title, conversation.created_at, conversation.updated_at))
            await db.commit()
        
        log_operation(
            logger=logger,
            operation_type="create_conversation",
            entity_id=conversation.id,
            success=True,
            details={"title": conversation.title}
        )
        
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, title, created_at, updated_at
                FROM conversations 
                WHERE id = ?
            """, (conversation_id,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return Conversation(
                        id=row[0],
                        title=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        updated_at=datetime.fromisoformat(row[3])
                    )
                return None
    
    async def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """List conversations with pagination."""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, title, created_at, updated_at
                FROM conversations 
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)) as cursor:
                rows = await cursor.fetchall()
                
                return [
                    Conversation(
                        id=row[0],
                        title=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        updated_at=datetime.fromisoformat(row[3])
                    )
                    for row in rows
                ]
    
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update conversation."""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE conversations 
                SET title = ?, updated_at = ?
                WHERE id = ?
            """, (conversation.title, conversation.updated_at, conversation.id))
            await db.commit()
        
        log_operation(
            logger=logger,
            operation_type="update_conversation",
            entity_id=conversation.id,
            success=True,
            details={"title": conversation.title}
        )
        
        return conversation
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and all its messages.
        
        Thanks to foreign key constraints with ON DELETE CASCADE,
        deleting the conversation will automatically delete all associated messages.
        """
        await self._init_db()
        
        async with self._get_db_connection() as db:
            cursor = await db.execute("""
                DELETE FROM conversations WHERE id = ?
            """, (conversation_id,))
            await db.commit()
            
            success = cursor.rowcount > 0
        
        log_operation(
            logger=logger,
            operation_type="delete_conversation",
            entity_id=conversation_id,
            success=success
        )
        
        return success
    
    async def create_conversation_with_message(self, conversation: Conversation, first_message: ChatMessage) -> tuple[Conversation, ChatMessage]:
        """Atomically create a conversation and add the first message."""
        await self._init_db()
        
        async with self._get_transaction() as db:
            await db.begin_transaction()
            
            # Create conversation
            await db.execute("""
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (conversation.id, conversation.title, conversation.created_at, conversation.updated_at))
            
            # Add first message
            await db.execute("""
                INSERT INTO chat_messages (id, conversation_id, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (first_message.id, first_message.conversation_id, first_message.role, first_message.content, first_message.timestamp))
            
            # Update conversation timestamp to match first message
            await db.execute("""
                UPDATE conversations 
                SET updated_at = ?
                WHERE id = ?
            """, (first_message.timestamp, conversation.id))
            
            # Transaction commits automatically on successful exit
        
        log_operation(
            logger=logger,
            operation_type="create_conversation_with_message",
            entity_id=conversation.id,
            success=True,
            details={
                "title": conversation.title,
                "first_message_role": first_message.role,
                "content_length": len(first_message.content)
            }
        )
        
        return conversation, first_message
    
    async def add_messages_batch(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        """Add multiple messages atomically."""
        if not messages:
            return []
        
        await self._init_db()
        
        async with self._get_transaction() as db:
            await db.begin_transaction()
            
            # Group messages by conversation for efficient updates
            conversation_updates = {}
            
            for message in messages:
                # Insert message
                await db.execute("""
                    INSERT INTO chat_messages (id, conversation_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (message.id, message.conversation_id, message.role, message.content, message.timestamp))
                
                # Track latest timestamp per conversation
                if message.conversation_id not in conversation_updates or message.timestamp > conversation_updates[message.conversation_id]:
                    conversation_updates[message.conversation_id] = message.timestamp
            
            # Update conversation timestamps
            for conversation_id, latest_timestamp in conversation_updates.items():
                await db.execute("""
                    UPDATE conversations 
                    SET updated_at = ?
                    WHERE id = ?
                """, (latest_timestamp, conversation_id))
        
        log_operation(
            logger=logger,
            operation_type="add_messages_batch",
            entity_id=f"batch-{len(messages)}",
            success=True,
            details={
                "message_count": len(messages),
                "conversations_updated": len(conversation_updates)
            }
        )
        
        return messages
    
    async def add_message(self, message: ChatMessage) -> ChatMessage:
        """Add message to conversation with atomic transaction."""
        await self._init_db()
        
        async with self._get_transaction() as db:
            await db.begin_transaction()
            
            # Insert the message
            await db.execute("""
                INSERT INTO chat_messages (id, conversation_id, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (message.id, message.conversation_id, message.role, message.content, message.timestamp))
            
            # Update conversation's updated_at timestamp atomically
            await db.execute("""
                UPDATE conversations 
                SET updated_at = ?
                WHERE id = ?
            """, (message.timestamp, message.conversation_id))
            
            # Transaction will be committed automatically on successful exit
        
        log_operation(
            logger=logger,
            operation_type="add_message",
            entity_id=message.id,
            success=True,
            details={
                "conversation_id": message.conversation_id,
                "role": message.role,
                "content_length": len(message.content)
            }
        )
        
        return message
    
    async def get_messages(self, conversation_id: str, limit: int = 100, offset: int = 0) -> List[ChatMessage]:
        """Get messages for a conversation with pagination."""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, conversation_id, role, content, timestamp
                FROM chat_messages 
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
                LIMIT ? OFFSET ?
            """, (conversation_id, limit, offset)) as cursor:
                rows = await cursor.fetchall()
                
                return [
                    ChatMessage(
                        id=row[0],
                        conversation_id=row[1],
                        role=row[2],
                        content=row[3],
                        timestamp=datetime.fromisoformat(row[4])
                    )
                    for row in rows
                ]
    
    async def get_message(self, message_id: str) -> Optional[ChatMessage]:
        """Get specific message by ID."""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, conversation_id, role, content, timestamp
                FROM chat_messages 
                WHERE id = ?
            """, (message_id,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return ChatMessage(
                        id=row[0],
                        conversation_id=row[1],
                        role=row[2],
                        content=row[3],
                        timestamp=datetime.fromisoformat(row[4])
                    )
                return None
    
    async def delete_message(self, message_id: str) -> bool:
        """Delete specific message."""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM chat_messages WHERE id = ?
            """, (message_id,))
            await db.commit()
            
            success = cursor.rowcount > 0
        
        log_operation(
            logger=logger,
            operation_type="delete_message",
            entity_id=message_id,
            success=success
        )
        
        return success 