from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.entities.aws_account import AWSAccount


class AWSAccountRepositoryPort(ABC):
    """Outbound port for AWS account repository operations"""

    @abstractmethod
    async def save_account(self, account: AWSAccount) -> AWSAccount:
        """Save an AWS account"""
        pass

    @abstractmethod
    async def get_account_by_alias(self, alias: str) -> Optional[AWSAccount]:
        """Get an AWS account by alias"""
        pass

    @abstractmethod
    async def list_accounts(self) -> List[AWSAccount]:
        """List all AWS accounts"""
        pass

    @abstractmethod
    async def delete_account(self, alias: str) -> bool:
        """Delete an AWS account by alias"""
        pass

    @abstractmethod
    async def get_default_account(self) -> Optional[AWSAccount]:
        """Get the default AWS account"""
        pass

    @abstractmethod
    async def set_default_account(self, alias: str) -> bool:
        """Set an account as default (and unset others)"""
        pass

    @abstractmethod
    async def account_exists(self, alias: str) -> bool:
        """Check if an AWS account with the given alias exists"""
        pass 