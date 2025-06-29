from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class ResourceStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    PENDING = "pending"
    TERMINATED = "terminated"
    UNKNOWN = "unknown"


class ResourceType(Enum):
    EC2_INSTANCE = "ec2_instance"
    RDS_INSTANCE = "rds_instance"
    S3_BUCKET = "s3_bucket"
    LAMBDA_FUNCTION = "lambda_function"
    ELB = "load_balancer"
    VPC = "vpc"
    SECURITY_GROUP = "security_group"
    IAM_ROLE = "iam_role"
    CLOUDFORMATION_STACK = "cloudformation_stack"


@dataclass
class AWSResource:
    """Domain entity representing an AWS resource"""
    id: str
    name: str
    resource_type: ResourceType
    region: str
    status: ResourceStatus
    tags: Dict[str, str] = None
    properties: Dict[str, Any] = None
    cost_estimate: Optional[float] = None
    security_score: Optional[int] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.properties is None:
            self.properties = {}

    def has_tag(self, key: str) -> bool:
        """Check if resource has a specific tag"""
        return key in self.tags

    def get_tag(self, key: str) -> Optional[str]:
        """Get tag value by key"""
        return self.tags.get(key)

    def add_tag(self, key: str, value: str) -> None:
        """Add a tag to the resource"""
        self.tags[key] = value

    def is_running(self) -> bool:
        """Check if resource is in running state"""
        return self.status == ResourceStatus.RUNNING

    def get_property(self, key: str) -> Any:
        """Get property value by key"""
        return self.properties.get(key)

    def set_property(self, key: str, value: Any) -> None:
        """Set property value"""
        self.properties[key] = value 