from typing import List, Dict, Any
from core.ports.inbound.aws_service_port import AWSServicePort
from core.domain.entities.aws_resource import AWSResource, ResourceType
from core.domain.value_objects.aws_credentials import AWSAccountInfo, AWSCredentials
from core.use_cases.aws_analysis_use_case import AWSAnalysisUseCase


class AWSApplicationService(AWSServicePort):
    """Application service for AWS operations"""

    def __init__(
        self,
        aws_analysis_use_case: AWSAnalysisUseCase,
        default_credentials: AWSCredentials = None
    ):
        self._aws_analysis_use_case = aws_analysis_use_case
        self._default_credentials = default_credentials

    async def get_account_info(self) -> AWSAccountInfo:
        """Get AWS account information"""
        credentials = self._get_credentials()
        return await self._aws_analysis_use_case.get_account_info(credentials)

    async def list_resources(self, resource_type: ResourceType, region: str = None) -> List[AWSResource]:
        """List AWS resources of a specific type"""
        credentials = self._get_credentials()
        # This would need more implementation to convert raw AWS data to domain entities
        # For now, return empty list as placeholder
        return []

    async def get_resource(self, resource_id: str, resource_type: ResourceType, region: str = None) -> AWSResource:
        """Get a specific AWS resource"""
        # Placeholder implementation
        raise NotImplementedError("Resource retrieval not yet implemented")

    async def analyze_costs(self, time_period_days: int = 30) -> Dict[str, Any]:
        """Analyze AWS costs for a given time period"""
        credentials = self._get_credentials()
        return await self._aws_analysis_use_case.analyze_costs(credentials, time_period_days)

    async def check_security(self, resource_type: ResourceType = None) -> Dict[str, Any]:
        """Perform security analysis on AWS resources"""
        credentials = self._get_credentials()
        return await self._aws_analysis_use_case.security_audit(credentials)

    async def optimize_resources(self, resource_type: ResourceType = None) -> List[Dict[str, Any]]:
        """Get optimization recommendations for AWS resources"""
        credentials = self._get_credentials()
        analysis_result = await self._aws_analysis_use_case.analyze_resources(credentials, resource_type)
        
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
        # In a real implementation, this would get credentials from API session
        # For now, use default credentials or environment
        if self._default_credentials:
            return self._default_credentials
        
        # Default to environment credentials
        return AWSCredentials(region="us-east-1") 