"""Configuration management using pydantic-settings."""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql://streamdata:streamdata_password@localhost:5432/streaming_platform"
    
    # Twitch API (optional - not needed for Kick-only deployment)
    twitch_client_id: Optional[str] = None
    twitch_client_secret: Optional[str] = None
    
    # Kick API
    kick_client_id: Optional[str] = None
    kick_client_secret: Optional[str] = None

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Collector Settings
    collection_interval_minutes: int = 2
    max_streams_per_collection: int = 100
    
    # Retry Settings
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
