"""Application settings loaded from environment variables."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Telegram Bot Configuration
    bot_token: str
    
    # GigaChat API Configuration
    gigachat_key: str
    gigachat_scope: str = "GIGACHAT_API_PERS"
    gigachat_model: str = "GigaChat-Pro"
    
    # Database Configuration
    database_path: str = "users.db"
    
    # Logging Configuration
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def db_path(self) -> Path:
        """Get database path as Path object."""
        return Path(self.database_path)


# Global settings instance
settings = Settings()