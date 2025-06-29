from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.domain.entities.aws_resource import AWSResource, ResourceType
from core.domain.value_objects.aws_credentials import AWSAccountInfo


class AWSServicePort(ABC):
    """Inbound port for AWS operations"""

    @abstractmethod
    async def get_account_info(self) -> AWSAccountInfo:
        """Get AWS account information"""
        pass

    @abstractmethod
    async def list_resources(self, resource_type: ResourceType, region: str = None) -> List[AWSResource]:
        """List AWS resources of a specific type"""
        pass

    @abstractmethod
    async def get_resource(self, resource_id: str, resource_type: ResourceType, region: str = None) -> AWSResource:
        """Get a specific AWS resource"""
        pass

    @abstractmethod
    async def analyze_costs(self, time_period_days: int = 30) -> Dict[str, Any]:
        """Analyze AWS costs for a given time period"""
        pass

    @abstractmethod
    async def check_security(self, resource_type: ResourceType = None) -> Dict[str, Any]:
        """Perform security analysis on AWS resources"""
        pass

    @abstractmethod
    async def optimize_resources(self, resource_type: ResourceType = None) -> List[Dict[str, Any]]:
        """Get optimization recommendations for AWS resources"""
        pass 