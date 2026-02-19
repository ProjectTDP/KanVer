from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application configuration using Pydantic Settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str = ""  # Optional, defaults to DATABASE_URL

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Firebase
    FIREBASE_CREDENTIALS: str = "/app/firebase-credentials.json"

    # App
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Location
    MAX_SEARCH_RADIUS_KM: int = 10
    DEFAULT_SEARCH_RADIUS_KM: int = 5

    # Cooldown
    WHOLE_BLOOD_COOLDOWN_DAYS: int = 90
    APHERESIS_COOLDOWN_HOURS: int = 48

    # Timeout
    COMMITMENT_TIMEOUT_MINUTES: int = 60

    # Gamification
    HERO_POINTS_WHOLE_BLOOD: int = 50
    HERO_POINTS_APHERESIS: int = 100
    NO_SHOW_PENALTY: int = -10

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
