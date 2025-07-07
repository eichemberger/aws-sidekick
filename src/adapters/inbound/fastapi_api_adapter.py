from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, AsyncGenerator
import uuid
from datetime import datetime
import pathlib
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
        
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=config.api.cors_origins,
            allow_credentials=config.api.cors_allow_credentials,
            allow_methods=config.api.cors_allow_methods,
            allow_headers=config.api.cors_allow_headers,
        )
        
        self._setup_static_files()
        
        logger.info("registering_api_routes | starting_route_setup")
        self._setup_routes()
        logger.info("api_routes_registered | setup_complete")

    def _setup_static_files(self):
        """Setup static file serving for the Vue.js client"""
        current_dir = pathlib.Path(__file__).parent.parent.parent.parent
        client_dist_dir = current_dir / "client" / "dist"
        
        if client_dist_dir.exists():
            self._app.mount("/assets", StaticFiles(directory=str(client_dist_dir / "assets")), name="assets")
            
            for static_dir in ["css", "js", "img", "fonts"]:
                static_path = client_dist_dir / static_dir
                if static_path.exists():
                    self._app.mount(f"/{static_dir}", StaticFiles(directory=str(static_path)), name=static_dir)

    def _setup_routes(self):
        """Setup API routes"""
        
        @self._app.get("/api", summary="Health check")
        async def health_check():
            return {
                "message": "AWS Cloud Engineer Agent API",
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            }

        @self._app.get("/api/debug/tasks", summary="Debug tasks endpoint")
        async def debug_tasks():
            """Debug endpoint to test task retrieval"""
            try:
                start_time = datetime.now()
                tasks = await self._task_service.get_tasks(limit=5, offset=0)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                return {
                    "status": "success",
                    "task_count": len(tasks),
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "tasks": [
                        {
                            "id": task.id,
                            "description": task.description[:50] + "..." if len(task.description) > 50 else task.description,
                            "status": task.status.value,
                            "created_at": task.created_at.isoformat()
                        }
                        for task in tasks
                    ]
                }
            except Exception as e:
                return {
                    "status": "error", 
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

        @self._app.post("/api/chat", response_model=ChatResponse, summary="Chat with the agent")
        async def chat(request: ChatRequest):
            """Send a message to the agent and get immediate response with persistence"""
            try:
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
                if isinstance(e, AccountValidationError):
                    logger.warning(f"Account validation error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
                elif isinstance(e, ConversationNotFoundError):
                    logger.warning(f"Conversation not found: {e}")
                    raise HTTPException(status_code=404, detail=str(e))
                elif isinstance(e, MessageProcessingError):
                    logger.error(f"Message processing error: {e}")
                    raise HTTPException(status_code=422, detail=str(e))
                elif isinstance(e, DomainException):
                    logger.error(f"Domain error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
                else:
                    # Unexpected errors
                    logger.error(f"Unexpected error in chat endpoint: {e}")
                    raise HTTPException(status_code=500, detail="Failed to process chat request")

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
        async def chat_async(request: ChatRequest):
            """Send a message to the agent and execute in background"""
            try:
                # Execute the task asynchronously (returns immediately)
                task_id = await self._task_service.execute_task_async(request.message)
                
                return TaskCreatedResponse(
                    task_id=task_id,
                    status="pending",
                    message="Task created and executing in background"
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

        @self._app.post("/api/tasks", response_model=TaskCreatedResponse, status_code=202, summary="Execute a task asynchronously")
        async def execute_task(request: TaskRequest):
            """Execute a task asynchronously and return task ID immediately"""
            try:
                # Execute task asynchronously (returns immediately)
                task_id = await self._task_service.execute_task_async(request.description)
                
                return TaskCreatedResponse(
                    task_id=task_id,
                    status="pending",
                    message="Task created and executing in background"
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

        @self._app.get("/api/tasks", response_model=List[TaskResponse], summary="List tasks")
        async def list_tasks(limit: int = 10, offset: int = 0):
            """List recent tasks"""
            try:
                tasks = await self._task_service.get_tasks(limit=limit, offset=offset)
                
                return [
                    TaskResponse(
                        task_id=task.id,
                        description=task.description,
                        status=task.status.value,
                        result=task.result,
                        error_message=task.error_message,
                        created_at=task.created_at,
                        completed_at=task.completed_at,
                        duration=task.duration()
                    )
                    for task in tasks
                ]
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving tasks: {str(e)}")

        @self._app.get("/api/tasks/{task_id}", response_model=TaskResponse, summary="Get task by ID")
        async def get_task(task_id: str):
            """Get a specific task by ID"""
            try:
                task = await self._task_service.get_task(task_id)
                
                if not task:
                    raise HTTPException(status_code=404, detail="Task not found")
                
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
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving task: {str(e)}")

        @self._app.get("/api/aws/account-info", response_model=AWSAccountInfo, summary="Get AWS account information")
        async def get_aws_account_info():
            """Get AWS account information"""
            try:
                account_info = await self._aws_service.get_account_info()
                
                return AWSAccountInfo(
                    account_id=account_info.account_id,
                    region=account_info.region,
                    user_arn=account_info.user_arn
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving AWS account info: {str(e)}")

        @self._app.post("/api/aws/analyze", response_model=TaskCreatedResponse, status_code=202, summary="Analyze AWS infrastructure asynchronously")
        async def analyze_aws():
            """Perform AWS infrastructure analysis in background"""
            try:
                description = "Analyze AWS infrastructure and provide recommendations"
                task_id = await self._task_service.execute_task_async(description)
                
                return TaskCreatedResponse(
                    task_id=task_id,
                    status="pending",
                    message="AWS analysis started in background"
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error starting AWS analysis: {str(e)}")

        @self._app.post("/api/aws/security-audit", response_model=TaskCreatedResponse, status_code=202, summary="Perform security audit asynchronously")
        async def security_audit():
            """Perform AWS security audit in background"""
            try:
                description = "Perform comprehensive security audit of AWS resources"
                task_id = await self._task_service.execute_task_async(description)
                
                return TaskCreatedResponse(
                    task_id=task_id,
                    status="pending",
                    message="Security audit started in background"
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error starting security audit: {str(e)}")

        @self._app.post("/api/aws/cost-optimization", response_model=TaskCreatedResponse, status_code=202, summary="Analyze costs and optimize asynchronously")
        async def cost_optimization():
            """Perform AWS cost analysis and optimization in background"""
            try:
                description = "Analyze AWS costs and provide optimization recommendations"
                task_id = await self._task_service.execute_task_async(description)
                
                return TaskCreatedResponse(
                    task_id=task_id,
                    status="pending",
                    message="Cost optimization analysis started in background"
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error starting cost optimization: {str(e)}")

        logger = get_logger(__name__)
        logger.info("registering_multi_account_endpoints | starting_registration")
        
        @self._app.post("/api/aws/accounts", response_model=AWSAccountResponse, status_code=201, summary="Register AWS account")
        async def register_aws_account(request: AWSAccountRequest):
            """Register a new AWS account"""
            try:
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
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error registering AWS account: {e}")
                raise HTTPException(status_code=500, detail="Failed to register AWS account")

        @self._app.get("/api/aws/accounts", response_model=List[AWSAccountResponse], summary="List AWS accounts")
        async def list_aws_accounts():
            """List all registered AWS accounts"""
            try:
                accounts = await self._aws_account_service.list_accounts()
                return [
                    AWSAccountResponse(
                        alias=account.alias,
                        description=account.description,
                        region=account.region,
                        account_id=account.account_id,
                        uses_profile=account.uses_profile,
                        is_default=account.is_default,
                        created_at=account.created_at,
                        updated_at=account.updated_at
                    )
                    for account in accounts
                ]
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error listing AWS accounts: {e}")
                raise HTTPException(status_code=500, detail="Failed to list AWS accounts")

        @self._app.get("/api/aws/accounts/{alias}", response_model=AWSAccountResponse, summary="Get AWS account")
        async def get_aws_account(alias: str):
            """Get a specific AWS account by alias"""
            try:
                account = await self._aws_account_service.get_account(alias)
                if not account:
                    raise HTTPException(status_code=404, detail=f"AWS account '{alias}' not found")
                
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
            except HTTPException:
                raise
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error getting AWS account: {e}")
                raise HTTPException(status_code=500, detail="Failed to get AWS account")

        @self._app.put("/api/aws/accounts/{alias}/credentials", response_model=AWSAccountResponse, summary="Update AWS account credentials")
        async def update_aws_account_credentials(alias: str, request: AWSAccountUpdateRequest):
            """Update credentials for an AWS account"""
            try:
                # Convert Pydantic model to domain credentials
                credentials = AWSCredentials(
                    access_key_id=request.credentials.access_key_id,
                    secret_access_key=request.credentials.secret_access_key,
                    session_token=request.credentials.session_token,
                    region=request.credentials.region,
                    profile=request.credentials.profile
                )
                
                account = await self._aws_account_service.update_account_credentials(alias, credentials)
                
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
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error updating AWS account credentials: {e}")
                raise HTTPException(status_code=500, detail="Failed to update AWS account credentials")

        @self._app.delete("/api/aws/accounts/{alias}", status_code=204, summary="Delete AWS account")
        async def delete_aws_account(alias: str):
            """Delete an AWS account"""
            try:
                success = await self._aws_account_service.delete_account(alias)
                if not success:
                    raise HTTPException(status_code=404, detail=f"AWS account '{alias}' not found")
            except HTTPException:
                raise
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error deleting AWS account: {e}")
                raise HTTPException(status_code=500, detail="Failed to delete AWS account")

        @self._app.get("/api/aws/accounts/default", response_model=AWSAccountResponse, summary="Get default AWS account")
        async def get_default_aws_account():
            """Get the default AWS account"""
            try:
                account = await self._aws_account_service.get_default_account()
                if not account:
                    raise HTTPException(status_code=404, detail="No default AWS account set")
                
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
            except HTTPException:
                raise
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error getting default AWS account: {e}")
                raise HTTPException(status_code=500, detail="Failed to get default AWS account")

        @self._app.post("/api/aws/accounts/{alias}/default", status_code=204, summary="Set default AWS account")
        async def set_default_aws_account(alias: str):
            """Set an AWS account as the default"""
            try:
                success = await self._aws_account_service.set_default_account(alias)
                if not success:
                    raise HTTPException(status_code=404, detail=f"AWS account '{alias}' not found")
            except HTTPException:
                raise
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error setting default AWS account: {e}")
                raise HTTPException(status_code=500, detail="Failed to set default AWS account")

        @self._app.post("/api/aws/active-account", status_code=204, summary="Set active AWS account")
        async def set_active_aws_account(request: SetActiveAccountRequest):
            """Set the active AWS account for the current session"""
            try:
                await self._aws_service.set_active_account(request.account_alias)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error setting active AWS account: {e}")
                raise HTTPException(status_code=500, detail="Failed to set active AWS account")

        @self._app.delete("/api/aws/active-account", status_code=204, summary="Clear active AWS account")
        async def clear_active_aws_account():
            """Clear the active AWS account for the current session"""
            try:
                await self._aws_service.clear_active_account()
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error clearing active AWS account: {e}")
                raise HTTPException(status_code=500, detail="Failed to clear active AWS account")

        @self._app.get("/api/aws/active-account", response_model=ActiveAccountResponse, summary="Get active AWS account")
        async def get_active_aws_account():
            """Get the currently active AWS account alias"""
            try:
                active_alias = self._aws_service.get_active_account_alias()
                return ActiveAccountResponse(account_alias=active_alias)
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error getting active AWS account: {e}")
                raise HTTPException(status_code=500, detail="Failed to get active AWS account")

        @self._app.post("/api/aws/accounts/{alias}/validate", response_model=ValidationResponse, summary="Validate AWS account credentials")
        async def validate_aws_account_credentials(alias: str):
            """Validate the credentials for an AWS account"""
            try:
                is_valid = await self._aws_account_service.validate_account_credentials(alias)
                return ValidationResponse(valid=is_valid)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error validating AWS account credentials: {e}")
                raise HTTPException(status_code=500, detail="Failed to validate AWS account credentials")

        logger.info("multi_account_endpoints_registered | endpoints=<register,list,get,update,delete,default,set_default,validate>")

        @self._app.get("/debug/credentials-status")
        async def debug_credentials_status():
            """Debug endpoint to check credential storage status"""
            try:
                import os
                from infrastructure.credential_manager import get_credential_manager
                credential_manager = get_credential_manager()
                
                accounts_with_creds = await credential_manager.list_accounts_with_credentials()
                
                active_alias = self._aws_service.get_active_account_alias()
                
                env_vars = {
                    "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", "NOT_SET"),
                    "AWS_SECRET_ACCESS_KEY": "***" if os.environ.get("AWS_SECRET_ACCESS_KEY") else "NOT_SET",
                    "AWS_SESSION_TOKEN": "***" if os.environ.get("AWS_SESSION_TOKEN") else "NOT_SET",
                    "AWS_PROFILE": os.environ.get("AWS_PROFILE", "NOT_SET"),
                    "AWS_DEFAULT_REGION": os.environ.get("AWS_DEFAULT_REGION", "NOT_SET")
                }
                
                debug_info = {
                    "active_account_alias": active_alias,
                    "accounts_with_credentials_in_memory": accounts_with_creds,
                    "total_accounts_with_credentials": len(accounts_with_creds),
                    "current_environment_variables": env_vars
                }
                
                if active_alias:
                    has_creds = await credential_manager.has_credentials(active_alias)
                    debug_info["active_account_has_credentials"] = has_creds
                
                return debug_info
                
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error in debug credentials status: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self._app.get("/debug/performance-stats")
        async def debug_performance_stats():
            """Debug endpoint to check chat processing performance statistics"""
            try:
                process_chat_use_case = get_container().get_process_chat_message_use_case()
                
                stats = process_chat_use_case.get_performance_stats()
                
                return {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "performance_stats": stats,
                    "optimization_notes": {
                        "parallel_execution": "User message persistence and agent execution run in parallel",
                        "account_caching": "AWS account validation results cached for 5 minutes",
                        "conversation_caching": "Conversation metadata cached in memory",
                        "response_timeouts": "Agent processing has 30-second timeout for resource management",
                        "fire_and_forget": "Agent response persistence runs asynchronously after response sent"
                    }
                }
                
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error in debug performance stats: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self._app.post("/debug/clear-caches", status_code=204)
        async def debug_clear_caches():
            """Debug endpoint to clear performance caches"""
            try:
                process_chat_use_case = get_container().get_process_chat_message_use_case()
                
                process_chat_use_case.clear_caches()
                
                logger = get_logger(__name__)
                logger.info("Performance caches cleared via debug endpoint")
                
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error clearing performance caches: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self._app.get("/api/conversations", response_model=List[ConversationResponse], summary="List conversations")
        async def list_conversations(limit: int = 50, offset: int = 0):
            """Get list of conversations with pagination"""
            try:
                conversations = await self._chat_service.list_conversations(limit=limit, offset=offset)
                return [ConversationResponse(**conv.to_dict()) for conv in conversations]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error fetching conversations: {str(e)}")

        @self._app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse, summary="Get conversation")
        async def get_conversation(conversation_id: str):
            """Get specific conversation"""
            try:
                conversation = await self._chat_service.get_conversation(conversation_id)
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                return ConversationResponse(**conversation.to_dict())
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error fetching conversation: {str(e)}")

        @self._app.get("/api/conversations/{conversation_id}/messages", response_model=List[MessageResponse], summary="Get conversation messages")
        async def get_conversation_messages(conversation_id: str, limit: int = 100, offset: int = 0):
            """Get messages for a conversation"""
            try:
                messages = await self._chat_service.get_conversation_messages(conversation_id, limit=limit, offset=offset)
                return [MessageResponse(**msg.to_dict()) for msg in messages]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

        @self._app.post("/api/conversations", response_model=ConversationResponse, status_code=201, summary="Create conversation")
        async def create_conversation(title: str = "New Conversation"):
            """Create a new conversation"""
            try:
                conversation = await self._chat_service.create_conversation(title)
                return ConversationResponse(**conversation.to_dict())
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")

        @self._app.put("/api/conversations/{conversation_id}", response_model=ConversationResponse, summary="Update conversation")
        async def update_conversation(conversation_id: str, title: str):
            """Update conversation title"""
            try:
                conversation = await self._chat_service.update_conversation_title(conversation_id, title)
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                return ConversationResponse(**conversation.to_dict())
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating conversation: {str(e)}")

        @self._app.delete("/api/conversations/{conversation_id}", status_code=204, summary="Delete conversation")
        async def delete_conversation(conversation_id: str):
            """Delete conversation and all messages"""
            try:
                success = await self._chat_service.delete_conversation(conversation_id)
                if not success:
                    raise HTTPException(status_code=404, detail="Conversation not found")
                return Response(status_code=204)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

        @self._app.get("/{path:path}")
        async def serve_spa(path: str):
            """Serve the Vue.js SPA for all non-API routes"""
            current_dir = pathlib.Path(__file__).parent.parent.parent.parent
            client_dist_dir = current_dir / "client" / "dist"
            index_file = client_dist_dir / "index.html"
            
            if not client_dist_dir.exists():
                return {
                    "message": "Vue.js client not built",
                    "instructions": "Run 'cd client && npm run build' to build the client"
                }
            
            if not index_file.exists():
                return {
                    "message": "Vue.js build incomplete",
                    "instructions": "Run 'cd client && npm run build' to build the client"
                }
            
            return FileResponse(str(index_file))


    @property
    def app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self._app 