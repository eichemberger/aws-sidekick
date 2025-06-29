from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AWSCredentials:
    """Value object for AWS credentials"""
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    region: str = "us-east-1"
    profile: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if credentials are valid"""
        # Either we have access keys or a profile
        return (
            (self.access_key_id and self.secret_access_key) or 
            self.profile is not None
        )

    def uses_profile(self) -> bool:
        """Check if using AWS profile"""
        return self.profile is not None

    def uses_keys(self) -> bool:
        """Check if using access keys"""
        return self.access_key_id is not None and self.secret_access_key is not None


@dataclass(frozen=True)
class AWSAccountInfo:
    """Value object for AWS account information"""
    account_id: str
    user_arn: str
    region: str
    
    def is_root_account(self) -> bool:
        """Check if this is a root account"""
        return "root" in self.user_arn.lower() 