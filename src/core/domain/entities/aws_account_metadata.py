from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AWSAccountMetadata:
    """Domain entity representing AWS account metadata (without credentials)"""
    alias: str
    account_id: Optional[str] = None
    description: Optional[str] = None
    region: str = "us-east-1"
    uses_profile: bool = False
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def update_account_id(self, account_id: str) -> None:
        """Update the AWS account ID after validation"""
        self.account_id = account_id
        self.updated_at = datetime.utcnow()
    
    def mark_as_default(self) -> None:
        """Mark this account as the default"""
        self.is_default = True
        self.updated_at = datetime.utcnow()
    
    def unmark_as_default(self) -> None:
        """Remove default status from this account"""
        self.is_default = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'alias': self.alias,
            'account_id': self.account_id,
            'description': self.description,
            'is_default': self.is_default,
            'region': self.region,
            'uses_profile': self.uses_profile,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 