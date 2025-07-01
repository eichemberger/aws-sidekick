from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from core.domain.value_objects.aws_credentials import AWSCredentials
from core.domain.entities.aws_account_metadata import AWSAccountMetadata
from infrastructure.credential_manager import get_credential_manager


@dataclass
class AWSAccount:
    """
    Domain entity representing a registered AWS account.
    
    This is a composite entity that combines metadata (stored in DB) 
    with credentials (stored in memory only).
    """
    metadata: AWSAccountMetadata
    credentials: Optional[AWSCredentials] = None
    
    @property
    def alias(self) -> str:
        """Get account alias"""
        return self.metadata.alias
    
    @property
    def account_id(self) -> Optional[str]:
        """Get AWS account ID"""
        return self.metadata.account_id
    
    @property
    def description(self) -> Optional[str]:
        """Get account description"""
        return self.metadata.description
    
    @property
    def region(self) -> str:
        """Get account region"""
        return self.metadata.region
    
    @property
    def is_default(self) -> bool:
        """Check if this is the default account"""
        return self.metadata.is_default
    
    @property
    def uses_profile(self) -> bool:
        """Check if account uses AWS profile"""
        return self.metadata.uses_profile
    
    @property
    def created_at(self) -> Optional[datetime]:
        """Get creation timestamp"""  
        return self.metadata.created_at
    
    @property
    def updated_at(self) -> Optional[datetime]:
        """Get last update timestamp"""
        return self.metadata.updated_at
    
    @classmethod
    def create(cls, alias: str, credentials: AWSCredentials, 
               account_id: Optional[str] = None, description: Optional[str] = None,
               is_default: bool = False) -> 'AWSAccount':
        """Create a new AWS account with metadata and credentials"""
        metadata = AWSAccountMetadata(
            alias=alias,
            account_id=account_id,
            description=description,
            region=credentials.region,
            uses_profile=credentials.uses_profile(),
            is_default=is_default
        )
        return cls(metadata=metadata, credentials=credentials)
    
    async def update_credentials(self, credentials: AWSCredentials) -> None:
        """Update account credentials (stored in memory only)"""
        self.credentials = credentials
        self.metadata.region = credentials.region
        self.metadata.uses_profile = credentials.uses_profile()
        self.metadata.updated_at = datetime.utcnow()
    
    def update_account_id(self, account_id: str) -> None:
        """Update the AWS account ID after validation"""
        self.metadata.update_account_id(account_id)
    
    def mark_as_default(self) -> None:
        """Mark this account as the default"""
        self.metadata.mark_as_default()
    
    def unmark_as_default(self) -> None:
        """Remove default status from this account"""
        self.metadata.unmark_as_default()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses (excludes sensitive credentials)"""
        return self.metadata.to_dict()
    
    async def load_credentials(self) -> bool:
        """Load credentials from in-memory store"""
        credential_manager = get_credential_manager()
        self.credentials = await credential_manager.get_credentials(self.alias)
        return self.credentials is not None
    
    async def store_credentials(self) -> None:
        """Store credentials in in-memory store"""
        if self.credentials:
            credential_manager = get_credential_manager()
            await credential_manager.store_credentials(self.alias, self.credentials)
    
    async def remove_credentials(self) -> bool:
        """Remove credentials from in-memory store"""
        credential_manager = get_credential_manager()
        removed = await credential_manager.remove_credentials(self.alias)
        if removed:
            self.credentials = None
        return removed 