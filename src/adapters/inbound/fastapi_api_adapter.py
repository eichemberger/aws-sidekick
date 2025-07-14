from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, AsyncGenerator
from datetime import datetime
import json
import asyncio

from core.ports.inbound.task_service_port import TaskServicePort
from core.ports.inbound.aws_service_port import AWSServicePort
from core.ports.inbound.chat_service_port import ChatServicePort
from core.ports.inbound.aws_account_service_port import AWSAccountServicePort
from core.domain.value_objects.aws_credentials import AWSCredentials
from infrastructure.config import get_config
from infrastructure.logging import get_logger
from infrastructure.dependency_injection import get_container
from .exception_handlers import create_domain_exception_handlers, with_error_handling
from .middleware import setup_all_middleware
from .static_files import setup_all_static_serving, setup_spa_fallback


# Pydantic models for API requests/responses
class TaskRequest(BaseModel):
    description: str = Field(..., description="Description of the task to execute")


class TaskResponse(BaseModel):
    task_id: str
    description: str
    status: str
    result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="Chat message to send to the agent")
    conversation_id: Optional[str] = Field(None, pattern=r'^[a-f0-9-]{36}$', description="ID of the conversation to continue")
    account_alias: Optional[str] = Field(None, min_length=1, max_length=100, description="AWS account alias to use for this chat")


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime
    conversation_id: str
    message_id: str


class ConversationResponse(BaseModel):
    id: str
    title: str
    account_id: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    timestamp: datetime


class AWSAccountInfo(BaseModel):
    account_id: str
    region: str
    user_arn: str


class AWSCredentialsRequest(BaseModel):
    access_key_id: Optional[str] = Field(None, description="AWS Access Key ID")
    secret_access_key: Optional[str] = Field(None, description="AWS Secret Access Key")
    session_token: Optional[str] = Field(None, description="AWS Session Token")
    region: str = Field("us-east-1", description="AWS Region")
    profile: Optional[str] = Field(None, description="AWS Profile name")


class AWSCredentialsResponse(BaseModel):
    region: str
    profile: Optional[str] = None
    has_access_key: bool
    has_session_token: bool
    is_valid: bool


class TaskCreatedResponse(BaseModel):
    task_id: str
    status: str = "pending"
    message: str = "Task created and executing in background"


# Multi-Account AWS Management Models
class AWSAccountRequest(BaseModel):
    alias: str = Field(..., description="Unique alias for the AWS account")
    credentials: AWSCredentialsRequest = Field(..., description="AWS credentials")
    description: Optional[str] = Field(None, description="Optional description of the account")
    set_as_default: bool = Field(False, description="Set this account as the default")


class AWSAccountResponse(BaseModel):
    alias: str
    description: Optional[str] = None
    region: str
    account_id: Optional[str] = None
    uses_profile: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime


class AWSAccountUpdateRequest(BaseModel):
    credentials: AWSCredentialsRequest = Field(..., description="Updated AWS credentials")


class SetActiveAccountRequest(BaseModel):
    account_alias: str = Field(..., description="Alias of the account to set as active")


class ActiveAccountResponse(BaseModel):
    account_alias: Optional[str] = None


class ValidationResponse(BaseModel):
    valid: bool


