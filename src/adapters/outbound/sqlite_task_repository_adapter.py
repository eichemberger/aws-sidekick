import asyncio
import json
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from core.ports.outbound.task_repository_port import TaskRepositoryPort
from core.domain.entities.task import Task, TaskStatus
from infrastructure.logging import get_logger


class SQLiteTaskRepositoryAdapter(TaskRepositoryPort):
    """SQLite task repository adapter for local persistence"""

    def __init__(self, db_path: str = "data/tasks.db"):
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
            
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    result TEXT,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            await db.commit()
            
        self.logger.info(
            "DATABASE | aws-sidekick.persistence | "
            f"database_path=<{self.db_path}> | SQLite database initialized"
        )
        self._initialized = True

    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """Convert Task entity to dictionary for database storage"""
        return {
            'id': task.id,
            'description': task.description,
            'status': task.status.value,
            'created_at': task.created_at.isoformat(),
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'result': task.result,
            'error_message': task.error_message,
            'metadata': json.dumps(task.metadata) if task.metadata else None
        }

    def _dict_to_task(self, row: Dict[str, Any]) -> Task:
        """Convert database row to Task entity"""
        return Task(
            id=row['id'],
            description=row['description'],
            status=TaskStatus(row['status']),
            created_at=datetime.fromisoformat(row['created_at']),
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            result=row['result'],
            error_message=row['error_message'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )

    async def save_task(self, task: Task) -> Task:
        """Save a task to the database"""
        try:
            await self._ensure_initialized()
            
            task_dict = self._task_to_dict(task)
            
            # Simplified without lock for debugging
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO tasks 
                    (id, description, status, created_at, completed_at, result, error_message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_dict['id'], task_dict['description'], task_dict['status'], 
                    task_dict['created_at'], task_dict['completed_at'],
                    task_dict['result'], task_dict['error_message'], task_dict['metadata']
                ))
                await db.commit()
                
            self.logger.info(
                "DATABASE | aws-sidekick.persistence | "
                f"task_id=<{task.id}> status=<{task.status.value}> | Task saved to database"
            )
            return task
        except Exception as e:
            self.logger.error(f"Error saving task: {e} | task_id: {task.id}")
            raise

    async def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by ID from the database"""
        try:
            await self._ensure_initialized()
            
            # Simplified without lock for debugging
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
                row = await cursor.fetchone()
                await cursor.close()
                    
            if row:
                try:
                    task = self._dict_to_task(dict(row))
                    self.logger.info(
                        "DATABASE | aws-sidekick.persistence | "
                        f"task_id=<{task_id}> | Task retrieved from database"
                    )
                    return task
                except Exception as e:
                    self.logger.error(f"Error converting row to task: {e} | task_id: {task_id}")
                    return None
                    
            self.logger.info(
                "DATABASE | aws-sidekick.persistence | "
                f"task_id=<{task_id}> | Task not found in database"
            )
            return None
        except Exception as e:
            self.logger.error(f"Error in get_task_by_id: {e} | task_id: {task_id}")
            return None

    async def get_tasks(self, limit: int = 100, offset: int = 0) -> List[Task]:
        """Get list of tasks with pagination"""
        try:
            await self._ensure_initialized()
            
            # Simplified without lock for debugging
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )
                rows = await cursor.fetchall()
                await cursor.close()
                    
            tasks = []
            for row in rows:
                try:
                    task = self._dict_to_task(dict(row))
                    tasks.append(task)
                except Exception as e:
                    self.logger.error(f"Error converting row to task: {e} | row: {dict(row)}")
                    continue
                    
            self.logger.info(
                "DATABASE | aws-sidekick.persistence | "
                f"limit=<{limit}> offset=<{offset}> count=<{len(tasks)}> | Tasks retrieved from database"
            )
            return tasks
        except Exception as e:
            self.logger.error(f"Error in get_tasks: {e}")
            return []

    async def update_task(self, task: Task) -> Task:
        """Update an existing task"""
        try:
            await self._ensure_initialized()
            
            # Just save the task directly - no need to check if it exists
            return await self.save_task(task)
        except Exception as e:
            self.logger.error(f"Error updating task: {e} | task_id: {task.id}")
            raise

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task from the database"""
        await self._ensure_initialized()
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                await db.commit()
                deleted = cursor.rowcount > 0
                
            if deleted:
                self.logger.info(
                    "DATABASE | aws-sidekick.persistence | "
                    f"task_id=<{task_id}> | Task deleted from database"
                )
            else:
                self.logger.debug(
                    "DATABASE | aws-sidekick.persistence | "
                    f"task_id=<{task_id}> | Task not found for deletion"
                )
                
            return deleted

    async def clear_all_tasks(self) -> None:
        """Clear all tasks from the database (useful for testing)"""
        await self._ensure_initialized()
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM tasks")
                await db.commit()
                
            self.logger.info(
                "DATABASE | aws-sidekick.persistence | "
                "All tasks cleared from database"
            )

    async def get_task_count(self) -> int:
        """Get total task count"""
        await self._ensure_initialized()
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT COUNT(*) FROM tasks") as cursor:
                    row = await cursor.fetchone()
                    count = row[0] if row else 0
                    
            self.logger.debug(
                "DATABASE | aws-sidekick.persistence | "
                f"count=<{count}> | Task count retrieved from database"
            )
            return count

    async def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks by status"""
        await self._ensure_initialized()
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC",
                    (status.value,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    
                tasks = [self._dict_to_task(dict(row)) for row in rows]
                self.logger.debug(
                    "DATABASE | aws-sidekick.persistence | "
                    f"status=<{status.value}> count=<{len(tasks)}> | Tasks by status retrieved from database"
                )
                return tasks

    # Removed get_tasks_by_type method - simplified task system 