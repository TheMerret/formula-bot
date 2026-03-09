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
    
    # Search Configuration
    enable_search: bool = True
    search_max_results: int = 5
    search_cache_ttl: int = 86400  # 24 hours in seconds
    
    # RAG Configuration
    enable_rag: bool = True
    rag_source_urls: list[str] = [
        "https://raw.githubusercontent.com/hse-tex/hse-tex/refs/heads/master/course-1/mathematical-analysis/mathematical-analysis-exam-1.tex"
    ]
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 100
    rag_retrieval_k: int = 3  # Number of chunks to retrieve per query
    
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