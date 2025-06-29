"""
Configuration management for the AWS Cloud Engineer Agent

This module handles all configuration settings, environment variables,
and provides validation with helpful error messages.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for the AI model"""
    provider: str = "anthropic"  # "anthropic" or "openai"
    model_id: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1000
    temperature: float = 0.7
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    
    @property
    def api_key(self) -> str:
        """Get the appropriate API key based on provider"""
        if self.provider == "anthropic":
            return self.anthropic_api_key
        elif self.provider == "openai":
            return self.openai_api_key
        else:
            return ""
    
    def validate(self) -> None:
        """Validate model configuration"""
        if self.provider not in ["anthropic", "openai"]:
            raise ValueError(
                f"MODEL_PROVIDER must be either 'anthropic' or 'openai', got: {self.provider}"
            )
        
        if self.provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when using Anthropic models. Please set it in your .env file:\n"
                "ANTHROPIC_API_KEY=your_api_key_here"
            )
        
        if self.provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when using OpenAI models. Please set it in your .env file:\n"
                "OPENAI_API_KEY=your_api_key_here"
            )
    
    def get_default_model_id(self) -> str:
        """Get default model ID based on provider"""
        if self.provider == "anthropic":
            return "claude-sonnet-4-20250514"
        elif self.provider == "openai":
            return "gpt-4o"
        else:
            return self.model_id


@dataclass(frozen=True)
class AWSConfig:
    """Configuration for AWS operations"""
    default_region: str = "us-east-1"
    profile: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    
    def validate(self) -> None:
        """Validate AWS configuration"""
        has_keys = bool(self.access_key_id and self.secret_access_key)
        has_profile = bool(self.profile)
        
        if not has_keys and not has_profile:
            raise ValueError(
                "AWS credentials are required. Please configure either:\n"
                "1. AWS access keys: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY\n"
                "2. AWS profile: AWS_PROFILE\n"
                "Set these in your .env file or environment variables."
            )
        
        if has_keys and has_profile:
            raise ValueError(
                "Cannot use both AWS access keys and profile simultaneously. "
                "Please configure either access keys OR profile, not both."
            )


@dataclass(frozen=True)
class GitHubConfig:
    """Configuration for GitHub integration"""
    personal_access_token: Optional[str] = None
    
    @property
    def is_available(self) -> bool:
        """Check if GitHub integration is available"""
        return self.personal_access_token is not None


@dataclass(frozen=True)
class MCPServerConfig:
    """Configuration for a single MCP server"""
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


@dataclass(frozen=True)
class MCPConfig:
    """Configuration for all MCP servers"""
    servers: Dict[str, MCPServerConfig] = field(default_factory=dict)
    
    @classmethod
    def default(cls) -> 'MCPConfig':
        """Get default MCP server configuration"""
        return cls(servers={
            "aws_docs": MCPServerConfig(
                command="uvx",
                args=["awslabs.aws-documentation-mcp-server@latest"]
            ),
            "aws_diagram": MCPServerConfig(
                command="uvx", 
                args=["awslabs.aws-diagram-mcp-server@latest"]
            ),
            "github": MCPServerConfig(
                command="npx",
                args=["@modelcontextprotocol/server-github"],
                env={}  # Will be populated with token if available
            ),
            "cdk": MCPServerConfig(
                command="uvx",
                args=["awslabs.cdk-mcp-server@latest"]
            ),
            "terraform": MCPServerConfig(
                command="uvx",
                args=["awslabs.terraform-mcp-server"]
            ),
            "cost_explorer": MCPServerConfig(
                command="uvx",
                args=["awslabs.cost-explorer-mcp-server"]
            ),
            "cloudwatch": MCPServerConfig(
                command="uvx",
                args=["awslabs.cloudwatch-logs-mcp-server"]
            )
        })


@dataclass(frozen=True)
class DatabaseConfig:
    """Configuration for database operations"""
    type: str = "sqlite"  # "sqlite" or "memory"
    sqlite_path: str = "data/tasks.db"
    
    def validate(self) -> None:
        """Validate database configuration"""
        if self.type not in ["sqlite", "memory"]:
            raise ValueError(
                f"DATABASE_TYPE must be either 'sqlite' or 'memory', got: {self.type}"
            )


@dataclass(frozen=True)
class APIConfig:
    """Configuration for the API server"""
    title: str = "AWS Cloud Engineer Agent API"
    description: str = "API for AWS infrastructure analysis, optimization, and security auditing"
    version: str = "1.0.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = field(default_factory=lambda: ["*"])


