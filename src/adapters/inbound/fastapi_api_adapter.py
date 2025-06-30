from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime
import re
import ast
import pathlib

from core.ports.inbound.task_service_port import TaskServicePort
from core.ports.inbound.aws_service_port import AWSServicePort
from core.ports.inbound.chat_service_port import ChatServicePort
# Removed TaskType import - simplified to just background task execution
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
    message: str = Field(..., description="Chat message to send to the agent")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation to continue")


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime
    conversation_id: str
    message_id: str


class ConversationResponse(BaseModel):
    id: str
    title: str
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


class FastAPIAdapter:
    """FastAPI adapter for the AWS Cloud Engineer Agent API"""

    def __init__(
        self,
        task_service: TaskServicePort,
        aws_service: AWSServicePort,
        chat_service: ChatServicePort
    ):
        self._task_service = task_service
        self._aws_service = aws_service
        self._chat_service = chat_service
        
        # Get agent repository from container
        container = get_container()
        self._agent_repository = container.get_agent_repository_adapter()
        
        # Get configuration
        config = get_config()
        
        self._app = FastAPI(
            title=config.api.title,
            description=config.api.description,
            version=config.api.version,
            docs_url=config.api.docs_url,
            redoc_url=config.api.redoc_url
        )
        
        # Add CORS middleware
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=config.api.cors_origins,
            allow_credentials=config.api.cors_allow_credentials,
            allow_methods=config.api.cors_allow_methods,
            allow_headers=config.api.cors_allow_headers,
        )
        
        # Setup static file serving for Vue.js client
        self._setup_static_files()
        self._setup_routes()

    def _setup_static_files(self):
        """Setup static file serving for the Vue.js client"""
        # Get the client build directory path
        current_dir = pathlib.Path(__file__).parent.parent.parent.parent
        client_dist_dir = current_dir / "client" / "dist"
        
        # Check if the build directory exists
        if client_dist_dir.exists():
            # Mount static files (JS, CSS, images, etc.)
            self._app.mount("/assets", StaticFiles(directory=str(client_dist_dir / "assets")), name="assets")
            
            # Serve other static files if they exist
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
                # Get or create conversation
                if request.conversation_id:
                    conversation = await self._chat_service.get_conversation(request.conversation_id)
                    if not conversation:
                        raise HTTPException(status_code=404, detail="Conversation not found")
                else:
                    # For new conversations, create one with a title based on the message
                    conversation = await self._chat_service.create_conversation_from_message(request.message)
                
                # Add user message to conversation
                user_message = await self._chat_service.add_message_to_conversation(
                    conversation.id, 'user', request.message
                )
                
                # Execute using the dedicated chat method for better responsiveness
                result = await self._agent_repository.execute_chat_prompt(request.message)
                
                # Clean the response
                cleaned_response = self._clean_response(result)
                
                # Add assistant response to conversation
                assistant_message = await self._chat_service.add_message_to_conversation(
                    conversation.id, 'assistant', cleaned_response
                )
                
                return ChatResponse(
                    response=cleaned_response,
                    timestamp=assistant_message.timestamp,
                    conversation_id=conversation.id,
                    message_id=assistant_message.id
                )
                
            except Exception as e:
                # Still try to persist error message if we have a conversation
                error_msg = f"❌ I'm having trouble processing your request: {str(e)}. Please try again."
                
                try:
                    if 'conversation' in locals():
                        await self._chat_service.add_message_to_conversation(
                            conversation.id, 'assistant', error_msg
                        )
                except Exception:
                    pass  # Don't fail the entire request if we can't persist the error
                
                return ChatResponse(
                    response=error_msg,
                    timestamp=datetime.now(),
                    conversation_id=getattr(locals().get('conversation'), 'id', 'unknown'),
                    message_id=str(uuid.uuid4())
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
                        result=self._clean_response(task.result) if task.result else None,
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
                    result=self._clean_response(task.result) if task.result else None,
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

        # AWS Credentials Management Endpoints
        @self._app.post("/api/aws/credentials", response_model=AWSCredentialsResponse, summary="Set AWS credentials")
        async def set_aws_credentials(request: AWSCredentialsRequest):
            """Set AWS credentials for the current session"""
            try:
                # Create credentials object
                credentials = AWSCredentials(
                    access_key_id=request.access_key_id,
                    secret_access_key=request.secret_access_key,
                    session_token=request.session_token,
                    region=request.region,
                    profile=request.profile
                )
                
                # Validate credentials
                if not credentials.is_valid():
                    raise HTTPException(
                        status_code=400, 
                        detail="Invalid credentials: Either provide access_key_id and secret_access_key, or a profile name"
                    )
                
                # Test credentials by attempting to validate them
                is_valid = await self._aws_service.validate_credentials(credentials)
                if not is_valid:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid AWS credentials: Unable to authenticate with AWS"
                    )
                
                # Set credentials in service
                await self._aws_service.set_credentials(credentials)
                
                return AWSCredentialsResponse(
                    region=credentials.region,
                    profile=credentials.profile,
                    has_access_key=credentials.uses_keys(),
                    has_session_token=credentials.session_token is not None,
                    is_valid=True
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error setting AWS credentials: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to set credentials: {str(e)}")

        @self._app.get("/api/aws/credentials", response_model=AWSCredentialsResponse, summary="Get current AWS credentials info")
        async def get_aws_credentials():
            """Get information about current AWS credentials (without exposing sensitive data)"""
            try:
                credentials = self._aws_service.get_current_credentials()
                if not credentials:
                    raise HTTPException(status_code=404, detail="No credentials configured")
                
                # Test if credentials are still valid
                is_valid = await self._aws_service.validate_credentials(credentials)
                
                return AWSCredentialsResponse(
                    region=credentials.region,
                    profile=credentials.profile,
                    has_access_key=credentials.uses_keys(),
                    has_session_token=credentials.session_token is not None,
                    is_valid=is_valid
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error getting AWS credentials info: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self._app.post("/api/aws/credentials/validate", summary="Validate AWS credentials")
        async def validate_aws_credentials(request: AWSCredentialsRequest):
            """Validate AWS credentials without setting them"""
            try:
                credentials = AWSCredentials(
                    access_key_id=request.access_key_id,
                    secret_access_key=request.secret_access_key,
                    session_token=request.session_token,
                    region=request.region,
                    profile=request.profile
                )
                
                if not credentials.is_valid():
                    return {"valid": False, "error": "Invalid credential format"}
                
                is_valid = await self._aws_service.validate_credentials(credentials)
                
                if is_valid:
                    # Get account info to provide feedback
                    try:
                        account_info = await self._aws_service.get_account_info(credentials)
                        return {
                            "valid": True,
                            "account_id": account_info.account_id,
                            "region": credentials.region,
                            "user_arn": account_info.user_arn
                        }
                    except Exception:
                        return {"valid": True}
                else:
                    return {"valid": False, "error": "Unable to authenticate with AWS"}
                    
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error validating AWS credentials: {e}")
                return {"valid": False, "error": str(e)}

        @self._app.delete("/api/aws/credentials", status_code=204, summary="Clear AWS credentials")
        async def clear_aws_credentials():
            """Clear current AWS credentials"""
            try:
                await self._aws_service.clear_credentials()
                return Response(status_code=204)
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error clearing AWS credentials: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Chat/Conversation Management Endpoints
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
            # Get the client build directory path
            current_dir = pathlib.Path(__file__).parent.parent.parent.parent
            client_dist_dir = current_dir / "client" / "dist"
            index_file = client_dist_dir / "index.html"
            
            # If the build directory doesn't exist, return a helpful message
            if not client_dist_dir.exists():
                return {
                    "message": "Vue.js client not built",
                    "instructions": "Run 'cd client && npm run build' to build the client"
                }
            
            # If index.html doesn't exist, return error
            if not index_file.exists():
                return {
                    "message": "Vue.js build incomplete",
                    "instructions": "Run 'cd client && npm run build' to build the client"
                }
            
            # Serve the index.html file for SPA routing
            return FileResponse(str(index_file))

    # Removed _classify_user_input method - simplified task system

    def _clean_response(self, response):
        """Clean and format response from agent"""
        # Handle None or empty responses
        if not response:
            return "No response received from agent."
        
        # Convert to string if it's not already
        if not isinstance(response, str):
            try:
                response = str(response)
            except Exception:
                return "Error: Could not convert response to string"
        
        # Remove <thinking>...</thinking> blocks
        cleaned = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
        
        # Check if response is in structured format like {'role': 'assistant', 'content': [{'text': '...'}]}
        if "'role': 'assistant'" in cleaned and "'content'" in cleaned and "'text'" in cleaned:
            try:
                # Try to parse as Python literal
                data = ast.literal_eval(cleaned)
                if isinstance(data, dict) and 'content' in data and isinstance(data['content'], list):
                    for item in data['content']:
                        if isinstance(item, dict) and 'text' in item:
                            # Return the text content directly (preserves markdown)
                            return item['text']
            except Exception:
                # If parsing fails, try regex as fallback
                match = re.search(r"'text': '(.+?)(?:'}]|})", cleaned, re.DOTALL)
                if match:
                    # Unescape the content to preserve markdown
                    text = match.group(1)
                    text = text.replace('\\n', '\n')  # Replace escaped newlines
                    text = text.replace('\\t', '\t')  # Replace escaped tabs
                    text = text.replace("\\'", "'")   # Replace escaped single quotes
                    text = text.replace('\\"', '"')   # Replace escaped double quotes
                    return text
        
        return cleaned.strip()

    @property
    def app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self._app 