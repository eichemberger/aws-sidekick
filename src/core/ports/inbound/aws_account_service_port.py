from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.entities.aws_account import AWSAccount
from core.domain.value_objects.aws_credentials import AWSCredentials


class AWSAccountServicePort(ABC):
    """Inbound port for AWS account management operations"""

    @abstractmethod
    async def register_account(
        self, 
        alias: str, 
        credentials: AWSCredentials, 
        description: Optional[str] = None,
        set_as_default: bool = False
    ) -> AWSAccount:
        """Register a new AWS account with credentials"""
        pass

    @abstractmethod
    async def update_account_credentials(self, alias: str, credentials: AWSCredentials) -> AWSAccount:
        """Update credentials for an existing account"""
        pass

    @abstractmethod
    async def get_account(self, alias: str) -> Optional[AWSAccount]:
        """Get an AWS account by alias"""
        pass

    @abstractmethod
    async def list_accounts(self) -> List[AWSAccount]:
        """List all registered AWS accounts"""
        pass

    @abstractmethod
    async def delete_account(self, alias: str) -> bool:
        """Delete an AWS account"""
        pass

    @abstractmethod
    async def get_default_account(self) -> Optional[AWSAccount]:
        """Get the default AWS account"""
        pass

    @abstractmethod
    async def set_default_account(self, alias: str) -> bool:
        """Set an account as the default"""
        pass

    @abstractmethod
    async def validate_account_credentials(self, alias: str) -> bool:
        """Validate credentials for a specific account"""
        pass 