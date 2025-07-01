"""
In-memory credential manager for secure AWS credential storage.
Never persists credentials to disk in production.
In development mode, optionally persists to local file for convenience.
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Optional
from core.domain.value_objects.aws_credentials import AWSCredentials
from infrastructure.logging import get_logger


class InMemoryCredentialManager:
    """
    Secure in-memory storage for AWS credentials.
    Credentials are never persisted to disk.
    """
    
    def __init__(self):
        self._credentials: Dict[str, AWSCredentials] = {}
        self._lock = asyncio.Lock()
        self.logger = get_logger(__name__)
        
        # Development mode persistence (for convenience only)
        self._dev_mode = self._is_dev_mode()
        self._dev_storage_path = Path.home() / ".aws-agent-dev" / "credentials.json"
        
        if self._dev_mode:
            self.logger.info("Development mode detected - credentials will persist across restarts")
            self.logger.warning("DEV MODE: Credentials stored in plain text for convenience only!")
            self._dev_initialized = False
        else:
            self.logger.info("Production mode - credentials will NOT persist across restarts")
            self._dev_initialized = True
    
    async def store_credentials(self, alias: str, credentials: AWSCredentials) -> None:
        """Store credentials for an account alias in memory (and dev storage if in dev mode)"""
        async with self._lock:
            self._credentials[alias] = credentials
            self.logger.info(f"Stored credentials for account '{alias}' in memory")
            
            # In dev mode, also persist to encrypted file
            if self._dev_mode:
                await self._save_dev_credentials()
    
    async def get_credentials(self, alias: str) -> Optional[AWSCredentials]:
        """Retrieve credentials for an account alias"""
        # Ensure dev credentials are loaded if in dev mode
        await self._ensure_dev_initialized()
        
        async with self._lock:
            credentials = self._credentials.get(alias)
            if credentials:
                self.logger.debug(f"Retrieved credentials for account '{alias}' from memory")
            else:
                self.logger.debug(f"No credentials found for account '{alias}' in memory")
            return credentials
    
    async def remove_credentials(self, alias: str) -> bool:
        """Remove credentials for an account alias"""
        async with self._lock:
            if alias in self._credentials:
                del self._credentials[alias]
                self.logger.info(f"Removed credentials for account '{alias}' from memory")
                
                # In dev mode, also update persisted storage
                if self._dev_mode:
                    await self._save_dev_credentials()
                return True
            return False
    
    async def has_credentials(self, alias: str) -> bool:
        """Check if credentials exist for an account alias"""
        # Ensure dev credentials are loaded if in dev mode
        await self._ensure_dev_initialized()
        
        async with self._lock:
            return alias in self._credentials
    
    async def list_accounts_with_credentials(self) -> list[str]:
        """List all account aliases that have credentials stored"""
        # Ensure dev credentials are loaded if in dev mode
        await self._ensure_dev_initialized()
        
        async with self._lock:
            return list(self._credentials.keys())
    
    async def clear_all(self) -> None:
        """Clear all credentials from memory (and dev storage if in dev mode)"""
        async with self._lock:
            count = len(self._credentials)
            self._credentials.clear()
            self.logger.info(f"Cleared {count} credentials from memory")
            
            # In dev mode, also clear persisted storage
            if self._dev_mode:
                await self._save_dev_credentials()
    
    def _is_dev_mode(self) -> bool:
        """Check if we're in development mode"""
        try:
            from infrastructure.config import get_config
            config = get_config()
            return config.debug or config.environment.lower() in ["development", "dev", "local"]
        except Exception:
            # Fallback to environment variables
            env = os.getenv("ENVIRONMENT", "development").lower()
            debug = os.getenv("DEBUG", "false").lower() in ["true", "1", "yes"]
            return debug or env in ["development", "dev", "local"]
    
    async def _ensure_dev_initialized(self) -> None:
        """Ensure dev credentials are loaded if in dev mode"""
        if not self._dev_mode or self._dev_initialized:
            return
            
        await self._load_dev_credentials()
        self._dev_initialized = True
    
    async def _save_dev_credentials(self) -> None:
        """Save credentials to dev storage (plain text for convenience)"""
        if not self._dev_mode:
            return
            
        try:
            # Convert credentials to serializable format
            data = {}
            for alias, creds in self._credentials.items():
                data[alias] = {
                    "access_key_id": creds.access_key_id,
                    "secret_access_key": creds.secret_access_key,
                    "session_token": creds.session_token,
                    "region": creds.region,
                    "profile": creds.profile
                }
            
            # Ensure directory exists
            self._dev_storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON data
            with open(self._dev_storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Set restrictive permissions (owner only)
            os.chmod(self._dev_storage_path, 0o600)
            
            self.logger.debug(f"Saved {len(data)} credentials to dev storage")
            
        except Exception as e:
            self.logger.error(f"Failed to save dev credentials: {e}")
    
    async def _load_dev_credentials(self) -> None:
        """Load credentials from dev storage"""
        if not self._dev_mode or not self._dev_storage_path.exists():
            return
            
        try:
            # Read JSON data
            with open(self._dev_storage_path, 'r') as f:
                data = json.load(f)
            
            # Load credentials
            for alias, cred_data in data.items():
                credentials = AWSCredentials(
                    access_key_id=cred_data.get("access_key_id"),
                    secret_access_key=cred_data.get("secret_access_key"),
                    session_token=cred_data.get("session_token"),
                    region=cred_data.get("region", "us-east-1"),
                    profile=cred_data.get("profile")
                )
                self._credentials[alias] = credentials
            
            self.logger.info(f"Loaded {len(data)} credentials from dev storage")
            
        except Exception as e:
            self.logger.warning(f"Failed to load dev credentials (will start fresh): {e}")
            # Don't raise exception - just start with empty credentials


# Global instance
_credential_manager = None


def get_credential_manager() -> InMemoryCredentialManager:
    """Get the global credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = InMemoryCredentialManager()
    return _credential_manager 