class FastAPIAdapter:
    """FastAPI adapter for the AWS Cloud Engineer Agent API"""

    def __init__(
        self,
        task_service: TaskServicePort,
        aws_service: AWSServicePort,
        chat_service: ChatServicePort,
        aws_account_service: AWSAccountServicePort
    ):
        from infrastructure.logging import get_logger
        logger = get_logger(__name__)
        
        logger.info("initializing_fastapi_adapter | checking_service_availability")
        
        if not task_service:
            raise ValueError("task_service cannot be None")
        if not aws_service:
            raise ValueError("aws_service cannot be None")
        if not chat_service:
            raise ValueError("chat_service cannot be None")
        if not aws_account_service:
            raise ValueError("aws_account_service cannot be None")
        
        self._task_service = task_service
        self._aws_service = aws_service
        self._chat_service = chat_service
        self._aws_account_service = aws_account_service
        
        logger.info("fastapi_adapter_services_validated | all_services=<available>")
        
        config = get_config()
        
        self._app = FastAPI(
            title=config.api.title,
            description=config.api.description,
            version=config.api.version,
            docs_url=config.api.docs_url,
            redoc_url=config.api.redoc_url
        )
        
        setup_all_middleware(self._app)
        create_domain_exception_handlers(self._app)
        setup_all_static_serving(self._app)
        
        logger.info("registering_api_routes | starting_route_setup")
        self._setup_routes()
        logger.info("api_routes_registered | setup_complete")
        
        setup_spa_fallback(self._app)

    def _to_task_response(self, task) -> TaskResponse:
        """Maps a Task domain entity to a TaskResponse Pydantic model."""
        return TaskResponse(
            task_id=task.id,
            description=task.description,
            status=task.status.value,
            result=task.result,
            error_message=task.error_message,
            created_at=task.created_at,
            completed_at=task.completed_at,
            duration=task.duration()
        )

    def _to_aws_account_response(self, account) -> AWSAccountResponse:
        """Maps an AWSAccount domain entity to an AWSAccountResponse Pydantic model."""
        return AWSAccountResponse(
            alias=account.alias,
            description=account.description,
            region=account.region,
            account_id=account.account_id,
            uses_profile=account.uses_profile,
            is_default=account.is_default,
            created_at=account.created_at,
            updated_at=account.updated_at
        )

    def _setup_routes(self):
        """Setup API routes"""
        
        @self._app.get("/api", summary="Health check")
        async def health_check():
            return {
                "message": "AWS Cloud Engineer Agent API",
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            }



        @self._app.post("/api/chat", response_model=ChatResponse, summary="Chat with the agent")
        @with_error_handling("process chat message")
        async def chat(request: ChatRequest):
            """Send a message to the agent and get immediate response with persistence"""
            # Basic input validation
            if not request.message.strip():
                raise HTTPException(status_code=400, detail="Message cannot be empty")
            
            # Get the process chat message use case
            process_chat_use_case = get_container().get_process_chat_message_use_case()
            
            # Execute the use case with all the business logic
            result = await process_chat_use_case.execute(
                message=request.message,
                conversation_id=request.conversation_id,
                account_alias=request.account_alias
            )
            
            # Map the result to the HTTP response
            return ChatResponse(
                response=result.response,
                timestamp=result.timestamp,
                conversation_id=result.conversation_id,
                message_id=result.message_id
            )

        @self._app.post("/api/chat/stream", summary="Chat with the agent (streaming response)")
        async def chat_stream(request: ChatRequest):
            """Send a message to the agent and get streaming response for better perceived performance"""
            
            async def stream_response() -> AsyncGenerator[str, None]:
                """Stream the chat response in chunks"""
                try:
                    # Basic input validation
                    if not request.message.strip():
                        yield f"data: {json.dumps({'error': 'Message cannot be empty', 'status': 'error'})}\n\n"
                        return
                    
                    # Send initial status
                    yield f"data: {json.dumps({'status': 'processing', 'message': 'Processing your request...'})}\n\n"
                    
                    # Get the process chat message use case
                    process_chat_use_case = get_container().get_process_chat_message_use_case()
                    
                    # Execute the use case with all the business logic
                    result = await process_chat_use_case.execute(
                        message=request.message,
                        conversation_id=request.conversation_id,
                        account_alias=request.account_alias
                    )
                    
                    # Stream the response in chunks for better UX
                    response_text = result.response
                    chunk_size = 50  # Characters per chunk
                    
                    for i in range(0, len(response_text), chunk_size):
                        chunk = response_text[i:i + chunk_size]
                        chunk_data = {
                            'type': 'content',
                            'content': chunk,
                            'timestamp': result.timestamp.isoformat(),
                            'conversation_id': result.conversation_id,
                            'message_id': result.message_id
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                        
                        # Small delay to make streaming visible
                        await asyncio.sleep(0.05)
                    
                    # Send completion status
                    completion_data = {
                        'type': 'complete',
                        'status': 'success',
                        'conversation_id': result.conversation_id,
                        'message_id': result.message_id,
                        'timestamp': result.timestamp.isoformat()
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
                    
                except Exception as e:
                    # Import domain exceptions here to avoid circular imports
                    from core.domain.exceptions import (
                        AccountValidationError, 
                        ConversationNotFoundError, 
                        MessageProcessingError,
                        DomainException
                    )
                    
                    logger = get_logger(__name__)
                    
                    # Handle specific domain exceptions with appropriate HTTP status codes
                    error_message = str(e)
                    if isinstance(e, AccountValidationError):
                        logger.warning(f"Account validation error: {e}")
                        error_type = "account_validation_error"
                    elif isinstance(e, ConversationNotFoundError):
                        logger.warning(f"Conversation not found: {e}")
                        error_type = "conversation_not_found"
                    elif isinstance(e, MessageProcessingError):
                        logger.error(f"Message processing error: {e}")
                        error_type = "message_processing_error"
                    elif isinstance(e, DomainException):
                        logger.error(f"Domain error: {e}")
                        error_type = "domain_error"
                    else:
                        # Unexpected errors
                        logger.error(f"Unexpected error in chat stream endpoint: {e}")
                        error_type = "unexpected_error"
                        error_message = "Failed to process chat request"
                    
                    error_data = {
                        'type': 'error',
                        'error_type': error_type,
                        'error_message': error_message,
                        'status': 'error',
                        'timestamp': datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
            
            return StreamingResponse(
                stream_response(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )

        @self._app.post("/api/chat-async", response_model=TaskCreatedResponse, status_code=202, summary="Chat with the agent asynchronously")
        @with_error_handling("process async chat")
        async def chat_async(request: ChatRequest):
            """Send a message to the agent and execute in background"""
            # Execute the task asynchronously (returns immediately)
            task_id = await self._task_service.execute_task_async(request.message)
            
            return TaskCreatedResponse(
                task_id=task_id,
                status="pending",
                message="Task created and executing in background"
            )

        @self._app.post("/api/tasks", response_model=TaskCreatedResponse, status_code=202, summary="Execute a task asynchronously")
        @with_error_handling("create task")
        async def execute_task(request: TaskRequest):
            """Execute a task asynchronously and return task ID immediately"""
            # Execute task asynchronously (returns immediately)
            task_id = await self._task_service.execute_task_async(request.description)
            
            return TaskCreatedResponse(
                task_id=task_id,
                status="pending",
                message="Task created and executing in background"
            )

        @self._app.get("/api/tasks", response_model=List[TaskResponse], summary="List tasks")
        @with_error_handling("list tasks")
        async def list_tasks(limit: int = 10, offset: int = 0):
            """List recent tasks"""
            tasks = await self._task_service.get_tasks(limit=limit, offset=offset)
            return [self._to_task_response(task) for task in tasks]

        @self._app.get("/api/tasks/{task_id}", response_model=TaskResponse, summary="Get task by ID")
        @with_error_handling("get task")
        async def get_task(task_id: str):
            """Get a specific task by ID"""
            task = await self._task_service.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            return self._to_task_response(task)

        @self._app.get("/api/aws/account-info", response_model=AWSAccountInfo, summary="Get AWS account information")
        @with_error_handling("get AWS account info")
        async def get_aws_account_info():
            """Get AWS account information"""
            account_info = await self._aws_service.get_account_info()
            
            return AWSAccountInfo(
                account_id=account_info.account_id,
                region=account_info.region,
                user_arn=account_info.user_arn
            )

        @self._app.post("/api/aws/analyze", response_model=TaskCreatedResponse, status_code=202, summary="Analyze AWS infrastructure asynchronously")
        @with_error_handling("start AWS analysis")
        async def analyze_aws():
            """Perform AWS infrastructure analysis in background"""
            description = "Analyze AWS infrastructure and provide recommendations"
            task_id = await self._task_service.execute_task_async(description)
            
            return TaskCreatedResponse(
                task_id=task_id,
                status="pending",
                message="AWS analysis started in background"
            )

        @self._app.post("/api/aws/security-audit", response_model=TaskCreatedResponse, status_code=202, summary="Perform security audit asynchronously")
        @with_error_handling("start security audit")
        async def security_audit():
            """Perform AWS security audit in background"""
            description = "Perform comprehensive security audit of AWS resources"
            task_id = await self._task_service.execute_task_async(description)
            
            return TaskCreatedResponse(
                task_id=task_id,
                status="pending",
                message="Security audit started in background"
            )

        @self._app.post("/api/aws/cost-optimization", response_model=TaskCreatedResponse, status_code=202, summary="Analyze costs and optimize asynchronously")
        @with_error_handling("start cost optimization")
        async def cost_optimization():
            """Perform AWS cost analysis and optimization in background"""
            description = "Analyze AWS costs and provide optimization recommendations"
            task_id = await self._task_service.execute_task_async(description)
            
            return TaskCreatedResponse(
                task_id=task_id,
                status="pending",
                message="Cost optimization analysis started in background"
            )

        logger = get_logger(__name__)
        logger.info("registering_multi_account_endpoints | starting_registration")
        
        @self._app.post("/api/aws/accounts", response_model=AWSAccountResponse, status_code=201, summary="Register AWS account")
        @with_error_handling("register AWS account")
        async def register_aws_account(request: AWSAccountRequest):
            """Register a new AWS account"""
            credentials = AWSCredentials(
                access_key_id=request.credentials.access_key_id,
                secret_access_key=request.credentials.secret_access_key,
                session_token=request.credentials.session_token,
                region=request.credentials.region,
                profile=request.credentials.profile
            )
            
            account = await self._aws_account_service.register_account(
                alias=request.alias,
                credentials=credentials,
                description=request.description,
                set_as_default=request.set_as_default
            )
            
            return self._to_aws_account_response(account)

        @self._app.get("/api/aws/accounts", response_model=List[AWSAccountResponse], summary="List AWS accounts")
        @with_error_handling("list AWS accounts")
        async def list_aws_accounts():
            """List all registered AWS accounts"""
            accounts = await self._aws_account_service.list_accounts()
            return [self._to_aws_account_response(account) for account in accounts]

        @self._app.get("/api/aws/accounts/{alias}", response_model=AWSAccountResponse, summary="Get AWS account")
        @with_error_handling("get AWS account")
        async def get_aws_account(alias: str):
            """Get a specific AWS account by alias"""
            account = await self._aws_account_service.get_account(alias)
            if not account:
                raise HTTPException(status_code=404, detail=f"AWS account '{alias}' not found")
            
            return self._to_aws_account_response(account)

        @self._app.put("/api/aws/accounts/{alias}/credentials", response_model=AWSAccountResponse, summary="Update AWS account credentials")
        @with_error_handling("update AWS account credentials")
        async def update_aws_account_credentials(alias: str, request: AWSAccountUpdateRequest):
            """Update credentials for an AWS account"""
            # Convert Pydantic model to domain credentials
            credentials = AWSCredentials(
                access_key_id=request.credentials.access_key_id,
                secret_access_key=request.credentials.secret_access_key,
                session_token=request.credentials.session_token,
                region=request.credentials.region,
                profile=request.credentials.profile
            )
            
            account = await self._aws_account_service.update_account_credentials(alias, credentials)
            
            return self._to_aws_account_response(account)

        @self._app.delete("/api/aws/accounts/{alias}", status_code=204, summary="Delete AWS account")
        @with_error_handling("delete AWS account")
        async def delete_aws_account(alias: str):
            """Delete an AWS account"""
            success = await self._aws_account_service.delete_account(alias)
            if not success:
                raise HTTPException(status_code=404, detail=f"AWS account '{alias}' not found")

        @self._app.get("/api/aws/accounts/default", response_model=AWSAccountResponse, summary="Get default AWS account")
        @with_error_handling("get default AWS account")
        async def get_default_aws_account():
            """Get the default AWS account"""
            account = await self._aws_account_service.get_default_account()
            if not account:
                raise HTTPException(status_code=404, detail="No default AWS account set")
            
            return self._to_aws_account_response(account)

        @self._app.post("/api/aws/accounts/{alias}/default", status_code=204, summary="Set default AWS account")
        @with_error_handling("set default AWS account")
        async def set_default_aws_account(alias: str):
            """Set an AWS account as the default"""
            success = await self._aws_account_service.set_default_account(alias)
            if not success:
                raise HTTPException(status_code=404, detail=f"AWS account '{alias}' not found")

        @self._app.post("/api/aws/active-account", status_code=204, summary="Set active AWS account")
        @with_error_handling("set active AWS account")
        async def set_active_aws_account(request: SetActiveAccountRequest):
            """Set the active AWS account for the current session"""
            await self._aws_service.set_active_account(request.account_alias)

        @self._app.delete("/api/aws/active-account", status_code=204, summary="Clear active AWS account")
        @with_error_handling("clear active AWS account")
        async def clear_active_aws_account():
            """Clear the active AWS account for the current session"""
            await self._aws_service.clear_active_account()

        @self._app.get("/api/aws/active-account", response_model=ActiveAccountResponse, summary="Get active AWS account")
        @with_error_handling("get active AWS account")
        async def get_active_aws_account():
            """Get the currently active AWS account alias"""
            active_alias = self._aws_service.get_active_account_alias()
            return ActiveAccountResponse(account_alias=active_alias)

        @self._app.post("/api/aws/accounts/{alias}/validate", response_model=ValidationResponse, summary="Validate AWS account credentials")
        @with_error_handling("validate AWS account credentials")
        async def validate_aws_account_credentials(alias: str):
            """Validate the credentials for an AWS account"""
            is_valid = await self._aws_account_service.validate_account_credentials(alias)
            return ValidationResponse(valid=is_valid)

        logger.info("multi_account_endpoints_registered | endpoints=<register,list,get,update,delete,default,set_default,validate>")

        @self._app.get("/api/performance/chat", summary="Get chat performance statistics")
        @with_error_handling("get chat performance stats")
        async def get_chat_performance_stats():
            """Get performance statistics for chat operations"""
            process_chat_use_case = get_container().get_process_chat_message_use_case()
            stats = process_chat_use_case.get_performance_stats()
            return {
                "chat_performance": stats,
                "timestamp": datetime.now().isoformat()
            }

        @self._app.get("/api/conversations", response_model=List[ConversationResponse], summary="List conversations")
        @with_error_handling("list conversations")
        async def list_conversations(limit: int = 50, offset: int = 0):
            """Get list of conversations with pagination"""
            conversations = await self._chat_service.list_conversations(limit=limit, offset=offset)
            return [ConversationResponse(**conv.to_dict()) for conv in conversations]

        @self._app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse, summary="Get conversation")
        @with_error_handling("get conversation")
        async def get_conversation(conversation_id: str):
            """Get specific conversation"""
            conversation = await self._chat_service.get_conversation(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            return ConversationResponse(**conversation.to_dict())

        @self._app.get("/api/conversations/{conversation_id}/messages", response_model=List[MessageResponse], summary="Get conversation messages")
        @with_error_handling("get conversation messages")
        async def get_conversation_messages(conversation_id: str, limit: int = 100, offset: int = 0):
            """Get messages for a conversation"""
            messages = await self._chat_service.get_conversation_messages(conversation_id, limit=limit, offset=offset)
            return [MessageResponse(**msg.to_dict()) for msg in messages]

        @self._app.post("/api/conversations", response_model=ConversationResponse, status_code=201, summary="Create conversation")
        @with_error_handling("create conversation")
        async def create_conversation(title: str = "New Conversation"):
            """Create a new conversation"""
            conversation = await self._chat_service.create_conversation(title)
            return ConversationResponse(**conversation.to_dict())

        @self._app.put("/api/conversations/{conversation_id}", response_model=ConversationResponse, summary="Update conversation")
        @with_error_handling("update conversation")
        async def update_conversation(conversation_id: str, title: str):
            """Update conversation title"""
            conversation = await self._chat_service.update_conversation_title(conversation_id, title)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            return ConversationResponse(**conversation.to_dict())

        @self._app.delete("/api/conversations/{conversation_id}", status_code=204, summary="Delete conversation")
        @with_error_handling("delete conversation")
        async def delete_conversation(conversation_id: str):
            """Delete conversation and all messages"""
            success = await self._chat_service.delete_conversation(conversation_id)
            if not success:
                raise HTTPException(status_code=404, detail="Conversation not found")
            return Response(status_code=204)

    @property
    def app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self._app