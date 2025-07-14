import asyncio
import time
from collections import OrderedDict
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from core.domain.entities.chat import ChatProcessingResult, ChatMessage
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
        chat_service: ChatServicePort,
        max_cache_size: int = 100,
        agent_timeout: float = 120.0
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
        self._conversation_cache: OrderedDict[str, Any] = OrderedDict()
        self._max_cache_size = max_cache_size
        self._agent_timeout = agent_timeout
        
        # Performance metrics
        self._request_count = 0
        self._total_processing_time = 0.0
        self._timeout_count = 0
        self._avg_agent_processing_time = 0.0
    
    async def execute(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        account_alias: Optional[str] = None
    ) -> ChatProcessingResult:
        """Execute chat message processing with advanced performance optimizations"""
        
        start_time = time.monotonic()
        self._request_count += 1
        
        try:
            # Phase 1: Fast path validation (in parallel)
            validation_tasks = []
            if account_alias:
                validation_tasks.append(self._validate_account_context(account_alias))
            if conversation_id:
                validation_tasks.append(self._validate_conversation_context(conversation_id))
            
            if validation_tasks:
                results = await asyncio.gather(*validation_tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        raise res
            
            # Phase 2: Prepare conversation context
            conversation = await self._ensure_conversation_context(
                conversation_id, account_alias, message
            )
            
            # Phase 3: High-performance parallel execution
            agent_task = asyncio.create_task(
                self._execute_agent_processing(message, conversation.id)
            )

            # Non-critical tasks that can run in the background
            background_tasks = [
                asyncio.create_task(
                    self._persist_user_message(conversation.id, message)
                ),
            ]
            if conversation_id:
                background_tasks.append(
                    asyncio.create_task(
                        self._preload_conversation_history(conversation_id)
                    )
                )

            # Phase 4: Process critical path result
            try:
                agent_result = await agent_task
            except Exception as e:
                self._logger.error(f"Agent processing failed: {e}")
                # Cancel background tasks if critical task fails
                for task in background_tasks:
                    task.cancel()
                raise MessageProcessingError(f"Agent processing failed: {e}")

            # Log errors from non-critical background tasks without failing the request
            for task in background_tasks:
                task.add_done_callback(self._log_background_task_error)

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
            processing_time = time.monotonic() - start_time
            self._total_processing_time += processing_time
            
            self._logger.info(
                f"chat_message_processed | "
                f"conversation_id={conversation.id} | "
                f"processing_time={processing_time:.3f}s | "
                f"avg_processing_time={self._total_processing_time/self._request_count:.3f}s"
            )
            
            return processed_response
            
        except Exception as e:
            processing_time = time.monotonic() - start_time
            self._logger.error(
                f"chat_message_failed | "
                f"processing_time={processing_time:.3f}s | "
                f"error={str(e)}"
            )
            raise

    def _log_background_task_error(self, task: asyncio.Task) -> None:
        """Callback to log exceptions from background tasks."""
        if task.cancelled():
            return
        if task.exception():
            self._logger.warning(
                f"A non-critical background task failed: {task.exception()}"
            )
    
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
            self._conversation_cache.move_to_end(conversation_id)
            return
        
        try:
            conversation = await self._chat_repository.get_conversation(conversation_id)
            if not conversation:
                raise ConversationNotFoundError(f"Conversation {conversation_id} not found")
            
            # Cache the conversation
            self._conversation_cache[conversation_id] = conversation
            if len(self._conversation_cache) > self._max_cache_size:
                self._conversation_cache.popitem(last=False)
            
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
                self._conversation_cache.move_to_end(conversation_id)
                return self._conversation_cache[conversation_id]
            
            conversation = await self._chat_repository.get_conversation(conversation_id)
            if not conversation:
                raise ConversationNotFoundError(f"Conversation {conversation_id} not found")
            
            # Cache for future use
            self._conversation_cache[conversation_id] = conversation
            if len(self._conversation_cache) > self._max_cache_size:
                self._conversation_cache.popitem(last=False)
            return conversation
        
        # Create new conversation using the chat service which will generate proper title
        conversation = await self._chat_service.create_conversation_from_message(
            message, account_alias
        )
        
        # Cache the new conversation
        self._conversation_cache[conversation.id] = conversation
        if len(self._conversation_cache) > self._max_cache_size:
            self._conversation_cache.popitem(last=False)
        return conversation
    
    async def _persist_user_message(self, conversation_id: str, message: str) -> str:
        """Persist user message with optimized database call"""
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
        start_time = time.monotonic()
        
        try:
            # Execute agent with timeout for better resource management
            # Increased timeout to accommodate complex operations with multiple tool calls
            agent_response = await asyncio.wait_for(
                self._agent_repository.execute_chat_prompt(message),
                timeout=self._agent_timeout  # Use configurable timeout
            )
            
            processing_time = time.monotonic() - start_time
            
            # Update agent processing time statistics
            if self._request_count > 0:
                self._avg_agent_processing_time = (
                    (self._avg_agent_processing_time * (self._request_count - 1) + processing_time) / self._request_count
                )
            else:
                self._avg_agent_processing_time = processing_time
            
            self._logger.debug(f"Agent processing completed in {processing_time:.3f}s")
            
            return agent_response
            
        except asyncio.TimeoutError:
            processing_time = time.monotonic() - start_time
            self._logger.error(f"Agent processing timed out after {processing_time:.3f}s (configured timeout: {self._agent_timeout}s)")
            self._timeout_count += 1
            
            # Provide more helpful timeout message based on duration
            if processing_time > 60:
                timeout_message = (
                    "The request is taking longer than expected due to complex operations. "
                    "This often happens when searching documentation or performing detailed analysis. "
                    "Please try a simpler question or break your request into smaller parts."
                )
            else:
                timeout_message = (
                    "The request timed out. This might be due to high system load or complex operations. "
                    "Please try again in a moment."
                )
            
            raise MessageProcessingError(timeout_message)
        except Exception as e:
            processing_time = time.monotonic() - start_time
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
            "conversation_cache_size": len(self._conversation_cache),
            "timeout_count": self._timeout_count,
            "avg_agent_processing_time": self._avg_agent_processing_time
        }
    
    def clear_caches(self) -> None:
        """Clear all caches for memory management"""
        self._account_cache.clear_cache()
        self._conversation_cache.clear()
        self._logger.info("All caches cleared for memory optimization")
 