import asyncio
from typing import Dict, Any
from contextlib import asynccontextmanager
from core.ports.outbound.agent_repository_port import AgentRepositoryPort
from infrastructure.logging import get_logger

logger = get_logger(__name__)


class AgentRepositoryAdapter(AgentRepositoryPort):
    """Agent repository adapter with improved async implementation"""

    def __init__(self, agent, docs_tools, diagram_tools, github_tools=None):
        self._agent = agent
        self._docs_tools = docs_tools
        self._diagram_tools = diagram_tools
        self._github_tools = github_tools or []
        self._available = agent is not None
        
        # Connection management - Increased concurrency for better responsiveness
        self._agent_semaphore = asyncio.Semaphore(15)  # Increased from 5 to 15
        self._chat_semaphore = asyncio.Semaphore(10)   # Separate semaphore for chat operations
        self._default_timeout = 120.0  # 2 minutes default timeout
        self._chat_timeout = 45.0  # Increased from 30 to 45 seconds for chat reliability
        self._retry_max_attempts = 2
        
        if not self._available:
            logger.warning("agent=<unavailable> | Agent repository initialized but agent is not available | This usually means the API key is missing or invalid")
        else:
            tool_count = len(self._docs_tools or []) + len(self._diagram_tools or []) + len(self._github_tools or [])
            logger.debug(f"tool_count=<{tool_count}> | agent repository initialized")

    @asynccontextmanager
    async def _agent_context(self):
        """Context manager for agent operations with connection limiting"""
        async with self._agent_semaphore:
            if not self._available:
                raise RuntimeError(
                    "AI agent is not available. Please check that your AI provider API key is set in your .env file."
                )
            yield self._agent

    @asynccontextmanager
    async def _chat_agent_context(self):
        """Context manager for chat operations with separate connection limiting"""
        async with self._chat_semaphore:
            if not self._available:
                raise RuntimeError(
                    "AI agent is not available. Please check that your AI provider API key is set in your .env file."
                )
            yield self._agent

    async def _execute_with_retry(self, operation_func, timeout: float = None, max_attempts: int = None, *args, **kwargs):
        """Execute operation with retry logic and timeout"""
        timeout = timeout or self._default_timeout
        max_attempts = max_attempts or self._retry_max_attempts
        
        for attempt in range(max_attempts):
            try:
                # Check if agent supports async natively
                if hasattr(self._agent, '__call__') and asyncio.iscoroutinefunction(self._agent):
                    # Native async agent
                    return await asyncio.wait_for(
                        operation_func(*args, **kwargs),
                        timeout=timeout
                    )
                else:
                    # Sync agent - use improved thread pool with timeout and proper cancellation
                    loop = asyncio.get_event_loop()
                    
                    # Create a cancellable task
                    future = loop.run_in_executor(
                        None,  # Use default thread pool
                        lambda: operation_func(*args, **kwargs)
                    )
                    
                    try:
                        return await asyncio.wait_for(future, timeout=timeout)
                    except asyncio.CancelledError:
                        # Ensure the future is cancelled properly
                        future.cancel()
                        raise
                        
            except asyncio.TimeoutError:
                if attempt < max_attempts - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"attempt=<{attempt + 1}/{max_attempts}> | wait_time=<{wait_time}s> | agent operation timed out, retrying")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"max_attempts=<{max_attempts}> | timeout=<{timeout}s> | agent operation timed out after all attempts")
                    raise RuntimeError(
                        f"Agent operation timed out after {timeout}s and {max_attempts} attempts"
                    )
                    
            except Exception as e:
                if attempt < max_attempts - 1:
                    # Only retry on specific errors
                    if self._is_retriable_error(e):
                        wait_time = 2 ** attempt
                        logger.warning(f"attempt=<{attempt + 1}/{max_attempts}> | wait_time=<{wait_time}s> | error=<{str(e)}> | agent operation failed, retrying")
                        await asyncio.sleep(wait_time)
                        continue
                
                logger.error(f"error=<{str(e)}> | agent operation failed")
                raise RuntimeError(f"Error executing agent operation: {str(e)}")

    def _is_retriable_error(self, error: Exception) -> bool:
        """Determine if an error is retriable"""
        # Add specific error types that should be retried
        retriable_errors = [
            "rate limit",
            "timeout",
            "temporary",
            "service unavailable",
            "too many requests",
            "connection",
            "network"
        ]
        
        error_message = str(error).lower()
        return any(retriable_msg in error_message for retriable_msg in retriable_errors)
    
    def _extract_response_content(self, response) -> str:
        """Extract content from different AI model response formats"""
        try:
            # Handle None response
            if response is None:
                return ""
            
            # Handle string response (simple case)
            if isinstance(response, str):
                return response
            
            # Handle Strands agent response objects
            if hasattr(response, 'message') and response.message:
                return str(response.message)
            elif hasattr(response, 'content') and response.content:
                return str(response.content)
            elif hasattr(response, 'text') and response.text:
                return str(response.text)
            
            # Handle dictionary responses
            if isinstance(response, dict):
                # Try different common keys
                for key in ['message', 'content', 'text', 'response', 'output']:
                    if key in response and response[key]:
                        return str(response[key])
                
                # Handle nested structures
                if 'choices' in response and response['choices']:
                    # OpenAI-style response
                    choice = response['choices'][0]
                    if isinstance(choice, dict):
                        if 'message' in choice and 'content' in choice['message']:
                            return str(choice['message']['content'])
                        elif 'text' in choice:
                            return str(choice['text'])
                
                # Handle Anthropic-style response
                if 'content' in response and isinstance(response['content'], list):
                    content_blocks = response['content']
                    if content_blocks and 'text' in content_blocks[0]:
                        return str(content_blocks[0]['text'])
            
            # Handle list responses (multiple content blocks)
            if isinstance(response, list) and len(response) > 0:
                first_item = response[0]
                if isinstance(first_item, dict) and 'text' in first_item:
                    return str(first_item['text'])
                elif isinstance(first_item, str):
                    return first_item
            
            # Fallback: convert to string
            response_str = str(response)
            if response_str and response_str != "None":
                return response_str
            
            return ""
            
        except Exception as e:
            logger.error(f"error=<{str(e)}> | response extraction failed")
            return f"❌ Error processing AI response: {str(e)}"

    async def execute_prompt(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Execute a prompt using the AI agent with improved async handling"""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
            
        # Use chat timeout for all interactive requests
        timeout = self._chat_timeout
        
        # Log prompt execution
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        logger.debug(f"prompt=<{prompt_preview}> | executing agent prompt")
        
        async with self._agent_context() as agent:
            try:
                # Prepare the operation with better error handling
                def agent_operation():
                    try:
                        logger.debug("submitting prompt to agent")
                        result = agent(prompt)
                        return result
                    except Exception as tool_error:
                        # Handle tool execution errors gracefully
                        error_msg = str(tool_error)
                        logger.warning(f"tool_error=<{error_msg[:100]}> | tool execution error occurred")
                        if "invalid_request_error" in error_msg and "tool_use" in error_msg:
                            return f"Tool execution failed: {error_msg}. This may be due to missing AWS credentials or configuration issues. Please check your AWS setup."
                        elif "BadRequestError" in error_msg:
                            return f"Request error: {error_msg}. Please check your input and try again."
                        else:
                            raise tool_error
                
                # Execute with improved timeout and retry handling
                result = await self._execute_with_retry(
                    agent_operation,
                    timeout=timeout,
                    max_attempts=self._retry_max_attempts
                )
                
                # Extract and return content
                response_content = self._extract_response_content(result)
                
                if not response_content:
                    logger.warning("empty_response | agent returned empty or invalid response")
                    return "❌ I encountered an issue processing your request. Please try again or rephrase your question."
                
                logger.debug(f"response_length=<{len(response_content)}> | agent prompt executed successfully")
                return response_content
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"error=<{error_msg}> | agent prompt execution failed")
                
                # Provide user-friendly error messages
                if "timeout" in error_msg.lower():
                    return "⏱️ The request is taking longer than expected. This might be due to complex operations or high load. Please try again."
                elif "rate limit" in error_msg.lower():
                    return "🚦 Rate limit reached. Please wait a moment and try again."
                elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                    return "🔑 Authentication issue. Please check your API key configuration."
                else:
                    return f"❌ I encountered an error: {error_msg}. Please try again or contact support if the issue persists."

    async def execute_chat_prompt(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Execute a chat prompt using the AI agent with priority handling for chat operations"""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
            
        # Use shorter timeout for chat to ensure responsiveness
        timeout = self._chat_timeout
        
        # Log prompt execution
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        logger.debug(f"prompt=<{prompt_preview}> | executing chat prompt")
        
        async with self._chat_agent_context() as agent:
            try:
                # Prepare the operation with better error handling
                def agent_operation():
                    try:
                        logger.debug("submitting chat prompt to agent")
                        result = agent(prompt)
                        return result
                    except Exception as tool_error:
                        # Handle tool execution errors gracefully
                        error_msg = str(tool_error)
                        logger.warning(f"tool_error=<{error_msg[:100]}> | chat tool execution error occurred")
                        if "invalid_request_error" in error_msg and "tool_use" in error_msg:
                            return f"Tool execution failed: {error_msg}. This may be due to missing AWS credentials or configuration issues. Please check your AWS setup."
                        elif "BadRequestError" in error_msg:
                            return f"Request error: {error_msg}. Please check your input and try again."
                        else:
                            raise tool_error
                
                # Execute with improved timeout and retry handling
                result = await self._execute_with_retry(
                    agent_operation,
                    timeout=timeout,
                    max_attempts=1  # Single attempt for chat to ensure responsiveness
                )
                
                # Extract and return content
                response_content = self._extract_response_content(result)
                
                if not response_content:
                    logger.warning("empty_response | agent returned empty or invalid response")
                    return "❌ I encountered an issue processing your request. Please try again or rephrase your question."
                
                logger.debug(f"response_length=<{len(response_content)}> | chat prompt executed successfully")
                return response_content
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"error=<{error_msg}> | chat prompt execution failed")
                
                # Provide user-friendly error messages
                if "timeout" in error_msg.lower():
                    return "⏱️ The request is taking longer than expected. Please try a simpler question or try again."
                elif "rate limit" in error_msg.lower():
                    return "🚦 Rate limit reached. Please wait a moment and try again."
                elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                    return "🔑 Authentication issue. Please check your API key configuration."
                else:
                    return f"❌ I encountered an error: {error_msg}. Please try again or contact support if the issue persists."

    async def generate_diagram(self, description: str, diagram_type: str = "architecture") -> str:
        """Generate an AWS architecture diagram"""
        if not description or not description.strip():
            raise ValueError("Description cannot be empty")
            
        logger.debug(f"tool_name=<aws_diagram> | diagram_type=<{diagram_type}> | generating diagram")
            
        diagram_prompt = f"""
        Generate an AWS architecture diagram for the following description:
        
        {description}
        
        Diagram Type: {diagram_type}
        
        Please use the AWS diagram tools to create a visual representation.
        Include proper AWS service icons and connections between services.
        """

        # Use longer timeout for diagram generation as it can be slow
        async with self._agent_context():
            def diagram_operation():
                return self._agent(diagram_prompt)
            
            return await self._execute_with_retry(
                diagram_operation, 
                timeout=180.0  # 3 minutes for diagram generation
            )

    async def search_documentation(self, query: str, service: str = None) -> str:
        """Search AWS documentation"""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
            
        logger.debug(f"tool_name=<aws_docs> | query=<{query[:50]}...> | searching documentation")
            
        search_prompt = f"""
        Search AWS documentation for: {query}
        """
        
        if service:
            search_prompt += f"\nSpecifically for AWS service: {service}"
            
        search_prompt += "\n\nPlease use the AWS documentation tools to find relevant information."

        async with self._agent_context():
            def search_operation():
                return self._agent(search_prompt)
            
            return await self._execute_with_retry(search_operation)

    async def github_operation(self, operation: str, **kwargs) -> str:
        """Execute GitHub operations"""
        if not operation or not operation.strip():
            raise ValueError("Operation cannot be empty")
            
        if not self._github_tools:
            raise RuntimeError("GitHub tools are not available. Please configure GITHUB_PERSONAL_ACCESS_TOKEN.")
            
        logger.debug(f"tool_name=<github> | operation=<{operation}> | executing GitHub operation")

        github_prompt = f"""
        Perform the following GitHub operation: {operation}
        
        Parameters: {kwargs}
        
        Please use the GitHub tools to execute this operation.
        """

        async with self._agent_context():
            def github_operation_func():
                return self._agent(github_prompt)
            
            return await self._execute_with_retry(github_operation_func)

    async def execute_with_tools(self, prompt: str, tool_types: list = None) -> str:
        """Execute a prompt with specific tool types"""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
            
        tool_context = ""
        if tool_types:
            available_tools = []
            if "docs" in tool_types and self._docs_tools:
                available_tools.append("AWS documentation tools")
            if "diagram" in tool_types and self._diagram_tools:
                available_tools.append("AWS diagram tools")
            if "github" in tool_types and self._github_tools:
                available_tools.append("GitHub tools")
            
            if available_tools:
                tool_context = f"\nAvailable tools: {', '.join(available_tools)}"
        
        enhanced_prompt = prompt + tool_context
        
        async with self._agent_context():
            def tool_operation():
                return self._agent(enhanced_prompt)
            
            return await self._execute_with_retry(tool_operation)

    def is_available(self) -> bool:
        """Check if agent is available"""
        return self._available

    def get_available_tools(self) -> Dict[str, Any]:
        """Get information about available tools"""
        return {
            "docs_tools": len(self._docs_tools) if self._docs_tools else 0,
            "diagram_tools": len(self._diagram_tools) if self._diagram_tools else 0,
            "github_tools": len(self._github_tools) if self._github_tools else 0,
            "agent_available": self._available,
            "max_concurrent_operations": self._agent_semaphore._value,
            "default_timeout": self._default_timeout
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the agent"""
        if not self._available:
            return {
                "status": "unavailable",
                "message": "Agent is not available"
            }
        
        try:
            # Simple test prompt
            test_response = await self.execute_prompt(
                "Respond with 'OK' if you are working properly.",
                context={"test": True}
            )
            
            return {
                "status": "healthy" if "OK" in test_response else "degraded",
                "message": "Agent is responding",
                "test_response": test_response[:100]  # Truncate for brevity
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}"
            }

    async def cleanup(self):
        """Cleanup resources"""
        # Cancel any pending operations if needed
        # This method can be extended for more cleanup operations
        logger.debug("agent repository adapter cleanup completed")

 