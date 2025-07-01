"""
Migration helper to safely migrate from old insecure database format to new secure format.

This script handles the migration from storing credentials in the database
to storing only metadata in the database and credentials in memory.
"""
import asyncio
import aiosqlite
import json
from pathlib import Path
from typing import List, Dict, Any
from core.domain.value_objects.aws_credentials import AWSCredentials
from core.domain.entities.aws_account_metadata import AWSAccountMetadata
from infrastructure.logging import get_logger
from infrastructure.credential_manager import get_credential_manager


class DatabaseMigrationHelper:
    """Helper class to migrate from old insecure format to new secure format"""
    
    def __init__(self, db_path: str = "data/aws_accounts.db"):
        self.db_path = Path(db_path)
        self.logger = get_logger(__name__)
        
    async def check_old_format_exists(self) -> bool:
        """Check if the old insecure format exists"""
        if not self.db_path.exists():
            return False
            
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='aws_accounts'"
                )
                result = await cursor.fetchone()
                await cursor.close()
                return result is not None
        except Exception as e:
            self.logger.error(f"Error checking for old format: {e}")
            return False
    
    async def migrate_from_old_format(self) -> bool:
        """
        Migrate from the old insecure format to the new secure format.
        
        WARNING: This will display credentials in the console for manual backup.
        Users should manually re-enter credentials after migration.
        """
        if not await self.check_old_format_exists():
            self.logger.info("No old format detected, migration not needed")
            return True
            
        self.logger.warning("=" * 60)
        self.logger.warning("SECURITY MIGRATION DETECTED")
        self.logger.warning("=" * 60)
        self.logger.warning("Your existing database contains AWS credentials stored insecurely.")
        self.logger.warning("These credentials will be migrated to memory-only storage.")
        self.logger.warning("Please backup your credentials before proceeding.")
        self.logger.warning("=" * 60)
        
        try:
            # Read old format data
            old_accounts = await self._read_old_format()
            
            if not old_accounts:
                self.logger.info("No accounts found in old format")
                return True
            
            # Display credentials for manual backup
            self.logger.warning("PLEASE BACKUP THESE CREDENTIALS:")
            self.logger.warning("-" * 40)
            for account in old_accounts:
                self.logger.warning(f"Account: {account['alias']}")
                self.logger.warning(f"  Description: {account.get('description', 'N/A')}")
                self.logger.warning(f"  Region: {account.get('region', 'us-east-1')}")
                self.logger.warning(f"  Access Key ID: {account.get('access_key_id', 'N/A')}")
                self.logger.warning(f"  Secret Access Key: {account.get('secret_access_key', 'N/A')}")
                if account.get('session_token'):
                    self.logger.warning(f"  Session Token: {account['session_token']}")
                if account.get('profile'):
                    self.logger.warning(f"  Profile: {account['profile']}")
                self.logger.warning("-" * 40)
            
            # Create new format data (metadata only)
            await self._create_new_format(old_accounts)
            
            # Drop old table
            await self._drop_old_table()
            
            self.logger.warning("MIGRATION COMPLETE")
            self.logger.warning("Your credentials have been removed from the database.")
            self.logger.warning("Please re-register your accounts with credentials via the UI.")
            self.logger.warning("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return False
    
    async def _read_old_format(self) -> List[Dict[str, Any]]:
        """Read data from the old insecure format"""
        accounts = []
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM aws_accounts")
            rows = await cursor.fetchall()
            await cursor.close()
            
            for row in rows:
                row_dict = dict(row)
                
                # Parse credentials JSON
                try:
                    credentials_data = json.loads(row_dict['credentials_json'])
                    account_info = {
                        'alias': row_dict['alias'],
                        'account_id': row_dict['account_id'],
                        'description': row_dict['description'],
                        'is_default': bool(row_dict['is_default']),
                        'created_at': row_dict['created_at'],
                        'updated_at': row_dict['updated_at'],
                        'access_key_id': credentials_data.get('access_key_id'),
                        'secret_access_key': credentials_data.get('secret_access_key'),
                        'session_token': credentials_data.get('session_token'),
                        'region': credentials_data.get('region', 'us-east-1'),
                        'profile': credentials_data.get('profile'),
                    }
                    accounts.append(account_info)
                except Exception as e:
                    self.logger.error(f"Error parsing credentials for {row_dict['alias']}: {e}")
                    continue
        
        return accounts
    
    async def _create_new_format(self, old_accounts: List[Dict[str, Any]]) -> None:
        """Create metadata entries in the new secure format"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create new table
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
            
            # Insert metadata (NO credentials)
            for account in old_accounts:
                await db.execute("""
                    INSERT INTO aws_account_metadata 
                    (alias, account_id, description, region, uses_profile, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    account['alias'], 
                    account['account_id'],
                    account['description'],
                    account['region'],
                    1 if account.get('profile') else 0,
                    1 if account['is_default'] else 0,
                    account['created_at'],
                    account['updated_at']
                ))
            
            await db.commit()
    
    async def _drop_old_table(self) -> None:
        """Drop the old insecure table"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DROP TABLE IF EXISTS aws_accounts")
            await db.commit()
        
        self.logger.info("Dropped old insecure table 'aws_accounts'")


async def migrate_database_if_needed(db_path: str = "data/aws_accounts.db") -> bool:
    """
    Convenience function to migrate database if needed.
    
    Returns True if migration was successful or not needed.
    """
    migrator = DatabaseMigrationHelper(db_path)
    
    if await migrator.check_old_format_exists():
        return await migrator.migrate_from_old_format()
    
    return True  # No migration needed 