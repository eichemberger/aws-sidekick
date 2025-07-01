from typing import List, Dict, Any, Optional
from core.ports.inbound.aws_service_port import AWSServicePort
from core.ports.outbound.aws_account_repository_port import AWSAccountRepositoryPort
from core.domain.entities.aws_resource import AWSResource, ResourceType
from core.domain.value_objects.aws_credentials import AWSAccountInfo, AWSCredentials
from core.use_cases.aws_analysis_use_case import AWSAnalysisUseCase
from core.ports.outbound.mcp_reinitialization_port import MCPReinitializationPort
import os
from infrastructure.config import get_config
import logging

logger = logging.getLogger(__name__)


class AWSApplicationService(AWSServicePort):
    """Application service for AWS operations with multi-account support"""

    def __init__(
        self,
        aws_analysis_use_case: AWSAnalysisUseCase,
        account_repository: AWSAccountRepositoryPort,
        mcp_reinitialization_port: Optional[MCPReinitializationPort] = None,
        default_credentials: AWSCredentials = None
    ):
        self._aws_analysis_use_case = aws_analysis_use_case
        self._account_repository = account_repository
        self._mcp_reinitialization_port = mcp_reinitialization_port
        self._default_credentials = default_credentials
        self._active_account_alias: Optional[str] = None
        # Keep legacy session credentials for backward compatibility
        self._session_credentials: Optional[AWSCredentials] = None

    async def set_active_account(self, account_alias: str) -> None:
        """Set active AWS account for current session"""
        # Get account from repository
        account = await self._account_repository.get_account_by_alias(account_alias)
        if not account:
            raise ValueError(f"Account with alias '{account_alias}' not found")
        
        # Load credentials from memory
        credentials_loaded = await account.load_credentials()
        if not credentials_loaded or not account.credentials:
            logger.error(f"No credentials available for account '{account_alias}' - they may have been cleared on restart")
            raise ValueError(f"No credentials available for account '{account_alias}'. Please re-enter credentials via the UI.")
        
        # Set as active account
        self._active_account_alias = account_alias
        
        # Update environment variables for MCP tools
        await self._update_environment_with_credentials(account.credentials)
        
        logger.info(f"Set active AWS account to '{account_alias}' (Account ID: {account.account_id})")
        logger.info(f"Using credential type: {'profile' if account.credentials.uses_profile() else 'access keys'}")
        logger.info("Successfully updated environment variables with account credentials")

    async def clear_active_account(self) -> None:
        """Clear active AWS account"""
        self._active_account_alias = None
        await self._restore_default_environment()
        logger.info("Cleared active AWS account")

    def get_active_account_alias(self) -> Optional[str]:
        """Get current active account alias"""
        return self._active_account_alias

    async def _update_environment_with_credentials(self, credentials: AWSCredentials) -> None:
        """Update environment variables with credentials"""
        logger.info(f"Updating environment variables with credentials for region: {credentials.region}")
        
        if credentials.uses_keys():
            logger.info("Setting environment variables for access key credentials")
            os.environ["AWS_ACCESS_KEY_ID"] = credentials.access_key_id or ""
            os.environ["AWS_SECRET_ACCESS_KEY"] = credentials.secret_access_key or ""
            if credentials.session_token:
                os.environ["AWS_SESSION_TOKEN"] = credentials.session_token
                logger.info("Set AWS_SESSION_TOKEN (temporary credentials)")
            else:
                os.environ.pop("AWS_SESSION_TOKEN", None)
                logger.info("Cleared AWS_SESSION_TOKEN (permanent credentials)")
            os.environ.pop("AWS_PROFILE", None)
            logger.info("Cleared AWS_PROFILE (using access keys)")
        elif credentials.uses_profile():
            logger.info(f"Setting environment variables for profile credentials: {credentials.profile}")
            os.environ["AWS_PROFILE"] = credentials.profile or ""
            os.environ.pop("AWS_ACCESS_KEY_ID", None)
            os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
            os.environ.pop("AWS_SESSION_TOKEN", None)
            logger.info("Cleared explicit credential environment variables (using profile)")
        
        os.environ["AWS_DEFAULT_REGION"] = credentials.region
        logger.info(f"Set AWS_DEFAULT_REGION to: {credentials.region}")
        
        # Reinitialize MCP servers with new credentials
        if self._mcp_reinitialization_port:
            try:
                logger.info("Reinitializing MCP servers with new credentials")
                await self._mcp_reinitialization_port.reinitialize_with_new_credentials()
                logger.info("MCP servers reinitialized successfully")
            except Exception as e:
                logger.warning(f"MCP reinitialization failed: {e}")

    async def _restore_default_environment(self) -> None:
        """Restore default environment variables"""
        config = get_config()
        
        if config.aws.access_key_id:
            os.environ["AWS_ACCESS_KEY_ID"] = config.aws.access_key_id
        else:
            os.environ.pop("AWS_ACCESS_KEY_ID", None)
            
        if config.aws.secret_access_key:
            os.environ["AWS_SECRET_ACCESS_KEY"] = config.aws.secret_access_key
        else:
            os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
            
        if config.aws.session_token:
            os.environ["AWS_SESSION_TOKEN"] = config.aws.session_token
        else:
            os.environ.pop("AWS_SESSION_TOKEN", None)
            
        if config.aws.profile:
            os.environ["AWS_PROFILE"] = config.aws.profile
        else:
            os.environ.pop("AWS_PROFILE", None)
            
        os.environ["AWS_DEFAULT_REGION"] = config.aws.default_region
        
        if self._mcp_reinitialization_port:
            try:
                await self._mcp_reinitialization_port.reinitialize_with_new_credentials()
            except Exception as e:
                logger.warning(f"MCP reinitialization failed: {e}")

    async def _get_credentials_for_account(self, account_alias: Optional[str] = None) -> AWSCredentials:
        """Get credentials for the specified account or active account"""
        if account_alias:
            account = await self._account_repository.get_account_by_alias(account_alias)
            if not account:
                raise ValueError(f"Account with alias '{account_alias}' not found")
            # Load credentials from memory
            credentials_loaded = await account.load_credentials()
            if not credentials_loaded or not account.credentials:
                raise ValueError(f"No credentials available for account '{account_alias}'. Please re-enter credentials via the UI.")
            return account.credentials
        elif self._active_account_alias:
            account = await self._account_repository.get_account_by_alias(self._active_account_alias)
            if not account:
                raise ValueError(f"Active account '{self._active_account_alias}' not found")
            # Load credentials from memory
            credentials_loaded = await account.load_credentials()
            if not credentials_loaded or not account.credentials:
                raise ValueError(f"No credentials available for active account '{self._active_account_alias}'. Please re-enter credentials via the UI.")
            return account.credentials
        else:
            # Fall back to default account or session credentials
            default_account = await self._account_repository.get_default_account()
            if default_account:
                credentials_loaded = await default_account.load_credentials()
                if credentials_loaded and default_account.credentials:
                    return default_account.credentials
            
            if self._session_credentials:
                return self._session_credentials
            elif self._default_credentials:
                return self._default_credentials
            else:
                raise ValueError("No credentials available. Please select an account and ensure credentials are entered via the UI.")

    # Legacy method for backward compatibility
    async def set_credentials(self, credentials: AWSCredentials) -> None:
        """Set session-specific AWS credentials and update environment"""
        # Validate the credentials first
        is_valid = await self.validate_credentials(credentials)
        if not is_valid:
            raise ValueError("Invalid AWS credentials provided")
        
        # Store in session
        self._session_credentials = credentials
        
        # Also update environment variables so MCP tools can use them
        if credentials.uses_keys():
            os.environ["AWS_ACCESS_KEY_ID"] = credentials.access_key_id or ""
            os.environ["AWS_SECRET_ACCESS_KEY"] = credentials.secret_access_key or ""
            if credentials.session_token:
                os.environ["AWS_SESSION_TOKEN"] = credentials.session_token
            else:
                # Remove session token if not provided
                os.environ.pop("AWS_SESSION_TOKEN", None)
            # Clear profile when using keys
            os.environ.pop("AWS_PROFILE", None)
        elif credentials.uses_profile():
            os.environ["AWS_PROFILE"] = credentials.profile or ""
            # Clear explicit keys when using profile
            os.environ.pop("AWS_ACCESS_KEY_ID", None)
            os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
            os.environ.pop("AWS_SESSION_TOKEN", None)
        
        # Always set the region
        os.environ["AWS_DEFAULT_REGION"] = credentials.region
        
        # Reinitialize MCP servers with new credentials
        if self._mcp_reinitialization_port:
            try:
                await self._mcp_reinitialization_port.reinitialize_with_new_credentials()
            except Exception as e:
                logger.warning(f"mcp_reinitialization_failed | error=<{str(e)}> | credentials may not be available to all tools")
        else:
            logger.warning("mcp_reinitialization_port_not_configured | credentials may not be available to all tools")
        
        logger.info(f"session_credentials_updated | region=<{credentials.region}> | credential_type=<{'profile' if credentials.uses_profile() else 'keys'}>")

    async def clear_credentials(self) -> None:
        """Clear session-specific AWS credentials and restore defaults (deprecated, use clear_active_account)"""
        self._session_credentials = None
        await self._restore_default_environment()
        logger.info("session_credentials_cleared | restored_default_configuration")

    def get_current_credentials(self) -> Optional[AWSCredentials]:
        """Get current session credentials (deprecated, use get_active_account_alias)"""
        return self._session_credentials

    async def validate_credentials(self, credentials: AWSCredentials) -> bool:
        """Validate AWS credentials (deprecated)"""
        return await self._aws_analysis_use_case.validate_credentials(credentials)

    async def get_account_info(self, account_alias: Optional[str] = None) -> AWSAccountInfo:
        """Get AWS account information"""
        creds = await self._get_credentials_for_account(account_alias)
        return await self._aws_analysis_use_case.get_account_info(creds)

    async def list_resources(self, resource_type: ResourceType, region: str = None, account_alias: Optional[str] = None) -> List[AWSResource]:
        """List AWS resources of a specific type"""
        # This would need more implementation to convert raw AWS data to domain entities
        # For now, return empty list as placeholder
        return []

    async def get_resource(self, resource_id: str, resource_type: ResourceType, region: str = None, account_alias: Optional[str] = None) -> AWSResource:
        """Get a specific AWS resource"""
        # Placeholder implementation
        raise NotImplementedError("Resource retrieval not yet implemented")

    async def analyze_costs(self, time_period_days: int = 30, account_alias: Optional[str] = None) -> Dict[str, Any]:
        """Analyze AWS costs for a given time period"""
        creds = await self._get_credentials_for_account(account_alias)
        return await self._aws_analysis_use_case.analyze_costs(creds, time_period_days)

    async def check_security(self, resource_type: ResourceType = None, account_alias: Optional[str] = None) -> Dict[str, Any]:
        """Perform security analysis on AWS resources"""
        creds = await self._get_credentials_for_account(account_alias)
        return await self._aws_analysis_use_case.security_audit(creds)

    async def optimize_resources(self, resource_type: ResourceType = None, account_alias: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get optimization recommendations for AWS resources"""
        creds = await self._get_credentials_for_account(account_alias)
        analysis_result = await self._aws_analysis_use_case.analyze_resources(creds, resource_type)
        
        # Extract recommendations from the analysis
        recommendations = []
        if 'ai_insights' in analysis_result:
            # Parse AI insights for recommendations
            recommendations.append({
                'type': 'ai_recommendation',
                'description': analysis_result['ai_insights']
            })
        
        return recommendations

    def _get_credentials(self) -> AWSCredentials:
        """Get AWS credentials from session state or default (deprecated)"""
        # Priority: session credentials -> default credentials -> environment credentials
        if self._session_credentials:
            return self._session_credentials
        
        if self._default_credentials:
            return self._default_credentials
        
        # Default to environment credentials
        return AWSCredentials(region="us-east-1") 