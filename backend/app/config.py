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
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    PASSWORD_MIN_LENGTH: int = 8
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    
    # Location Settings
    MAX_SEARCH_RADIUS_KM: int = 10
    DEFAULT_SEARCH_RADIUS_KM: int = 5
    
    # Cooldown Settings
    WHOLE_BLOOD_COOLDOWN_DAYS: int = 90
    APHERESIS_COOLDOWN_HOURS: int = 48
    
    # Timeout Settings
    COMMITMENT_TIMEOUT_MINUTES: int = 60
    
    # Gamification Settings
    HERO_POINTS_WHOLE_BLOOD: int = 50
    HERO_POINTS_APHERESIS: int = 100
    NO_SHOW_PENALTY: int = -10
    
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
