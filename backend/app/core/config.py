"""
Application configuration using Pydantic Settings

Loads configuration from environment variables.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via .env file or environment variables.
    """
    
    # Application
    APP_NAME: str = "KanVer API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str
    
    # JWT Settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    PASSWORD_MIN_LENGTH: int = 8
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    
    # Redis (optional)
    REDIS_URL: Optional[str] = None
    
    # Firebase (optional)
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
