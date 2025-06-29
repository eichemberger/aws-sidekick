from typing import List, Dict, Any, Optional
from core.ports.inbound.aws_service_port import AWSServicePort
from core.domain.entities.aws_resource import AWSResource, ResourceType
from core.domain.value_objects.aws_credentials import AWSAccountInfo, AWSCredentials
from core.use_cases.aws_analysis_use_case import AWSAnalysisUseCase
from core.ports.outbound.mcp_reinitialization_port import MCPReinitializationPort
import os
from infrastructure.config import get_config
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AWSApplicationService(AWSServicePort):
    """Application service for AWS operations"""

    def __init__(
        self,
        aws_analysis_use_case: AWSAnalysisUseCase,
        mcp_reinitialization_port: Optional[MCPReinitializationPort] = None,
        default_credentials: AWSCredentials = None
    ):
        self._aws_analysis_use_case = aws_analysis_use_case
        self._mcp_reinitialization_port = mcp_reinitialization_port
        self._default_credentials = default_credentials
        self._session_credentials: Optional[AWSCredentials] = None

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
        """Clear session-specific AWS credentials and restore defaults"""
        self._session_credentials = None
        
        # Restore original environment variables from config
        config = get_config()
        
        # Restore original AWS configuration
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
        
        # Reinitialize MCP servers with restored credentials
        if self._mcp_reinitialization_port:
            try:
                await self._mcp_reinitialization_port.reinitialize_with_new_credentials()
            except Exception as e:
                logger.warning(f"mcp_reinitialization_failed | error=<{str(e)}> | default credentials may not be available to all tools")
        else:
            logger.warning("mcp_reinitialization_port_not_configured | default credentials may not be available to all tools")
        
        logger.info("session_credentials_cleared | restored_default_configuration")

    def get_current_credentials(self) -> Optional[AWSCredentials]:
        """Get current session credentials"""
        return self._session_credentials

    async def validate_credentials(self, credentials: AWSCredentials) -> bool:
        """Validate AWS credentials"""
        return await self._aws_analysis_use_case.validate_credentials(credentials)

    async def get_account_info(self, credentials: Optional[AWSCredentials] = None) -> AWSAccountInfo:
        """Get AWS account information"""
        creds = credentials or self._get_credentials()
        return await self._aws_analysis_use_case.get_account_info(creds)

    async def list_resources(self, resource_type: ResourceType, region: str = None, credentials: Optional[AWSCredentials] = None) -> List[AWSResource]:
        """List AWS resources of a specific type"""
        creds = credentials or self._get_credentials()
        # This would need more implementation to convert raw AWS data to domain entities
        # For now, return empty list as placeholder
        return []

    async def get_resource(self, resource_id: str, resource_type: ResourceType, region: str = None, credentials: Optional[AWSCredentials] = None) -> AWSResource:
        """Get a specific AWS resource"""
        # Placeholder implementation
        raise NotImplementedError("Resource retrieval not yet implemented")

    async def analyze_costs(self, time_period_days: int = 30, credentials: Optional[AWSCredentials] = None) -> Dict[str, Any]:
        """Analyze AWS costs for a given time period"""
        creds = credentials or self._get_credentials()
        return await self._aws_analysis_use_case.analyze_costs(creds, time_period_days)

    async def check_security(self, resource_type: ResourceType = None, credentials: Optional[AWSCredentials] = None) -> Dict[str, Any]:
        """Perform security analysis on AWS resources"""
        creds = credentials or self._get_credentials()
        return await self._aws_analysis_use_case.security_audit(creds)

    async def optimize_resources(self, resource_type: ResourceType = None, credentials: Optional[AWSCredentials] = None) -> List[Dict[str, Any]]:
        """Get optimization recommendations for AWS resources"""
        creds = credentials or self._get_credentials()
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
        """Get AWS credentials from session state or default"""
        # Priority: session credentials -> default credentials -> environment credentials
        if self._session_credentials:
            return self._session_credentials
        
        if self._default_credentials:
            return self._default_credentials
        
        # Default to environment credentials
        return AWSCredentials(region="us-east-1") 