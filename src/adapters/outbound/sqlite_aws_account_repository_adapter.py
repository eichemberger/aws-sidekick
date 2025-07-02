import asyncio
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from core.ports.outbound.aws_account_repository_port import AWSAccountRepositoryPort
from core.domain.entities.aws_account import AWSAccount
from core.domain.entities.aws_account_metadata import AWSAccountMetadata
from infrastructure.logging import get_logger


class SQLiteAWSAccountRepositoryAdapter(AWSAccountRepositoryPort):
    """
    SQLite AWS account repository adapter for local persistence.
    
    SECURITY: This adapter ONLY stores account metadata.
    AWS credentials are NEVER persisted to disk - they are stored
    securely in memory only via the InMemoryCredentialManager.
    """

    def __init__(self, db_path: str = "data/aws_accounts.db"):
        self.db_path = Path(db_path)
        self.logger = get_logger(__name__)
        self._lock = asyncio.Lock()
        
        # Ensure the data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize the database on first use
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database is initialized with proper schema"""
        if self._initialized:
            return
            
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Create secure table structure (NO credentials stored)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS aws_account_metadata (
                        alias TEXT PRIMARY KEY,
                        account_id TEXT,
                        description TEXT,
                        region TEXT DEFAULT 'us-east-1',
                        uses_profile INTEGER DEFAULT 0,
                        is_default INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Create index for finding default account
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_aws_account_metadata_default 
                    ON aws_account_metadata (is_default)
                """)
                
                await db.commit()
                
                # Verify the table was created
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='aws_account_metadata'"
                )
                result = await cursor.fetchone()
                await cursor.close()
                
                if result:
                    self.logger.info(f"AWS account metadata database initialized at {self.db_path}")
                    self.logger.info("SECURITY: Credentials are NEVER stored in database - only in memory")
                else:
                    raise RuntimeError("Failed to create aws_account_metadata table")
                
            self._initialized = True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS account database at {self.db_path}: {e}")
            self.logger.error("Database initialization failed - this will cause account operations to fail")
            # Don't set _initialized to True if there was an error
            raise RuntimeError(f"Database initialization failed: {e}")

    def _metadata_to_dict(self, metadata: AWSAccountMetadata) -> dict:
        """Convert AWSAccountMetadata entity to dictionary for database storage"""
        return {
            'alias': metadata.alias,
            'account_id': metadata.account_id,
            'description': metadata.description,
            'region': metadata.region,
            'uses_profile': 1 if metadata.uses_profile else 0,
            'is_default': 1 if metadata.is_default else 0,
            'created_at': metadata.created_at.isoformat() if metadata.created_at else datetime.utcnow().isoformat(),
            'updated_at': metadata.updated_at.isoformat() if metadata.updated_at else datetime.utcnow().isoformat()
        }

    def _dict_to_metadata(self, row: dict) -> AWSAccountMetadata:
        """Convert database row to AWSAccountMetadata entity"""
        return AWSAccountMetadata(
            alias=row['alias'],
            account_id=row['account_id'],
            description=row['description'],
            region=row.get('region', 'us-east-1'),
            uses_profile=bool(row.get('uses_profile', 0)),
            is_default=bool(row['is_default']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    async def _create_account_from_metadata(self, metadata: AWSAccountMetadata) -> AWSAccount:
        """Create AWSAccount entity from metadata and attempt to load credentials from memory"""
        account = AWSAccount(metadata=metadata)
        # Try to load credentials from memory
        credentials_loaded = await account.load_credentials()
        if credentials_loaded:
            self.logger.debug(f"Loaded credentials for account '{metadata.alias}' from memory")
        else:
            self.logger.warning(f"No credentials found in memory for account '{metadata.alias}' - user will need to re-enter them")
        return account

    async def save_account(self, account: AWSAccount) -> AWSAccount:
        """
        Save an AWS account (metadata only - credentials stored separately in memory)
        """
        try:
            await self._ensure_initialized()
            
            # Store credentials in memory (never in database)
            await account.store_credentials()
            
            # Store only metadata in database
            metadata_dict = self._metadata_to_dict(account.metadata)
            
            async with self._lock:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("""
                        INSERT OR REPLACE INTO aws_account_metadata 
                        (alias, account_id, description, region, uses_profile, is_default, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metadata_dict['alias'], metadata_dict['account_id'], 
                        metadata_dict['description'], metadata_dict['region'],
                        metadata_dict['uses_profile'], metadata_dict['is_default'], 
                        metadata_dict['created_at'], metadata_dict['updated_at']
                    ))
                    await db.commit()
                
            self.logger.info(f"Saved AWS account metadata '{account.alias}' to database")
            self.logger.debug(f"Credentials for '{account.alias}' stored securely in memory only")
            return account
        except Exception as e:
            self.logger.error(f"Error saving AWS account: {e} | alias: {account.alias}")
            raise

    async def get_account_by_alias(self, alias: str) -> Optional[AWSAccount]:
        """Get an AWS account by alias (loads metadata from DB and credentials from memory)"""
        try:
            await self._ensure_initialized()
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM aws_account_metadata WHERE alias = ?", (alias,)
                )
                row = await cursor.fetchone()
                await cursor.close()
                    
            if row:
                try:
                    metadata = self._dict_to_metadata(dict(row))
                    account = await self._create_account_from_metadata(metadata)
                    self.logger.debug(f"Retrieved AWS account '{alias}' from database")
                    return account
                except Exception as e:
                    self.logger.error(f"Error converting row to account: {e} | alias: {alias}")
                    return None
                    
            self.logger.debug(f"AWS account '{alias}' not found in database")
            return None
        except Exception as e:
            self.logger.error(f"Error in get_account_by_alias: {e} | alias: {alias}")
            return None

    async def list_accounts(self) -> List[AWSAccount]:
        """List all AWS accounts (loads metadata from DB and credentials from memory)"""
        try:
            await self._ensure_initialized()
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM aws_account_metadata ORDER BY is_default DESC, created_at ASC"
                )
                rows = await cursor.fetchall()
                await cursor.close()
                    
            accounts = []
            for row in rows:
                try:
                    metadata = self._dict_to_metadata(dict(row))
                    account = await self._create_account_from_metadata(metadata)
                    accounts.append(account)
                except Exception as e:
                    self.logger.error(f"Error converting row to account: {e} | row: {dict(row)}")
                    continue
                    
            self.logger.debug(f"Retrieved {len(accounts)} AWS accounts from database")
            return accounts
        except Exception as e:
            self.logger.error(f"Error in list_accounts: {e}")
            return []

    async def delete_account(self, alias: str) -> bool:
        """Delete an AWS account by alias (removes both metadata and credentials)"""
        try:
            await self._ensure_initialized()
            
            # Remove credentials from memory
            from infrastructure.credential_manager import get_credential_manager
            credential_manager = get_credential_manager()
            await credential_manager.remove_credentials(alias)
            
            # Remove metadata from database
            async with self._lock:
                async with aiosqlite.connect(self.db_path) as db:
                    cursor = await db.execute("DELETE FROM aws_account_metadata WHERE alias = ?", (alias,))
                    await db.commit()
                    deleted = cursor.rowcount > 0
                    
            if deleted:
                self.logger.info(f"Deleted AWS account '{alias}' metadata from database and credentials from memory")
            else:
                self.logger.debug(f"AWS account '{alias}' was not found for deletion")
                
            return deleted
        except Exception as e:
            self.logger.error(f"Error deleting AWS account: {e} | alias: {alias}")
            return False

    async def get_default_account(self) -> Optional[AWSAccount]:
        """Get the default AWS account"""
        try:
            await self._ensure_initialized()
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM aws_account_metadata WHERE is_default = 1 LIMIT 1"
                )
                row = await cursor.fetchone()
                await cursor.close()
                    
            if row:
                try:
                    metadata = self._dict_to_metadata(dict(row))
                    account = await self._create_account_from_metadata(metadata)
                    self.logger.debug("Retrieved default AWS account from database")
                    return account
                except Exception as e:
                    self.logger.error(f"Error converting default account row: {e}")
                    return None
                    
            self.logger.debug("No default AWS account found in database")
            return None
        except Exception as e:
            self.logger.error(f"Error in get_default_account: {e}")
            return None

    async def set_default_account(self, alias: str) -> bool:
        """Set the default AWS account by alias"""
        try:
            await self._ensure_initialized()
            
            async with self._lock:
                async with aiosqlite.connect(self.db_path) as db:
                    # First, clear all default flags
                    await db.execute("UPDATE aws_account_metadata SET is_default = 0")
                    
                    # Then set the specified account as default
                    cursor = await db.execute(
                        "UPDATE aws_account_metadata SET is_default = 1 WHERE alias = ?", (alias,)
                    )
                    await db.commit()
                    
                    updated = cursor.rowcount > 0
                    
            if updated:
                self.logger.info(f"Set AWS account '{alias}' as default")
            else:
                self.logger.debug(f"AWS account '{alias}' not found for setting as default")
                
            return updated
        except Exception as e:
            self.logger.error(f"Error setting default account: {e} | alias: {alias}")
            return False

    async def account_exists(self, alias: str) -> bool:
        """Check if an AWS account with the given alias exists"""
        try:
            await self._ensure_initialized()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT 1 FROM aws_account_metadata WHERE alias = ? LIMIT 1", (alias,)
                )
                row = await cursor.fetchone()
                await cursor.close()
                    
            exists = row is not None
            self.logger.debug(f"AWS account '{alias}' exists: {exists}")
            return exists
        except Exception as e:
            self.logger.error(f"Error checking if account exists: {e} | alias: {alias}")
            return False 