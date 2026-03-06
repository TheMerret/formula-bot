"""Database repository for user operations."""

import logging
from pathlib import Path
from typing import Optional

import aiosqlite

from .models import User, CREATE_USERS_TABLE

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user database operations."""
    
    def __init__(self, db_path: Path):
        """
        Initialize the user repository.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
    
    async def init_db(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_USERS_TABLE)
            await db.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    async def user_exists(self, user_id: int) -> bool:
        """
        Check if a user exists in the database.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user exists, False otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id FROM users WHERE id = ?", (user_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result is not None
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            User object if found, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, username, first_name, last_name FROM users WHERE id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        id=row[0],
                        username=row[1],
                        first_name=row[2],
                        last_name=row[3]
                    )
                return None
    
    async def create_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """
        Create a new user in the database.
        
        Args:
            user_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            
        Returns:
            Created User object
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO users (id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, username, first_name, last_name)
            )
            await db.commit()
        
        logger.info(f"User {user_id} registered successfully")
        return User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
    
    async def get_all_users(self) -> list[User]:
        """
        Get all registered users.
        
        Returns:
            List of User objects
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, username, first_name, last_name FROM users"
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    User(
                        id=row[0],
                        username=row[1],
                        first_name=row[2],
                        last_name=row[3]
                    )
                    for row in rows
                ]