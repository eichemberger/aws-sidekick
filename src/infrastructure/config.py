"""
Configuration management for the AWS Cloud Engineer Agent

This module handles all configuration settings, environment variables,
and provides validation with helpful error messages.
"""

import os
import re
import yaml
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path


def get_logger(name: str):
    """Simple logger function to avoid circular imports"""
    import logging
    return logging.getLogger(name)


logger = get_logger(__name__)


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
    
    def validate(self, require_credentials: bool = False) -> None:
        """Validate AWS configuration"""
        if not require_credentials:
            # Skip credential validation during startup - credentials can be set later via UI
            return
            
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
    enabled: bool = True
    env: Optional[Dict[str, str]] = None
    description: Optional[str] = None


@dataclass(frozen=True)
class MCPConfig:
    """Configuration for all MCP servers"""
    servers: Dict[str, MCPServerConfig] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, yaml_path: str = "config/mcp-config.yaml") -> 'MCPConfig':
        """Load MCP server configuration from YAML file"""
        yaml_file = Path(yaml_path)
        
        if not yaml_file.exists():
            # Create default config file if it doesn't exist
            cls._create_default_yaml(yaml_file)
            logger.info(f"created_default_mcp_config | path=<{yaml_path}>")
        
        try:
            with open(yaml_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            servers = {}
            mcp_servers_config = config_data.get('mcp_servers', {})
            
            for server_name, server_config in mcp_servers_config.items():
                # Expand environment variables in configuration
                expanded_config = cls._expand_env_vars(server_config)
                
                servers[server_name] = MCPServerConfig(
                    command=expanded_config['command'],
                    args=expanded_config.get('args', []),
                    enabled=expanded_config.get('enabled', True),
                    env=expanded_config.get('env'),
                    description=expanded_config.get('description')
                )
            
            # Only return enabled servers
            enabled_servers = {k: v for k, v in servers.items() if v.enabled}
            
            logger.info(f"loaded_mcp_config | total_servers=<{len(servers)}> | enabled_servers=<{len(enabled_servers)}> | file=<{yaml_path}>")
            
            return cls(servers=enabled_servers)
            
        except Exception as e:
            logger.error(f"failed_to_load_mcp_config | file=<{yaml_path}> | error=<{str(e)}>")
            # Fall back to default configuration
            return cls.default()
    
    @staticmethod
    def _expand_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively expand environment variables in configuration"""
        if isinstance(config, dict):
            return {k: MCPConfig._expand_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [MCPConfig._expand_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Replace ${VAR_NAME} with environment variable value
            def replace_env_var(match):
                var_name = match.group(1)
                env_value = os.getenv(var_name)
                if env_value is None:
                    # Return None for unset environment variables instead of the placeholder
                    return None
                return env_value
            
            # Check if this string contains environment variable placeholders
            if '${' in config:
                expanded = re.sub(r'\$\{([^}]+)\}', replace_env_var, config)
                # If the expansion resulted in None, return None
                if expanded is None or 'None' in expanded:
                    return None
                return expanded
            return config
        else:
            return config
    
    @staticmethod
    def _create_default_yaml(yaml_path: Path) -> None:
        """Create a default YAML configuration file"""
        default_config = {
            'mcp_servers': {
                'aws_docs': {
                    'enabled': True,
                    'command': 'uvx',
                    'args': ['awslabs.aws-documentation-mcp-server@latest'],
                    'description': 'AWS documentation and service information'
                },
                'aws_diagram': {
                    'enabled': True,
                    'command': 'uvx',
                    'args': ['awslabs.aws-diagram-mcp-server@latest'],
                    'description': 'Generate AWS architecture diagrams'
                },
                'github': {
                    'enabled': True,
                    'command': 'npx',
                    'args': ['@modelcontextprotocol/server-github'],
                    'env': {
                        'GITHUB_PERSONAL_ACCESS_TOKEN': '${GITHUB_PERSONAL_ACCESS_TOKEN}'
                    },
                    'description': 'GitHub repository management and operations'
                }
            }
        }
        
        # Ensure directory exists
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(yaml_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
    
    @classmethod  
    def default(cls) -> 'MCPConfig':
        """Get fallback default MCP server configuration"""
        return cls(servers={
            "aws_docs": MCPServerConfig(
                command="uvx",
                args=["awslabs.aws-documentation-mcp-server@latest"],
                enabled=True,
                description="AWS documentation and service information"
            ),
            "aws_diagram": MCPServerConfig(
                command="uvx", 
                args=["awslabs.aws-diagram-mcp-server@latest"],
                enabled=True,
                description="Generate AWS architecture diagrams"
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
class SystemPromptConfig:
    """Configuration for system prompts"""
    prompt: str = ""
    
    @classmethod
    def from_yaml(cls, yaml_path: str = "config/system-prompt.yaml") -> 'SystemPromptConfig':
        """Load system prompt configuration from YAML file"""
        yaml_file = Path(yaml_path)
        
        if not yaml_file.exists():
            # Create default config file if it doesn't exist
            cls._create_default_yaml(yaml_file)
            logger.info(f"created_default_system_prompt | path=<{yaml_path}>")
        
        try:
            with open(yaml_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            system_prompt = config_data.get('system_prompt', '')
            
            logger.info(f"loaded_system_prompt | length=<{len(system_prompt)}> | file=<{yaml_path}>")
            
            return cls(prompt=system_prompt)
            
        except Exception as e:
            logger.error(f"failed_to_load_system_prompt | file=<{yaml_path}> | error=<{str(e)}>")
            # Fall back to default prompt
            return cls.default()
    
    @staticmethod
    def _create_default_yaml(yaml_path: Path) -> None:
        """Create a default system prompt YAML configuration file"""
        default_config = {
            'system_prompt': """You are a Senior AWS Cloud Engineer with deep expertise in cloud infrastructure, automation, and DevOps practices. 
You don't just provide advice - you execute solutions and get things done.

Your Communication Style:
- For simple questions: provide concise, direct answers
- For complex questions: provide comprehensive analysis and detailed recommendations
- For infrastructure changes: ONLY execute when given explicit, clear commands

General Principles:
- Always consider security, cost optimization, and operational excellence
- Use infrastructure as code whenever possible for repeatability
- Follow AWS Well-Architected Framework principles

IMPORTANT: Never include <thinking> tags or expose your internal thought process in responses."""
        }
        
        # Ensure directory exists
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(yaml_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
    
    @classmethod
    def default(cls) -> 'SystemPromptConfig':
        """Get fallback default system prompt"""
        default_prompt = """You are a Senior AWS Cloud Engineer with deep expertise in cloud infrastructure, automation, and DevOps practices. 
You don't just provide advice - you execute solutions and get things done.

Your Communication Style:
- For simple questions: provide concise, direct answers
- For complex questions: provide comprehensive analysis and detailed recommendations
- For infrastructure changes: ONLY execute when given explicit, clear commands

General Principles:
- Always consider security, cost optimization, and operational excellence
- Use infrastructure as code whenever possible for repeatability
- Follow AWS Well-Architected Framework principles

IMPORTANT: Never include <thinking> tags or expose your internal thought process in responses."""
        
        return cls(prompt=default_prompt)


@dataclass(frozen=True)
class Config:
    """Main application configuration"""
    model: ModelConfig
    aws: AWSConfig
    github: GitHubConfig
    database: DatabaseConfig
    mcp: MCPConfig
    system_prompt: SystemPromptConfig
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
        mcp = MCPConfig.from_yaml()
        
        # Update GitHub environment if token is available
        if github.is_available and 'github' in mcp.servers:
            github_server = mcp.servers['github']
            if github_server.env is None:
                # Create new server config with environment
                from dataclasses import replace
                github_server_with_env = replace(
                    github_server,
                    env={"GITHUB_PERSONAL_ACCESS_TOKEN": github.personal_access_token}
                )
                mcp = MCPConfig(servers={**mcp.servers, 'github': github_server_with_env})
        
        # System prompt configuration
        system_prompt = SystemPromptConfig.from_yaml()
        
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
            system_prompt=system_prompt,
            api=api,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "development")
        )
    
    def validate(self, require_aws_credentials: bool = False) -> None:
        """Validate all configuration settings"""
        try:
            self.model.validate()
            self.aws.validate(require_credentials=require_aws_credentials)
            self.database.validate()
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {str(e)}")
    
    def print_status(self) -> None:
        """Print configuration status for debugging"""
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
        _config.validate(require_aws_credentials=False)  # Don't require AWS credentials at startup
    return _config


def initialize_config(env_file: Optional[str] = None, validate: bool = True, require_aws_credentials: bool = False) -> Config:
    """Initialize the global configuration"""
    global _config
    _config = Config.from_env(env_file)
    if validate:
        _config.validate(require_aws_credentials=require_aws_credentials)
    return _config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)"""
    global _config
    _config = None 