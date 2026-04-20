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

    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False  # Default to False for security

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
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Location
    MAX_SEARCH_RADIUS_KM: int = 100
    DEFAULT_SEARCH_RADIUS_KM: int = 100

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

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # requests per minute
    RATE_LIMIT_PERIOD_SECONDS: int = 60
    RATE_LIMIT_AUTH_REQUESTS: int = 10  # stricter for auth endpoints

    def __init__(self, **kwargs):
        """Initialize settings with security validation."""
        super().__init__(**kwargs)
        self._validate_security_settings()

    def _validate_security_settings(self) -> None:
        """
        Validate security-critical settings.

        Raises:
            ValueError: If security settings are invalid
        """
        # SECRET_KEY must be at least 32 characters
        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters for security. "
                f"Current length: {len(self.SECRET_KEY)}"
            )

        # DEBUG cannot be True in production
        if self.ENVIRONMENT == "production" and self.DEBUG:
            raise ValueError(
                "DEBUG cannot be True in production environment. "
                "Set DEBUG=False or ENVIRONMENT=development"
            )

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
