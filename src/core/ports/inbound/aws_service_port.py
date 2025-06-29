from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.domain.entities.aws_resource import AWSResource, ResourceType
from core.domain.value_objects.aws_credentials import AWSAccountInfo, AWSCredentials


class AWSServicePort(ABC):
    """Inbound port for AWS operations"""

    @abstractmethod
    async def set_credentials(self, credentials: AWSCredentials) -> None:
        """Set AWS credentials for current session"""
        pass

    @abstractmethod
    async def clear_credentials(self) -> None:
        """Clear session AWS credentials"""
        pass

    @abstractmethod
    def get_current_credentials(self) -> Optional[AWSCredentials]:
        """Get current session credentials"""
        pass

    @abstractmethod
    async def validate_credentials(self, credentials: AWSCredentials) -> bool:
        """Validate AWS credentials"""
        pass

    @abstractmethod
    async def get_account_info(self, credentials: Optional[AWSCredentials] = None) -> AWSAccountInfo:
        """Get AWS account information"""
        pass

    @abstractmethod
    async def list_resources(self, resource_type: ResourceType, region: str = None, credentials: Optional[AWSCredentials] = None) -> List[AWSResource]:
        """List AWS resources of a specific type"""
        pass

    @abstractmethod
    async def get_resource(self, resource_id: str, resource_type: ResourceType, region: str = None, credentials: Optional[AWSCredentials] = None) -> AWSResource:
        """Get a specific AWS resource"""
        pass

    @abstractmethod
    async def analyze_costs(self, time_period_days: int = 30, credentials: Optional[AWSCredentials] = None) -> Dict[str, Any]:
        """Analyze AWS costs for a given time period"""
        pass

    @abstractmethod
    async def check_security(self, resource_type: ResourceType = None, credentials: Optional[AWSCredentials] = None) -> Dict[str, Any]:
        """Perform security analysis on AWS resources"""
        pass

    @abstractmethod
    async def optimize_resources(self, resource_type: ResourceType = None, credentials: Optional[AWSCredentials] = None) -> List[Dict[str, Any]]:
        """Get optimization recommendations for AWS resources"""
        pass 