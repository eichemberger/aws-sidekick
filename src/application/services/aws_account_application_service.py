from typing import List, Optional
import logging
from core.ports.inbound.aws_account_service_port import AWSAccountServicePort
from core.ports.outbound.aws_account_repository_port import AWSAccountRepositoryPort
from core.ports.outbound.aws_client_port import AWSClientPort
from core.domain.entities.aws_account import AWSAccount
from core.domain.value_objects.aws_credentials import AWSCredentials

logger = logging.getLogger(__name__)


class AWSAccountApplicationService(AWSAccountServicePort):
    """Application service for AWS account management"""

    def __init__(
        self,
        account_repository: AWSAccountRepositoryPort,
        aws_client: AWSClientPort
    ):
        self._account_repository = account_repository
        self._aws_client = aws_client

    async def register_account(
        self, 
        alias: str, 
        credentials: AWSCredentials, 
        description: Optional[str] = None,
        set_as_default: bool = False
    ) -> AWSAccount:
        """Register a new AWS account with credentials"""
        # Check if alias already exists
        if await self._account_repository.account_exists(alias):
            raise ValueError(f"Account with alias '{alias}' already exists")
        
        # Validate credentials by making an AWS call
        if not await self._aws_client.validate_credentials(credentials):
            raise ValueError("Invalid AWS credentials provided")
        
        # Get account info to store account ID
        try:
            account_info = await self._aws_client.get_caller_identity(credentials)
            account_id = account_info.account_id
        except Exception as e:
            logger.warning(f"Could not retrieve account ID for alias '{alias}': {e}")
            account_id = None
        
        # Create account entity
        account = AWSAccount.create(
            alias=alias,
            credentials=credentials,
            account_id=account_id,
            description=description,
            is_default=False  # We'll set this after saving if needed
        )
        
        # Save the account
        saved_account = await self._account_repository.save_account(account)
        
        # Set as default if requested
        if set_as_default:
            await self._account_repository.set_default_account(alias)
            saved_account.mark_as_default()
        
        logger.info(f"Registered AWS account '{alias}' with account ID '{account_id}'")
        return saved_account

    async def update_account_credentials(self, alias: str, credentials: AWSCredentials) -> AWSAccount:
        """Update credentials for an existing account"""
        # Get existing account
        account = await self._account_repository.get_account_by_alias(alias)
        if not account:
            raise ValueError(f"Account with alias '{alias}' not found")
        
        # Validate new credentials
        if not await self._aws_client.validate_credentials(credentials):
            raise ValueError("Invalid AWS credentials provided")
        
        # Update account with new credentials and account ID
        try:
            account_info = await self._aws_client.get_caller_identity(credentials)
            account.update_account_id(account_info.account_id)
        except Exception as e:
            logger.warning(f"Could not retrieve account ID for alias '{alias}': {e}")
        
        await account.update_credentials(credentials)
        
        # Save updated account
        updated_account = await self._account_repository.save_account(account)
        
        logger.info(f"Updated credentials for AWS account '{alias}'")
        return updated_account

    async def get_account(self, alias: str) -> Optional[AWSAccount]:
        """Get an AWS account by alias"""
        return await self._account_repository.get_account_by_alias(alias)

    async def list_accounts(self) -> List[AWSAccount]:
        """List all registered AWS accounts"""
        return await self._account_repository.list_accounts()

    async def delete_account(self, alias: str) -> bool:
        """Delete an AWS account"""
        # Check if account exists
        account = await self._account_repository.get_account_by_alias(alias)
        if not account:
            return False
        
        # If this is the default account, we need to handle that
        if account.is_default:
            # Find another account to make default, or leave none as default
            all_accounts = await self._account_repository.list_accounts()
            other_accounts = [acc for acc in all_accounts if acc.alias != alias]
            
            if other_accounts:
                # Make the first other account the default
                await self._account_repository.set_default_account(other_accounts[0].alias)
                logger.info(f"Made account '{other_accounts[0].alias}' the new default after deleting '{alias}'")
        
        # Delete the account
        success = await self._account_repository.delete_account(alias)
        
        if success:
            logger.info(f"Deleted AWS account '{alias}'")
        
        return success

    async def get_default_account(self) -> Optional[AWSAccount]:
        """Get the default AWS account"""
        return await self._account_repository.get_default_account()

    async def set_default_account(self, alias: str) -> bool:
        """Set an account as the default"""
        # Check if account exists
        if not await self._account_repository.account_exists(alias):
            raise ValueError(f"Account with alias '{alias}' not found")
        
        success = await self._account_repository.set_default_account(alias)
        
        if success:
            logger.info(f"Set AWS account '{alias}' as default")
        
        return success

    async def validate_account_credentials(self, alias: str) -> bool:
        """Validate credentials for a specific account"""
        account = await self._account_repository.get_account_by_alias(alias)
        if not account:
            return False
        
        if not account.credentials:
            return False
        return await self._aws_client.validate_credentials(account.credentials) 