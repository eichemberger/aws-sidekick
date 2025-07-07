import asyncio
from typing import Optional
from datetime import datetime
import uuid

from core.domain.entities.chat import ChatProcessingResult
from core.domain.services.response_processor import AgentResponseProcessor
from core.domain.services.account_context_cache import AccountContextCache
from core.domain.exceptions import (
    AccountValidationError,
    ConversationNotFoundError,
    MessageProcessingError
)
from core.ports.outbound.aws_account_repository_port import AWSAccountRepositoryPort
from core.ports.outbound.chat_repository_port import ChatRepositoryPort
from core.ports.outbound.agent_repository_port import AgentRepositoryPort
from core.ports.outbound.aws_client_port import AWSClientPort
from core.ports.inbound.chat_service_port import ChatServicePort
from infrastructure.logging import get_logger


class ProcessChatMessageUseCase:
    """Enhanced use case for processing chat messages with performance optimizations"""
    
    def __init__(
        self,
        aws_account_repository: AWSAccountRepositoryPort,
        chat_repository: ChatRepositoryPort,
        agent_repository: AgentRepositoryPort,
        aws_client: AWSClientPort,
        chat_service: ChatServicePort
    ):
        self._aws_account_repository = aws_account_repository
        self._chat_repository = chat_repository
        self._agent_repository = agent_repository
        self._aws_client = aws_client
        self._chat_service = chat_service
        self._logger = get_logger(__name__)
        self._response_processor = AgentResponseProcessor()
        
        # Initialize performance optimizations
        self._account_cache = AccountContextCache(ttl_seconds=300)  # 5 minutes cache
        self._conversation_cache = {}  # Simple in-memory cache for conversations
        
        # Performance metrics
        self._request_count = 0
        self._total_processing_time = 0.0
    
    async def execute(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        account_alias: Optional[str] = None
    ) -> ChatProcessingResult:
        """Execute chat message processing with advanced performance optimizations"""
        
        start_time = asyncio.get_event_loop().time()
        self._request_count += 1
        
        try:
            # Phase 1: Fast path validation (parallel where possible)
            validation_tasks = []
            
            # 1a. Account context validation (with caching)
            if account_alias:
                validation_tasks.append(
                    self._validate_account_context(account_alias)
                )
            
            # 1b. Conversation validation (with caching)
            if conversation_id:
                validation_tasks.append(
                    self._validate_conversation_context(conversation_id)
                )
            
            # Execute validation tasks in parallel
            if validation_tasks:
                await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Phase 2: Prepare conversation context
            conversation = await self._ensure_conversation_context(
                conversation_id, account_alias, message
            )
            
            # Phase 3: High-performance parallel execution
            # Create tasks for parallel execution
            tasks = []
            
            # 3a. Persist user message (fire-and-forget with result capture)
            user_message_task = asyncio.create_task(
                self._persist_user_message(conversation.id, message)
            )
            tasks.append(user_message_task)
            
            # 3b. Execute agent processing (main processing path)
            agent_task = asyncio.create_task(
                self._execute_agent_processing(message, conversation.id)
            )
            tasks.append(agent_task)
            
            # 3c. Optional: Preload conversation history for context (if needed)
            if conversation_id:
                history_task = asyncio.create_task(
                    self._preload_conversation_history(conversation_id)
                )
                tasks.append(history_task)
            
            # Execute all tasks in parallel with optimized gathering
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Phase 4: Process results with error handling
            user_message_result = results[0]
            agent_result = results[1]
            
            # Handle any exceptions from parallel execution
            if isinstance(user_message_result, Exception):
                self._logger.warning(f"User message persistence failed: {user_message_result}")
                # Continue processing - this is not critical for response
            
            if isinstance(agent_result, Exception):
                self._logger.error(f"Agent processing failed: {agent_result}")
                raise MessageProcessingError(f"Agent processing failed: {agent_result}")
            
            # Phase 5: Fast response processing
            processed_response = await self._process_agent_response(
                agent_result, conversation.id
            )
            
            # Phase 6: Async response persistence (fire-and-forget)
            asyncio.create_task(
                self._persist_agent_response(
                    conversation.id, 
                    processed_response.response,
                    processed_response.message_id
                )
            )
            
            # Update performance metrics
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time
            self._total_processing_time += processing_time
            
            self._logger.info(
                f"chat_message_processed | "
                f"conversation_id={conversation.id} | "
                f"processing_time={processing_time:.3f}s | "
                f"avg_processing_time={self._total_processing_time/self._request_count:.3f}s"
            )
            
            return processed_response
            
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time
            self._logger.error(
                f"chat_message_failed | "
                f"processing_time={processing_time:.3f}s | "
                f"error={str(e)}"
            )
            raise
    
    async def _validate_account_context(self, account_alias: str) -> None:
        """Fast account context validation with caching"""
        try:
            # Use cached validation to avoid redundant AWS calls
            await self._account_cache.get_validated_context(
                account_alias,
                lambda alias: self._aws_account_repository.get_account_by_alias(alias)
            )
        except Exception as e:
            self._logger.warning(f"Account validation failed for '{account_alias}': {e}")
            raise AccountValidationError(f"Invalid account alias: {account_alias}")
    
    async def _validate_conversation_context(self, conversation_id: str) -> None:
        """Fast conversation validation with caching"""
        # Check cache first
        if conversation_id in self._conversation_cache:
            return
        
        try:
            conversation = await self._chat_repository.get_conversation(conversation_id)
            if not conversation:
                raise ConversationNotFoundError(f"Conversation {conversation_id} not found")
            
            # Cache the conversation
            self._conversation_cache[conversation_id] = conversation
            
        except Exception as e:
            if isinstance(e, ConversationNotFoundError):
                raise
            self._logger.error(f"Conversation validation failed: {e}")
            raise MessageProcessingError(f"Failed to validate conversation: {e}")
    
    async def _ensure_conversation_context(
        self, 
        conversation_id: Optional[str], 
        account_alias: Optional[str],
        message: str
    ):
        """Ensure conversation context exists with optimized creation"""
        
        if conversation_id:
            # Use cached conversation if available
            if conversation_id in self._conversation_cache:
                return self._conversation_cache[conversation_id]
            
            conversation = await self._chat_repository.get_conversation(conversation_id)
            if not conversation:
                raise ConversationNotFoundError(f"Conversation {conversation_id} not found")
            
            # Cache for future use
            self._conversation_cache[conversation_id] = conversation
            return conversation
        
        # Create new conversation using the chat service which will generate proper title
        conversation = await self._chat_service.create_conversation_from_message(
            message, account_alias
        )
        
        # Cache the new conversation
        self._conversation_cache[conversation.id] = conversation
        return conversation
    
    async def _persist_user_message(self, conversation_id: str, message: str) -> str:
        """Persist user message with optimized database call"""
        from core.domain.entities.chat import ChatMessage
        
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="user",
            content=message,
            timestamp=datetime.now()
        )
        
        result = await self._chat_repository.add_message(user_message)
        return result.id
    
    async def _execute_agent_processing(self, message: str, conversation_id: str) -> str:
        """Execute agent processing with performance monitoring"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Execute agent with timeout for better resource management
            agent_response = await asyncio.wait_for(
                self._agent_repository.execute_chat_prompt(message),
                timeout=30.0  # 30 second timeout
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            self._logger.debug(f"Agent processing completed in {processing_time:.3f}s")
            
            return agent_response
            
        except asyncio.TimeoutError:
            self._logger.error("Agent processing timed out after 30 seconds")
            raise MessageProcessingError("Agent processing timed out")
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            self._logger.error(f"Agent processing failed after {processing_time:.3f}s: {e}")
            raise MessageProcessingError(f"Agent execution failed: {e}")
    
    async def _preload_conversation_history(self, conversation_id: str) -> None:
        """Preload conversation history for better context (optional optimization)"""
        try:
            # This could be used to warm up context for the agent
            # For now, just log that we're preloading
            self._logger.debug(f"Preloading context for conversation {conversation_id}")
        except Exception as e:
            # Non-critical - don't fail the request
            self._logger.debug(f"Context preloading failed: {e}")
    
    async def _process_agent_response(
        self, 
        agent_response: str, 
        conversation_id: str
    ) -> ChatProcessingResult:
        """Process agent response with optimized response handling"""
        
        # Generate unique message ID
        message_id = str(uuid.uuid4())
        
        # Clean response using the domain service
        cleaned_response = self._response_processor.clean_response(agent_response)
        
        return ChatProcessingResult(
            response=cleaned_response,
            timestamp=datetime.now(),
            conversation_id=conversation_id,
            message_id=message_id
        )
    
    async def _persist_agent_response(
        self, 
        conversation_id: str, 
        response: str, 
        message_id: str
    ) -> None:
        """Persist agent response asynchronously (fire-and-forget)"""
        try:
            from core.domain.entities.chat import ChatMessage
            
            agent_message = ChatMessage(
                id=message_id,
                conversation_id=conversation_id,
                role="assistant",
                content=response,
                timestamp=datetime.now()
            )
            
            await self._chat_repository.add_message(agent_message)
            self._logger.debug(f"Agent response persisted for conversation {conversation_id}")
        except Exception as e:
            # Log but don't fail - response already sent to user
            self._logger.warning(f"Failed to persist agent response: {e}")
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics for monitoring"""
        return {
            "request_count": self._request_count,
            "total_processing_time": self._total_processing_time,
            "avg_processing_time": self._total_processing_time / max(self._request_count, 1),
            "account_cache_stats": self._account_cache.get_cache_stats(),
            "conversation_cache_size": len(self._conversation_cache)
        }
    
    def clear_caches(self) -> None:
        """Clear all caches for memory management"""
        self._account_cache.clear_cache()
        self._conversation_cache.clear()
        self._logger.info("All caches cleared for memory optimization")
 