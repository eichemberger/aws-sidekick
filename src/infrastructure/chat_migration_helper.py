import aiosqlite
from infrastructure.logging import get_logger

logger = get_logger(__name__)

async def migrate_chat_database_if_needed(db_path: str) -> bool:
    """
    Migrate chat database from account_alias to account_id.
    
    Returns True if migration was successful or not needed, False if failed.
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            # Check if we need to migrate
            cursor = await db.execute("PRAGMA table_info(conversations)")
            columns = await cursor.fetchall()
            
            # Check if account_alias column exists
            has_account_alias = any(col[1] == 'account_alias' for col in columns)
            has_account_id = any(col[1] == 'account_id' for col in columns)
            
            if has_account_alias and not has_account_id:
                logger.info("Migrating chat database from account_alias to account_id")
                
                # Add account_id column
                await db.execute("ALTER TABLE conversations ADD COLUMN account_id TEXT")
                
                # Copy data from account_alias to account_id (for now, they'll be the same)
                await db.execute("UPDATE conversations SET account_id = account_alias")
                
                # Make account_id NOT NULL
                await db.execute("""
                    CREATE TABLE conversations_new (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        account_id TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    )
                """)
                
                # Copy data to new table
                await db.execute("""
                    INSERT INTO conversations_new (id, title, account_id, created_at, updated_at)
                    SELECT id, title, account_id, created_at, updated_at FROM conversations
                """)
                
                # Drop old table and rename new one
                await db.execute("DROP TABLE conversations")
                await db.execute("ALTER TABLE conversations_new RENAME TO conversations")
                
                await db.commit()
                logger.info("Chat database migration completed successfully")
                
            elif has_account_id:
                logger.info("Chat database already migrated to account_id")
            else:
                logger.info("Chat database is new, no migration needed")
                
        return True
        
    except Exception as e:
        logger.error(f"Chat database migration failed: {e}")
        return False 