@dataclass(frozen=True)
class Config:
    """Main application configuration"""
    model: ModelConfig
    aws: AWSConfig
    github: GitHubConfig
    database: DatabaseConfig
    mcp: MCPConfig
    api: APIConfig
    debug: bool = False
    environment: str = "development"
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'Config':
        """Create configuration from environment variables"""
        # Load .env file if specified or if it exists
        if env_file or Path(".env").exists():
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
        
        # Model configuration
        provider = os.getenv("MODEL_PROVIDER", "anthropic").lower()
        default_model_id = "claude-sonnet-4-20250514" if provider == "anthropic" else "gpt-4o"
        
        model = ModelConfig(
            provider=provider,
            model_id=os.getenv("MODEL_ID", default_model_id),
            max_tokens=int(os.getenv("MAX_TOKENS", "1000")),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", "")
        )
        
        # AWS configuration
        aws = AWSConfig(
            default_region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            profile=os.getenv("AWS_PROFILE"),
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            session_token=os.getenv("AWS_SESSION_TOKEN")
        )
        
        # GitHub configuration
        github = GitHubConfig(
            personal_access_token=os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        )
        
        # Database configuration
        database = DatabaseConfig(
            type=os.getenv("DATABASE_TYPE", "sqlite").lower(),
            sqlite_path=os.getenv("DATABASE_SQLITE_PATH", "data/tasks.db")
        )
        
        # MCP configuration
        mcp = MCPConfig.default()
        # Create new MCP config with GitHub token if available
        if github.is_available:
            # Create a new github server config with the token
            github_server = MCPServerConfig(
                command="npx",
                args=["@modelcontextprotocol/server-github"],
                env={"GITHUB_PERSONAL_ACCESS_TOKEN": github.personal_access_token}
            )
            # Create new servers dict with the updated github config
            servers = dict(mcp.servers)
            servers["github"] = github_server
            mcp = MCPConfig(servers=servers)
        
        # API configuration
        api = APIConfig(
            title=os.getenv("API_TITLE", "AWS Cloud Engineer Agent API"),
            version=os.getenv("API_VERSION", "1.0.0"),
            cors_origins=os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
        )
        
        return cls(
            model=model,
            aws=aws,
            github=github,
            database=database,
            mcp=mcp,
            api=api,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "development")
        )
    
    def validate(self) -> None:
        """Validate all configuration settings"""
        try:
            self.model.validate()
            self.aws.validate()
            self.database.validate()
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {str(e)}")
    
    def print_status(self) -> None:
        """Print configuration status for debugging"""
        from infrastructure.logging import get_logger
        logger = get_logger(__name__)
        
        logger.info(f"environment=<{self.environment}> | debug_mode=<{self.debug}> | configuration status")
        logger.info(f"model_provider=<{self.model.provider}> | model_id=<{self.model.model_id}>")
        
        if self.model.provider == "anthropic":
            if self.model.anthropic_api_key:
                logger.info(f"ANTHROPIC_API_KEY=<...{self.model.anthropic_api_key[-4:]}> | configured")
            else:
                logger.error("ANTHROPIC_API_KEY=<missing> | not configured")
        elif self.model.provider == "openai":
            if self.model.openai_api_key:
                logger.info(f"OPENAI_API_KEY=<...{self.model.openai_api_key[-4:]}> | configured")
            else:
                logger.error("OPENAI_API_KEY=<missing> | not configured")
        
        if self.github.is_available:
            logger.info("github_integration=<available>")
        else:
            logger.warning("github_integration=<unavailable> | GITHUB_PERSONAL_ACCESS_TOKEN missing")
        
        logger.info(f"aws_region=<{self.aws.default_region}> | aws_profile=<{self.aws.profile if self.aws.profile else 'not_set'}>")
        logger.info(f"database_type=<{self.database.type}> | database_path=<{self.database.sqlite_path}>")
        logger.info(f"mcp_servers=<{len(self.mcp.servers)}> | configured")


_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = Config.from_env()
        _config.validate()
    return _config


def initialize_config(env_file: Optional[str] = None, validate: bool = True) -> Config:
    """Initialize the global configuration"""
    global _config
    _config = Config.from_env(env_file)
    if validate:
        _config.validate()
    return _config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)"""
    global _config
    _config = None 