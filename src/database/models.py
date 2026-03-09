"""Database models and schema definitions."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """User model representing a registered bot user."""
    
    id: int  # Telegram user ID
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of the user."""
        name_parts = []
        if self.first_name:
            name_parts.append(self.first_name)
        if self.last_name:
            name_parts.append(self.last_name)
        
        if name_parts:
            return " ".join(name_parts)
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User {self.id}"


# SQL schema for users table
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# SQL schema for search cache table
CREATE_SEARCH_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formula_normalized TEXT NOT NULL UNIQUE,
    search_query TEXT NOT NULL,
    results TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_formula_normalized ON search_cache(formula_normalized);
CREATE INDEX IF NOT EXISTS idx_expires_at ON search_cache(expires_at);
"""