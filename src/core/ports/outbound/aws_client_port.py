from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.domain.value_objects.aws_credentials import AWSCredentials, AWSAccountInfo


class AWSClientPort(ABC):
    """Outbound port for AWS client operations"""

    @abstractmethod
    async def validate_credentials(self, credentials: AWSCredentials) -> bool:
        """Validate AWS credentials"""
        pass

    @abstractmethod
    async def get_caller_identity(self, credentials: AWSCredentials) -> AWSAccountInfo:
        """Get AWS caller identity information"""
        pass

    @abstractmethod
    async def list_ec2_instances(self, credentials: AWSCredentials, region: str = None) -> List[Dict[str, Any]]:
        """List EC2 instances"""
        pass

    @abstractmethod
    async def list_rds_instances(self, credentials: AWSCredentials, region: str = None) -> List[Dict[str, Any]]:
        """List RDS instances"""
        pass

    @abstractmethod
    async def list_s3_buckets(self, credentials: AWSCredentials) -> List[Dict[str, Any]]:
        """List S3 buckets"""
        pass

    @abstractmethod
    async def get_cost_and_usage(self, credentials: AWSCredentials, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get cost and usage data"""
        pass

    @abstractmethod
    async def describe_security_groups(self, credentials: AWSCredentials, region: str = None) -> List[Dict[str, Any]]:
        """Describe security groups"""
        pass 